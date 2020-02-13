#!/usr/bin/env python3
# Requires PyAudio
from ServerKeys import apikey, url

from ibm_watson import TextToSpeechV1
from ibm_watson.websocket import SynthesizeCallback
import pyaudio
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

authenticator = IAMAuthenticator(apikey)
service = TextToSpeechV1(authenticator=authenticator)
service.set_service_url(url)

class Play(object):
    """
    Wrapper to play the audio in a blocking mode
    """
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

test_callback = MySynthesizeCallback()

my_text = "This is a test of the IBM  Watson text-to-speech"

service.synthesize_using_websocket(my_text,
                                   test_callback,
                                   accept='audio/wav',
                                   voice="en-US_AllisonVoice"
                                  )