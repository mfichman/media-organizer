#!/usr/bin/env python

# Copyright (c) 2020 Matt Fichman <matt.fichman@gmail.com>
#
# This file is subject to the license terms in the LICENSE.md file found in
# the top-level directory of this software package. No person may use, copy,
# modify, publish, distribute, sublicense and/or sell any part of this file
# except according to the terms contained in the LICENSE.md file.

from . import pil
from . import exif
from . import hachoir
from . import stat
from . import path

parsers = {
    # .gif, .png, .mpg, .mpeg, .mkv, .mp4
    '.jpg': [stat, path, exif, pil],
    '.jpeg': [stat, path, exif, pil],
    '.jp2': [stat, path, exif, pil],
    '.heic': [stat, path, exif, pil],
    '.png': [stat, path],
    '.gif': [stat, path],
    '.mov': [stat, path, hachoir],
    '.mp4': [stat, path, hachoir],
    '.mkv': [stat, path, hachoir],
    '.aae': [stat, path]
}

def remove_nulls(metadata):
    return {k: v for k, v in metadata.items() if v is not None}

def parse(path):
    merged_metadata = {}
    merged_raw = {}

    for parser in parsers[path.suffix.lower()]:
        raw, metadata = parser.parse(path)

        merged_metadata.update(remove_nulls(metadata))
        merged_raw.update(remove_nulls(raw))

    return merged_raw, merged_metadata
