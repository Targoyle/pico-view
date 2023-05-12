# pico-view
#     viewer.py

__version__ = '0.0.0 alpha'

import os
import sys
import time
from collections import deque
from multiprocessing import Array, Process, Queue, freeze_support
from statistics import mean

import _queue
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import psutil
import serial
from _tkinter import TclError
from matplotlib.ticker import ScalarFormatter

# ---

PORT = 'COM4'
BAUD = 115200

Q_TIMEOUT = 1

N = 1000
CHANNEL_NUM = 4

US_INT_MAX = 65535

# ---

def sampling(q, sig):
    ser = serial.Serial(
        port=PORT,
        baudrate = BAUD,
        timeout=1,
        write_timeout=1,
        exclusive=True,
    )
    priority = psutil.Process()
    priority.nice(psutil.ABOVE_NORMAL_PRIORITY_CLASS)

    ser.flush()
    receive_bytes = ser.read_all()

    while True:
        if not sig.empty():
            break

        receive_bytes = ser.read_all()
        receive = receive_bytes.decode('utf-8').splitlines()

        if receive:
            q.put(receive)

    ser.close()


def on_close(event, sig):
    sig.put(True)


def viewer(data_array, sig):
    plt.ion()

    fig = plt.figure(
        "pico-view [{}]".format(PORT),
        figsize=(11.1, 6.2))
    fig.suptitle("ADC Monitor".format())
    fig.subplots_adjust(hspace=0.3)
    fig.canvas.mpl_connect('close_event', lambda event: on_close(event, sig))

    ax0 = fig.add_subplot(111,)
    bg0 = fig.canvas.copy_from_bbox(ax0.bbox)

    n_array = np.linspace(-N, 0, N)
    y_init = np.ones(N)

    linewidth = 2

    line_0, = ax0.plot(n_array, y_init, label="Ch.0", linewidth=linewidth)
    line_1, = ax0.plot(n_array, y_init, label="Ch.1", linewidth=linewidth)
    line_2, = ax0.plot(n_array, y_init, label="Ch.2", linewidth=linewidth)
    line_3, = ax0.plot(n_array, y_init, label="Ch.3", linewidth=linewidth)

    ax0.set_xlabel("n")
    ax0.set_ylabel("a.u.")
    ax0.set_xlim([-N, 0])
    ax0.set_yticks(np.linspace(0, US_INT_MAX + 1, 5))

    ax0.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ax0.grid()
    ax0.legend(bbox_to_anchor=(1.01, 1), loc="upper left", borderaxespad=0,)

    while True:
        if not sig.empty():
            break

        adc_0 = np.array(data_array[0])
        adc_1 = np.array(data_array[1])
        adc_2 = np.array(data_array[2])
        adc_3 = np.array(data_array[3])

        line_0.set_ydata(adc_0)
        line_1.set_ydata(adc_1)
        line_2.set_ydata(adc_2)
        line_3.set_ydata(adc_3)

        fig.canvas.blit(ax0.bbox)
        fig.canvas.flush_events()


def main():
    freeze_support()

    sig = Queue()

    q = Queue()
    collector = Process(
        target=sampling,
        kwargs={"q": q, "sig": sig, },
    )
    collector.start()

    data_array = []
    for i in range(CHANNEL_NUM):
        data_array += [Array('i', range(N))]

    display = Process(
        target=viewer,
        args=(
            data_array,
        ),
        kwargs={
            "sig": sig,
        },
    )
    display.start()

    queue_array = []
    for i in range(CHANNEL_NUM):
        queue_array += [
            deque(
                np.zeros(N).astype(np.int16),
                maxlen=N,
            )
        ]

    try:
        while collector.is_alive() and display.is_alive():
            if not sig.empty():
                break

            receive = q.get(timeout=Q_TIMEOUT)

            if not receive:
                continue
            if len(receive[0]) != (20):
                continue

            for i in range(CHANNEL_NUM):
                queue_array[i].append(
                    int(receive[0][i*5:i*5+5])
                )

            for i in range(CHANNEL_NUM):
                data_array[i][:] = list(queue_array[i])

    except KeyboardInterrupt:
        sig.put(True)

    except _queue.Empty:
        sig.put(True)

    sig.put(True)
    display.join()
    collector.join()


if __name__ == '__main__':
    print('===============================================')
    print(' pico-view ver.{}'.format(__version__))
    print('===============================================')
    main()
