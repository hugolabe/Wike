# This file is part of Wike (com.github.hugolabe.Wike)
# SPDX-FileCopyrightText: 2021-25 Hugo Olabera
# SPDX-License-Identifier: GPL-3.0-or-later


from gi.repository import Gio, Gtk, Adw

from wike import wikipedia
from wike.data import settings, languages
from wike.languages import LanguagesDialog


# Search panel for sidebar

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/gtk/search.ui')
class SearchPanel(Adw.Bin):

  __gtype_name__ = 'SearchPanel'

  search_entry = Gtk.Template.Child()
  settings_button = Gtk.Template.Child()
  suggestions_list = Gtk.Template.Child()

  # Create suggestions list and connect search entry events

  def __init__(self, window):
    super().__init__()

    self.window = window
    self._delegate = self.search_entry.get_delegate()

    self.settings_popover = SettingsPopover(self)
    self.settings_button.set_popover(self.settings_popover)

    self._delegate.connect('notify::has-focus', self._search_has_focus_cb)
    self.search_entry.connect('changed', self._search_changed_cb)
    self.search_entry.connect('stop-search', self._search_stop_cb)
    self.search_entry.connect('activate', self._search_activate_cb)
    self.suggestions_list.connect('row-activated', self._list_activated_cb)

    self.search_entry.set_key_capture_widget(window)

  # Populate search suggestions list

  def _populate(self, suggestions):
    while True:
      row = self.suggestions_list.get_row_at_index(0)
      if row:
        self.suggestions_list.remove(row)
      else:
        break

    if suggestions:
      for title, uri in zip(suggestions[0], suggestions[1]):
        row = SearchRow(title, uri)
        self.suggestions_list.append(row)

  # When entry loses focus select text

  def _search_has_focus_cb(self, delegate, parameter):
    if not delegate.has_focus():
      self.search_entry.select_region(0, -1)

  # When text changes run search async

  def _search_changed_cb(self, search_entry):
    self.window.search_button.set_active(True)
    if not self._delegate.has_focus():
      self.search_entry.grab_focus()

    if settings.get_boolean('search-suggestions'):
      text, lang = self._get_search_terms(search_entry.get_text())
      if len(text) > 2:
        wikipedia.search(text.lower(), lang, 20, self._on_search_finished)
      else:
        self._populate(None)
    else:
      self._populate(None)

  # On search finished get results and populate suggestions list

  def _on_search_finished(self, session, async_result, user_data):
    try:
      results = wikipedia.search_result(async_result)
    except:
      self._populate(None)
    else:
      self._populate(results)

  # Split search terms to get language prefix

  def _get_search_terms(self, text):
    text = text.lower()
    lang = settings.get_string('search-language')
    if text.startswith('-'):
      terms = text.split(' ', 1)
      prefix = terms[0].lstrip('-')
      if prefix in languages.wikilangs.keys():
        lang = prefix
      if len(terms) > 1:
        text = terms[1]
      else:
        text = ''
    return text, lang

  # When search stoped with ESC hide suggestions
  
  def _search_stop_cb(self, search_entry):
    if len(search_entry.get_text()) > 0:
      search_entry.delete_text(0, -1)
    else:
      if self.window.panel_split.get_collapsed():
        self.window.panel_split.set_show_sidebar(False)
      self.window.page.set_focus()

  # On entry activated search for text async

  def _search_activate_cb(self, search_entry):
    if self.window.panel_split.get_collapsed():
      self.window.panel_split.set_show_sidebar(False)

    text, lang = self._get_search_terms(search_entry.get_text())
    if text != '':
      wikipedia.search(text.lower(), lang, 1, self._on_activate_result)

  # On search activate finished get result and load article
  
  def _on_activate_result(self, session, async_result, user_data):
    try:
      results = wikipedia.search_result(async_result)
    except:
      self.window.page.wikiview.load_message('error')
    else:
      if results:
        uri = results[1][0]
        self.window.page.wikiview.load_wiki(uri)
      else:
        self.window.page.wikiview.load_message('notfound')

  # On list activated load article in view

  def _list_activated_cb(self, suggestions_list, row):
    if self.window.panel_split.get_collapsed():
      self.window.panel_split.set_show_sidebar(False)

    self.window.page.wikiview.load_wiki(row.uri)


