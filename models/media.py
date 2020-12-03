#!/usr/bin/env python

# Copyright (c) 2020 Matt Fichman <matt.fichman@gmail.com>
#
# This file is subject to the license terms in the LICENSE.md file found in
# the top-level directory of this software package. No person may use, copy,
# modify, publish, distribute, sublicense and/or sell any part of this file
# except according to the terms contained in the LICENSE.md file.

import models
import peewee
import datetime

class Media(peewee.Model):
    class Meta:
        database = models.db
        indexes = ((('extension', 'stem'), False),)

    types = (
        '.png', '.gif', '.jpg', '.jpeg', '.heic', '.jp2',
        '.mpg', '.mp4', '.mov', '.mkv',
    )

    name = peewee.CharField()
    stem = peewee.CharField()
    extension = peewee.CharField()
    path = peewee.CharField(index=True)
    digest = peewee.CharField(index=True)
    size = peewee.BigIntegerField()
    metadata = peewee.CharField()
    created_at = peewee.DateTimeField(default=datetime.datetime.now)
    updated_at = peewee.DateTimeField(default=datetime.datetime.now)
    taken_at = peewee.DateTimeField(index=True)
    organized_at = peewee.DateTimeField(null=True)
    source = peewee.CharField(unique=True)
    duplicate = peewee.BooleanField()
