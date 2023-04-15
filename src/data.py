# This file is part of Wike (com.github.hugolabe.Wike)
# SPDX-FileCopyrightText: 2021-23 Hugo Olabera <hugolabe@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later


import json
from datetime import datetime

from gi.repository import GLib, Gio


# Create app settings object and set data path

settings = Gio.Settings.new('com.github.hugolabe.Wike')
_data_path = GLib.get_user_data_dir()


# Wikipedia languages (wikilangs dict: all languages, items dict: user languages)

class Languages:

  items = {}
  global _data_path
  _file_path = _data_path + '/languages.json'

  # Load all languages from resource and user languages from file

  def __init__(self):
    gfile = Gio.File.new_for_uri('resource:///com/github/hugolabe/Wike/languages/languages.min.json')
    try:
      gfile_contents = gfile.load_contents(None)
    except:
      print('Can\'t load languages file from resources')
      return
    else:
      content = gfile_contents[1].decode('utf-8')
      self.wikilangs = json.loads(content)

    try:
      with open(self._file_path, 'r') as file:
        self.items = json.load(file)
    except:
      self.items['en'] = 'English'

  # Clear languages list (user)

  def clear(self):
    self.items.clear()

  # Save json languages file

  def save(self):
    with open(self._file_path, 'w') as file:
      json.dump(self.items, file)


# History of recent articles

class History:

  global _data_path
  _file_path = _data_path + '/historic.json'

  # Load json history file

  def __init__(self):
    global settings

    if settings.get_boolean('keep-history'):
      try:
        with open(self._file_path, 'r') as file:
          self.items = json.load(file)
      except:
        self.items = {}
    else:
      self.items = {}

  # Add article to history

  def add(self, uri, title, lang):
    now = datetime.today()
    date = now.strftime('%Y-%m-%d')
    time = now.strftime('%H:%M:%S')
    if date in self.items:
      self.items[date][uri] = [time, title, lang]
    else:
      self.items[date] = {uri: [time, title, lang]}

  # Clear history

  def clear(self):
    self.items.clear()

  # Save json history file

  def save(self):
    with open(self._file_path, 'w') as file:
      json.dump(self.items, file)


# Lists of bookmarks

class Bookmarks:

  global _data_path
  _file_path = _data_path + '/bookmarks.json'
  _lists_path = _data_path + '/booklists.json'

  # Load json bookmarks and lists files

  def __init__(self):

    try:
      with open(self._file_path, 'r') as file:
        self.items = json.load(file)
    except:
      self.items = {}

    try:
      with open(self._lists_path, 'r') as file:
        self.lists = json.load(file)
    except:
      self.lists = {}

  # Add article to bookmarks list

  def add(self, uri, title, lang, list_name):
    if list_name:
      bookmarks_items = self.lists[list_name]
    else:
      bookmarks_items = self.items

    if not uri in bookmarks_items:
      bookmarks_items[uri] = [title, lang]
      return True
    else:
      return False

  # Remove article from bookmarks list

  def remove(self, uri, list_name):
    if list_name:
      bookmarks_items = self.lists[list_name]
    else:
      bookmarks_items = self.items

    if uri in bookmarks_items:
      del bookmarks_items[uri]
      return True
    else:
      return False

  # Create new empty list of bookmarks

  def new_list(self, list_name):
    if not list_name in self.lists.keys():
      self.lists[list_name] = {}
      return True
    else:
      return False

  # Remove an existing list of bookmarks

  def remove_list(self, list_name):
    if list_name in self.lists.keys():
      del self.lists[list_name]
      return True
    else:
      return False

  # Rename an existing list of bookmarks

  def rename_list(self, list_name, new_name):
    if list_name in self.lists.keys():
      self.lists[new_name] = self.lists.pop(list_name)
      return True
    else:
      return False

  # Clear (empty) a list of bookmarks

  def clear_list(self, list_name):
    if list_name:
      self.lists[list_name].clear()
    else:
      self.items.clear()

  # Save json bookmarks and lists files

  def save(self):
    with open(self._file_path, 'w') as file:
      json.dump(self.items, file)

    with open(self._lists_path, 'w') as file:
      json.dump(self.lists, file)


# Create global objects for languages, history and bookmarks

languages = Languages()
history = History()
bookmarks = Bookmarks()
