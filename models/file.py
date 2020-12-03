#!/usr/bin/env python

# Copyright (c) 2020 Matt Fichman <matt.fichman@gmail.com>
#
# This file is subject to the license terms in the LICENSE.md file found in
# the top-level directory of this software package. No person may use, copy,
# modify, publish, distribute, sublicense and/or sell any part of this file
# except according to the terms contained in the LICENSE.md file.

import models
import peewee

class File(peewee.Model):
    class Meta:
        database = models.db

    path = peewee.CharField(index=True, unique=True)
    stem = peewee.CharField(index=True)
    extension = peewee.CharField(index=True)
    inspected_at = peewee.DateTimeField(index=True, null=True)
