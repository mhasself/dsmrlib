"""
Classes that store time-ordered data somehow.

The data model for 
"""
from .base import Measurements

import numpy as np

class IOEngine:
    """This is the base class for reading and writing time-ordered data.
    In the read and write functions below, "info" is a dict that
    addresses some chunk of data somehow.  It might simply contain a
    filename, or it might contain filename and group name within an
    HDF archive.
    """

    def read(self, info, time_ranges, fields=None):
        """Given the chunk data info, load all data for the identified fields
        that overlaps with the time_ranges given.  Return the data as
        a dictionary of Measurements, keyed by field name.

        """
        raise NotImplementedError

    def write(self, info, measurements):
        """Write data into chunk identified by info.  measurements is a
        dictionary of Measurements objects.  It is assumed that this
        should replace all data in the specified chunk.

        """
        raise NotImplementedError

class SimpleAscii(IOEngine):
    """Storage of time-stamped numerical data in ASCII files.  Field names
    are not stored with the data and must be specified by the
    constructor.  All fields addressed through this object must be
    co-sampled.

    Remember that ASCII is only momentarily convenient.

    See IOEngine base class for documentation of the API.

    """
    def __init__(self, fields=['default'],
                 time_format='%.1f', data_format='%.5e'):
        """The order of the fields must correspond to the columns in the data
        files.  Note the first column is a timestamp, and subsequent
        columns are mapped, in order, to the fields listed here.

        """
        self.field_names = fields
        self.time_format = time_format
        self.data_format = data_format
        
    def read(self, info, time_ranges=None, fields=None):
        if fields is None:
            fields = self.field_names
        index = [self.field_names.index(f) for f in fields]
        rows = []
        for line in open(info['filename']):
            w = line.split()
            if len(w) == 0 or w[0][0] == '#':
                continue
            rows.append(map(float, w))
        data = map(np.array, zip(*rows))
        t, cols = data[0], data[1:]
        if time_ranges is not None:
            s = np.zeros(len(t), bool)
            for t0, t1 in time_ranges:
                s += (t0 <= t)*(t < t1)
            t = t[s]
            cols = [c[s] for c in cols]
        return dict([(self.field_names[i], Measurements.from_simple(t, c))
                     for (i,c) in zip(index, cols)])

    def write(self, info, measurements):
        assert(len(measurements) == len(self.field_names))
        
        cols = [measurements[0].t]
        for m in measurements:
            assert np.all(m.t == measurements[0].t)
            cols.append(m.data)

        rows = zip(*cols)
        fmt = self.time_format + ' ' + ' '.join([self.data_format] * len(measurements))
        fout = open(info['filename'], 'w')
        for r in rows:
            fout.write(fmt % tuple(r) + '\n')
        fout.close()
