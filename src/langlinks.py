# langlinks.py
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


import gi
gi.require_version('Gtk', '4.0')
from gi.repository import GLib, Gtk

from wike.data import languages


# Popover class for langlinks
# Show links to other languages for current page

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/ui/langlinks.ui')
class LanglinksPopover(Gtk.Popover):

  __gtype_name__ = 'LanglinksPopover'

  langlinks_list = Gtk.Template.Child()
  filter_entry = Gtk.Template.Child()

  # Set list filter function for entry content and connect signals

  def __init__(self, window):
    super().__init__()

    self._window = window

    self._langlinks = None
    self.langlinks_list.set_filter_func(self._filter_list, self.filter_entry)
    self.langlinks_list.set_sort_func(self._sort_list)
    self.langlinks_list.set_header_func(self._set_row_separator)

    self.langlinks_list.connect('row-activated', self._list_activated_cb)
    self.filter_entry.connect('search-changed', self._filter_entry_changed_cb)
    self.connect('show', self._popover_show_cb)

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

  # Set langlink row separator

  def _set_row_separator(self, row, before):
    if before and not row.get_header():
      separator = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)
      row.set_header(separator)

  # Populate langlinks list

  def populate(self, langlinks):
    self._langlinks = langlinks

    return self.refresh()

  # Refresh langlinks list

  def refresh(self):
    rows = self.langlinks_list.get_children()
    for row in rows:
      self.langlinks_list.remove(row)

    if self._langlinks != None:
      for langlink in self._langlinks:
        if langlink['lang'] in languages.items:
          row = LanglinkBoxRow(langlink['url'], langlink['lang'], langlink['autonym'].capitalize(), langlink['*'])
          self.langlinks_list.add(row)

    if len(self.langlinks_list.get_children()) > 0:
      return True
    else:
      return False

  # Load article in view on list activated

  def _list_activated_cb(self, langlinks_list, row):
    self.hide()
    self._window.page.wikiview.load_wiki(row.uri)

  # Refresh list on filter entry changed

  def _filter_entry_changed_cb(self, filter_entry):
    self.langlinks_list.invalidate_filter()

  # Unselect items and show popover

  def _popover_show_cb(self, popover):
    self.langlinks_list.show_all()
    self.langlinks_list.unselect_all()


# Class for row in langlinks list
# Create row from uri, language and page title

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/ui/langlinks-row.ui')
class LanglinkBoxRow(Gtk.ListBoxRow):

  __gtype_name__ = 'LanglinkBoxRow'

  langlink_lang = Gtk.Template.Child()
  langlink_title = Gtk.Template.Child()
  langlink_id = Gtk.Template.Child()

  # Set values

  def __init__(self, uri, lang, lang_name, title):
    super().__init__()

    self.uri = uri
    self.lang = lang
    self.lang_name = lang_name

    self.langlink_lang.set_label(lang_name)
    self.langlink_title.set_markup('<small>' + GLib.markup_escape_text(title, -1) + '</small>')
    self.langlink_id.set_label(lang)

