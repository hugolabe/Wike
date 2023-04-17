# This file is part of Wike (com.github.hugolabe.Wike)
# SPDX-FileCopyrightText: 2021-23 Hugo Olabera <hugolabe@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later


from threading import Thread

from gi.repository import GLib, Gio, Gtk

from wike import wikipedia
from wike.data import settings, languages
from wike.languages import LanguagesWindow


# Box with entry for manage searchs in Wikipedia

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/ui/search.ui')
class SearchBox(Gtk.Box):

  __gtype_name__ = 'SearchBox'
  
  search_entry = Gtk.Template.Child()
  lang_label = Gtk.Template.Child()
  settings_button = Gtk.Template.Child()
  
  # Create suggestions list and connect search entry events

  def __init__(self, window):
    super().__init__()

    self.window = window
    self._delegate = self.search_entry.get_delegate()

    self.results_list = None
    self._results_changed = False
    lang_id = settings.get_string('search-language')

    self.settings_popover = SettingsPopover(self)
    self.suggestions_popover = SuggestionsPopover(self)
    self.settings_button.set_popover(self.settings_popover)

    event_controller = Gtk.EventControllerKey()
    self._delegate.add_controller(event_controller)
    
    event_controller.connect('key-pressed', self._search_key_pressed_cb)
    self._delegate.connect('notify::has-focus', self._search_has_focus_cb)
    self.search_entry.connect('search-changed', self._search_changed_cb)
    self.search_entry.connect('stop-search', self._search_stop_cb)
    self.search_entry.connect('activate', self._search_activate_cb)

    self.search_entry.set_key_capture_widget(window)

  # Search text in Wikipedia and load results list

  def _search_wikipedia(self, text):
    try:
      self.results_list = wikipedia.search(text.lower(), settings.get_string('search-language'), 10)
    except:
      self.results_list = None
    self._results_changed = True

  # When down key pressed set focus to suggestions popover
  
  def _search_key_pressed_cb(self, event_controller, keyval, keycode, modifier):
    if keyval == 65364:
      if self.suggestions_popover.is_visible():
        self.suggestions_popover.set_can_focus(True)
        
    return False
    
  # When entry is focused add timeout function

  def _search_has_focus_cb(self, delegate, parameter):
    if delegate.has_focus():
      self.suggestions_popover.set_can_focus(False)
      if settings.get_boolean('search-suggestions'):
        GLib.timeout_add(250, self._timeout_cb)

  # When text changes run search in new thread

  def _search_changed_cb(self, search_entry):
    search_entry.grab_focus()
    if settings.get_boolean('search-suggestions'):
      text = search_entry.get_text()
      if len(text) > 2:
        t = Thread(target=self._search_wikipedia, args=(text, ))
        t.start()
      else:
        self.results_list = None
        self._results_changed = True

  # When search stoped with ESC hide suggestions
  
  def _search_stop_cb(self, search_entry):
    if self.suggestions_popover.is_visible():
      self.suggestions_popover.hide()
    else:
      if len(search_entry.get_text()) > 0:
        search_entry.delete_text(0, -1)
      else:
        self.window.page.wikiview.grab_focus()

  # Timeout function which show search results in popover

  def _timeout_cb(self):
    if not self._delegate.has_focus():
      return False

    if self._results_changed:
      if self.results_list != None:
        self.suggestions_popover.populate(self.results_list)
        if not self.suggestions_popover.is_visible():
          self.suggestions_popover.show()
      else:
        self.suggestions_popover.hide()
      self._results_changed = False
    return True

  # On entry activated search for text in Wikipedia and load result

  def _search_activate_cb(self, search_entry):
    text = search_entry.get_text()
    self.suggestions_popover.hide()
    search_entry.delete_text(0, -1)
    if text != '':
      try:
        result = wikipedia.search(text.lower(), settings.get_string('search-language'), 1)
      except:
        self.window.page.wikiview.load_message('notfound')
      else:
        if result != None:
          uri = result[1][0]
          self.window.page.wikiview.load_wiki(uri)
        else:
          self.window.page.wikiview.load_message('notfound')

  # Close suggestions and empty search entry
  
  def reset(self):
    if self.suggestions_popover.is_visible():
      self.suggestions_popover.hide()
    self.search_entry.delete_text(0, -1)


