#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  watson_text_talker.py
#
#  Copyright 2018 Jeff Greenberg
#
#  MIT License
#
#  Text-to-Speech Interface using IBM's Watson Cloud based Text to Speech
#

# pip install watson-developer-cloud
from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ServerKeys import *

# pip install pygame
import pygame

# pip install python-slugify
from slugify import slugify

import os, time

from random import randrange

class TT_Config:

    # Username & Password combination not in use anymore
    API_KEY = apikey
    API_URL = url

    TTS_VOICE = 'en-US_AllisonVoice'
    TTS_ACCEPT = 'audio/mp3'

    CACHE_DIRECTORY = 'voice_mp3s'

    # when True cache direcory will be relative to the current working directory
    # if False then cache directory should be fully pathed
    CACHE_DIRECTORY_IS_RELATIVE = True

    VOICE_FILE_EXTENSION = 'mp3'

    # some environments may require a delay if first speech is cut off
    # generally 1, 2 or 3 seconds will work
    INITIALIZATION_DELAY = 0


class TT_Importance:
    SAY_ALWAYS = 1
    SAY_90_PERCENT = 2
    SAY_80_PERCENT = 3
    SAY_70_PERCENT = 4
    SAY_60_PERCENT = 5
    SAY_50_PERCENT = 6
    SAY_40_PERCENT = 7
    SAY_30_PERCENT = 8
    SAY_20_PERCENT = 9
    SAY_10_PERCENT = 10
    SAY_NEVER = 11


class TextTalker:
    config = None
    text_to_speech = None
    cache_directory = ""
    quiet_level = 0 # + is quieter, - is talkier, 0 is nuetral
    # main routine will say text presented
    # text should be < 255 characters

    def say(self, text):

        voice_filename_pathed = self.pre_store(text)

        # test if pre_store failed

        if voice_filename_pathed == "":
            return False

        # speak it using the returned filepath
        self.speak_from_file(voice_filename_pathed)

        return True

    def say_group(self, text_tuples):

        importance = 0 # first in tuple
        text = 1 # second in tuple

        for text_tuple in text_tuples:
            if self.should_say(text_tuple[importance]):
                self.say(text_tuple[text])

    # returns a boolean based on the importance factor
    def should_say(self, importance):

        if importance == TT_Importance.SAY_ALWAYS:
            return True

        percent = 100 - ((importance+self.quiet_level-1)*10)
        rand = randrange(100)

        # print(rand, percent) 
        return rand < percent

    # if the speech file exists return it's filepath
    # else write a new speech file and return it's filepath

    def pre_store(self, text):
        voice_file_name = slugify(text)

        if len(voice_file_name) > 255:
            print("we have an issue: text is tooo long")
            return ""

        voice_filename_pathed = self.cache_directory+'/'+voice_file_name+'.'+self.config.VOICE_FILE_EXTENSION

        if os.path.isfile(voice_filename_pathed):
            # print("speech from file")
            return voice_filename_pathed

        try:
            speech_data = self.text_to_speech.synthesize(text, accept=self.config.TTS_ACCEPT, voice=self.config.TTS_VOICE).result.content
        except:
            print("text to speech failed - check credentials")
            return ""

        self.write_voice_file(speech_data, voice_filename_pathed)
        # print("NEW speech: ", voice_file_name)

        return voice_filename_pathed

    def speak_from_file(self, voice_filename_pathed, wait = True):
        pygame.mixer.music.load(voice_filename_pathed)
        if wait:
            pygame.mixer.music.set_endevent(pygame.USEREVENT)
            pygame.event.set_allowed(pygame.USEREVENT)
        pygame.mixer.music.play()
        if wait:
            pygame.event.wait()

    def write_voice_file(self, speech_data, voice_filename_pathed):
        with open(voice_filename_pathed,'wb') as audio_file:
            audio_file.write(speech_data)

    def init_cache_directory(self):
        self.cache_directory = self.config.CACHE_DIRECTORY
        if self.config.CACHE_DIRECTORY_IS_RELATIVE:
            self.cache_directory = os.path.join(os.getcwd(), self.cache_directory)
        if not os.path.exists(self.cache_directory):
            os.makedirs(self.cache_directory)

    def init_watson_tts(self):
        authenticator = IAMAuthenticator(self.config.API_KEY)
        self.text_to_speech = TextToSpeechV1(authenticator=authenticator)
        self.text_to_speech.set_service_url(self.config.API_URL)
    # watson tts credentials for username & password
    # OR optionally use TT_Config which should have the credentials assigned, within
    
    def __init__(self, api_key=None, config=None):

        if config == None:
            self.config = TT_Config()
        else:
            self.config = config
        if api_key != None:
            self.config.API_KEY = api_key

        self.init_watson_tts()
        self.init_cache_directory()
        time.sleep(self.config.INITIALIZATION_DELAY)

        pygame.init()
        pygame.mixer.init()

