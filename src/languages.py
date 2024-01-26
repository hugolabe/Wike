# This file is part of Wike (com.github.hugolabe.Wike)
# SPDX-FileCopyrightText: 2021-23 Hugo Olabera <hugolabe@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later


from gi.repository import Gtk, Adw

from wike.data import languages


# Languages window to choose user languages

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/ui/languages.ui')
class LanguagesWindow(Adw.Window):

  __gtype_name__ = 'LanguagesWindow'

  search_bar = Gtk.Template.Child()
  languages_entry = Gtk.Template.Child()
  languages_list = Gtk.Template.Child()
  select_all_button = Gtk.Template.Child()
  select_none_button = Gtk.Template.Child()

  # Initialize and connect signals

  def __init__(self):
    super().__init__()

    self._languages_changed = False
    
    self.search_bar.set_key_capture_widget(self)
    self.languages_list.set_filter_func(self._filter_list)
    self._populate()

    self.languages_entry.connect('search-changed', self._languages_entry_changed_cb)
    self.languages_list.connect('row-activated', self._languages_list_selected_cb)
    self.select_all_button.connect('clicked', self._select_all_button_cb)
    self.select_none_button.connect('clicked', self._select_none_button_cb)
    self.connect('close-request', self._window_close_cb)

  # Filter languages list for languages entry content

  def _filter_list(self, row):
    text = self.languages_entry.get_text()
    if text == '':
      return True

    if row.lang_name.lower().startswith(text.lower()) or row.lang_id.lower().startswith(text.lower()):
      return True
    else:
      return False

  # Populate list of available languages

  def _populate(self):
    for lang_id in sorted(languages.wikilangs):
      lang_name = languages.wikilangs[lang_id].capitalize()
      if lang_id in languages.items:
        row = LanguagesRow(lang_name, lang_id, True)
      else:
        row = LanguagesRow(lang_name, lang_id, False)
      self.languages_list.append(row)
      row.lang_check.connect('toggled', self._language_checkbutton_cb)

  # Refresh languages list on languages entry changed

  def _languages_entry_changed_cb(self, languages_entry):
    self.languages_list.invalidate_filter()

  # On row selected set language check button

  def _languages_list_selected_cb(self, languages_list, row):
    row.lang_check.set_active(not row.lang_check.get_active())

  # Set languages changed variable on check button changed

  def _language_checkbutton_cb(self, check_button):
    if not self._languages_changed:
      self._languages_changed = True

  # On button click check all languages

  def _select_all_button_cb(self, select_all_button):
    i = 0
    while True:
      row = self.languages_list.get_row_at_index(i)
      if row:
        row.lang_check.set_active(True)
        i += 1
      else:
        break

  # On button click uncheck all languages

  def _select_none_button_cb(self, select_none_button):
    i = 0
    while True:
      row = self.languages_list.get_row_at_index(i)
      if row:
        row.lang_check.set_active(False)
        i += 1
      else:
        break

  # On window close refresh languages list (if changed)

  def _window_close_cb(self, prefs_window):
    if self._languages_changed:
      languages.clear()

      i = 0
      while True:
        row = self.languages_list.get_row_at_index(i)
        if row:
          if row.lang_check.get_active():
            languages.items[row.lang_id] = row.lang_name
          i += 1
        else:
          break

      if len(languages.items) == 0:
        languages.items['en'] = 'English'

      window = self.get_transient_for()
      window.search_box.settings_popover.populate_list()
      window.langlinks_panel.populate(window.page.wikiview.langlinks)

    return False


# Row in languages list

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/ui/languages-row.ui')
class LanguagesRow(Gtk.ListBoxRow):

  __gtype_name__ = 'LanguagesRow'

  name_label = Gtk.Template.Child()
  id_label = Gtk.Template.Child()
  lang_check = Gtk.Template.Child()

  # Set row values

  def __init__(self, lang_name, lang_id, checked):
    super().__init__()

    self.lang_name = lang_name
    self.lang_id = lang_id

    self.name_label.set_label(lang_name)
    self.id_label.set_label(lang_id)
    self.lang_check.set_active(checked)
