import numpy as np

class Measurements:
    """Measurements holds a vector of readings, the timestamps of those
    readings, and the upper and lower time ranges of the validity of
    those readings.
    """

    def __init__(self):
        self.t = None
        self.t_lo = None
        self.t_hi = None
        self.data = None
        self.v_keys = ['t', 't_lo', 't_hi', 'data']

    def intersect(self, t0, t1, centers=False):
        """Return a new Measurements that contains only the data with validity
        overlapping the interval [t0,t1).

        """
        if centers:
            # Consider only whether timestamp of point is in requested bounds.
            s = (t0 <= self.t) * (self.t < t1)
        else:
            # Include validity edges when intersecting.
            s = (self.t_hi >= t0) * (self.t_lo < t1)
        out = Measurements()
        for k in out.v_keys:
            setattr(out, k, getattr(self, k)[s])
        return out

    @classmethod
    def join(cls, args):
        args = [(a.t[0], a) for a in args if len(a.t)]
        args = [a[1] for a in sorted(args)]
        self = cls()
        for k in self.v_keys:
            setattr(self, k, np.hstack([getattr(a, k) for a in args]))
        return self

    @classmethod
    def from_simple(cls, t, y, max_step=None):
        """Returns a Measurements object corresponding to the time (t) and
        data (y) vectors.  Validity intervals are set to be the
        mid-point between each time measurement (and the first and
        last points are given symmetric intervals).  If max_step is
        specified, then validity intervals are truncated to be no
        larger than max_step/2 away from the sampling time given.

        """
        self = cls()
        self.t = t.copy()
        self.data = y.copy()
        if len(t) > 1:
            dt = np.diff(t)
            dt = np.hstack((dt[0], dt, dt[-1]))
            if max_step is not None:
                dt[dt>=max_step] = max_step
        else:
            dt = np.zeros(len(t)+1)
        self.t_lo = self.t - dt[:-1] / 2
        self.t_hi = self.t + dt[1:]/2
        return self
           
    def clean(self, heal_gaps=0.):
        """Discard invalid data points (nans).  In cases where the resulting
        validity gap is less than heal_gaps, extend the validity
        range of adjacent samples to cover the missing data.  (This
        allows us to ignore isolated bad data samples.)

        """
        mask = ~np.isnan(self.data)
        for k in self.v_keys:
            setattr(self, k, getattr(self, k)[mask])
        
        gap_size = self.t_lo[1:] - self.t_hi[:-1]
        healable = (gap_size > 0) * (gap_size < heal_gaps)
        for i in healable.nonzero()[0]:
            new_bound = (self.t_hi[i] + self.t_lo[i+1]) / 2
            self.t_hi[i] = new_bound
            self.t_lo[i+1] = new_bound

    def get_validity_intervals(self):
        dt = self.t_lo[1:] - self.t_hi[:-1]
        breaks = np.hstack((True, dt > 0, True))
        breaks = breaks.nonzero()[0]
        return [((b0, b1), (self.t_lo[b0], self.t_hi[b1-1]))
                for (b0,b1) in zip(breaks[:-1], breaks[1:])]

def test_measurements():
    t = np.arange(100.)
    y = np.zeros(len(t)) + .3
    y[10] = np.nan
    M = Measurements.from_simple(t, y)
    M.clean()
    print M.get_validity_intervals()
    M.clean(heal_gaps=3)
    print M.get_validity_intervals()
            

