gmusic-migrate
==============

Account migration tool for Google Music All Access using gmusicapi. Exports your library, playlists, and radio stations from one All Access account and imports them into another account.

**Note: this tool is still in the early stages of development, and it relies on an unofficial API. Use this code at your own risk!**

##Prerequisites

python 2.7 - https://www.python.org

gmusicapi - https://github.com/simon-weber/Unofficial-Google-Music-API

##Usage

`python gmusic-migrate <origin account> <destination account>`

There are a number of optional command-line arguments; run the script without specifying any accounts and the program will list these for you.

##Notes and limitations

* If you use two factor authentication you will need to temporarily disable it or create and use application-specific passwords
* This script does not migrate stored ("locker") tracks that were uploaded through Google Music Manager. You should use Music Manager to migrate these tracks on your own.
* Ratings and playlist information for "locker" tracks will not be migrated
* You may see a lot of warnings about locker tracks (you can ignore these!)
* Thumbs-down ratings will only be applied to tracks in your library that have not been deleted
* Playlist subscriptions will not be migrated
* Play counts will be 0 on your new account
* All migrated playlists will be created as private
* Imported songs will lose any custom metadata, except for thumbs-up and thumbs-down ratings
* Look in your user log folder (or search for gmusic-migrate.log) to find the debug logs, can be useful to help you figure out what needs to be migrated manually

##Acknowledgments

Many thanks to the authors of gmusicapi and gmusic-playlist for making this possible.
