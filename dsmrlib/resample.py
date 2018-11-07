import numpy as np
from scipy.interpolate import UnivariateSpline as smspline
from scipy.interpolate import InterpolatedUnivariateSpline as spline1d

from dsmrlib import Measurements

class SmoothSampler:
    def __init__(self):
        self.times = []
        self.interps = []
        
    @classmethod
    def for_measurements(cls, m):
        self = cls()
        assert(~np.any(np.isnan(m.data)))  # Measurement.clean() first!
        # Identify time gaps.
        ranges = [ii for (ii,tt) in m.get_validity_intervals()]
        # Make sure no range contains more than sp_max points?
        sp_max = 1000000
        i = 0
        while i < len(ranges):
            i0, i1 = ranges[i]
            if i1 - i0 > sp_max:
                split_i = min(i0+sp_max, (i1+i0)/2)
                ranges[i] = (i0, split_i)
                ranges.insert(i+1, (split_i, i1))
            i += 1
        # Create interpolator set for each range.
        for i0, i1 in ranges:
            # We want the spline to apply across the whole validity
            # interval.  We thus first perform a bi-linear
            # interpolation to place the data on the validity
            # boundaries rather than at the sampling times.
            t0 = m.t[i0]
            dt = np.diff(m.t[i0:i1])
            w = np.hstack((1., (m.t_hi[i0:i1-1] - m.t[i0:i1-1]) / dt[:], 0.))
            t = np.hstack((m.t_lo[i0], m.t_hi[i0:i1]))
            y = np.zeros(len(t))
            y[:-1] = w[:-1] * m.data[i0:i1]
            y[1:] += (1-w[1:]) * m.data[i0:i1]
            self.times.append((m.t_lo[i0], m.t_hi[i1-1]))
            sigma = np.diff(y).std() / 2**.5
            if sigma == 0: sigma = 1.
            k = min(len(y) - 1, 3)
            self.cache = (t, y, w)
            sp = smspline(t - t0, y, w=sigma**-1 + y*0, k=k)
            self.interps.append(sp)
        return self

    def get(self, t):
        output = np.empty(len(t))
        output[:] = np.nan
        for (t0, t1), interps in zip(self.times, self.interps):
            s = (t0 <= t) * (t <= t1)
            if s.any():
                output[s] = interps(t[s] - t0)
        return output

    def get_resampler(self, resolution, include_data=False):
        out = SmoothSampler()
        meas = []
        for (t0, t1), interp in zip(self.times, self.interps):
            out.times.append((t0,t1))
            # definite integral generator.
            spi = interp.antiderivative()
            n = max(((t1 - t0) / resolution * 2).round(), 1.)
            res = (t1 - t0) / n
            t = np.arange(n+1) * res
            y = np.diff(spi(t)) / res  # integrate in each bin.
            # bi-linear extrapolation
            y1 = np.zeros(len(y)+1)
            y1[:-1] = y/2
            y1[1:] += y/2
            y1[0] *= 2
            y1[-1] *= 2
            sp = spline1d(t, y1, k=min(3, len(y1)-1))
            out.interps.append(sp)
            if include_data:
                meas.append((t+t0, y1))
        if include_data:
            t, y = np.hstack([m[0] for m in meas]), np.hstack([m[1] for m in meas])
            m = Measurements.from_simple(t, y)
            return (out,m)
        return out
