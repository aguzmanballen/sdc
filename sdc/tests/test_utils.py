# -*- coding: utf-8 -*-
# *****************************************************************************
# Copyright (c) 2020, Intel Corporation All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     Redistributions of source code must retain the above copyright notice,
#     this list of conditions and the following disclaimer.
#
#     Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# *****************************************************************************

import string
import unittest

import numba
import numpy as np
import pandas

import sdc
from sdc.config import config_inline_overloads, config_use_parallel_overloads


test_global_input_data_unicode_kind4 = [
    '¡Y tú quién te crees?',
    '🐍⚡',
    '大处 着眼，c小处着手c。大大c大处',
]

test_global_input_data_unicode_kind1 = [
    'ascii',
    '12345',
    '1234567890',
]

min_float64 = np.finfo('float64').min
max_float64 = np.finfo('float64').max

test_global_input_data_float64 = [
    [1., -1., 0.1, min_float64, max_float64, max_float64, min_float64, -0.1],
    [1., np.nan, -1., 0., min_float64, max_float64, max_float64, min_float64],
    [1., np.inf, np.inf, -1., 0., np.inf, np.NINF, np.NINF],
    [np.nan, np.inf, np.inf, np.nan, np.nan, np.nan, np.NINF, np.NZERO],
]


def gen_int_df_index(length):
    """Generate random integer index for DataFrame"""
    arr = np.arange(length)
    np.random.seed(0)
    np.random.shuffle(arr)

    return arr


def gen_df(input_data, with_index=False):
    """Generate DataFrame based on list of data like a [[1, 2, 3], [4, 5, 6]]"""
    length = min(len(d) for d in input_data)
    data = {n: d[:length] for n, d in zip(string.ascii_uppercase, input_data)}

    index = None
    if with_index:
        index = gen_int_df_index(length)

    return pandas.DataFrame(data, index=index)


def gen_df_int_cols(input_data, with_index=False):
    """Generate DataFrame based on list of data like a [[1, 2, 3], [4, 5, 6]]"""
    length = min(len(d) for d in input_data)
    data = {n: d[:length] for n, d in enumerate(input_data)}

    index = None
    if with_index:
        index = gen_int_df_index(length)

    return pandas.DataFrame(data, index=index)


def count_array_REPs():
    if sdc.config.config_pipeline_hpat_default:
        from sdc.distributed import Distribution
        vals = sdc.distributed.dist_analysis.array_dists.values()
        return sum([v == Distribution.REP for v in vals])
    else:
        return 0


def count_parfor_REPs():
    if sdc.config.config_pipeline_hpat_default:
        from sdc.distributed import Distribution
        vals = sdc.distributed.dist_analysis.parfor_dists.values()
        return sum([v == Distribution.REP for v in vals])
    else:
        return 0


def count_parfor_OneDs():
    from sdc.distributed import Distribution
    vals = sdc.distributed.dist_analysis.parfor_dists.values()
    return sum([v == Distribution.OneD for v in vals])


def count_array_OneDs():
    from sdc.distributed import Distribution
    vals = sdc.distributed.dist_analysis.array_dists.values()
    return sum([v == Distribution.OneD for v in vals])


def count_parfor_OneD_Vars():
    from sdc.distributed import Distribution
    vals = sdc.distributed.dist_analysis.parfor_dists.values()
    return sum([v == Distribution.OneD_Var for v in vals])


def count_array_OneD_Vars():
    from sdc.distributed import Distribution
    vals = sdc.distributed.dist_analysis.array_dists.values()
    return sum([v == Distribution.OneD_Var for v in vals])


def dist_IR_contains(*args):
    return sum([(s in sdc.distributed.fir_text) for s in args])


@sdc.jit
def get_rank():
    return sdc.distributed_api.get_rank()


@sdc.jit
def get_start_end(n):
    rank = sdc.distributed_api.get_rank()
    n_pes = sdc.distributed_api.get_size()
    start = sdc.distributed_api.get_start(n, n_pes, rank)
    end = sdc.distributed_api.get_end(n, n_pes, rank)
    return start, end


def check_numba_version(version):
    return numba.__version__ == version


def msg_and_func(msg_or_func=None):
    if msg_or_func is None:
        # No signature, no function
        func = None
        msg = None
    elif isinstance(msg_or_func, str):
        # A message is passed
        func = None
        msg = msg_or_func
    else:
        # A function is passed
        func = msg_or_func
        msg = None
    return msg, func


def skip_numba_jit(msg_or_func=None):
    msg, func = msg_and_func(msg_or_func)
    wrapper = unittest.skipUnless(sdc.config.config_pipeline_hpat_default, msg or "numba pipeline not supported")
    if sdc.config.test_expected_failure:
        wrapper = unittest.expectedFailure
    # wrapper = lambda f: f  # disable skipping
    return wrapper(func) if func else wrapper


def skip_sdc_jit(msg_or_func=None):
    msg, func = msg_and_func(msg_or_func)
    wrapper = unittest.skipIf(sdc.config.config_pipeline_hpat_default, msg or "sdc pipeline not supported")
    if sdc.config.test_expected_failure:
        wrapper = unittest.expectedFailure
    # wrapper = lambda f: f  # disable skipping
    return wrapper(func) if func else wrapper


def sdc_limitation(func):
    return unittest.expectedFailure(func)


def skip_parallel(msg_or_func):
    msg, func = msg_and_func(msg_or_func)
    wrapper = unittest.skipIf(config_use_parallel_overloads, msg or "fails in parallel mode")
    if sdc.config.test_expected_failure:
        wrapper = unittest.expectedFailure
    # wrapper = lambda f: f  # disable skipping
    return wrapper(func) if func else wrapper


def skip_inline(msg_or_func):
    msg, func = msg_and_func(msg_or_func)
    wrapper = unittest.skipIf(config_inline_overloads, msg or "fails in inline mode")
    if sdc.config.test_expected_failure:
        wrapper = unittest.expectedFailure
    # wrapper = lambda f: f  # disable skipping
    return wrapper(func) if func else wrapper


def take_k_elements(k, data, repeat=False, seed=None):
    if seed is not None:
        np.random.seed(seed)
    return np.random.choice(np.asarray(data), k, replace=repeat)


def create_series_from_values(size, data_values, index_values=None, name=None, unique=True, seed=None):
    if seed is not None:
        np.random.seed(seed)

    min_size = min(size, len(data_values))
    if index_values:
        min_size = min(min_size, len(index_values))
    repeat = False if unique and min_size == size else True

    series_data = take_k_elements(size, data_values, repeat)
    series_index = take_k_elements(size, index_values, repeat) if index_values else None

    return pandas.Series(series_data, series_index, name)
