import sys
import time
import signal
import argparse
import logging as log
from functools import partial

from controller import Controller
from pattern import Pattern
from light import Light

quit = False

def signal_handler(sig, frame, transceiver):
    global quit

    log.warning('You pressed Ctrl+C!')
    log.warning("Stopping transceiver " + str(transceiver))
    quit = True
    transceiver.stop()
    try:
        sys.exit(0)
    except:
        pass

def run(args: list):
    log.debug("Running with args: %s", args)

    lights = [Light(x) for x in range(0, 10)]
    pattern = Pattern(lights)
    
    redis_transceiver = None
    serial_transceiver = None

    if args.redis:
        import redis_xcvr
        redis_transceiver = redis_xcvr.Transceiver()

    if args.port is not None:
        import serial_xcvr
        serial_transceiver = serial_xcvr.Transceiver(args.port)

    transceivers = []
    for transceiver in [redis_transceiver, serial_transceiver]:
        if transceiver is not None:
            transceivers.append(transceiver)

    cont = Controller(transceivers, pattern)

    for transceiver in transceivers:
        transceiver.register_controller(cont)

    log.debug("Registering signal handler")
    handler = partial(signal_handler, transceiver=transceiver)
    signal.signal(signal.SIGINT, handler)

    while quit is False:
        cont.tick()
        time.sleep(0.001)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=str)
    parser.add_argument("-r", "--redis", action="store_true")
    parser.add_argument("-v", "--verbosity", type=str)

    args = parser.parse_args()
    
    log.basicConfig(level=getattr(log, args.verbosity), format='%(asctime)s %(levelname)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S')

    run(args)