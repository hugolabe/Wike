# search.py
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


from threading import Thread

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gio, GLib, GObject, Gtk

from wike import wikipedia
from wike.data import settings, languages
from wike.view import wikiview


# Search entry class
# Manage article searchs in Wikipedia

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/ui/search.ui')
class SearchEntry(Gtk.SearchEntry):

  __gtype_name__ = 'SearchEntry'

  # Create suggestions list and connect search entry events

  def __init__(self, search_button):
    super().__init__()

    self.settings_popover = SettingsPopover(self)
    self.suggestions_popover = SuggestionsPopover(self)
    self.results_list = None
    self._results_changed = False

    lang_id = settings.get_string('search-language')
    self.set_icon_tooltip_text(Gtk.EntryIconPosition.PRIMARY, languages.wikilangs[lang_id].capitalize())

    self.connect('show', self._entry_show_cb)
    self.connect('key-press-event', self._key_press_cb, search_button)
    self.connect('icon-release',self._icon_release_cb)

  # Search text in Wikipedia and load results list

  def _search_wikipedia(self, text):
    try:
      self.results_list = wikipedia.search(text.lower(), 10)
    except:
      self.results_list = None
    self._results_changed = True

  # When entry show add timeout function

  def _entry_show_cb(self, entry):
    if self.suggestions_popover.is_visible(): self.suggestions_popover.hide()
    if settings.get_boolean('search-suggestions'): GLib.timeout_add(250, self._timeout_cb)

  # Timeout function which show search results in popover

  def _timeout_cb(self):
    if not self.is_visible(): return False
    if self._results_changed:
      if self.results_list != None:
        self.suggestions_popover.populate(self.results_list)
        if not self.suggestions_popover.is_visible(): self.suggestions_popover.show_all()
      else:
        self.suggestions_popover.hide()
      self._results_changed = False
    return True

  # Manage ESC and Down keys

  def _key_press_cb(self, entry, event, search_button):
    if event.keyval == 65364:
      if self.suggestions_popover.is_visible():
        self.suggestions_popover.grab_focus()
      return True
    elif event.keyval == 65307:
      if self.suggestions_popover.is_visible():
        self.suggestions_popover.hide()
      else:
        search_button.set_active(False)

  # Show settings popover on icon clicked

  def _icon_release_cb(self, entry, icon_pos, event):
    if icon_pos == Gtk.EntryIconPosition.PRIMARY:
      if self.suggestions_popover.is_visible():
        self.suggestions_popover.hide()
      self.settings_popover.show_all()

  # When text changes run search in new thread

  def do_search_changed(self):
    if settings.get_boolean('search-suggestions'):
      text = self.get_text()
      if len(text) > 2:
        t = Thread(target=self._search_wikipedia, args=(text, ))
        t.start()
      else:
        self.results_list = None
        self._results_changed = True

  # On entry activated search for text in Wikipedia and load result

  def do_activate(self):
    text = self.get_text()
    if text != '':
      try:
        result = wikipedia.search(text.lower(), 1)
      except:
        wikiview.load_message('error')
      else:
        if result != None:
          uri = result[1][0]
          wikiview.load_wiki(uri)
        else:
          wikiview.load_message('notfound')


# Popover class for search suggestions
# Show search suggestions when user type in entry

class SuggestionsPopover(Gtk.Popover):

  # Create menu and actions for suggestions

  def __init__(self, search_entry):
    super().__init__()
    self.set_relative_to(search_entry)
    self.set_size_request(360, -1)
    self.set_modal(False)

    self._results_menu = Gio.Menu()
    self.bind_model(self._results_menu, None)

    actions = Gio.SimpleActionGroup()
    action = Gio.SimpleAction.new('suggestion', GLib.VariantType('s'))
    action.connect('activate', self._suggestion_activate_cb)
    actions.add_action(action)
    self.insert_action_group('suggestions_popover', actions)

  # Populate search results list

  def populate(self, results_list):
    self._results_menu.remove_all()
    for index, item in enumerate(results_list[0]):
      action_string = 'suggestions_popover.suggestion(\'' + str(index) + '\')'
      button = Gio.MenuItem.new(item, action_string)
      self._results_menu.append_item(button)

  # Set focus to search entry on ESC key press

  def do_key_press_event(self, event):
    if event.keyval == 65307:
      search_entry = self.get_relative_to()
      search_entry.grab_focus_without_selecting()
      self.hide()

  # On menu activated get uri for selected result and load it

  def _suggestion_activate_cb(self, action, parameter):
    index = int(parameter.unpack())
    search_entry = self.get_relative_to()
    uri = search_entry.results_list[1][index]
    wikiview.load_wiki(uri)