# Suggestion row in search suggestions list

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/gtk/search-row.ui')
class SearchRow(Gtk.ListBoxRow):

  __gtype_name__ = 'SearchRow'

  suggestion_label = Gtk.Template.Child()

  # Set label title and uri

  def __init__(self, title, uri):
    super().__init__()
    
    self.title = title
    self.uri = uri

    self.suggestion_label.set_label(title)


# Popover for search settings

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/gtk/search-settings.ui')
class SettingsPopover(Gtk.Popover):

  __gtype_name__ = 'SettingsPopover'

  languages_button = Gtk.Template.Child()
  languages_list = Gtk.Template.Child()
  suggestions_switch = Gtk.Template.Child()

  # Populate search languages list and connect signals and bindings

  def __init__(self, search_panel):
    super().__init__()

    self._search_panel = search_panel
    self._window = search_panel.window

    self.populate_list()

    settings.bind('search-suggestions', self.suggestions_switch, 'active', Gio.SettingsBindFlags.DEFAULT)
    settings.connect('changed::search-suggestions', self._settings_search_suggestions_changed_cb)
    settings.connect('changed::show-flags', self._settings_show_flags_changed_cb)
    
    self.languages_button.connect('clicked', self._languages_button_clicked_cb)
    self.languages_list.connect('row-activated', self._languages_list_activated_cb)
    self.connect('show', self._popover_show_cb)

  # Populate languages list

  def populate_list(self):
    lang_id = settings.get_string('search-language')
    self._search_panel.settings_button.set_label(lang_id)
    self._search_panel.settings_button.set_tooltip_text(languages.wikilangs[lang_id].capitalize())
    self.languages_list.remove_all()

    if len(languages.items) > 0:
      for lang_id in sorted(languages.items):
        lang_name = languages.items[lang_id].capitalize()
        check_mark = (lang_id == settings.get_string('search-language'))
        row = SettingsLangsRow(lang_name, lang_id, check_mark)
        self.languages_list.append(row)

  # Settings search suggestions changed event

  def _settings_search_suggestions_changed_cb(self, settings, key):
    self._search_panel.search_entry.emit('changed')

  # Settings show flags changed event

  def _settings_show_flags_changed_cb(self, settings, key):
    self.populate_list()

  # On button clicked open languages window

  def _languages_button_clicked_cb(self, languages_button):
    self.hide()
    languages_dialog = LanguagesDialog(self._window)
    languages_dialog.present(self._window)

  # On list activated change search language

  def _languages_list_activated_cb(self, lang_list, row):
    settings.set_string('search-language', row.lang_id)
    self.hide()
    self.populate_list()
    self._search_panel.search_entry.emit('changed')

  # On popover show unselect items and hide suggestions

  def _popover_show_cb(self, settings_popover):
    self.languages_list.unselect_all()


# Language row in search settings

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/gtk/search-settings-row.ui')
class SettingsLangsRow(Gtk.ListBoxRow):

  __gtype_name__ = 'SettingsLangsRow'

  name_label = Gtk.Template.Child()
  id_label = Gtk.Template.Child()
  flag_image = Gtk.Template.Child()
  check_image = Gtk.Template.Child()

  # Set values and initialize widgets

  def __init__(self, lang_name, lang_id, check_mark):
    super().__init__()

    self.lang_name = lang_name
    self.lang_id = lang_id

    self.name_label.set_label(lang_name)
    if check_mark:
      self.check_image.set_from_icon_name('checkmark-symbolic')
    self.id_label.set_label(lang_id)
    if settings.get_boolean('show-flags'):
      gfile = Gio.File.new_for_uri('resource:///com/github/hugolabe/Wike/icons/scalable/emblems/' + lang_id + '.svg')
      if gfile.query_exists():
        self.flag_image.set_from_icon_name(lang_id)
    else:
      self.flag_image.set_visible(False)
