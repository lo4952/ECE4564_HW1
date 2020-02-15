#!/usr/bin/env python3
# Requires PyAudio, wolframalpha, cryptography, ibm_watson, watson_text_talker

# Using code from the watson_text_talker github project

from ServerKeys import *
from watson_text_talker import *

from ibm_watson import TextToSpeechV1
from ibm_watson.websocket import SynthesizeCallback
import sys, pyaudio, socket, wolframalpha, hashlib, cryptography, pickle, time
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from cryptography.fernet import Fernet

authenticator = IAMAuthenticator(apikey)
service = TextToSpeechV1(authenticator=authenticator)
service.set_service_url(url)

def get_answer(query_text):
	client = wolframalpha.Client(app_id)
	res = client.query(query_text)
	answer = next(res.results).text 
	return answer

config = TT_Config()
config.API_KEY=apikey
config.API_URL=url
config.TTS_Voice = 'en-US_MichaelVoice'
config.CACHE_DIRECTORY = 'custom_cache'
config.INITIALIZATION_DELAY = 2

text_talker = TextTalker(config=config)

def get_time():
	ts = time.gmtime()
	str_time = (time.strftime("%Y-%m-%d %H:%M:%S", ts))
	return str_time


TCP_IP = ''
TCP_PORT = int(sys.argv[2]) # get from command line
BUFFER_SIZE = int(sys.argv[4]) # get from command line

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

str_time = get_time()
print("[" + str_time + "] Created Socket at " + sys.argv[2] + " on port " + sys.argv[4])

s.bind((TCP_IP, TCP_PORT))
s.listen(1)

str_time = get_time()
print("[" + str_time + "] Listening for client connections")

conn, addr = s.accept()
while 1:
	pickle_tuple = conn.recv(BUFFER_SIZE)
	if not pickle_tuple: break
	
	str_time = get_time()
	print("[" + str_time + "] Accepted client connection from " + str(addr[0]) + " on port " + str(addr[1]))

	data_tuple = pickle.loads(pickle_tuple)

	str_time = get_time()
	print("[" + str_time + "] Recieved data: ", str(data_tuple[1]))

	verify_hash = hashlib.md5(data_tuple[1]).digest() # hash the encrypted question

	f = Fernet(data_tuple[0])
	query_text = f.decrypt(data_tuple[1]) # decrypted second element
	query_str = query_text.decode()

	str_time = get_time()
	print("[" + str_time + "] Decrypt: Key: " + str(data_tuple[0]) + "| Plain Text: " + query_str)

	str_time = get_time()
	print("[" + str_time + "] Speaking Question: ", query_str)

    text_talker.say(query_str)

	str_time = get_time()
	print("[" + str_time + "] Sending question to Wolframalpha: ", query_str)

	answer_text = get_answer(query_str)

	str_time = get_time()
	print("[" + str_time + "] Recieved answer from Wolframalpha: ", answer_text)

	answer_text = answer_text.encode() 
	encrypted_answer_text = f.encrypt(answer_text) 

	str_time = get_time()
	print("[" + str_time + "] Encrypt: Key: " + str(data_tuple[0]) + " | Ciphertext: " + str(encrypted_answer_text))

	answer_hash = hashlib.md5(encrypted_answer_text).digest()

	str_time = get_time()
	print("[" + str_time + "] Generated MD5 Checksum: ", answer_hash)

	answer_payload = (encrypted_answer_text, answer_hash)

	str_time = get_time()
	print("[" + str_time + "] Sending answer: ", answer_payload)

	answer_payload = pickle.dumps(answer_payload) # pickle outgoing tuple
	conn.send(answer_payload)  # send back answer
conn.close()