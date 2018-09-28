import time
import math
import logging as log
from collections import defaultdict

# def translate(value, leftMin, leftMax, rightMin, rightMax):
#     # Figure out how 'wide' each range is
#     leftSpan = leftMax - leftMin
#     rightSpan = rightMax - rightMin

#     # Convert the left range into a 0-1 range (float)
#     valueScaled = float(value - leftMin) / float(leftSpan)

#     # Convert the 0-1 range into a value in the right range.
#     return rightMin + (valueScaled * rightSpan)
TRIGGER_MAX = 0.5

class Ripple:

    def __init__(self, event):
        self.event = event
        self.lights = [0] * 10
        self.offset = 0
        self.last_tick = 0
        self.start = event.address
        self.ripple_time = 0.05

    def __iter__(self):
        return self

    def __next__(self):

        q = 1

        #      Positive offset limit                    Negative offset limit
        while (self.offset < (10 - self.start) + 1) or ((self.start - self.offset) + 2 > 0):

            # Set the ripple time based on the trigger duration from ProxEvent
            self.ripple_time = self.event.trigger_duration / 10

            if time.time() - self.last_tick < self.ripple_time:
                return
            else:
                # log.info("Event %s", self.event)
                # log.info("%s %s", self.ripple_time, self.event.trigger_duration)
                # log.debug("Start: %s Offset: %s", start, offset)
                
                # Calculate the upper and lower edge of the outward ripple
                lower_marker = self.start - self.offset;
                upper_marker = self.start + self.offset;

                # Set each light level according to their distance from
                # the upper or lower marker
                for light in range(0, 10):
                    
                    dist_lower = abs(lower_marker - light)
                    dist_upper = abs(upper_marker - light)
                    mult = 0
                    
                    if dist_lower < q:
                        mult = 1 - dist_lower
                    elif dist_upper < q:
                        mult = 1 - dist_upper
                    level = int(255 * mult)

                    self.lights[light] = level
                
                self.offset += 0.1
                self.last_tick = time.time()
                return self.lights
        raise StopIteration

# Keep track of trigger/untrigger time for effect speed
# class ProxEvent:
#     trigger_duration = 0.5 # Maximum

#     def __init__(self, address):
#         self.address = address
#         self.trigger_time = time.time()

#     def untrigger(self):
#         duration = time.time() - self.trigger_time
#         self.trigger_duration = duration if duration < 0.5 else 0.5
#         # log.info("Updated duration to %s", self.trigger_duration)

# class Pattern:

#     def __init__(self, lights):
#         self.lights = lights
#         self.updates = []
#         self.effects = defaultdict(list)
#         self.output_stack = [[0]*10]
#         self.events = {}

    # def prox_event(self, address, payload):
    #     log.debug("Pattern prox event for %s (%s)", address, payload)
    #     log.debug("Events: %s", self.events)

    #     # Trigger a ripple effect
    #     if payload < 12000 and address not in self.events:
    #             log.debug("Prox trigger on %s", address)
    #             event = ProxEvent(address)

    #             self.effects[address].append(Ripple(event))
    #             self.events[address] = 1

    #     # Untrigger the ripple effect
    #     elif payload > 12000 and address in self.events:
    #             log.debug("Prox untrigger on %s", address)
    #             try:
    #                 self.effects[address][-1].event.untrigger()
    #             except IndexError:
    #                 pass
    #             del self.events[address]

    # def touch_event(self, address, state):
    #     log.info("Pattern touch event for %s (%s)", address, state)
        
    #     # We registered a new touch event
    #     if state is True:
    #         log.info("Touch trigger on %s", address)
    #         event = ProxEvent(address)

    #         # Add a new ripple effect to the effects list
    #         self.effects[address].append(Ripple(event))

    #     # Ending a touch event
    #     else:
    #         log.info("Touch untrigger on %s", address)
    #         try:
    #             # Untrigger the ripple effect
    #             self.effects[address][-1].event.untrigger()
    #         except IndexError:
    #             pass

    # def tick(self):
    #     # Get the next output for each effect running
    #     for address in self.effects:
    #         for effect in self.effects[address]:
    #             try:
    #                 output = next(effect)
    #                 if output is not None:
    #                     log.debug("Got output %s" % output)

    #                     self.output_stack.append(output)

    #             except StopIteration:
    #                 log.debug("Ripple finished")
    #                 self.effects[address].remove(effect)

    #     # Set the light level for each light for each output in the stack
    #     for light_idx in range(0, 10):
    #         level = max([output[light_idx] for output in self.output_stack])
    #         self.lights[light_idx].set_level(level)

        # # Add each light to be updeated to the updates list
        # for light in self.lights:
        #     if light.update is True:
        #         self.updates.append(light)
        #         light.update = False



