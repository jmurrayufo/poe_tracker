import numpy as np

"""
['__add__', '__class__', '__contains__', '__delattr__', '__delitem__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__getitem__', '__gt__', '__hash__', '__iadd__', '__imul__', '__init__', '__init_subclass__', '__iter__', '__le__', '__len__', '__lt__', '__mul__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__reversed__', '__rmul__', '__setattr__', '__setitem__', '__sizeof__', '__str__', '__subclasshook__', 'append', 'clear', 'copy', 'count', 'extend', 'index', 'insert', 'pop', 'remove', 'reverse', 'sort']
"""

class Bins:


    def __init__(self, edges=5, max_edge=1000, bin_cap=None):
        """
        @param edges Is either an Int for auto calculated edge values, or an iter of values to be sorted and used
        as edges. Note that the first and last bins are handlede automaticly. So if edges were [1,2,3], then 
        the internal structure of the bins would be [0,1,2,3,'inf'].

        @param max_edge Maximum edge if `edges` was an Int, otherwise ignored. 

        @param bin_cap If given Int, bins will pop oldest value if new insert causes them to be larger than
        bin_cap. 
        """
        try:
            self.edges = [e for e in edges]
            self.edges = np.asarray(self.edges)
        except TypeError:
            self.edges = np.logspace(0,np.log10(max_edge),edges-1)

        if self.edges[0] != 0:
            self.edges = np.insert(self.edges, 0, 0)

        self.bins = [list() for x in range(len(self.edges))]
        self.bin_cap = bin_cap


    def append(self, bin_index, value):
        self.bins[bin_index].append(value)
        if self.bin_cap and len(self.bins[bin_index]) > self.bin_cap:
            self.bins[bin_index].pop(0)


    def insert(self, value, item):
        for idx in range(len(self.edges)-1):
            if self.edges[idx] <= value < self.edges[idx+1]:
                self.bins[idx].append(item)
                if self.bin_cap and len(self.bins[idx]) > self.bin_cap:
                    self.bins[idx].pop(0)
                break
        else:
            self.bins[-1].append(item)
            if self.bin_cap and len(self.bins[-1]) > self.bin_cap:
                self.bins[-1].pop(0)


    def clear(self, bin_index=None):
        if bin_index is None:
            self.bins = [list() for x in range(len(self.edges))]
            return
        self.bins[bin_index] = list()


    def __len__(self):
        return len(self.bins)


    @property
    def size(self):
        return sum(len(x) for x in self.bins)
    @property
    def shape(self):
        return tuple(len(x) for x in self.bins)


    def __iter__(self):
        for bin in self.bins:
            yield bin


    def __getitem__(self, index):
        return self.bins[index]
    def __setitem__(self, index, value):
        self.bins[index] = value


    def edge_values(self, index):
        """Return upper and lower bounds of bin at index.
        """

        try:
            return self.edges[index],self.edges[index+1]
        except IndexError:
            return self.edges[index], float('inf')

    def bin_value(self, index):
        """Return the mean value of items in the given index
        Note that the final bin will only be the lower bound, as the upper bound is infinity.
        """
        try:
            return (self.edges[index]+self.edges[index+1])/2
        except IndexError:
            return self.edges[index]

    def predict_value(self, pred_array):
        """Given iterable pred_array, return the average expected value. pred_array is expcted
        to be a normalized array of values of equal dimension to the number of bins
        """
        if len(pred_array) != len(self):
            raise IndexError("pred_array must be of equal length to bins.")
        if sum(pred_array)-1 > 0.001:
            pred_array = [x/sum(pred_array) for x in pred_array]

        return sum([self.bin_value(i)*pred_array[i] for i in range(len(pred_array))])

    def get_index(self, value):
        """Given a value, return it's proper index in the bins
        """
        for idx in range(len(self.edges)-1):
            if self.edges[idx] <= value < self.edges[idx+1]:
                return idx
        else:
            return idx



if __name__ == '__main__':
    x = Bins(5, max_edge=140)
    x.insert(0.5, 1)
    x.insert(1, 2)
    x.insert(1e50, 3)
    print(x.edges)
    print(x.shape)
    print(x.predict_value([0,0.5,0.25,0.25,0]))

