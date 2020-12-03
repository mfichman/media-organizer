#!/usr/bin/env python

# Copyright (c) 2020 Matt Fichman <matt.fichman@gmail.com>
#
# This file is subject to the license terms in the LICENSE.md file found in
# the top-level directory of this software package. No person may use, copy,
# modify, publish, distribute, sublicense and/or sell any part of this file
# except according to the terms contained in the LICENSE.md file.

import datetime
import re

def parse(path):
    match = re.search(r'\b\d{8}-\d{6}\b', str(path))
    if match:
        time = datetime.datetime.strptime(match.group(0), '%Y%m%d-%H%M%S')
        raw = {'path': {'taken_at': time.isoformat()}}
        return raw, {'taken_at': time}
    else:
        return {}, {}
