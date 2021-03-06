#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
@author: thibaud
"""
import logging
from threading import Thread
import time
from user_interface.config import parameters
from user_interface.config import models
import operator
import random

# Constants
BUFFER_SIZE = 200           # Number of frames to store in the buffer (200 -> 5s)
SAMPLE_PER_FRAME = 1024     # See audio module
SAMPLE_RATE = 44100         # See audio module


# This class provide a thread for the Manager module
class ManagerModule(Thread):
    def __init__(self, midi_module):
        Thread.__init__(self)
        self.terminated = False  # Stop flag
        self.midi_module = midi_module
        self.boolean_states = {}    # Boolean state dict
        self.continuous_states = {}     # Continuous state dict
        self.operators = {'<': operator.lt, '>': operator.gt, '=': operator.eq}
        self.chase_state = {}
        for category in parameters.BOOLEAN_PARAM:       # Populate dict
            for duo in category[1]:
                self.boolean_states[duo[0]] = True
        for duo in parameters.CONTINUOUS_PARAM:
            self.boolean_states[duo[0]] = 0
        self.last_beat_timestamp = 0
        self.beats = 0

    # Thread linking audio features to light features
    def run(self):
        logging.info("Starting Manager thread")
        # This loop condition have to be checked frequently, so the code inside may not be blocking
        while not self.terminated:
            # Synchro beat generator
            while self.last_beat_timestamp == 0:        # Wait for info from beat tracker
                time.sleep(0.02)
            self._beat()
            if len(self.beats) >= 2:                    # If data is usefull
                last = self.beats[0]
                for t in self.beats[1:]:
                    time.sleep(t-last)
                    last = t
                    self._beat()
                # Generate missing beats
                while time.time()+(self.beats[1]-self.beats[0]) < self.last_beat_timestamp + (BUFFER_SIZE*SAMPLE_PER_FRAME*SAMPLE_RATE):
                    time.sleep(self.beats[1]-self.beats[0])     # Last one
                    print("Rajout")
                    self._beat()
            self.last_beat_timestamp = 0

            # Write here non-blocking code (use timeout...)

    # Method called to stop the thread
    def stop(self):
        self.terminated = True

    def _continuous_change(self, continuous_id, value):
        active_config = models.Configuration.objects.filter(active=True)
        #  Continuous rule process
        for rule in models.ContinuousRule.objects.filter(continuous_param=continuous_id, config=active_config):
            if value < rule.scale_down:
                midi_value = 0
            elif value > rule.scale_up:
                midi_value = 127
            else:
                midi_value = int(127*(value-rule.scale_down)/(rule.scale_up - rule.scale_down))
            self.midi_module.control_change(rule.midi_cc, midi_value)

    def _event(self, event_id):
        active_config = models.Configuration.objects.filter(active=True)
        #  Standard rule process
        for rule in models.StandardRule.objects.filter(event_param=event_id, config=active_config):
            for condition in rule.standardrulecondition_set.all():
                if condition.bool_param:
                    if self.boolean_states[condition.bool_param] and not condition.bool_active_on_false: continue
                    if not self.boolean_states[condition.bool_param] and condition.bool_active_on_false: continue
                else:
                    if self.operators[condition.operator](condition.continuous_param, condition.value): continue
                return
            self.midi_module.note_on(rule.note)
        # Chase rule process
        for rule in models.ChaseRule.objects.filter(event_param=event_id, config=active_config):
            for condition in rule.chaserulecondition_set.all():
                if condition.bool_param:
                    if self.boolean_states[condition.bool_param] and not condition.bool_active_on_false: continue
                    if not self.boolean_states[condition.bool_param] and condition.bool_active_on_false: continue
                else:
                    if self.operators[condition.operator](condition.continuous_param, condition.value): continue
                return
            print(rule)
            self._next_chase_state(rule)

    def _next_chase_state(self, chase_rule):
        if chase_rule.id in self.chase_state:    # Chase is already active
            if chase_rule.objects.count() > self.boolean_states[chase_rule.id] + 1:
                state = chase_rule.objects.all()[(self.chase_state[chase_rule.id] + 1)].get()
            else:
                self.midi_module.note_off(chase_rule.chaserulestate_set.filter(id=self.chase_state[chase_rule.id]))
                del self.chase_state[chase_rule.id]
                return
        else:       # Chase not active
            if chase_rule.random_states:
                state = random.choice(chase_rule.chaserulestate_set.all())
            else:
                state = chase_rule.objects.all()[0].get()
        self.midi_module.note_off(chase_rule.chaserulestate_set.filter(id=self.chase_state[chase_rule.id]))
        self.chase_state[chase_rule.id] = state.id
        self.midi_module.note_on(state.note)

    def new_bpm(self, new_bpm):
        logging.info("New BPM : " + str(new_bpm))
        self._event(parameters.BPM_CHANGE_EVENT)
        self._continuous_change(parameters.BPM_CONTINUOUS, int(new_bpm))

    def drop(self):
        logging.info("Drop ! ")
        self._event(parameters.DROP_EVENT)

    def bass(self):
        logging.info("Bass ! ")
        self._event(parameters.BASS_EVENT)

    def sweep(self):
        logging.info("Sweep ! ")
        self._event(parameters.SWEEP_EVENT)

    def silence(self):
        logging.info("Silence ! ")
        self._event(parameters.SILENCE_EVENT)

    def bass_break(self):
        logging.info("Break ! ")
        self._event(parameters.SILENCE_EVENT)

    def new_gender(self, gender_id):
        logging.info("New gender : " + str(gender_id))
        #for duo in parameters.BOOLEAN_PARAM[0][1]:
        #    self.boolean_states[duo[0]] = False
        #self.boolean_states[gender_id] = True
        #self._event(parameters.GENDER_CHANGE_EVENT)

    def new_energy(self, new_energy):
        logging.debug("New energy : " + str(new_energy))
        self._continuous_change(parameters.RMS_POWER_CONTINUOUS, new_energy)

    def new_bass_energy(self, new_bass_energy):
        logging.debug("New bass energy : " + str(new_bass_energy))
        self._continuous_change(parameters.BASS_ENERGY_CONTINUOUS, new_bass_energy)

    def new_high_energy(self, new_high_energy):
        logging.debug("New high energy : " + str(new_high_energy))
        self._continuous_change(parameters.HIGH_ENERGY_CONTINUOUS, new_high_energy)

    def new_tuning(self, new_tuning):
        logging.debug("New tuning : " + str(new_tuning))
        self._continuous_change(parameters.TUNING_CONTINUOUS, new_tuning)

    def synchro(self, last_beat_timestamp, beats):
        self.last_beat_timestamp = last_beat_timestamp
        self.beats = beats

    def _beat(self):
        logging.info("Beat ! ")
        self._event(parameters.BEAT_EVENT)
