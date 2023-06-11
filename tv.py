import os, os.path
import random, sys, time
import cec
import threading, subprocess, queue
import datetime
from enum import Enum
import schedule

class State(Enum):
    OFF = 0
    ON = 1
    TURNING_OFF = 2
    TURNING_ON = 3
    UNKNOWN = 4

class Command(Enum):
    STATUS = 0
    TURN_ON = 1
    TURN_OFF = 2

class TVPower(object):
    def __init__(self):
        cec.init()
        self.tv = cec.Device(cec.CECDEVICE_TV)

    def power_on(self):
        print('Turning TV on')
        self.tv.power_on()

    def power_off(self):
        print('Turning TV off')
        self.tv.standby()


class TVSchedule(object):
    def __init__(self):
        self.tv = TVPower()

        sunday_on = datetime.time(hour = 6, minute = 0)
        sunday_off = datetime.time(hour = 18, minute = 0)
        tuesday_on = datetime.time(hour = 18, minute = 30)
        tuesday_off = datetime.time(hour = 21, minute = 30)

        schedule.every().sunday.at(sunday_on.strftime('%H:%M')).do(self.tv.power_on)
        schedule.every().sunday.at(sunday_off.strftime('%H:%M')).do(self.tv.power_off)
        schedule.every().tuesday.at(tuesday_on.strftime('%H:%M')).do(self.tv.power_on)
        schedule.every().tuesday.at(tuesday_off.strftime('%H:%M')).do(self.tv.power_off)

        now = datetime.datetime.now()
        if now.weekday() == 6 and now.time() >= sunday_on and now.time() < sunday_off:
            self.tv.power_on()
        elif now.weekday() == 1 and now.time() >= tuesday_on and now.time() < tuesday_off:
            self.tv.power_on()
        else:
            self.tv.power_off()

        self.running = True
        self.thr = threading.Thread(target = self.__run_scheduler)
        self.thr.start()

    def __run_scheduler(self):
        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def stop(self):
        self.running = False

if __name__ == '__main__':
    tv = TVPower()
    tv.power_off()
    
