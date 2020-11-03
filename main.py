import base64
import urllib3
import json as json1
import pprint
from twython import Twython, TwythonStreamer, TwythonError
import os
import tempfile

def hello_pubsub(event, context):
    """Triggered from a message on a Cloud Pub/Sub topic.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    #pubsub_message = base64.b64decode(event['data']).decode('utf-8')
    #print(pubsub_message)

   
    debug = 0
    do_tweet = 1
    seperator = "--------------------------------------------------------------"


    consumer_key = "____data___here_____"
    consumer_secret = "____data___here_____"
    access_token = "____data___here_____"
    access_token_secret = "____data___here_____"

    t = Twython(consumer_key,
        consumer_secret,
        access_token,
        access_token_secret)


    # TO DO need to make these environment variables
    client_id = "____data___here_____"
    client_secret = "____data___here_____"

    retries = urllib3.util.Retry(total=14, backoff_factor=0.2,status_forcelist=[500, 502, 503, 504])
    retries.method_whitelist = frozenset(['HEAD', 'TRACE', 'GET', 'PUT', 'OPTIONS', 'DELETE', 'POST'])
    retries.BACKOFF_MAX = 30
    http = urllib3.PoolManager(retries=retries)
    urllib3.disable_warnings()

    url = 'https://api.petfinder.com/v2/oauth2/token'

    r = http.request('POST', url, fields={'grant_type': 'client_credentials', 'client_id': client_id, 'client_secret': client_secret})
    json_data = json1.loads(r.data.decode('utf-8'))
    status_code = r.status

    if debug:
        print("Getting token from petfinger...")
        print("urllib3 Status Code: "+str(status_code))
        #print("urllib3 Message: "+json_data['message'])
        pprint.pprint(json_data)
        print(seperator)

    access_token = json_data['access_token']

    url = 'https://api.petfinder.com/v2/animals?type=dog&sort=random&limit=1&status=adoptable&location=80021&distance=100'

    hed = {'Authorization': 'Bearer ' + access_token}

    r = http.request('GET', url, headers=hed)
    j = json1.loads(r.data.decode('utf-8'))
    status_code = r.status
    if debug:
        print("Getting random dog...")
        print("urllib3 Status Code: "+str(status_code))
        pprint.pprint(j)
        print(seperator)

    d = j['animals'][0]

    url = 'https://api.petfinder.com/v2/organizations/'+d['organization_id']
    hed = {'Authorization': 'Bearer ' + access_token}
    r = http.request('GET', url, headers=hed)
    j = json1.loads(r.data.decode('utf-8'))
    status_code = r.status

    if debug:
        print("Getting organization info...")
        print("urllib3 Status Code: "+str(status_code))
        pprint.pprint(j)
        print(seperator)

    org_name = j['organization']['name']
    org_state = j['organization']['address']['state']

    if d['gender'] == "Female":
        pronoun = "She"
        describe = "She is"
    elif d['gender'] == "Male":
        pronoun = "He"
        describe = "He is"
    else:
        pronoun = "They"
        describe = "They are"

    txt = "This is "+d['name']+". "+describe+" a " + d['breeds']['primary'] + " from " + org_name + ". Adopt me: "+d['url']

    photo_count = len(d['photos'])

    if photo_count > 0:
        photo_url = d['photos'][0]['medium']

        if debug:
            print("Number of photos: "+str(photo_count))
            pprint.pprint(d['photos'])

        if debug:
            print("Getting photo...")
            print(photo_url)
            print(txt)
            print(seperator)


    if photo_count > 0:
        r = http.request('GET', photo_url, preload_content=False)

        # Credit: https://stackoverflow.com/questions/17285464/whats-the-best-way-to-download-file-using-urllib3

        with tempfile.TemporaryFile(mode='w+b') as fp:
            while True:
                data = r.read(65536)
                if not data:
                    break
                fp.write(data)

            r.release_conn()

            fp.seek(0)

            # Credit: https://stackoverflow.com/questions/27094275/how-to-post-image-to-twitter-with-twython
            # Doc: https://twython.readthedocs.io/en/latest/usage/advanced_usage.html
            try:  
                #img = open(out_file, 'rb')
                if do_tweet:
                    response = t.upload_media(media=fp)
                    t.update_status(status=txt, media_ids=[response['media_id']])
                    #t.update_status(status='test')
            except TwythonError as e:
                pprint.pprint(e)

    else:
        if do_tweet:
            t.update_status(status=txt, media_ids=[response['media_id']])
