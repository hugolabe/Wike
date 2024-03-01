# This file is part of Wike (com.github.hugolabe.Wike)
# SPDX-FileCopyrightText: 2021-24 Hugo Olabera <hugolabe@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later


from gi.repository import Gio, Gtk, Adw, WebKit

from wike.data import settings
from wike.view import network_session


# Preferences window

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/gtk/prefs.ui')
class PrefsWindow(Adw.PreferencesWindow):

  __gtype_name__ = 'PrefsWindow'

  start_combo = Gtk.Template.Child()
  tabs_switch = Gtk.Template.Child()
  desktop_switch = Gtk.Template.Child()
  history_switch = Gtk.Template.Child()
  clear_history_button = Gtk.Template.Child()
  data_switch = Gtk.Template.Child()
  clear_data_button = Gtk.Template.Child()

  # Connect signals and bindings

  def __init__(self):
    super().__init__()

    settings.bind('on-start-load', self.start_combo, 'selected', Gio.SettingsBindFlags.DEFAULT)
    settings.bind('hide-tabs', self.tabs_switch, 'active', Gio.SettingsBindFlags.DEFAULT)
    settings.bind('search-desktop', self.desktop_switch, 'active', Gio.SettingsBindFlags.DEFAULT)
    settings.bind('keep-history', self.history_switch, 'active', Gio.SettingsBindFlags.DEFAULT)
    settings.bind('clear-data', self.data_switch, 'active', Gio.SettingsBindFlags.DEFAULT)

    self.clear_history_button.connect('clicked', self._clear_history_button_cb)
    self.clear_data_button.connect('clicked', self._clear_data_button_cb)

  # Show clear history dialog

  def _clear_history_button_cb(self, clear_history_button):
    builder = Gtk.Builder()
    builder.add_from_resource('/com/github/hugolabe/Wike/gtk/dialogs.ui')
    clear_history_dialog = builder.get_object('clear_history_dialog')
    clear_history_dialog.set_transient_for(self)

    clear_history_dialog.connect('response', self._clear_history_response_cb)

    clear_history_dialog.show()

  # On response clear history

  def _clear_history_response_cb(self, dialog, response):
    if response == 'clear':
      window = self.get_transient_for()
      window.history_panel.clear_history()

  # Show clear personal data dialog

  def _clear_data_button_cb(self, clear_data_button):
    builder = Gtk.Builder()
    builder.add_from_resource('/com/github/hugolabe/Wike/gtk/dialogs.ui')
    clear_data_dialog = builder.get_object('clear_data_dialog')
    clear_data_dialog.set_transient_for(self)

    clear_data_dialog.connect('response', self._clear_data_response_cb)

    clear_data_dialog.show()

  # On response clear personal data

  def _clear_data_response_cb(self, dialog, response):
    if response == 'clear':
      data_manager = network_session.get_website_data_manager()
      data_manager.clear(WebKit.WebsiteDataTypes.ALL, 0, None, None, None)
