# -*- coding: utf-8 -*-

from getpass import getpass
from gmusicapi import Mobileclient

# merge two track lists based on ID
def merge_track_lists(tracks, new_tracks):
    track_ids = [t.get('id') for t in tracks]
    for t in new_tracks:
        if t.get('id') not in track_ids:
            tracks.append(t)
    return tracks

# create a list of All Access track IDs from a list of tracks
def track_list_to_track_ids(tracks):
    return [get_aa_id(t) for t in tracks if get_aa_id(t)]

# check if track appears to be a valid All Access track
def track_has_aa_data(track):
    # test for unmatched track
    if track.get('type') == 2:
        return False
    # check storeId
    if track.has_key('storeId') and track.get('storeId').startswith('T'):
        return True
    #elif track.has_key('nid') and track.get('nid').startswith('T'):
    #    return True
    
    return False
  
# get key/value pair representing a radio station ID, return False if ID not present
# pass allowLocker = True to allow stations that are based on uploaded songs
def get_station_id(station, allowLocker = False):
    id_types = ['albumId', 'artistId', 'genreId', 'trackId']
    
    # if non-AA tracks are allowed, include trackLockerId
    if allowLocker: id_types.append('trackLockerId')
    
    return next(({t: station.get(t)} for t in id_types if station.has_key(t)), False)

# log into google music using a specified username and optional password
def mobile_api_login(username, password = False):
    if not password:
        # get the password from a prompt (probably safer than storing in plaintext)
        password = getpass(username + '\'s password: ')
    
    api = Mobileclient()
    if not api.login(username, password):
        print '*** ERROR: unable to login. Check your password or internet connection?'
        exit()
    password = None
    
    return api
