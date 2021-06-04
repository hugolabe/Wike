# prefs.py
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
gi.require_version('Gtk', '3.0')
gi.require_version('Handy', '1')
from gi.repository import Gio, Gtk, Handy

from wike.data import settings, languages


# Preferences window
# Manage application preferences

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/ui/prefs.ui')
class PrefsWindow(Handy.PreferencesWindow):

  __gtype_name__ = 'PrefsWindow'

  on_start_combo = Gtk.Template.Child()
  historic_switch = Gtk.Template.Child()
  clear_bookmarks_switch = Gtk.Template.Child()
  font_size_spin = Gtk.Template.Child()
  custom_font_switch = Gtk.Template.Child()
  custom_font_combo = Gtk.Template.Child()
  languages_list = Gtk.Template.Child()
  select_all_button = Gtk.Template.Child()
  select_none_button = Gtk.Template.Child()

  # Connect signals and bindings

  def __init__(self):
    super().__init__()

    self._languages_changed = False
    self._populate_on_start_combo()
    self._populate_custom_font_combo()
    self._populate_languages_list()

    settings.bind('on-start-load', self.on_start_combo, 'selected-index', Gio.SettingsBindFlags.DEFAULT)
    settings.bind('keep-historic', self.historic_switch, 'active', Gio.SettingsBindFlags.DEFAULT)
    settings.bind('clear-bookmarks', self.clear_bookmarks_switch, 'active', Gio.SettingsBindFlags.DEFAULT)
    settings.bind('font-size', self.font_size_spin, 'value', Gio.SettingsBindFlags.DEFAULT)
    settings.bind('custom-font', self.custom_font_switch, 'active', Gio.SettingsBindFlags.DEFAULT)

    self.custom_font_combo.connect('notify::selected-index', self._custom_font_combo_selected_cb)
    self.languages_list.connect('row-activated', self._languages_list_selected_cb)
    self.select_all_button.connect('clicked', self._select_all_button_cb)
    self.select_none_button.connect('clicked', self._select_none_button_cb)

    self.connect('delete-event', self._window_delete_cb)

  # Populate list of available options for start page

  def _populate_on_start_combo(self):
    model = Gio.ListStore.new(Handy.ValueObject)
    options = (_('Wikipedia main page'), _('Random article'), _('Last article'))
    for index, option in enumerate(options):
      model.insert(index, Handy.ValueObject.new(option))
    self.on_start_combo.bind_name_model(model, Handy.ValueObject.dup_string)

  # Populate font list for custom font combo

  def _populate_custom_font_combo(self):
    model = Gio.ListStore.new(Handy.ValueObject)
    fonts = []
    custom_font = settings.get_string('font-family')
    pango_context = self.get_pango_context()
    for font_familie in pango_context.list_families():
      fonts.append(font_familie.get_name())
    fonts.sort(key=str.lower)
    selected = 0
    for index, font in enumerate(fonts):
      model.insert(index, Handy.ValueObject.new(font))
      if font == custom_font: selected = index
    self.custom_font_combo.bind_name_model(model, Handy.ValueObject.dup_string)
    self.custom_font_combo.set_selected_index(selected)

  # Populate list of available languages

  def _populate_languages_list(self):
    for lang_id in sorted(languages.wikilangs):
      lang_name = languages.wikilangs[lang_id].capitalize()
      if lang_id in languages.items:
        row = LanguageBoxRow(lang_name, lang_id, True)
      else:
        row = LanguageBoxRow(lang_name, lang_id, False)
      self.languages_list.add(row)
      row.lang_check.connect('toggled', self._language_checkbutton_cb)

  # On window close refresh languages list (if changed)

  def _window_delete_cb(self, prefs_window, event):
    if self._languages_changed:
      languages.clear()
      rows = self.languages_list.get_children()
      for row in rows:
        if row.lang_check.get_active(): languages.items[row.lang_id] = row.lang_name

      if len(languages.items) == 0: languages.items['en'] = 'English'

      window = self.get_transient_for()
      window.headerbar.refresh_langs()

    return False

  # On custom font selected update settings

  def _custom_font_combo_selected_cb(self, custom_font_combo, value):
    model = custom_font_combo.get_model()
    index = custom_font_combo.get_selected_index()
    font = model.get_item(index).dup_string()
    settings.set_string('font-family', font)

  # On row selected set language check button

  def _languages_list_selected_cb(self, languages_list, row):
    row.lang_check.set_active(not row.lang_check.get_active())

  # Set languages changed variable on check button changed

  def _language_checkbutton_cb(self, check_button):
    if not self._languages_changed: self._languages_changed = True

  # On button click check all languages

  def _select_all_button_cb(self, select_all_button):
    rows = self.languages_list.get_children()
    for row in rows:
      row.lang_check.set_active(True)

  # On button click uncheck all languages

  def _select_none_button_cb(self, select_none_button):
    rows = self.languages_list.get_children()
    for row in rows:
      row.lang_check.set_active(False)


# Class for row in languages list
# Create row from name, id and filter status

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/ui/prefs-row.ui')
class LanguageBoxRow(Gtk.ListBoxRow):

  __gtype_name__ = 'LanguageBoxRow'

  lang_name_label = Gtk.Template.Child()
  lang_id_label = Gtk.Template.Child()
  lang_check = Gtk.Template.Child()

  # Set row values

  def __init__(self, lang_name, lang_id, checked):
    super().__init__()

    self.lang_name = lang_name
    self.lang_id = lang_id
    self.lang_name_label.set_label(lang_name)
    self.lang_id_label.set_label(lang_id)
    self.lang_check.set_active(checked)

