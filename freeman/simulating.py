import pandas as pd

from math import inf, isinf
from timeit import default_timer
from abc import ABC, abstractmethod


class Simulation(ABC):
    def print(self, data, condition=True):
        if not isinstance(data, dict):
            raise TypeError('print data must be a dict')
        if not data:
            raise ValueError('print data must have at least one item')
        if condition:
            print(', '.join('{}: {}'.format(key, value) for key, value in data.items()))

    def print_every(self, data, counter, interval):
        if not isinstance(counter, int):
            raise TypeError('print counter must be an integer')
        if counter <= 0:
            raise ValueError('print counter must be positive')
        if not isinstance(interval, int):
            raise TypeError('print interval must be an integer')
        if interval <= 0:
            raise ValueError('print interval must be positive')
        self.print(data, counter % interval == 0)

    def append(self, data):
        if not isinstance(data, dict):
            raise TypeError('append data must be a dict')
        if not data:
            raise ValueError('append data must have at least one item')
        if self.data:
            if self.data.keys() != data.keys():
                raise KeyError('append data keys must be always the same')
            for key in data:
                prev = self.data[key][-1]
                curr = data[key]
                if prev is not None and curr is not None and type(prev) != type(curr):
                    raise TypeError('append data values must not change the type')
        else:
            for key in data:
                self.data[key] = []
        for key, value in data.items():
            self.data[key].append(value)

    def before_each(self):
        pass

    def before_iter(self):
        pass

    @abstractmethod
    def iterate(self):
        return False

    def after_iter(self, iteration, elapsed):
        pass

    def after_each(self, repetition, iterations, elapsed):
        pass

    def run(self, times=1, max_iter=inf):
        if not isinstance(times, int):
            raise TypeError('run times must be an integer')
        if times <= 0:
            raise ValueError('run times must be positive')

        if not isinstance(max_iter, int) and not (isinstance(max_iter, float) and isinf(max_iter)):
            raise TypeError('run iters must be an integer or inf')
        if max_iter <= 0:
            raise ValueError('run iters must be positive')

        self.data = {}

        repetition = 1
        while True:
            self.before_each()
            start_each = default_timer()

            iteration = 1
            while True:
                self.before_iter()
                start_iter = default_timer()

                repeat = self.iterate()

                end_iter = default_timer()
                self.after_iter(iteration, end_iter - start_iter)

                if repeat and iteration < max_iter:
                    iteration += 1
                else:
                    break

            end_each = default_timer()
            self.after_each(repetition, iteration, end_each - start_each)

            if repetition < times:
                repetition += 1
            else:
                break

        return pd.DataFrame(self.data)
