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
import re
import signal
import sys
import peewee

import models
import metadata

from models import Media, File

def file_size(path):
    try:
        print('stat:', path)
        return path.stat().st_size
    except:
        return 0;

def file_count_total(paths):
    return sum(1 for _ in paths)

def file_size_total(paths):
    return sum(file_size(path) for path in paths)

def digest_for(path):
    sha = hashlib.sha256()
    buf = bytearray(32768)
    mv = memoryview(buf)

    with open(path, 'rb', buffering=0) as fd:
        for offset in iter(lambda: fd.readinto(mv), 0):
            sha.update(mv[:offset])

    return sha.hexdigest()

def metadata_for(path):
    return metadata.parse(path)

def path_for(args, digest, stem, taken_at, suffix):
    year = taken_at.strftime('%Y')
    month = taken_at.strftime('%m')
    day = taken_at.strftime('%d')
    sec = taken_at.strftime('%H%M%S')
    stem = '-'.join((sec, stem, digest[:16]))

    return args.output.joinpath(year, month, day, stem).with_suffix(suffix)

def record_for(args, source):
    suffix = source.suffix.lower()

    if suffix not in Media.types:
        return (source, None, ['skipped'])

    try:
        digest = digest_for(source)
        raw, metadata = metadata_for(source)
        taken_at = metadata['taken_at']

        path = path_for(args, digest, source.stem, taken_at, suffix)

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
    except FileNotFoundError:
        return (source, None, ['missing'])

def save_media(params):
    query = Media.insert(params).on_conflict(conflict_target=[Media.source], update=params)
    query.execute()

    mark_processed(params['source'])

    return Media.select().where(Media.digest == params['digest']).execute()[0]

def mark_processed(path):
    query = File.update(inspected_at=datetime.datetime.now()).where(File.path == path)
    query.execute()

def input_iterator(args):
    for folder in args.input:
        folder = pathlib.Path(folder)
        for path in itertools.chain([folder], folder.glob(r'**\*')):
            if path.is_file():
                yield path

def init_worker():
    signal.signal(signal.SIGINT, signal.SIG_IGN)

def find(args):
    total = file_count_total(input_iterator(args))

    for index, path in enumerate(input_iterator(args)):
        print('find: {} {}/{}'.format(path, index, total))
        params = dict(path=path, extension=path.suffix, stem=path.stem)
        File.insert(params)\
            .on_conflict(
                preserve=[File.inspected_at],
                conflict_target=[File.path],
                update=params
            )\
            .execute()

def process(args, pool, log):
    files = File.select().where(File.inspected_at.is_null()).execute()
    paths = [pathlib.Path(f.path) for f in files]

    count_total = file_count_total(paths)
    size_total = file_size_total(paths)

    parse = functools.partial(record_for, args)

    count_processed = 0
    size_processed = 0

    for (path, result, messages) in pool.imap(parse, paths):
    #for (path, result, messages) in map(parse, input_iterator(args)):
        count_processed += 1
        size_processed += file_size(path)

        for message in messages:
            print('error: {}: {}'.format(message, path))

        if result is None:
            mark_processed(path)
            continue

        save_media(result)

        print('process: {} {} {}/{} {}/{}'.format(
            result['source'],
            result['path'],
            count_processed,
            count_total,
            humanize.naturalsize(size_processed),
            humanize.naturalsize(size_total)
        ))

def organize(args, pool, log):
    photos = Media.select()\
        .where(Media.organized_at.is_null(), ~Media.duplicate)\
        .order_by(Media.id.asc())

    for parent in set(pathlib.Path(photo.path).parent for photo in photos):
        parent.mkdir(parents=True, exist_ok=True)

    for photo in photos:
        photo.organized_at = datetime.datetime.now()
        photo.save()
        source = pathlib.Path(photo.source)
        try:
            source.rename(photo.path)
            print('mv:', photo.source, photo.path)
        except FileNotFoundError as e:
            print('error:', str(e))

def deduplicate():
    gold = Media.select(
        peewee.fn.first_value(Media.id).over(
            partition_by=Media.digest,
            order_by=[
                Media.organized_at.asc(nulls='LAST'),
                peewee.fn.length(Media.stem).asc(),
                Media.taken_at.asc()
            ]
        ).distinct()
    )

    with Media.db:
        Media.update(duplicate=False).execute()
        Media.update(duplicate=True).where(Media.id.not_in(gold)).execute()

def main():
    parser = argparse.ArgumentParser(description='organize photos')
    parser.add_argument('input', nargs='*', default=[])
    parser.add_argument('--output', '-o', default=r'E:\Photos', type=pathlib.Path)
    args = parser.parse_args()

    models.db.connect()
    models.db.create_tables([Media, File])

    pool = multiprocessing.Pool(2, init_worker)
    log = open('media.log', 'w')

    find(args)
    process(args, pool, log)
    deduplicate()
    organize(args, pool, log)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
