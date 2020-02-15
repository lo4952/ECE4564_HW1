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
#Reuse authentication from ServerKeys sine I'm too lazy to make my own separate file.
from ServerKeys import apikey, url
#If necessary my own API key is below:
#hRO4rFm_4RC41TDlqF8Xa7D9nUg2VgJZ0yBuwXuDcjFY

from ibm_watson import TextToSpeechV1
from ibm_watson.websocket import SynthesizeCallback
import pyaudio
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

authenticator = IAMAuthenticator(apikey)
service = TextToSpeechV1(authenticator=authenticator)
service.set_service_url(url)

#watson related classes, courtesy of watson developer cloud
class Play(object):
    def __init__(self):
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 22050
        self.chunk = 1024
        self.pyaudio = None
        self.stream = None

    def start_streaming(self):
        self.pyaudio = pyaudio.PyAudio()
        self.stream = self._open_stream()
        self._start_stream()

    def _open_stream(self):
        stream = self.pyaudio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            output=True,
            frames_per_buffer=self.chunk,
            start=False
        )
        return stream

    def _start_stream(self):
        self.stream.start_stream()

    def write_stream(self, audio_stream):
        self.stream.write(audio_stream)

    def complete_playing(self):
        self.stream.stop_stream()
        self.stream.close()
        self.pyaudio.terminate()

class MySynthesizeCallback(SynthesizeCallback):
    def __init__(self):
        SynthesizeCallback.__init__(self)
        self.play = Play()

    def on_connected(self):
        print('Opening stream to play')
        self.play.start_streaming()

    def on_error(self, error):
        print('Error received: {}'.format(error))

    def on_timing_information(self, timing_information):
        print(timing_information)

    def on_audio_stream(self, audio_stream):
        self.play.write_stream(audio_stream)

    def on_close(self):
        print('Completed synthesizing')
        self.play.complete_playing()

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
            test_callback = MySynthesizeCallback()
            service.synthesize_using_websocket(aDecrypted,test_callback,accept='audio/wav',voice="en-US_AllisonVoice")


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