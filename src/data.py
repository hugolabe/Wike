# data.py
#
# This file is part of Wike, a Wikipedia Reader for the GNOME Desktop.
# Copyright 2021 Hugo Olabera <hugolabe@gmail.com>.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import datetime
import errno
import json
import os

import gi
from gi.repository import Gio, GLib

from wike import wikipedia


# Create app settings object and set search language

settings = Gio.Settings.new('com.github.hugolabe.Wike')
if settings.get_string('search-language') != 'en':
  wikipedia.set_lang(settings.get_string('search-language'))

_data_path = GLib.get_user_data_dir()


# Class for Wikipedia languages
# wikilangs dict: all languages, items dict: filtered languages

class Languages:

  items = {}
  wikilangs = {}
  global _data_path
  _file_path = _data_path + '/languages.json'

  # Load all languages from resource and filtered languages from file

  def __init__(self):
    gfile = Gio.File.new_for_uri('resource:///com/github/hugolabe/Wike/languages/languages.min.json')
    try:
      gfile_contents = gfile.load_contents(None)
    except:
      print('Can\'t load languages file from resources')
      return
    else:
      content = gfile_contents[1].decode('utf-8')
      wikipedia_langs = json.loads(content)
      for lang_key in wikipedia_langs.keys():
        self.wikilangs[lang_key] = wikipedia_langs[lang_key]

    if os.path.exists(self._file_path):
      with open(self._file_path, 'r') as file:
        json_langs = json.load(file)
      for lang_key in json_langs.keys():
        self.items[lang_key] = json_langs[lang_key]
    else:
      self.items['en'] = 'English'

  # Clear languages list (filtered)

  def clear(self):
    self.items.clear()

  # Save json languages file

  def save(self):
    with open(self._file_path, 'w') as file:
      json.dump(self.items, file)


# Class for historic
# Maintains a list of viewed articles

class Historic:

  items = {}
  global _data_path
  _file_path = _data_path + '/historic.json'

  # Load json historic file

  def __init__(self):
    global settings

    if settings.get_boolean('keep-historic') and os.path.exists(self._file_path):
      with open(self._file_path, 'r') as file:
        json_historic = json.load(file)
        i = 0
        for item_key in sorted(json_historic.keys(), reverse=True):
          self.items[item_key] = json_historic[item_key]
          i += 1
          if i > 50: break

  # Add article to historic

  def add(self, uri, title, lang):
    now = datetime.datetime.today()
    date = now.strftime('%Y-%m-%d')
    time = now.strftime('%H:%M:%S')
    if date in self.items:
      self.items[date][uri] = [time, title, lang]
    else:
      self.items[date] = {uri: [time, title, lang]}

  # Clear historic

  def clear(self):
    self.items.clear()

  # Save json historic file

  def save(self):
    with open(self._file_path, 'w') as file:
      json.dump(self.items, file)


# Class for bookmarks
# List of articles marked for read later

class Bookmarks:

  items = {}
  global _data_path
  _file_path = _data_path + '/bookmarks.json'

  # Load json bookmarks file

  def __init__(self):
    if os.path.exists(self._file_path):
      with open(self._file_path, 'r') as file:
        json_bookmarks = json.load(file)
      for item_key in json_bookmarks.keys():
        self.items[item_key] = json_bookmarks[item_key]

  # Add article to bookmarks

  def add(self, uri, title, lang):
    if not uri in self.items:
      self.items[uri] = [title, lang]
      return True
    else:
      return False

  # Remove article from bookmarks

  def remove(self, uri):
    del self.items[uri]

  # Clear list of bookmarks

  def clear(self):
    self.items.clear()

  # Save json bookmarks file

  def save(self):
    with open(self._file_path, 'w') as file:
      json.dump(self.items, file)


# Create global objects for languages, historic and bookmarks

languages = Languages()
historic = Historic()
bookmarks = Bookmarks()

