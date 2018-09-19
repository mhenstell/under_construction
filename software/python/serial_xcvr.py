import logging as log
from queue import Queue
import time
import threading
import serial

import controller

from simple_hdlc import HDLC


# Parse 32 bit integer into address, command, and payload
def parseUCPacket(data):
    addr = data >> 24
    command = data >> 16 & 0xFF
    payload = data & 0xFFFF
    return addr, command, payload

class Transceiver:

    sendTimeout = 0

    def __init__(self, device):
        self.device = device
        self.port = serial.Serial(self.device, timeout=2)
        self.lastSent = 0
        self.transmitQueue = []
        self.rx_callback = None
        self.run = True
        self.readyToTransmit = False
        self.hdlc = HDLC(self.port)


        self.rx_thread = threading.Thread(target=self.reader)
        self.rx_thread.start()

    def reader(self):
        # first_line = True

        while self.run is True:
            # data = self.port.readline()
            # if len(data) == 0:
            #     log.warn("Serial timeout")
            #     self.stop()
            #     return
            # log.debug("Serial received: %s", data)
            
            # # Throw away first line
            # if first_line:
            #     first_line = False
            #     continue
            # data = str(data, encoding="ascii")
            # if data[0] == "!" and self.readyToTransmit is False:
            #     log.warning("Ready to transmit")
            #     self.readyToTransmit = True

            try:
                data = self.hdlc.readFrame(timeout=2)
                log.debug("Serial debug: %s", data)

            except ValueError:
                continue


            if self.rx_callback is not None:
            
                # if data[0] is not '#':
                #     log.debug("Serial debug: %s", data.strip())
                #     continue
                
                # addr, command, payload = parseUCPacket(int(data[1:]))
                addr, command, payload = data[0], data[1], data[2:4]
                payload = (payload[0] << 8) | payload[1]
                # log.info("Addr %s Cmd %s Pay %s", addr, command, payload)

                self.rx_callback(addr, command, payload)
        self.port.close()

    def stop(self):
        log.info("Closing serial connection")
        self.run = False

    def register_callback(self, callback):
        self.rx_callback = callback

    def _transmit(self, address, command, payload):
        log.debug("Transmitting ADDR %s CMD %s PAYLOAD %s", address, command, payload)
        output = bytearray([address, command, (payload >> 8), payload & 0xFF])
        self.hdlc.sendFrame(output)

    def transmit(self, address, command, payload):
        self.transmitQueue.append((address, command, payload))

    def tick(self):
        # if not self.readyToTransmit:
        #     return
        if (time.time() - self.lastSent) > self.sendTimeout:
            if len(self.transmitQueue) > 0:
                self._transmit(*self.transmitQueue.pop())
                # log.info("Transmit queue size %s", len(self.transmitQueue))
            self.lastSent = time.time()
