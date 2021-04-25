import os, os.path
import random, sys, time
import cec
import threading, subprocess
import datetime
from enum import Enum

class State(Enum):
    OFF = 0
    ON = 1
    TURNING_OFF = 2
    TURNING_ON = 3

class TV(object):
    def __init__(self):
        cec.init()
        # Force TV to turn on/off
        self.scheduled_state = self.__should_be_on()
        self.current_state = not self.scheduled_state

        self.tv = cec.Device(cec.CECDEVICE_TV)
        cec.add_callback(self.__response_handler, cec.EVENT_COMMAND)

        self.running = True
        self.thr = threading.Thread(target = self.__check_tv)
        self.thr.start()


    def __check_tv(self):
        while self.running:
            try:
                self.tv.is_on()
                time.sleep(1)
            except:
                pass

    def __response_handler(self, event, *args):
        if event == cec.EVENT_COMMAND:
            args = args[0]
            if args['opcode_set'] and args['opcode'] == 0x90:  # Report Power Status
                should_be_on = self.__should_be_on()

                if args['parameters'] == b'\x00':
                    # TV ON
                    tv_state = State.ON
                else:
                    # TV off or transitioning
                    tv_state = State.OFF

                # Only force a change if we have a schedule change
                if self.scheduled_state != should_be_on:
                    self.scheduled_state = should_be_on
                    # current state is transitioning
                    self.current_state = should_be_on + State.TRANSITIONING_OFF

                if self.current_state == State.TRANSITIONING_ON:
                    if tv_state == State.ON:
                        self.current_state = State.ON
                    else:
                        self.tv.power_on()
                        print('Turning TV on')
                elif self.current_state == State.TRANSITIONING_OFF:
                    if tv_state == State.OFF:
                        self.current_state = State.OFF
                    else:
                        self.tv.standby()
                        print('Turning TV off')
                else:
                    self.current_state = tv_state

    def __should_be_on(self):
        # This could be more convenient
        now = datetime.datetime.now()
        # dow starts with Monday
        day_of_week = now.weekday()
        if day_of_week == 6:
            # Sunday, on at 7am off at 6pm
            if now.hour >= 7 and now.hour < 14:
                return State.ON
        #elif day_of_week >= 1 and day_of_week <= 3:
        #    # Tues, Wed, Thu, 6pm to 9pm
        #    if now.hour >= 18 and now.hour < 21:
        #        return State.ON
        return State.OFF

    def stop(self):
        self.running = False

