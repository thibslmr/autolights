#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
@author: thibaud
"""
import logging
import sys
from manager import manager_interface

from audio.audio_module import AudioModule
from machine_learning.ml_module import MlModule
from manager.manager_module import ManagerModule
from midi.midi_module import MidiModule
from sys_expert.se_module import SeModule
from tools import log
from user_interface.web_server import WebServerModule
"""
This is the main script of the autolight project.
It start all threads and wait for the end.
"""

# Constants
WEB_SERVER = True
ML_MODULE = False
SE_MODULE = False
MIDI_MODULE = False
AUDIO_MODULE = False
MANAGER_MODULE = False


# Main function of the project
def main():
    # Start logging system
    log.config_logger()
    logging.info("##### Autolights is starting, hi ! #####")

    # Create modules
    logging.info("Building modules")
    manager = ManagerModule()
    audio_recorder = AudioModule()
    midi_generator = MidiModule()
    se = SeModule()
    ml = MlModule()
    server = WebServerModule()

    # Setup listeners
    logging.info("Setting up listeners")
    if AUDIO_MODULE:  audio_recorder.listeners += se.new_audio
    if ML_MODULE:     audio_recorder.listeners += ml.new_audio
    # Register Manager
    logging.info("Registering manager")
    if MANAGER_MODULE: manager_interface.init(manager)

    # Start threads
    logging.info("Starting threads")
    if AUDIO_MODULE: audio_recorder.start()
    if MIDI_MODULE: midi_generator.start()
    if SE_MODULE: se.start()
    if ML_MODULE: ml.start()
    if MANAGER_MODULE: manager.start()
    if WEB_SERVER: server.start()

    try:
        # Join all threads
        if WEB_SERVER:        server.join()
        if MANAGER_MODULE:    manager.join()
        if ML_MODULE:         ml.join()
        if SE_MODULE:         se.join()
        if MIDI_MODULE:       midi_generator.join()
        if AUDIO_MODULE:      audio_recorder.join()
    except KeyboardInterrupt:
        logging.info('Execution interrupted by user, stopping...')
        if WEB_SERVER:
            server.stop()  # Stop Server
            server.join()
        if MANAGER_MODULE:
            manager.stop()  # Stop Manager
            manager.join()
        if ML_MODULE:
            ml.stop()  # Stop ML
            ml.join()
        if SE_MODULE:
            se.stop()  # Stop SE
            se.join()
        if MIDI_MODULE:
            midi_generator.stop()  # Stop Midi
            midi_generator.join()
        if AUDIO_MODULE:
            audio_recorder.stop()  # Stop Audio
            audio_recorder.join()
        logging.info("##### All is stopped, bye #####")
        sys.exit(0)  # Finally, exit


# If main program, start main
if __name__ == "__main__":
    main()
