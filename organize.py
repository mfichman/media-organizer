#!/bin/env python

import argparse
import base64
import datetime
import functools
import glob
import hashlib
import humanize
import itertools
import json
import multiprocessing
import os
import pathlib
import peewee
import re
import signal
import sys

import metadata

db = peewee.SqliteDatabase('media.db', pragmas={'journal_mode': 'wal'})

class File(peewee.Model):
    class Meta:
        database = db

    path = peewee.CharField(index=True, unique=True)
    stem = peewee.CharField(index=True)
    extension = peewee.CharField(index=True)
    inspected_at = peewee.DateTimeField(index=True, null=True)

class Media(peewee.Model):
    class Meta:
        database = db
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

def parse_digest(path):
    sha = hashlib.sha256()
    buf = bytearray(32768)
    mv = memoryview(buf)

    with open(path, 'rb', buffering=0) as fd:
        for offset in iter(lambda: fd.readinto(mv), 0):
            sha.update(mv[:offset])

    return sha.hexdigest()

def parse_metadata(path):
    return metadata.parse(path)

def parse_media(args, source):
    suffix = source.suffix.lower()

    if suffix not in Media.types:
        return (source, None, ['skipped'])

    digest = parse_digest(source)
    raw, metadata = parse_metadata(source)
    taken_at = metadata['taken_at']

    year = taken_at.strftime('%Y')
    month = taken_at.strftime('%m')
    sec = taken_at.strftime('%H%M%S')
    stem = '-'.join((sec, digest[:16]))

    path = args.output.joinpath(year, month, stem).with_suffix(suffix)

    stat = source.stat()

    result = dict(
        name=str(source.name),
        stem=str(source.stem),
        extension=str(suffix),
        metadata=json.dumps(raw),
        path=str(path),
        digest=str(digest),
        size=int(stat.st_size),
        taken_at=taken_at,
        source=str(source),
    )

    messages = []
    if not metadata: messages.append('failed to parse metadata')

    return (source, result, messages)

def save_media(params):
    query = Media.insert(params).on_conflict(conflict_target=[Media.source], update=params)
    query.execute()

    query = File.update(inspected_at=datetime.datetime.now()).where(File.path == params['source'])
    query.execute()

    return Media.select().where(Media.digest == params['digest']).execute()[0]

def input_iterator(args):
    for folder in args.input:
        folder = pathlib.Path(folder)
        for path in itertools.chain([folder], folder.glob(r'**\*')):
            if path.is_file():
                yield path

def init_worker():
    signal.signal(signal.SIGINT, signal.SIG_IGN)

def log_write(log, message):
    log.write(message)
    log.write('\n')
    print(message)

def find_files(args, db):
    total = file_count_total(input_iterator(args))

    for index, path in enumerate(input_iterator(args)):
        print('{} {}/{}'.format(path, index, total))
        params = dict(path=path, extension=path.suffix, stem=path.stem)
        query = File.insert(params).on_conflict(conflict_target=[File.path], update=params)
        query.execute()

def file_count_total(paths):
    return sum(1 for _ in paths)

def file_size_total(paths):
    return sum(path.stat().st_size for path in paths)

def read_files(args, pool, db):
    files = File.select().where(File.inspected_at.is_null()).execute()
    paths = [pathlib.Path(f.path) for f in files]

    count_total = file_count_total(paths)
    size_total = file_size_total(paths)

    log = open('media.log', 'w')

    parse = functools.partial(parse_media, args)

    count_processed = 0
    size_processed = 0

    for (path, result, messages) in pool.imap(parse, paths):
    #for (path, result, messages) in map(parse, input_iterator(args)):
        count_processed += 1
        size_processed += path.stat().st_size

        for message in messages:
            log_write(log, '{}: {}'.format(message, path))

        if result is None:
            continue

        save_media(result)

        print('{} {} {}/{} {}/{}'.format(
            result['source'],
            result['path'],
            count_processed,
            count_total,
            humanize.naturalsize(size_processed),
            humanize.naturalsize(size_total)
        ))

def organize_files(args, pool, db):
    photos = Media.select()\
        .where(Media.organized_at.is_null())\
        .order_by(Media.taken_at.asc(), Media.id.asc())\
        .group_by(Media.digest)\
        .limit(10)

    for parent in set(pathlib.Path(photo.path).parent for photo in photos):
        parent.mkdir(parents=True, exist_ok=True)

    for photo in photos:
        with db:
            photo.organized_at = datetime.datetime.now()
            photo.save()
            source = pathlib.Path(photo.source)
            source.rename(photo.path)
            print('mv', photo.source, photo.path)

def main():
    parser = argparse.ArgumentParser(description='organize photos')
    parser.add_argument('input', nargs='*', default=[])
    parser.add_argument('--output', '-o', default=r'E:\Photos', type=pathlib.Path)
    args = parser.parse_args()

    db.connect()
    db.create_tables([Media, File])

    args.input = args.input or (
        r'E:\JilliPhotos',
        r'E:\iCloud Photos',
        r'E:\Google Photos (Newly Added Photos)',
        r'E:\Google Drive\Photos\Natalie',
        r'E:\Google Drive\Videos\Family Videos',
        r'E:\Google Drive\Videos\Year',
    )
    #import logging
    #logger = logging.getLogger('peewee')
    #logger.addHandler(logging.StreamHandler())
    #logger.setLevel(logging.DEBUG)

    pool = multiprocessing.Pool(2, init_worker)

    #find_files(args, db)
    read_files(args, pool, db)
    #organize_files(args, pool, db)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
