Data Model
==========

Raw data class contains irregularly sampled time-ordered data with
time-stamps.  Some of the data could be NaN.  A measurement is not an
instantaneous reading, but rather has some validity over some interval
of time -- perhaps half-way to the next-nearest point.  This should be
described in the raw data container.

First-pass processing of Raw data produces a piece-wise valid
interpolator with a particular resolution.


Resampling
==========

The raw data are irregularly sampled, and may have long gaps.

Pass 1: Downsample slightly but produce a regularly sampled vector, to
simplify subsequent processing.

Pass 2: For each subsequent down-sampling, process data in contiguous
chunks (perhaps with allowances for patching short gaps rather than
breaking and restarting).


