# This file is part of Wike (com.github.hugolabe.Wike)
# SPDX-FileCopyrightText: 2021-23 Hugo Olabera <hugolabe@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later


import json

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import GLib, Gio, Gtk, Adw

from wike.data import settings, languages


# Box for language links in sidebar

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/ui/langlinks.ui')
class LanglinksBox(Gtk.Box):

  __gtype_name__ = 'LanglinksBox'

  filter_entry = Gtk.Template.Child()
  langlinks_list = Gtk.Template.Child()
  langlinks_scroller = Gtk.Template.Child()
  langlinks_separator = Gtk.Template.Child()

  # Initialize widgets and connect signals

  def __init__(self, window):
    super().__init__()

    self._window = window

    self.langlinks_list.set_filter_func(self._filter_list, self.filter_entry)
    self.langlinks_list.set_sort_func(self._sort_list)
    
    settings.connect('changed::show-flags', self._settings_show_flags_changed_cb)

    self.filter_entry.connect('search-changed', self._filter_entry_changed_cb)
    self.langlinks_list.connect('row-activated', self._list_activated_cb)
    self.langlinks_scroller.get_vadjustment().connect('value-changed', self._langlinks_scrolled_cb)
    
  # Filter list for entry content

  def _filter_list(self, row, filter_entry):
    text = filter_entry.get_text()
    if text == '':
      return True

    if row.lang_name.lower().startswith(text.lower()) or row.lang.lower().startswith(text.lower()):
      return True
    else:
      return False

  # Sort list alphabetically

  def _sort_list(self, row1, row2):
    if row1.lang > row2.lang:
      return 1
    elif row1.lang < row2.lang:
      return -1
    else:
      return 0

  # Populate langlinks list

  def populate(self, langlinks):
    self.langlinks_scroller.get_vadjustment().set_value(0)

    while True:
      row = self.langlinks_list.get_row_at_index(0)
      if row:
        self.langlinks_list.remove(row)
      else:
        break

    if langlinks:
      for langlink in langlinks:
        if langlink['lang'] in languages.items:
          row = LanglinksRow(langlink['url'], langlink['lang'], langlink['autonym'].capitalize(), langlink['*'])
          self.langlinks_list.append(row)

  # Settings show flags changed event

  def _settings_show_flags_changed_cb(self, settings, key):
    self.populate(self._window.page.wikiview.langlinks)

  # Refresh list on filter entry changed

  def _filter_entry_changed_cb(self, filter_entry):
    self.langlinks_list.invalidate_filter()

  # On list activated load page in choosen language

  def _list_activated_cb(self, langs_list, row):
    if self._window.flap.get_fold_policy() == Adw.FlapFoldPolicy.ALWAYS:
      self._window.flap.set_reveal_flap(False)

    self._window.page.wikiview.load_wiki(row.uri)

  # Show/hide separator on scroll

  def _langlinks_scrolled_cb(self, adjustment):
    if adjustment.get_value() > 0:
      self.langlinks_separator.set_visible(True)
    else:
      self.langlinks_separator.set_visible(False)


# Row on langlinks list

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/ui/langlinks-row.ui')
class LanglinksRow(Gtk.ListBoxRow):

  __gtype_name__ = 'LanglinksRow'

  lang_label = Gtk.Template.Child()
  title_label = Gtk.Template.Child()
  flag_image = Gtk.Template.Child()

  # Set values and widgets

  def __init__(self, uri, lang, lang_name, title):
    super().__init__()

    self.uri = uri
    self.lang = lang
    self.lang_name = lang_name

    self.lang_label.set_label(lang_name)
    self.title_label.set_markup('<small>' + GLib.markup_escape_text(title, -1) + '</small>')

    if settings.get_boolean('show-flags'):
      gfile = Gio.File.new_for_uri('resource:///com/github/hugolabe/Wike/icons/scalable/emblems/' + lang + '.svg')
      if gfile.query_exists():
        self.flag_image.set_from_icon_name(lang)
    else:
      self.flag_image.set_visible(False)
