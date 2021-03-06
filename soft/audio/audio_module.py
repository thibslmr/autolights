#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
@author: thibaud
"""
import logging
import alsaaudio
import numpy as np
from threading import Thread
from tools.listeners import Listeners

# Constant :
_SAMPLES_PER_FRAME = 1024


# This class provide a thread for the audio module
class AudioModule(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.terminated = False  # Stop flag
        self.listeners = Listeners()  # Create the listeners list of functions to call on update

        # Open the soundCard in normal (blocking) mode, chanel 2 for mic
        self.input = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NORMAL, 'hw:1')

        # Set attributes
        self.input.setchannels(1)                           # Mono
        self.input.setrate(44100)                           # 44100 Hz
        self.input.setformat(alsaaudio.PCM_FORMAT_S16_LE)   # 8 bits
        # Set the number of frames per second
        self.input.setperiodsize(_SAMPLES_PER_FRAME)        # Set samples per frame

    # Thread recording audio in
    def run(self):
        logging.info("Starting audio_record thread")
        # This loop condition have to be checked frequently, so the code inside may not be blocking
        while not self.terminated:
            # Read data from device
            l, data = self.input.read()
            if l == _SAMPLES_PER_FRAME:
                self.listeners.notify_event(np.fromstring(data, np.int16))

    # Method called to stop the thread
    def stop(self):
        self.terminated = True
