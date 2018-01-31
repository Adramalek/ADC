from serial import Serial
from threading import Thread, Event
from os.path import exists, join, dirname, abspath
from os import mkdir, listdir, remove
from shutil import rmtree
import matplotlib.pyplot as plt
import time
import logging


def while_loop(condition, job):
    while condition():
        job()


class ADCPort(object):
    def __init__(self, name, store_path, stopper=None, baudrate=115200,
                 cr='\r', lf='\n', timeout=None, bufsize=100):
        self.ser = Serial(name, timeout=timeout)  # open serial port
        self.ser.baudrate = baudrate
        if not stopper:
            stopper = Event()
        self.stopper = stopper
        self.store_path = store_path
        if self.ser.name != name:
            raise ValueError()
        self.cr = cr.encode('ascii')
        self.lf = lf.encode('ascii')
        self.crlf = cr + lf
        self.buffer = []
        self.buffer_size = bufsize
        self.buffer_full_flag = Event()
        self.thread = None
        self.sample = 0

    def adc_start(self):
        def _read(obj):
            start = time.time()
            while not obj.stopper.is_set():
                # logging.info('Read adc value')
                line = obj.ser.read_until('\r'.encode('ascii'), 6)
                obj.ser.reset_input_buffer()
                # logging.info(line)
                try:
                    line = line.decode('ascii').replace('\n', '').replace('\r', '')
                    logging.info(line)
                    # logging.info('Append to buffer')
                    obj.buffer.append((int(line), (time.time()-start)))
                    if len(obj.buffer) >= obj.buffer_size:
                        obj.buffer_full_flag.set()
                        logging.info('Buffer is full')
                except (UnicodeDecodeError, ValueError):
                    continue
        if not self.thread:
            logging.info('Prepare')
            if not exists(self.store_path):
                mkdir(self.store_path)
            else:
                rmtree(self.store_path)
                mkdir(self.store_path)
            self.thread = Thread(target=_read, args=(self,))
            logging.info('Start thread')
            self.thread.start()
            while not self.stopper.is_set():
                if self.buffer_full_flag.is_set():
                    logging.info('Extract data from buffer')
                    data, self.buffer = self.buffer[:self.buffer_size], self.buffer[self.buffer_size:]
                    y, x = zip(*data)
                    logging.info('Make plot')
                    plt.plot(x, y)
                    logging.info('Save plot')
                    plt.savefig(join(self.store_path, 'Sample{}'.format(self.sample)))
                    self.sample += 1
                    plt.clf()
                    self.buffer_full_flag.clear()

    def close(self):
        logging.info('Close port')
        if self.thread:
            self.stopper.set()
            self.thread.join()
        self.ser.close()
        logging.info('Finished')


def init_log(file_name):
    if exists(file_name):
        remove(file_name)
    logging.basicConfig(filename=file_name, level=logging.INFO, format='[%(asctime)s]%(levelname)s:%(message)s')


if __name__ == '__main__':
    adc = ADCPort('COM5', join(dirname(abspath(__file__)), 'Plots'), bufsize=10**6)
    init_log(join(dirname(abspath(__file__)), 'info.log'))
    adc.adc_start()
    while len(listdir(adc.store_path)) < 10:
        pass
    adc.close()