# Popover for search suggestions

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/ui/suggestions.ui')
class SuggestionsPopover(Gtk.PopoverMenu):

  __gtype_name__ = 'SuggestionsPopover'

  # Create menu and actions for suggestions

  def __init__(self, search_box):
    super().__init__()

    self._search_box = search_box
    self._window = search_box.window

    self._results_menu = Gio.Menu()
    self.set_menu_model(self._results_menu)
    self.set_parent(search_box.search_entry)

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

  # On menu activated get uri for selected result and load it

  def _suggestion_activate_cb(self, action, parameter):
    index = int(parameter.unpack())
    uri = self._search_box.results_list[1][index]
    self._window.page.wikiview.load_wiki(uri)
    
  # On popover closed set focus to search entry
  
  def do_closed(self):
    self._search_box.search_entry.grab_focus()


# Popover for search settings

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/ui/search-settings.ui')
class SettingsPopover(Gtk.Popover):

  __gtype_name__ = 'SettingsPopover'

  filter_entry = Gtk.Template.Child()
  languages_button = Gtk.Template.Child()
  languages_list = Gtk.Template.Child()
  languages_scroller = Gtk.Template.Child()
  languages_separator = Gtk.Template.Child()
  suggestions_switch = Gtk.Template.Child()

  # Populate search languages list and connect signals and bindings

  def __init__(self, search_box):
    super().__init__()

    self._search_box = search_box
    self._window = search_box.window

    self.languages_list.set_filter_func(self._filter_list)
    self.populate_list()

    settings.bind('search-suggestions', self.suggestions_switch, 'active', Gio.SettingsBindFlags.DEFAULT)
    settings.connect('changed::show-flags', self._settings_show_flags_changed_cb)
    
    self.languages_button.connect('clicked', self._languages_button_clicked_cb)
    self.filter_entry.connect('search-changed', self._filter_entry_changed_cb)
    self.languages_list.connect('row-activated', self._languages_list_activated_cb)
    self.languages_scroller.get_vadjustment().connect('value-changed', self._languages_scrolled_cb)
    self.connect('show', self._popover_show_cb)

  # Filter languages list for filter entry content

  def _filter_list(self, row):
    text = self.filter_entry.get_text()
    if text == '':
      return True

    if row.lang_name.lower().startswith(text.lower()) or row.lang_id.lower().startswith(text.lower()):
      return True
    else:
      return False

  # Populate languages list

  def populate_list(self):
    lang_id = settings.get_string('search-language')
    self._search_box.lang_label.set_label(lang_id)
    self._search_box.lang_label.set_tooltip_text(languages.wikilangs[lang_id].capitalize())

    while True:
      row = self.languages_list.get_row_at_index(0)
      if row:
        self.languages_list.remove(row)
      else:
        break

    if len(languages.items) > 0:
      for lang_id in sorted(languages.items):
        lang_name = languages.items[lang_id].capitalize()
        check_mark = (lang_id == settings.get_string('search-language'))
        row = SettingsLangsRow(lang_name, lang_id, check_mark)
        self.languages_list.append(row)

  # Settings show flags changed event

  def _settings_show_flags_changed_cb(self, settings, key):
    self.populate_list()

  # On button clicked open languages window
  
  def _languages_button_clicked_cb(self, languages_button):
    self.hide()
    languages_window = LanguagesWindow()
    languages_window.set_transient_for(self._window)
    languages_window.show()

  # On filter entry changed refresh languages list

  def _filter_entry_changed_cb(self, filter_entry):
    self.languages_list.invalidate_filter()

  # On list activated change search language

  def _languages_list_activated_cb(self, lang_list, row):
    settings.set_string('search-language', row.lang_id)
    self.hide()
    self.populate_list()

  # Show/hide separator on scroll

  def _languages_scrolled_cb(self, adjustment):
    if adjustment.get_value() > 0:
      self.languages_separator.set_visible(True)
    else:
      self.languages_separator.set_visible(False)

  # On popover show unselect items and hide suggestions

  def _popover_show_cb(self, settings_popover):
    self.languages_list.unselect_all()
    self._search_box.suggestions_popover.hide()
    self.languages_scroller.get_vadjustment().set_value(0)


# Language row in search settings

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/ui/search-settings-row.ui')
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
      self.check_image.set_from_icon_name('emblem-ok-symbolic')
    self.id_label.set_label(lang_id)
    if settings.get_boolean('show-flags'):
      gfile = Gio.File.new_for_uri('resource:///com/github/hugolabe/Wike/icons/scalable/emblems/' + lang_id + '.svg')
      if gfile.query_exists():
        self.flag_image.set_from_icon_name(lang_id)
    else:
      self.flag_image.set_visible(False)
