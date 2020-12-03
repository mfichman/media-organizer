#!/usr/bin/env python

# Copyright (c) 2020 Matt Fichman <matt.fichman@gmail.com>
#
# This file is subject to the license terms in the LICENSE.md file found in
# the top-level directory of this software package. No person may use, copy,
# modify, publish, distribute, sublicense and/or sell any part of this file
# except according to the terms contained in the LICENSE.md file.

import exifread
import datetime
import base64

def parse_timestamp(metadata, date, subsec):
    try:
        value = '{}.{}'.format(metadata[date], metadata.get(subsec, 0))
        return datetime.datetime.strptime(value, '%Y:%m:%d %H:%M:%S.%f')
    except (ValueError, KeyError):
        return None

def parse(path):
    with open(path, 'rb') as fd:
        raw = {}
        for key, value in exifread.process_file(fd).items():
            if type(value) == bytes:
                raw[key] = base64.b64encode(value).decode('utf-8')
            else:
                raw[key] = str(value)

        time = (
            parse_timestamp(raw, 'EXIF DateTimeOriginal', 'EXIF SubSecTimeOriginal') or
            parse_timestamp(raw, 'EXIF DateTime', 'EXIF SubSecTime')
        )

        raw = {'exifread': raw}

        return raw, {'taken_at': time}