# Popover class for search settings
# Select search language and set search suggestions

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/ui/search-settings.ui')
class SettingsPopover(Gtk.Popover):

  __gtype_name__ = 'SettingsPopover'

  filter_entry = Gtk.Template.Child()
  languages_list = Gtk.Template.Child()
  suggestions_switch = Gtk.Template.Child()

  # Populate search languages list and connect signals and bindings

  def __init__(self, search_entry):
    super().__init__()
    self.set_relative_to(search_entry)

    self.languages_list.set_filter_func(self._filter_list)
    self.languages_list.set_header_func(self._set_row_separator)
    self.populate_list()

    settings.bind('search-suggestions', self.suggestions_switch, 'active', Gio.SettingsBindFlags.DEFAULT)
    self.filter_entry.connect('search-changed', self._filter_entry_changed_cb)
    self.languages_list.connect('row-activated', self._languages_list_activated_cb)

  # Filter languages list for filter entry content

  def _filter_list(self, row):
    text = self.filter_entry.get_text()
    if text == '':
      return True

    if row.lang_name.lower().startswith(text.lower()) or row.lang_id.lower().startswith(text.lower()):
      return True
    else:
      return False

  # Set language row separator

  def _set_row_separator(self, row, before):
    if before and not row.get_header():
      separator = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)
      row.set_header(separator)

  # Populate languages list

  def populate_list(self):
    rows = self.languages_list.get_children()
    for row in rows:
      self.languages_list.remove(row)

    if len(languages.items) > 0:
      for lang_id in sorted(languages.items):
        lang_name = languages.items[lang_id].capitalize()
        check_mark = (lang_id == settings.get_string('search-language'))
        row = SearchLangBoxRow(lang_name, lang_id, check_mark)
        self.languages_list.add(row)

  # Change search language on list activated

  def _languages_list_activated_cb(self, lang_list, row):
    search_entry = self.get_relative_to()
    search_entry.set_icon_tooltip_text(Gtk.EntryIconPosition.PRIMARY, languages.wikilangs[row.lang_id].capitalize())
    settings.set_string('search-language', row.lang_id)
    wikipedia.set_lang(row.lang_id)
    self.hide()
    message = _('Default search language: ') + row.lang_name
    window = self.get_toplevel()
    window.show_notification(message)
    self.populate_list()

  # Refresh languages list on filter entry changed

  def _filter_entry_changed_cb(self, filter_entry):
    self.languages_list.invalidate_filter()

  # Unselect items and show popover

  def show_all(self):
    self.languages_list.unselect_all()
    Gtk.Popover.show_all(self)


# Class for row in search languages list
# Create row from language name and id

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/ui/search-row.ui')
class SearchLangBoxRow(Gtk.ListBoxRow):

  __gtype_name__ = 'SearchLangBoxRow'

  label_name = Gtk.Template.Child()
  label_id = Gtk.Template.Child()
  image_check = Gtk.Template.Child()

  # Initialize widgets

  def __init__(self, lang_name, lang_id, check_mark):
    super().__init__()

    self.lang_name = lang_name
    self.lang_id = lang_id

    self.label_name.set_label(lang_name)
    if check_mark:
      self.image_check.set_from_icon_name('emblem-ok-symbolic', Gtk.IconSize.BUTTON)
    self.label_id.set_label(lang_id)

