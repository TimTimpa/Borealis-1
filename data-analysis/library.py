import matplotlib.pyplot as plt
from numpy import *
import csv

class getter:
    def __init__(self, headers, y):
        self.headers = headers
        self.y = y

    def __getitem__(self, key):
        if isinstance(key, str):
            key = self.headers.index(key)
        return self.y[key]
    def __setitem__(self, key, value):
        if isinstance(key, str):
            key = self.headers.index(key)
        self.y[key] = value

    def unget(self):
        return(self.y)

class read:
    def __init__(self, path: str = 'data.csv'):
        '''
        :param path: Namnet på din data-fil
        :type path: str
        '''
        self.time = []
        self.y = []
        with open(path, 'r') as file:
            reader = csv.DictReader(file)
            self.headers = reader.fieldnames[6:]
            for row in reader:
                data = []
                self.time.append(float(row['tid']))
                for header in self.headers:
                    data.append(float(row[header]))
                self.y.append(data)
        self.time = array(self.time)
        self.y = getter(self.headers, array(self.y).T)

class plotter:
    def __init__(self, data, name=None, *, x=None):
        self.data = data
        self.data.y = self.data.y.unget()
        self.dict = {}
        self.plots = []
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(label=name)
        if x is not None:
            self.data.time = x

    def __update(self, index, target, n):
        if index not in self.dict.keys():
            self.dict[index] = [None,None,None]
        self.dict[index][n] = target

    def plot(self, index=None):
        '''
        :param index: Det som ska ritas. Lämna tom för allt.
        '''
        if index is not None:
            if isinstance(index, str):
                label = index
                index = self.data.headers.index(index)
            else:
                label = self.data.headers[index]
            self.__update(index, self.data.y[index], 0)
            self.__update(index, label, 2)

        else:
            for i in range(len(self.data.y)):
                self.__update(i, self.data.y[i], 0)
                self.__update(i, self.data.headers[i], 2)

    def trend(self, index=None):
        if index is not None:
            if isinstance(index, str):
                label = index
                index = self.data.headers.index(index)
            else:
                label = self.data.headers[index]

            k = polyfit(self.data.time, self.data.y[index], 1)
            self.__update(index, k[0]*self.data.time + k[1], 1)
            self.__update(index, label, 2)

        else:
            for i in range(len(self.data.y)):
                k = polyfit(self.data.time, self.data.y[i], 1)
                self.__update(i, k[0]*self.data.time + k[1], 1)
                self.__update(i, label, 2)

    def show(self, grid=True):
        for p in self.dict.values():
            color = self.ax._get_lines.get_next_color()
            if p[0] is not None:
                self.ax.plot(self.data.time, p[0], label=p[2], color=color)
            if p[1] is not None:
                self.ax.plot(self.data.time, p[1], label=f'Trendlinje för: {p[2]}', color=color, linestyle=':', alpha=0.7)

        self.ax.set_xlabel('Tid')
        if grid:
            self.ax.grid(alpha=0.3)
        self.fig.tight_layout()
        self.fig.legend()
        plt.show()
