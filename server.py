#!/usr/bin/env python3
# Requires PyAudio, wolframalpha, cryptography

from ServerKeys import apikey, url, app_id

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

class Play(object):
    # Wrapper to play the audio in a blocking mode
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
        #print('Opening stream to play')
        self.play.start_streaming()

    def on_error(self, error):
    	pass
        #print('Error received: {}'.format(error))

    def on_timing_information(self, timing_information):
    	pass
        #print(timing_information)

    def on_audio_stream(self, audio_stream):
        self.play.write_stream(audio_stream)

    def on_close(self):
        #print('Completed synthesizing')
        self.play.complete_playing()

test_callback = MySynthesizeCallback()

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

	service.synthesize_using_websocket(query_str, test_callback, accept='audio/wav', voice="en-US_AllisonVoice")

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