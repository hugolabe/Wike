# This file is part of Wike (com.github.hugolabe.Wike)
# SPDX-FileCopyrightText: 2021-24 Hugo Olabera <hugolabe@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later


from datetime import datetime

from gi.repository import GObject, Gio, Gtk, Adw, Pango

from wike.data import settings, languages, history


# History panel for sidebar

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/gtk/history.ui')
class HistoryPanel(Adw.Bin):

  __gtype_name__ = 'HistoryPanel'

  filter_dropdown = Gtk.Template.Child()
  selection_button = Gtk.Template.Child()
  clear_button = Gtk.Template.Child()
  select_all_button = Gtk.Template.Child()
  select_none_button = Gtk.Template.Child()
  remove_button = Gtk.Template.Child()
  history_list = Gtk.Template.Child()

  # Initialize widgets and connect signals and bindings

  def __init__(self, window):
    super().__init__()

    self._window = window

    filters = { _('Today'): 1, _('Last 7 days'): 7, _('Last 30 days'): 30, _('Show full history'): 365 }
    self.filter_model = Gio.ListStore(item_type=HistoryFilter)
    for filter_name in filters.keys():
      self.filter_model.append(HistoryFilter(filter_name, filters[filter_name]))

    filter_factory = Gtk.SignalListItemFactory()
    filter_factory.connect('setup', self._filter_factory_setup)
    filter_factory.connect('bind', self._filter_factory_bind)

    self.filter_dropdown.set_model(self.filter_model)
    self.filter_dropdown.set_factory(filter_factory)

    settings.bind('filter-history', self.filter_dropdown, 'selected', Gio.SettingsBindFlags.DEFAULT)
    settings.connect('changed::keep-history', self._keep_history_changed_cb)
    settings.connect('changed::filter-history', self._filter_history_changed_cb)

    self._populate()

    self.clear_button.connect('clicked', self._clear_button_cb)
    self.select_all_button.connect('clicked', self._select_buttons_cb, True)
    self.select_none_button.connect('clicked', self._select_buttons_cb, False)
    self.remove_button.connect('clicked', self._remove_button_cb)
    self.history_list.connect('row-activated', self._list_activated_cb)

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

  # Populate history list

  def _populate(self):
    self._clear_list()

    history_filter = self.filter_dropdown.get_selected_item()
    filter_days = history_filter.days
    today = datetime.today()

    for date in sorted(history.items, reverse=True):
      delta = today - datetime.strptime(date, '%Y-%m-%d')
      days = delta.days
      if days >= filter_days:
        break

      date_label = Gtk.Label()
      date_label.set_label(date)
      date_label.add_css_class('heading')
      date_label.set_xalign(0)
      date_label.set_margin_start(3)
      date_label.set_margin_end(3)
      row = Gtk.ListBoxRow()
      row.set_child(date_label)
      row.set_activatable(False)
      row.set_selectable(False)
      self.history_list.append(row)

      history_item = history.items[date]
      for uri in sorted(history_item, key=history_item.get, reverse=True):
        time = history_item[uri][0]
        title = history_item[uri][1]
        lang = history_item[uri][2]
        row = HistoryRow(uri, title, lang, date, time)
        self.history_list.append(row)
        self.selection_button.bind_property('active', row.select_check, 'visible', Gio.SettingsBindFlags.DEFAULT)

  # Clear history list

  def _clear_list(self):
    self.selection_button.set_active(False)

    while True:
      row = self.history_list.get_row_at_index(0)
      if row:
        self.history_list.remove(row)
      else:
        break

  # Add article to history

  def add_item(self, uri, title, lang):
    history.add(uri, title, lang)
    self._populate()

  # Clear history of recent articles

  def clear_history(self):
    history.clear()
    history.save()
    self._clear_list()

  # Settings keep history changed event

  def _keep_history_changed_cb(self, settings, key):
    if settings.get_boolean(key):
      self._populate()
    else:
      self._clear_list()

  # Settings filter history changed event

  def _filter_history_changed_cb(self, settings, key):
    self._populate()

  # Show clear history dialog

  def _clear_button_cb(self, clear_button):
    builder = Gtk.Builder()
    builder.add_from_resource('/com/github/hugolabe/Wike/gtk/dialogs.ui')
    clear_history_dialog = builder.get_object('clear_history_dialog')
    clear_history_dialog.set_transient_for(self._window)

    clear_history_dialog.connect('response', self._clear_history_response_cb)

    clear_history_dialog.show()

  # On response clear history

  def _clear_history_response_cb(self, dialog, response):
    if response == 'clear':
      self.clear_history()

  # On select all or select none buttons do selection
  
  def _select_buttons_cb(self, button, select_mode):
    i = 0
    while True:
      row = self.history_list.get_row_at_index(i)
      if row:
        if row.get_activatable():
          row.select_check.set_active(select_mode)
        i += 1
      else:
        break

  # On button clicked remove selected items

  def _remove_button_cb(self, button):
    selected_rows = []
    i = 0
    while True:
      row = self.history_list.get_row_at_index(i)
      if row:
        if row.get_activatable():
          if row.select_check.get_active():
            selected_rows.append(row)
        i += 1
      else:
        break
        
    if len(selected_rows) > 0:
      for row in selected_rows:
        self._remove_row(row)

  # Remove row from history and list

  def _remove_row(self, row):
    item_deleted, date_deleted = history.remove(row.date, row.uri)
    row_index = row.get_index()

    if item_deleted:
      self.history_list.remove(row)

    if date_deleted:
      date_row = self.history_list.get_row_at_index(row_index-1)
      self.history_list.remove(date_row)

  # On list activated load article in view

  def _list_activated_cb(self, history_list, row):
    if self.selection_button.get_active():
      row.select_check.set_active(not row.select_check.get_active())
      return

    if self._window.panel_split.get_collapsed():
      self._window.panel_split.set_show_sidebar(False)

    self._window.page.wikiview.load_wiki(row.uri)


# This object represent an history filter in dropdown

class HistoryFilter(GObject.Object):
  __gtype_name__ = 'HistoryFilter'

  # Set values

  def __init__(self, name, days):
    super().__init__()

    self._name = name
    self._days = days

  # Name of filter property

  @GObject.Property(type=str)
  def name(self):
    return self._name

  # Number of days property

  @GObject.Property(type=int)
  def days(self):
    return self._days


# Row on history list

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/gtk/history-row.ui')
class HistoryRow(Gtk.ListBoxRow):

  __gtype_name__ = 'HistoryRow'

  title_label = Gtk.Template.Child()
  lang_label = Gtk.Template.Child()
  time_label = Gtk.Template.Child()
  select_check = Gtk.Template.Child()

  # Set values and widgets

  def __init__(self, uri, title, lang, date, time):
    super().__init__()

    self.uri = uri
    self.title = title
    self.lang = lang
    self.date = date
    self.time = time.rsplit(':', 1)[0]

    if lang in languages.wikilangs:
      lang_name = languages.wikilangs[lang].capitalize()
    else:
      lang_name = lang

    self.title_label.set_label(title)
    self.lang_label.set_label(lang_name)
    self.time_label.set_label(self.time)
