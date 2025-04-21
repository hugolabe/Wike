# This file is part of Wike (com.github.hugolabe.Wike)
# SPDX-FileCopyrightText: 2021-24 Hugo Olabera <hugolabe@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later


import json

from gi.repository import GObject, Gio, Gtk, Adw, Pango

from wike.data import settings, languages


# Language links panel for sidebar

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/gtk/langlinks.ui')
class LanglinksPanel(Adw.Bin):

  __gtype_name__ = 'LanglinksPanel'

  filter_dropdown = Gtk.Template.Child()
  search_entry = Gtk.Template.Child()
  langlinks_list = Gtk.Template.Child()

  # Initialize widgets and connect signals

  def __init__(self, window):
    super().__init__()

    self._window = window

    self.filter_model = Gio.ListStore(item_type=LanguagesFilter)
    self.filter_model.append(LanguagesFilter(_('Your languages'), 0))
    self.filter_model.append(LanguagesFilter(_('All languages'), 1))

    filter_factory = Gtk.SignalListItemFactory()
    filter_factory.connect('setup', self._filter_factory_setup)
    filter_factory.connect('bind', self._filter_factory_bind)

    self.filter_dropdown.set_model(self.filter_model)
    self.filter_dropdown.set_factory(filter_factory)

    self.langlinks_list.set_filter_func(self._filter_list, self.search_entry)

    settings.bind('filter-langlinks', self.filter_dropdown, 'selected', Gio.SettingsBindFlags.DEFAULT)
    settings.connect('changed::filter-langlinks', self._filter_langlinks_changed_cb)
    settings.connect('changed::show-flags', self._settings_show_flags_changed_cb)

    self.search_entry.connect('search-changed', self._search_entry_changed_cb)
    self.langlinks_list.connect('row-activated', self._list_activated_cb)

  # Setup filter item with a label

  def _filter_factory_setup(self, factory, list_item):
    label = Gtk.Label()
    label.set_xalign(0)
    label.set_ellipsize(Pango.EllipsizeMode.END)
    list_item.set_child(label)

  # Bind label property for filter item

  def _filter_factory_bind(self, factory, list_item):
    label = list_item.get_child()
    history_filter = list_item.get_item()
    history_filter.bind_property('name', label, 'label', GObject.BindingFlags.SYNC_CREATE)

  # Filter list for entry content

  def _filter_list(self, row, search_entry):
    text = search_entry.get_text()
    if text == '':
      return True

    if not row.get_activatable():
      return False

    if row.lang_name.lower().startswith(text.lower()) or row.lang.lower().startswith(text.lower()):
      return True
    else:
      return False

  # Populate langlinks list

  def populate(self, langlinks):
    while True:
      row = self.langlinks_list.get_row_at_index(0)
      if row:
        self.langlinks_list.remove(row)
      else:
        break

    if not langlinks:
      return

    user_langlinks = []
    other_langlinks = []
    for langlink in langlinks:
      if langlink['lang'] in languages.items:
        user_langlinks.append(langlink)
      else:
        other_langlinks.append(langlink)

    if user_langlinks:
      for langlink in sorted(user_langlinks, key=lambda x: x['lang']):
        row = LanglinksRow(langlink['url'], langlink['lang'], langlink['autonym'].capitalize(), langlink['*'])
        self.langlinks_list.append(row)

    if other_langlinks and settings.get_int('filter-langlinks') == 1:
      section_label = Gtk.Label()
      section_label.set_label(_('Other languages'))
      section_label.add_css_class('heading')
      section_label.set_xalign(0)
      section_label.set_margin_start(3)
      section_label.set_margin_end(3)
      row = Gtk.ListBoxRow()
      row.set_child(section_label)
      row.set_activatable(False)
      row.set_selectable(False)
      self.langlinks_list.append(row)
      for langlink in sorted(other_langlinks, key=lambda x: x['lang']):
        row = LanglinksRow(langlink['url'], langlink['lang'], langlink['autonym'].capitalize(), langlink['*'])
        self.langlinks_list.append(row)

  # Settings filter langlinks changed event

  def _filter_langlinks_changed_cb(self, settings, key):
    self.populate(self._window.page.wikiview.langlinks)

  # Settings show flags changed event

  def _settings_show_flags_changed_cb(self, settings, key):
    self.populate(self._window.page.wikiview.langlinks)

  # Refresh list on filter entry changed

  def _search_entry_changed_cb(self, search_entry):
    self.langlinks_list.invalidate_filter()

  # On list activated load page in choosen language

  def _list_activated_cb(self, langs_list, row):
    if self._window.panel_split.get_collapsed():
      self._window.panel_split.set_show_sidebar(False)

    self._window.page.wikiview.load_wiki(row.uri)


# This object represent a language filter in dropdown

class LanguagesFilter(GObject.Object):
  __gtype_name__ = 'LanguagesFilter'

  # Set values

  def __init__(self, name, level):
    super().__init__()

    self._name = name
    self._level = level

  # Name of filter property

  @GObject.Property(type=str)
  def name(self):
    return self._name

  # Id property

  @GObject.Property(type=int)
  def level(self):
    return self._level


# Row on langlinks list

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/gtk/langlinks-row.ui')
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
    self.title_label.set_label(title)

    if settings.get_boolean('show-flags'):
      gfile = Gio.File.new_for_uri('resource:///com/github/hugolabe/Wike/icons/scalable/emblems/' + lang + '.svg')
      if gfile.query_exists():
        self.flag_image.set_from_icon_name(lang)
    else:
      self.flag_image.set_visible(False)
