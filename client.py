#!/usr/bin/env python3

from ClientKeys import apikeyWatson, urlWatson, twitterCKey, twitterCSecret, twitterAToken, twitterATokenSecret

from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener

import datetime
import argparse
import pickle
import socket
from cryptography.fernet import Fernet
import hashlib

# watson text to talk API library from https://github.com/ziligy/watson-text-talker (slightly modified to work for us)
from watson_text_talker import *

#twitter stream
#Tweepy twitter stream code is from https://pythonprogramming.net/twitter-api-streaming-tweets-python-tutorial/

class listener(StreamListener):

    def on_data(self, data):
        try:
            tweet = data.split(',"text":"')[1].split('","source')[0]
            tweet = str(tweet.split('\"')[1].split('?')[0])
            tweet = tweet + '?'
            print('[', datetime.datetime.now(), ' | Checkpoint 03] New Question:', tweet)

            #get encryption key and encrypt encoded question
            cryptKey = Fernet.generate_key()
            f = Fernet(cryptKey)
            qEncoded = tweet.encode()
            qEncrypted = f.encrypt(qEncoded)

            #get hash checksum of encrypted question
            md5Hash = hashlib.md5(qEncrypted).digest()

            print('[', datetime.datetime.now(), ' | Checkpoint 04] Encrypt: Generated Key: ', cryptKey, ' Cipher text: ', qEncrypted)

            qPayload = (
                cryptKey,
                qEncrypted,
                md5Hash
            )

            #pickling time
            qPayload = pickle.dumps(qPayload)

            #sending data
            print('[', datetime.datetime.now(), ' | Checkpoint 05] Sending data: ', qPayload)
            s.send(qPayload)

            #receiving data
            aPayload = s.recv(size)
            print('[', datetime.datetime.now(), ' | Checkpoint 06] Received data: ', aPayload)

            #unpickle
            aPayload = pickle.loads(aPayload)

            #verifying hash
            verify_hash = hashlib.md5(aPayload[0]).digest()

            if verify_hash != aPayload[1]:
                print('[', datetime.datetime.now(), '] Checksums do not match for answer!')

            #decrypt data
            aDecrypted = f.decrypt(aPayload[0])
            aDecoded = aDecrypted.decode()

            print('[', datetime.datetime.now(), ' | Checkpoint 07] Decrypt: Using Key: ', cryptKey, ' | Plain text: ', aDecoded)

            #IBM watson speaking the answer
            text_talker.say(aDecoded)
            
            print('[', datetime.datetime.now(), ' | Checkpoint 08] Speaking Answer: ', aDecoded)

            return True

        except BaseException as e:
            print('failed on_data,', str(e))
            time.sleep(5)

    def on_error(self, status):
        print(status)

#parse arguments and assign to appropriate variables
parser = argparse.ArgumentParser(description='client arguments')

parser.add_argument("-sip", default="192.168.0.1", type=str, help="Server IP address")
parser.add_argument("-sp", default=0, type=int, help="Server Port")
parser.add_argument("-z", default=1024, type=int, help="Size of the socket")

args = parser.parse_args()
host = args.sip
port = args.sp
size = args.z

#IBM watson setup
config = TT_Config()
config.API_KEY=apikeyWatson
config.API_URL=urlWatson
config.TTS_Voice = 'en-US_MichaelVoice'
config.CACHE_DIRECTORY = 'custom_cache'
config.INITIALIZATION_DELAY = 2

text_talker = TextTalker(config=config)

#connecting client to host server
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((host,port))
print('[', datetime.datetime.now(), ' | Checkpoint 01] Connecting to ', host, ' on port ', port)

#twitter action
auth = OAuthHandler(twitterCKey, twitterCSecret)
auth.set_access_token(twitterAToken, twitterATokenSecret)
twitterStream = Stream(auth, listener())
print('[', datetime.datetime.now(), ' | Checkpoint 02] Listening for tweets from Twitter API that contain questions.')
twitterStream.filter(track=["#ECE4564T20"])
s.close()