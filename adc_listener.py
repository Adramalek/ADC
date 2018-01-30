from serial import Serial
from threading import Thread, Event
import matplotlib as plt


def while_loop(condition, job):
    while condition():
        job()


class COMPortController(object):
    def __init__(self, name, stopper, baudrate=115200, cr='\r', lf='\n', timeout=None, tries=10, bufsize=100):
        self.ser = Serial(name, timeout=timeout)  # open serial port
        self.ser.baudrate = baudrate
        self.stopper = stopper
        if self.ser.name != name:
            raise ValueError()
        self.cr = cr.encode('ascii')
        self.lf = lf.encode('ascii')
        self.crlf = cr + lf
        self.buffer = []
        self.bufsize = bufsize
        self.bufful = Event()
        self.thread = None

    def adc_start(self):
        def _plot():

            pass
        while not self.stopper.is_set():
            self.buffer.append(int(self.ser.read_until(self.cr, 6)
                                   .decode()
                                   .replace(self.cr, '')
                                   .replace(self.lf, '')))
            if len(self.buffer) == self.bufsize:


    def close(self):
        self.ser.close()
