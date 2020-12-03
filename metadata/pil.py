#!/usr/bin/env python

# Copyright (c) 2020 Matt Fichman <matt.fichman@gmail.com>
#
# This file is subject to the license terms in the LICENSE.md file found in
# the top-level directory of this software package. No person may use, copy,
# modify, publish, distribute, sublicense and/or sell any part of this file
# except according to the terms contained in the LICENSE.md file.

import PIL.Image
import PIL.ExifTags
import argparse
import pathlib
import base64
import datetime

def parse_failure(path):
    raise ValueError("failed to parse metadata: {}", path)

def parse_timestamp(metadata, date, subsec):
    try:
        value = '{}.{}'.format(metadata[date], metadata.get(subsec, 0))
        return datetime.datetime.strptime(value, '%Y:%m:%d %H:%M:%S.%f')
    except (ValueError, KeyError):
        return None

def parse(path):
    try:
        exif = PIL.Image.open(path).getexif().items()
        raw = {}
        for tag, value in exif:
            key = str(PIL.ExifTags.TAGS.get(tag))
            if type(value) == bytes:
                raw[key] = base64.b64encode(value).decode('utf-8')
            else:
                raw[key] = str(value)

        time = (
            parse_timestamp(raw, 'DateTimeOriginal', 'SubSecTimeOriginal') or
            parse_timestamp(raw, 'DateTime', 'SubSecTime')
        )

        raw = {'pil': raw}

        return raw, {'taken_at': time}
    except PIL.UnidentifiedImageError:
        return {}, {}
