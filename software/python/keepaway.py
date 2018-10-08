import time
import logging as log
from enum import Enum
import random
from prox_event import ProxEvent
BREATH_STEP = 15
MOVE_STEP = 1
SIT_TIMEOUT = 10

class Mode(Enum):
    SITTING = 0
    MOVING = 1

class Keepaway:

    keepawayInstance = None

    def __init__(self, event, frequency, start=None):
        self.lights = [0] * 10
        self.run = True
        self.freq = 0.05
        self.last_tick = 0
        self.event = event
        self.frequency = frequency

        self.mode = Mode.SITTING
        self.pointer = self.event.address
        self.breath_level = 0
        self.breath_direction = 1
        self.new_pointer = 0
        self.offset = 0
        self.move_direction = 1
        self.started_sitting = time.time()

    def newTouch(self, event, start_time, frequency):
        log.info("KA got new event %s", event)
        self.event = event
        if self.event.address == self.pointer:
            log.info("MOVE!")

            self.new_pointer = (self.pointer - random.randrange(1, 6)) % 10
            self.mode = Mode.MOVING
            self.move_direction = -1 if self.new_pointer < self.pointer else 1
            self.breath_direction = -1
            self.breath_level = 255


    def __iter__(self):
        return self

    def __next__(self):

        while self.run:

            if time.time() - self.last_tick <= (1 / self.frequency):
                return
            else:
                
                if self.mode == Mode.SITTING:
                    # log.debug("Sitting at %s", self.pointer)
                    
                    self.breath_level += BREATH_STEP * self.breath_direction

                    if self.breath_level >= 255 or self.breath_level <= 0:
                        self.breath_direction *= -1
                    self.lights[self.pointer] = self.breath_level

                    if time.time() - self.started_sitting > SIT_TIMEOUT:
                        log.info("Keepaway timeout")
                        fake_event = ProxEvent(self.pointer)
                        self.newTouch(fake_event, round(time.time() * 20, 0) / 20, self.frequency)
                    

                elif self.mode == Mode.MOVING:
                    # log.debug("Moving from %s to %s", self.pointer, self.new_pointer)
                    self.pointer = (self.pointer + (MOVE_STEP * self.move_direction)) % 10
                    if abs(self.pointer - self.new_pointer) < MOVE_STEP:
                        self.pointer = self.new_pointer
                        self.mode = Mode.SITTING
                        self.started_sitting = time.time()

                    self.lights = [0] * 10
                    self.lights[self.pointer] = 255


                self.last_tick = time.time()
                return self.lights
        self.run = False
        raise StopIteration