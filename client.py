#!/usr/bin/env python3

import pickle
import socket
from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener
import datetime
import argparse
import ClientKeys
from cryptography.fernet import Fernet
import hashlib

#parse arguments and assign to appropriate variables
parser = argparse.ArgumentParser(description='client arguments')

parser.add_argument("-sip", default="192.168.0.1", type=str, help="Server IP address")
parser.add_argument("-sp", default=0, type=int, help="Server Port")
parser.add_argument("-z", default=1024, type=int, help="Size of the socket")

args = parser.parse_args()

host = args.sip
port = args.sp
size = args.z

#connecting client to host server
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((host,port))
print('[', datetime.datetime.now(), '] Connecting to ', host, ' on port ', port)

#twitter stream
#Tweepy twitter stream code is from https://pythonprogramming.net/twitter-api-streaming-tweets-python-tutorial/

class listener(StreamListener):

    def on_data(self, data):
        try:
            tweet = data.split(',"text":"')[1].split('","source')[0]
            tweet = str(tweet.split('\"')[1])
            print('[', datetime.datetime.now(), '] New Question:', tweet)

            #get encryption key and encrypt encoded question
            cryptKey = Fernet.generate_key()
            f = Fernet(cryptKey)
            qEncoded = tweet.encode()
            qEncrypted = f.encrypt(qEncoded)

            #get hash checksum of encrypted question
            md5Hash = hashlib.md5(qEncrypted).digest()

            print('[', datetime.datetime.now(), '] Encrypt: Generated Key: ', cryptKey, ' Cipher text: ', qEncrypted)

            qPayload = (
                cryptKey,
                qEncrypted,
                md5Hash
            )

            #pickling time
            qPayload = pickle.dumps(qPayload)

            #sending data
            print('[', datetime.datetime.now(), '] Sending data: ', qPayload)
            s.send(qPayload)

            #receiving data
            aPayload = s.recv(size)
            print('[', datetime.datetime.now(), '] Received data: ', aPayload)

            #unpickle
            aPayload = pickle.loads(aPayload)

            #verifying hash
            verify_hash = hashlib.md5(aPayload[0]).digest()

            if verify_hash != aPayload[1]:
                print('[', datetime.datetime.now(), '] Checksums do not match for answer!')

            #decrypt data
            aDecrypted = f.decrypt(aPayload[0])
            aDecoded = aDecrypted.decode()

            print('[', datetime.datetime.now(), '] Decrypt: Using Key: ', cryptKey, ' | Plain text: ', aDecoded)

            #IBM watson speaking the answer

            return True

        except BaseException as e:
            print('failed on_data,', str(e))
            time.sleep(5)

    def on_error(self, status):
        print(status)

auth = OAuthHandler(ClientKeys.twitterCKey, ClientKeys.twitterCSecret)
auth.set_access_token(ClientKeys.twitterAToken, ClientKeys.twitterATokenSecret)
twitterStream = Stream(auth, listener())
print('[', datetime.datetime.now(), '] Listening for tweets from Twitter API that contain questions.')
twitterStream.filter(track=["#ECE4564T20"])
s.close()