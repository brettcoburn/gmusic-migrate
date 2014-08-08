#!/usr/bin/env python
# -*- coding: utf-8 -*-

#import os
#import sys
import argparse
import datetime
from gmusicapi.exceptions import CallFailure

from common import *

# parse command-line arguments
parser = argparse.ArgumentParser(description='Account migration tool for Google Music All Access using gmusicapi.')
parser.add_argument('origin', help='origin email account')
parser.add_argument('-op', default=False, help='password for origin email account')
parser.add_argument('destination', help='destination email account')
parser.add_argument('-dp', required=False, help='password for destination email account')
args = vars(parser.parse_args())
export_username = args.get('origin')
export_password = args.get('op')
import_username = args.get('destination')
import_password = args.get('dp')

# log in with both users
export_api = mobile_api_login(export_username, export_password)
import_api = mobile_api_login(import_username, export_password)

# load the library, playlists, thumbs up tracks, and stations
print 'Preparing to export data...'
print '* Exporting data from ' + export_username

# strip out any tracks that are not available on All Access
all_tracks = [t for t in export_api.get_all_songs() if track_has_aa_data(t)]
thumbs_up_tracks = [t for t in export_api.get_thumbs_up_songs() if track_has_aa_data(t)]

playlist_contents = export_api.get_all_user_playlist_contents()
radio_stations = export_api.get_all_stations()

# export done, logout 
print 'Export complete!\n'
print 'Preparing to import data...'
export_api.logout()

# import All Access tracks
print '* Importing All Access tracks'
for track in all_tracks:
    track_id = track.get('storeId')
    
    try:
        import_api.add_aa_track(track_id)
    except CallFailure as e:
        print "*** ERROR: Add failed for track " + track.get('artist') + " - " + track.get('title')

# create consolidated list of library and thumbs up tracks with a rating
print '* Importing track ratings'
rated_tracks = merge_track_lists(all_tracks, thumbs_up_tracks)
rated_tracks = [t for t in rated_tracks if t.get('rating', 0) > 0]

# set rating on tracks
for track in rated_tracks:
    track_id = track.get('storeId')
    track_rating = track.get('rating')
      
    # get track info from new account and set rating
    new_track = import_api.get_track_info(track_id)
    new_track['rating'] = track_rating
    
    try:
        import_api.change_song_metadata(new_track)
    except CallFailure as e:
        print "*** ERROR: Failed to set rating on track " + track.get('artist') + " - " + track.get('title')
             
# import all playlists
print '* Importing playlists'
for playlist in playlist_contents:
    playlist_name = playlist.get('name')
    playlist_description = playlist.get('description')
    playlist_created = playlist.get('creationTimestamp')
    
    # remove any songs not in All Access
    playlist_tracks = [t for t in playlist.get('tracks') if track_has_aa_data(t)]
    
    # skip empty playlists
    if len(playlist_tracks) == 0: continue
    
    # name noname playlists using date created
    if not playlist_name:
        playlist_name = datetime.datetime.utcfromtimestamp(
            int(playlist_created)).strftime('%c')
    
    # create playlist
    try:
        import_api.create_playlist(playlist_name)
    except CallFailure as e:
        print "*** ERROR: Failed to create playlist " + playlist_name
    
    # add All Access tracks to playlist
    track_ids = track_list_to_track_ids(playlist_tracks)
    
    try:
        import_api.add_songs_to_playlist(track_ids)
    except CallFailure as e:
        print "*** ERROR: Failed to add songs to playlist " + playlist_name

# import all radio stations
print '* Importing radio stations'
for station in radio_stations:
    station_id = get_station_id(station)
    
    if not station_id: continue
    
    try:
        import_api.create_station(station_id)
    except CallFailure as e:
        print "*** ERROR: Failed to create station for " + station_id

# import done, logout
import_api.logout()
print 'Migration complete!'
