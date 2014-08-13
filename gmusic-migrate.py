#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import datetime
from getpass import getpass

from gmusicapi import Mobileclient
from gmusicapi.utils import utils
from gmusicapi.exceptions import CallFailure

from common import *

# set up command-line arguments
parser = argparse.ArgumentParser(description='Account migration tool for Google Music All Access using gmusicapi')
parser.add_argument('origin', help='origin account email')
parser.add_argument('-op', default=False, help='password for origin account (note, passing this on the command line is OPTIONAL and not very secure!)')
parser.add_argument('destination', help='destination account email')
parser.add_argument('-dp', required=False, help='password for destination account')
parser.add_argument('-v', choices=['NONE', 'CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'], required=False, default='INFO', help='verbosity of console output, default is INFO')
parser.add_argument('-loglevel', choices=['NONE', 'CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'], required=False, default="DEBUG", help='verbosity for file logging, default is DEBUG')
parser.add_argument('-migrate', choices=['all', 'tracks', 'ratings', 'playlists', 'stations'], required=False, default='all', help='what to migrate, default is all')
parser.add_argument('-simulate', nargs='?', required=False, const=True, default=False, help='make a practice run (don\'t make any changes)')

# parse command-line arguments
args = vars(parser.parse_args())
export_username = args.get('origin')
export_password = args.get('op')
import_username = args.get('destination')
import_password = args.get('dp')
console_loglevel = args.get('v')
file_loglevel = args.get('loglevel')
migration_type = args.get('migrate')
simulate = args.get('simulate')

# create API objects to initialize logs
export_api = Mobileclient()
import_api = Mobileclient()

# set up logger
log = logger('gmusic-migrate', console_loglevel, file_loglevel)
log.debug('Logging initialized')

if simulate:
    log.info('Running as simulation (no changes will be made)')

# log in with both users
if not export_password:
    log.debug('No password provided, requesting from console')
    export_password = getpass('Password for ' + export_username + ': ')
log.debug('Logging in with user ' + export_username)
if not export_api.login(export_username, export_password):
    log.critical('Login failed! Check your username, password, and network connection')
    exit()
export_password = None
log.debug('Login successful for ' + export_username)

if not import_password:
    log.debug('No password provided, requesting from console')
    import_password = getpass('Password for ' + import_username + ': ')
log.debug('Logging in with user ' + import_username)
if not import_api.login(import_username, import_password):
    log.critical('Unable to login; check your username, password, and network connection')
    exit()
import_password = None
log.debug('Login successful for ' + import_username)

# load the library, playlists, thumbs up tracks, and stations

log.debug('Migration type is ' + migration_type)
log.info('Exporting data from ' + export_username)

if migration_type != 'stations':
    log.info('Retrieving tracks from ' + export_username)
    export_tracks = export_api.get_all_songs()
    # strip out any tracks that are not available on All Access
    all_tracks = [t for t in export_tracks if track_has_aa_data(t) and not t.get('deleted')]

if migration_type == 'all' or migration_type == 'ratings':
    log.info('Retrieving thumbs up tracks from ' + export_username)
    export_thumbs_up = export_api.get_thumbs_up_songs()
    # strip out any tracks that are not available on All Access
    thumbs_up_tracks = [t for t in export_thumbs_up if track_has_aa_data(t)]

if migration_type == 'all' or migration_type == 'playlists':
    log.info('Retrieving playlists from ' + export_username)
    export_playlists = export_api.get_all_user_playlist_contents()
    playlists = [p for p in export_playlists if not p.get('deleted')]

if migration_type == 'all' or migration_type == 'stations':  
    log.info('Retrieving stations from ' + export_username)
    export_stations = export_api.get_all_stations()
    radio_stations = [s for s in export_stations if not s.get('deleted')]

log.info('Export complete')
export_api.logout()
log.debug('API logout for ' + export_username)

# import tracks
if migration_type == 'all' or migration_type == 'tracks':
    log.info('Importing ' + str(len(all_tracks)) + ' All Access tracks to ' + import_username)
    
    for i, track in enumerate(all_tracks, start=1):
        track_id = get_aa_id(track)
        track_artist = track.get('artist')
        track_title = track.get('title')

        if i % 100 == 0:
            log.info('Importing track ' + str(i) + ' of ' + str(len(all_tracks)))
        if not simulate:
            try:
                import_api.add_aa_track(track_id)
            except CallFailure as e:
                log.error('Add failed for track ' + track_artist + ' - ' + track_title)
                log.debug('ID of failed track is ' + track_id)
                continue

