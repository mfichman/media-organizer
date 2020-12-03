#!/usr/bin/env python

# Copyright (c) 2020 Matt Fichman <matt.fichman@gmail.com>
#
# This file is subject to the license terms in the LICENSE.md file found in
# the top-level directory of this software package. No person may use, copy,
# modify, publish, distribute, sublicense and/or sell any part of this file
# except according to the terms contained in the LICENSE.md file.

import datetime

def parse(path):
    time = datetime.datetime.fromtimestamp(path.stat().st_ctime)
    raw = {'stat': {'taken_at': time.isoformat()}}
    return raw, {'taken_at': time}
