from serial import Serial
from threading import Thread, Event
from os.path import exists, join
from os import mkdir
import matplotlib.pyplot as plt
import time


def while_loop(condition, job):
    while condition():
        job()


class COMPortController(object):
    def __init__(self, name, stopper, store_path, baudrate=115200, cr='\r', lf='\n', timeout=None, tries=10, bufsize=100):
        self.ser = Serial(name, timeout=timeout)  # open serial port
        self.ser.baudrate = baudrate
        self.stopper = stopper
        self.store_path = store_path
        if self.ser.name != name:
            raise ValueError()
        self.cr = cr.encode('ascii')
        self.lf = lf.encode('ascii')
        self.crlf = cr + lf
        self.bufer = []
        self.bufsize = bufsize
        self.bufful = Event()
        self.thread = None
        self.sample = 0

    def adc_start(self):
        def _read(obj):
            start = time.time()
            while not obj.stopper.is_set():
                obj.bufer.append((int(obj.ser.read_until(obj.cr, 6)
                                      .decode()
                                      .replace(obj.cr, '')
                                      .replace(obj.lf, ''))),
                                 (time.time()-start).total_seconds())
                if len(obj.bufer) == obj.bufsize:
                    obj.bufful.set()
        if not self.thread:
            if not exists(self.store_path):
                mkdir(self.store_path)
            self.thread = Thread(target=_read, args=(self,))
            self.thread.start()
            while not self.stopper.is_set():
                if self.bufful.is_set():
                    data, self.bufer = self.bufer[:self.bufsize], self.bufer[self.bufsize:]
                    x, y = zip(*data)
                    plt.plot(x, y)
                    plt.savefig(join(self.store_path, 'Sample{}'.format(self.sample)))
                    self.sample += 1
                    plt.clf()
                    self.bufful.clear()

    def close(self):
        if self.thread:
            self.stopper.set()
            self.thread.join()
        self.ser.close()
