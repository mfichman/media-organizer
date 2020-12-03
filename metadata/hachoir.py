#!/usr/bin/env python

# Copyright (c) 2020 Matt Fichman <matt.fichman@gmail.com>
#
# This file is subject to the license terms in the LICENSE.md file found in
# the top-level directory of this software package. No person may use, copy,
# modify, publish, distribute, sublicense and/or sell any part of this file
# except according to the terms contained in the LICENSE.md file.

import hachoir.parser
import hachoir.metadata
import hachoir.core
import datetime

def parse_timestamp(metadata):
    try:
        return datetime.datetime.strptime(metadata['Creation date'], '%Y-%m-%d %H:%M:%S')
    except KeyError:
        return None

def parse(path):
    #hachoir.core.config.quiet = True

    try:
        parser = hachoir.parser.createParser(str(path))
        metadata = hachoir.metadata.extractMetadata(parser)
        raw = metadata.exportDictionary().get('Metadata', {})
        time = parse_timestamp(raw)

        raw = {'hachoir': raw}

        return raw, {'taken_at': time}
    except:
        return {}, {}
