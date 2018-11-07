import pickle
import math
import numpy as np

import dsmrlib

"""In the sisock data model, a data node stores time-ordered data for
some set of fields.  Field lists and data themselves can be requested
for any time interval.

"""

class ResArchive(object):
    """Abstract base class defining the ResArchive interface.

    The ResArchive exposes data sampled at some discrete set of
    resolutions.  The data at a given resolution may be stored in a
    series of files, organized by time range.  The ResArchive helps to
    track all that.
    """

    def __init__(self, iom=None):
        self.res_list = []
        self.filesets = {}  # map from res_id to ResArchiveFileset
        self.iom = iom

    @classmethod
    def from_file(cls, filename):
        self = pickle.load(open(filename))
        return self

    def relocate(self, new_path, old_path=''):
        for fs in self.filesets.values():
            fs.relocate(new_path, old_path)

    def write(self, filename):
        pickle.dump(self, open(filename, 'w'))

    def nearest_res(self, res):
        distance = [(abs(np.log(res/r)), r) for r in self.res_list]
        return min(distance)[1]

    def add_res(self, res):
        self.res_list.append(res)
        self.filesets[res] = ResArchiveFileset(res)

    def add_file(self, res, time_range, filename, fields=None):
        if not res in self.res_list:
            self.add_res(res)
        raf = self.filesets[res]
        return raf.add_file(time_range, filename, fields=fields)

    def get_fields(self, time_range, res=None):
        if res is None:
            res = self.res_list
        if not hasattr(res, '__iter__'):
            res = [res]
        fields = []
        for r in res:
            r = self.nearest_res(r)
            fs = self.filessets[r].get_fields(time_range)
            for f in fs:
                if not fs in fields:
                    fields.append(fs)
        return fields
            
    def cover_for_times(self, res, times, fields=None):
        res = self.nearest_res(res)
        return self.filesets[res].cover_for_times(times, fields=fields)

    def cover_for_intervals(self, res, time_ranges, fields=None):
        res = self.nearest_res(res)
        return self.filesets[res].cover_for_intervals(time_ranges, fields=fields)

    def get_data(self, res, time_ranges, fields=None, iom=None):
        if iom is None:
            iom = self.iom
        g = self.cover_for_intervals(res, time_ranges, fields=fields)
        output = {}
        for raf in g:
            M = iom.read(raf.data, time_ranges, fields=fields)
            for k,m in M.items():
                if not k in output:
                    output[k] = []
                output[k].append(m)
        # Super-join by field.
        for k in output.keys():
            output[k] = dsmrlib.Measurements.join(output[k])
        return output
    
class ResArchiveFile(object):
    def __init__(self, time_range, fields, data):
        self.time_range = time_range
        self.fields = fields
        self.data = data

class ResArchiveFileset(list):
    def __init__(self, res_id):
        list.__init__(self)
        self.res_id = res_id
        
    def __repr__(self):
        return '%s (res=%.1f, n_files=%i)' % (self.__class__, self.res_id, len(self))
    
    def relocate(self, new_path, old_path=''):
        for raf in self:
            fn = raf.data['filename']
            assert(fn.startswith(old_path))
            raf.data['filename'] = new_path + fn[len(old_path):]

    def add_file(self, time_range, filename, fields=None):
        self.append(ResArchiveFile(time_range, fields, {'filename': filename}))
        
    def get_fields(self, time_range):
        fields = []
        rafs = self.cover_for_times(time_range)
        for raf in rafs:
            for f in raf.fields:
                if not f in fields:
                    fields.append(f)
        return fields

    def cover_for_times(self, times, fields=None):
        times = np.asarray(times)
        output = []
        for raf in self:
            t0, t1 = raf.time_range
            s = (t0 <= times) * (times < t1)
            if s.any():
                output.append(raf)
        return output

    def cover_for_intervals(self, time_ranges, fields=None):
        output = []
        for raf in self:
            t0, t1 = raf.time_range
            for (x0, x1) in time_ranges:
                if (t0 <= x0 < t1) or (x0 <= t0 < x1):
                    output.append(raf)
                    break
        return output

class NameGen:
    def __init__(self, points_per_file=5000):
        self.points_per_file = 5000
    def get_eff_res(self, res):
        # Round res so that points_per_file fits into some nice ctime chunk size.
        n0 = res * self.points_per_file
        # Find round number.
        rats = []
        base = 10**int(math.log10(n0))
        for mul in [1,2,4,5,10]:
            rats.append((abs((mul*base / n0)-1), mul*base))
        return int(min(rats)[1])
    def cover_for_times(self, res, times):
        step = self.get_eff_res(res)
        times = np.asarray(times)
        n0 = int(np.floor(times.min() / step))
        t0 = n0 * step
        dns = sorted(list(set(np.floor((times-t0) / step))))
        return [(t0+dn*step, t0+(dn+1)*step) for dn in dns]
