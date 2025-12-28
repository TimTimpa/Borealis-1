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
    def values(self):
        return self.y
    def keys(self):
        return self.headers

class read:
    def __init__(self, path:str = 'data.csv'):
        '''
        :param path: Namnet på din data-fil
        :type path: str
        '''
        self.alt = []
        self.y = []
        with open(path, 'r') as file:
            reader = csv.DictReader(file)
            self.headers = reader.fieldnames[6:]
            for row in reader:
                data = []
                self.alt.append(float(row['tid']))
                for header in self.headers:
                    data.append(float(row[header]))
                self.y.append(data)
        self.alt = array(self.alt)
        self.y = getter(self.headers, array(self.y).T)

    def zero(self, index=None):
        if index is not None:
            self.y[index] -= self.y[index][0]

class plotter:
    def __init__(self, data:read, name:bool=None, *, x:bool=None):
        self.data = data
        self.data.y = self.data.y.values()
        self.dict = {}
        self.plots = []
        self.name = name
        if x is not None:
            self.data.alt = x
    
    def __update(self, index, target, n):
        if index not in self.dict.keys():
            self.dict[index] = [None,None,None,None]
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

    def trend(self, index=None, name=False):
        if index is not None:
            if isinstance(index, str):
                label = index
                index = self.data.headers.index(index)
            else:
                label = self.data.headers[index]
            
            k = polyfit(self.data.alt, self.data.y[index], 1)
            self.__update(index, k[0]*self.data.alt + k[1], 1)
            if name:
                self.__update(index, f'Trendline for {label}:\nk = {k[0]:.4f}\nm = {k[1]:.4f}\nR^2 = ...', 3)

        else:
            for i in range(len(self.data.y)):
                label = self.data.headers[i]
                k = polyfit(self.data.alt, self.data.y[i], 1)
                self.__update(i, k[0]*self.data.alt + k[1], 1)
                if name:
                    self.__update(i, f'Trendline for {label}:\nk = {k[0]:.4f}\nm = {k[1]:.4f}\nR^2 = ...', 3)

    def show(self, *, grid:bool=True):
        fig, ax = plt.subplots(label=self.name)
        for p in self.dict.values():
            color = ax._get_lines.get_next_color()
            if p[0] is not None:
                ax.plot(self.data.alt, p[0], label=p[2], color=color)
            if p[1] is not None:
                ax.plot(self.data.alt, p[1], label=p[3], color=color, linestyle=':', alpha=0.7)

        ax.set_xlabel('Tid')
        if grid:
            ax.grid(alpha=0.3)
        fig.tight_layout()
        fig.legend()
        plt.show()
    
    def showbox(self, *, grid:bool=True):
        fig, ax = plt.subplots(label=self.name)
        label = []
        q = []
        for p in self.dict.values():
            if p[0] is not None:
                label.append(p[2])
                q.append(p[0])
        ax.boxplot(q, showfliers=False)
        ax.set_xticklabels(label)
        if grid:
            ax.yaxis.grid(alpha=0.3)
        fig.tight_layout()
        fig.legend()
        plt.show()

    def showdist(self, normal:bool=True, *, grid:bool=True, res=100):
        q = []
        label = []
        for p in self.dict.values():
            if p[0] is not None:
                q.append(p[0])
                label.append(p[2])
        lenq = len(q)
        w = int(sqrt(lenq))
        h = int((lenq/w)+.499999999)

        fig, ax = plt.subplots(h, w, label=self.name)
        if lenq == 1:
            ax = [ax]
        
        for j in range(lenq):
            yrange = linspace(q[j].min(), q[j].max(), res)
            count = []
            for y in yrange:
                bl = sign(q[j] - y)
                for i in range(len(bl)-1):
                    if bl[i] != bl[i+1]:
                        count.append(y)
            sigma = std(count)
            mu = mean(count)
            factor = (q[j].max()-q[j].min())/res * len(count)
            color = ax[j]._get_lines.get_next_color()
            if normal:
                ax[j].plot(yrange, factor/(sigma * sqrt(2*pi)) * e**(- (yrange - mu)**2 / (2*sigma**2)), color=color, label=f'Normalfördelning:\n$\sigma = {sigma:.4f}$\n$\mu = {mu:.4f}$')
                ax[j].legend()
            color = ax[j]._get_lines.get_next_color()
            ax[j].hist(count, bins=res, color = color)
            ax[j].set_title(label[j])
        if grid:
            for k in ax:
                k.grid(alpha=0.3)
        fig.tight_layout()
        plt.show()
