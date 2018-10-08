import logging as log
from queue import Queue, Empty
import time
import threading
import serial
import itertools
import controller

from simple_hdlc import HDLC

# PACKET_RETRY = 0.1
# PACKET_MAX_TRIES = 3

# # Parse 32 bit integer into address, command, and payload
# def parseUCPacket(data):
#     addr = data >> 24
#     command = data >> 16 & 0xFF
#     payload = data & 0xFFFF
#     return addr, command, payload

class Packet:

    _counter = itertools.count()

    def __init__(self, trigger):
        self.num = next(self._counter) % 0xFF
        self.ack = False
        self.lastSent = 0
        self.tries = 0
        self.bytes = bytearray([trigger.light_id, self.num,
                                trigger.trigger_num, trigger.ramp_up,
                                trigger.hold, trigger.ramp_down, trigger.level])
    def shouldSend(self):
        return (self.tries < PACKET_MAX_TRIES) and (time.time() - self.lastSent > PACKET_RETRY)

class Transceiver:

    sendTimeout = 0

    def __init__(self, device):
        self.device = device
        self.port = serial.Serial(self.device, timeout=0.01)
        self.lastSent = 0
        self.transmitQueue = []
        # self.transmitTriggerQueue = []
        # self.transmitPacketQueue = Queue()
        self.rx_callback = None
        self.run = True
        self.readyToTransmit = False
        self.hdlc = HDLC(self.port)


        self.rx_thread = threading.Thread(target=self.reader)
        self.rx_thread.start()

        self.start_time = time.time()

    def reader(self):
        first_line = True

        while self.run is True:
            
            # Throw away first line
            if first_line:
                first_line = False
                continue

            try:
                data = self.hdlc.readFrame(timeout=2)
                # data = self.port.read(self.port.inWaiting())

                # currentFrame = bytearray()
                # activeFrame = False

                # while self.run:
                #     data = self.port.read(1)
                #     if len(data) == 0:
                #         continue
                #     if ord(data) == 0x7E and activeFrame is False:
                #         # Start
                #         activeFrame = True
                #         currentFrame = bytearray()
                #     elif ord(data) == 0x7E and activeFrame is True:
                #         # End
                #         activeFrame = False
                #         # log.info("Got frame: %s", currentFrame)
                #         break
                #     else:
                #         currentFrame += data

                # data = currentFrame

                log.debug("Serial debug: %s", data)
                
                # try:
                #     if data[0] == 0x7E and data[-3] == 0x7E:
                #         data = data[1:-3]
                # except IndexError:
                #     log.error("Error reading data: %s", data)

            except ValueError:
                continue
            except RuntimeError:
                log.error("readFrame timeout")
                continue

            if self.rx_callback is not None:
                
                addr, command = data[0], data[1]
                if len(data) > 2: payload = data[2:]
                else: payload = None

                self.rx_callback(addr, command, payload)

        self.port.close()

    def stop(self):
        log.info("Closing serial connection")
        self.run = False

    def register_callback(self, callback):
        self.rx_callback = callback

    def _transmit(self, address, command, payload):
        log.debug("Transmitting ADDR %s CMD %s PAYLOAD %s", address, command, payload)
        # output = bytearray([address, command, (payload >> 8), payload & 0xFF])
        
        output = bytearray([address, command])
        output += bytearray(payload)

        self.hdlc.sendFrame(output)

    def transmit(self, address, command, payload):
        self.transmitQueue.append((address, command, payload))

    def transmitBytes(self, bytes):
        log.info("Writing bytes: %s", bytes)
        self.hdlc.sendFrame(bytes)

    def tick(self):
     
        if (time.time() - self.lastSent) > self.sendTimeout:
            if len(self.transmitQueue) > 0:
                self._transmit(*self.transmitQueue.pop())

            self.lastSent = time.time()
        # try:
        #    data = self.hdlc.readFrame(0.01)
        #    print(data)
        #    if self.rx_callback is not None:
                
        #         addr, command, payload = data[0], data[1], data[2:]
        #         self.rx_callback(addr, command, payload)
        # except RuntimeError:
        #     pass
        # try:
        #     self._transmit(*self.transmitQueue.pop())
        # except IndexError:
        #     pass
