import sys
import time
import signal
import argparse
import logging as log
from functools import partial

from controller import Controller
from light import Light

quit = False

lights = [Light(x) for x in range(0, 10)]

def signal_handler(sig, frame, transceivers):
    global quit

    log.warning('You pressed Ctrl+C!')
    quit = True
    
    for transceiver in transceivers:
        transceiver.stop()
    try:
        sys.exit(0)
    except:
        pass

def run(args: list):
    log.debug("Running with args: %s", args)

    transceivers = []

    if args.port is not None:
        import serial_xcvr
        transceivers.append(serial_xcvr.Transceiver(args.port))

    if args.redis:
        import redis_xcvr
        transceivers.append(redis_xcvr.Transceiver())

    cont = Controller(transceivers, lights)

    for transceiver in transceivers:
        transceiver.register_callback(cont.received_message)

    log.debug("Registering signal handler")
    handler = partial(signal_handler, transceivers=transceivers)
    signal.signal(signal.SIGINT, handler)

    a = 0

    while quit is False:
        cont.tick()
        for transceiver in transceivers:
            transceiver.tick()
        # time.sleep(0.001)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=str)
    parser.add_argument("-r", "--redis", action="store_true")
    parser.add_argument("-v", "--verbosity", type=str)

    args = parser.parse_args()
    
    log.basicConfig(level=getattr(log, args.verbosity), format='%(asctime)s %(levelname)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S')

    run(args)