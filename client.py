#!/usr/bin/env python3

import pickle
import socket
from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener
import time
import argparse

#parse arguments and assign to appropriate variables
parser = argparse.ArgumentParser(description='client arguments')

parser.add_argument("-sip", default="192.168.0.1", type=str, help="Server IP address")
parser.add_argument("-sp", default=0, type=int, help="Server Port")
parser.add_argument("-z", default=1024, type=int, help="Size of the socket")

args = parser.parse_args()

host = args.sip
port = args.sp
size = args.z

#twitter stream
#Tweepy twitter stream code is from https://pythonprogramming.net/twitter-api-streaming-tweets-python-tutorial/

ckey = 'l69tgvNwIhLdWYzcV4QelcABL'
csecret = 'uWWBVX6WxQlgtKcsSLsIAa7T53iLyFhDZGodFRzvffFivJdasD'
atoken = '1228080512138403840-g767vEpHgGndUS5hDzC0KsZogUDHMU'
asecret = 'I0gEVmaFOSYoagUYwHhU5dEdIKRyKpKgDMShgs710S7Gk'

class listener(StreamListener):
    
    def on_data(self, data):
        try:
            tweet = data.split(',"text":"')[1].split('","source')[0]
            tweet = tweet.split('\"')[1]
            print("Question Received:", tweet)
            
            #now need to turn into tuple and encrypt before pickle
            
            # qPayload = {
            # "Encrypt/Decrypt Key",
            # "Encrypted Question text",
            # "MD5 hash of encrypted question text"
            # }

            
#             #pickling time
#             qPayload = {
#                 key,
#                 encrypted_q,
#                 md5hash
#             }
# 
#             with open('qPayload.pickle', 'wb') as f:
#                 # Pickle the 'qPayload' tuple using the highest protocol available.
#                 pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
#             #end of pickling
# 
#             #simple client setup
#             s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#             s.connect((host,port))
#             s.send(b'Hello, world')
#             data = s.recv(size)
#             s.close()
#             print ('Received:', data)
#             #end of client talking to server
            
            
            return True
        except BaseException as e:
            print('failed on_data,', str(e))
            time.sleep(5)
    
    def on_error(self, status):
        print(status)
        
auth = OAuthHandler(ckey, csecret)
auth.set_access_token(atoken, asecret)
twitterStream = Stream(auth, listener())
twitterStream.filter(track=["#ECE4564T20"])

