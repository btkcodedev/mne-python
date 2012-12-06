import os.path as op
import warnings

from nose.tools import assert_true, assert_equal
from numpy.testing import assert_array_equal
import numpy as np

from ...fiff import Raw
from ...fiff.proj import make_projector, activate_proj
from ..ssp import compute_proj_ecg, compute_proj_eog

data_path = op.join(op.dirname(__file__), '..', '..', 'fiff', 'tests', 'data')
raw_fname = op.join(data_path, 'test_raw.fif')
dur_use = 5.0
eog_times = np.array([0.5, 2.3, 3.6, 14.5])
raw_0 = Raw(raw_fname, preload=True).crop(0, 10, False)
raw_0.close()


def test_compute_proj_ecg():
    """Test computation of ECG SSP projectors"""
    for average in [False, True]:
        raw = raw_0.copy()
        # For speed, let's not filter here (must also not reject then)
        projs, events = compute_proj_ecg(raw, n_mag=2, n_grad=2, n_eeg=2,
                                    ch_name='MEG 1531', bads=['MEG 2443'],
                                    average=average, avg_ref=True,
                                    no_proj=True, l_freq=None, h_freq=None,
                                    reject=None, tmax=dur_use,
                                    qrs_threshold=0.5)
        assert_true(len(projs) == 7)
        # heart rate at least 0.5 Hz, but less than 3 Hz
        assert_true(events.shape[0] > 0.5 * dur_use and
                    events.shape[0] < 3 * dur_use)
        #XXX: better tests

        # without setting a bad channel, this should throw a warning (only
        # thrown once, so it's for average == True)
        with warnings.catch_warnings(record=True) as w:
            projs, events = compute_proj_ecg(raw, n_mag=2, n_grad=2, n_eeg=2,
                                            ch_name='MEG 1531', bads=[],
                                            average=average, avg_ref=True,
                                            no_proj=True, l_freq=None,
                                            h_freq=None, tmax=dur_use)
            assert_equal(len(w), 0 if average else 1)
        assert_equal(projs, None)


def test_compute_proj_eog():
    """Test computation of EOG SSP projectors"""
    for average in [False, True]:
        raw = raw_0.copy()
        n_projs_init = len(raw.info['projs'])
        projs, events = compute_proj_eog(raw, n_mag=2, n_grad=2, n_eeg=2,
                                     bads=['MEG 2443'], average=average,
                                     avg_ref=True, no_proj=False, l_freq=None,
                                     h_freq=None, reject=None, tmax=dur_use)
        assert_true(len(projs) == (7 + n_projs_init))
        assert_true(np.abs(events.shape[0] -
                    np.sum(np.less(eog_times, dur_use))) <= 1)
        #XXX: better tests

        # This will not throw a warning (?)
        with warnings.catch_warnings(record=True) as w:
            projs, events = compute_proj_eog(raw, n_mag=2, n_grad=2, n_eeg=2,
                                         average=average, bads=[],
                                         avg_ref=True, no_proj=False,
                                         l_freq=None, h_freq=None,
                                         tmax=dur_use)
            assert_equal(len(w), 0)
        assert_equal(projs, None)


def test_compute_proj_parallel():
    """Test computation of ExG projectors using parallelization"""
    raw = raw_0.copy()
    projs, _ = compute_proj_eog(raw, n_mag=2, n_grad=2, n_eeg=2,
                                bads=['MEG 2443'], average=False,
                                avg_ref=True, no_proj=False, n_jobs=1,
                                l_freq=None, h_freq=None, reject=None,
                                tmax=dur_use)
    raw_2 = raw_0.copy()
    projs_2, _ = compute_proj_eog(raw_2, n_mag=2, n_grad=2, n_eeg=2,
                                  bads=['MEG 2443'], average=False,
                                  avg_ref=True, no_proj=False, n_jobs=2,
                                  l_freq=None, h_freq=None, reject=None,
                                  tmax=dur_use)
    projs = activate_proj(projs)
    projs_2 = activate_proj(projs_2)
    projs, _, _ = make_projector(projs, raw_2.info['ch_names'],
                                 bads=['MEG 2443'])
    projs_2, _, _ = make_projector(projs_2, raw_2.info['ch_names'],
                                   bads=['MEG 2443'])
    assert_array_equal(projs, projs_2)
