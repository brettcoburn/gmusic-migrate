# -*- coding: utf-8 -*-

import os
import appdirs
import errno
import logging

# merge two track lists based on ID
def merge_track_lists(tracks, new_tracks):
    track_ids = [t.get('id') for t in tracks]
    for t in new_tracks:
        if t.get('id') not in track_ids:
            tracks.append(t)
    return tracks

# match playlist track to library track
def match_track_by_id(track_id, library):
    matching_tracks = [t for t in library if t.get('id') == track_id]
    if matching_tracks:
        return matching_tracks[0]
    else:
        return False

# return a valid id (storeId or nid)
def get_aa_id(track):
    if track.has_key('storeId') and track.get('storeId').startswith('T'):
        return track.get('storeId')
    elif track.has_key('nid') and track.get('nid').startswith('T'):
        return track.get('nid')
    return False
    
# check if track appears to be a valid All Access track
def track_has_aa_data(track):
    if track.has_key('storeId') and track.get('storeId').startswith('T'):
        return True
    elif track.has_key('nid') and track.get('nid').startswith('T'):
        return True
    return False
  
# get key/value pair representing a radio station ID, return False if ID not present
# pass allow_locker=True to allow stations that are based on uploaded songs
def get_station_id(station, allow_locker = False):    
    seed = station.get('seed')
    
    if seed.has_key('albumId'):
        return {'album_id': seed.get('albumId')}
    elif seed.has_key('artistId'):
        return {'artist_id': seed.get('artistId')}
    elif seed.has_key('trackId'):
        return {'track_id': seed.get('trackId')}
    elif seed.has_key('genreId'):
        return {'genre_id': seed.get('genreId')}
    if seed.has_key('trackLockerId') and allow_locker:
        return {'track_id': seed.get('trackLockerId')}
    
    return False

# initialize logger
def logger(name, console_loglevel = 'INFO', file_loglevel = 'INFO'):
    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)

    # create null handler if running silent
    if console_loglevel == 'NONE' and file_loglevel == 'NONE':
        nh = logging.NullHandler()
        log.addHandler(nh)

    # set up console logging
    if console_loglevel != 'NONE':
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

        if console_loglevel == 'CRITICAL':
            ch.setLevel(logging.CRITICAL)
        elif console_loglevel == 'ERROR':
            ch.setLevel(logging.ERROR)
        elif console_loglevel == 'WARNING':
            ch.setLevel(logging.WARNING)
        elif console_loglevel == 'DEBUG':
            ch.setLevel(logging.DEBUG)
        else: ch.setLevel(logging.INFO)

        log.addHandler(ch)

    # set up file logging
    if file_loglevel != 'NONE':
        log_path = os.path.join(appdirs.user_log_dir(name), name + '.log')
        try:
            os.makedirs(os.path.dirname(log_path), 0o700)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

        fh = logging.FileHandler(log_path)
        fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s [%(levelname)s]: %(message)s'))

        if file_loglevel == 'CRITICAL':
            fh.setLevel(logging.CRITICAL)
        elif file_loglevel == 'ERROR':
            fh.setLevel(logging.ERROR)
        elif file_loglevel == 'WARNING':
            fh.setLevel(logging.WARNING)
        elif file_loglevel == 'DEBUG':
            fh.setLevel(logging.DEBUG)
        else: fh.setLevel(logging.INFO)

        log.addHandler(fh)

    return log