# create consolidated list of library and thumbs up tracks with a rating
if migration_type == 'all' or migration_type == 'ratings':
    merged_tracks = merge_track_lists(all_tracks, thumbs_up_tracks)
    rated_tracks = [t for t in merged_tracks if t.get('rating', 0) > 0]
    
    log.info('Importing ' + str(len(rated_tracks)) + ' track ratings to ' + import_username)

    # set rating on tracks
    for i, track in enumerate(rated_tracks, start=1):
        track_id = get_aa_id(track)
        track_rating = track.get('rating')
        track_artist = track.get('artist')
        track_title = track.get('title')
        
        if i % 100 == 0:
            log.info('Rating track ' + str(i) + ' of ' + str(len(rated_tracks)))
        
        # get track info from new account and set rating
        try:
            new_track = import_api.get_track_info(track_id)
        except CallFailure as e:
            log.error('Failed to retrieve data for track ' + track_artist + ' - ' + track_title)
            log.debug('ID of failed track is ' + track_id)
            continue
        
        new_track['rating'] = track_rating
        new_track_artist = new_track.get('artist')
        new_track_title = new_track.get('title')
        
        if track_artist != new_track_artist:
            log.warning('Track artists do not match (' + track_artist + ' != ' + new_track_artist + ')')
        if track_title != new_track_title:
            log.warning('Track titles do not match (' + track_title + ' != ' + new_track_title + ')')
        
        if not simulate:
            try:
                import_api.change_song_metadata(new_track)
            except CallFailure as e:
                log.error('Failed to set rating on track ' + new_track_artist + ' - ' + new_track_title)
                log.debug('ID of failed track is ' + track_id)
                continue

# import all playlists
if migration_type == 'all' or migration_type == 'playlists':
    log.info('Importing ' + str(len(playlists)) + ' playlists to ' + import_username)
    
    for i, playlist in enumerate(playlists, start=1):
        if i % 10 == 0:
            log.info('Creating playlist ' + str(i) + ' of ' + str(len(playlists)))
        
        playlist_name = playlist.get('name')
        playlist_description = playlist.get('description')
        playlist_created = playlist.get('creationTimestamp')
        playlist_tracks = playlist.get('tracks')
        
        # match tracks with library tracks
        log.debug('Matching playlist track IDs')
        matched_tracks = [match_track_by_id(t.get('trackId'), all_tracks) for t in playlist_tracks]
        track_ids = [get_aa_id(t) for t in matched_tracks if t]
        
        # name noname playlists using date created
        if not playlist_name:
            log.warning('Replacing blank playlist name with timestamp')
            playlist_name = playlist_created

        # skip empty playlists
        if len(track_ids) == 0:
            log.warning('Skipping playlist ' + playlist_name + ' (no tracks available in All Access)')
            continue
            
        log.debug('Creating playlist ' + playlist_name)
        if not simulate:
            try:
                playlist_id = import_api.create_playlist(playlist_name)
            except CallFailure as e:
                log.error('Failed to create playlist ' + playlist_name)
                continue

        log.debug('Adding ' + str(len(track_ids)) + ' tracks to playlist')
        if not simulate:
            try:
                import_api.add_songs_to_playlist(playlist_id, track_ids)
            except CallFailure as e:
                log.error('Failed to add tracks to playlist ' + playlist_name)
                continue

# import all radio stations
if migration_type == 'all' or migration_type == 'stations':
    log.info('Importing ' + str(len(radio_stations)) + ' radio stations to ' + import_username)
    
    for station in radio_stations:
        station_name = station.get('name')
        station_id = get_station_id(station)

        if not station_id:
            log.warning('Skipping station with invalid ID (probably not All Access)')
            continue
        
        if not simulate:
            try:
                import_api.create_station(station_name, **station_id)
            except CallFailure as e:
                log.error('Failed to create station for ' + station_id)
                continue

# import done, logout
import_api.logout()
log.debug('API logout for user ' + import_username)
log.info('Migration complete!')
