# application.py
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


import os
import sys

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')
from gi.repository import Gio, GLib, Gtk, WebKit2

from wike.data import settings, languages, historic, bookmarks
from wike.prefs import PrefsWindow
from wike.view import wikiview
from wike.window import Window


# Main application class
# Wike Wikipedia Reader

class Application(Gtk.Application):

  # Initialize app

  def __init__(self):
    super().__init__(application_id='com.github.hugolabe.Wike', flags=Gio.ApplicationFlags.FLAGS_NONE)

    self._window = None

  # Initialize webcontext with cookie manager and set actions

  def do_startup(self):
    Gtk.Application.do_startup(self)

    web_context = WebKit2.WebContext.get_default()
    web_context.set_cache_model(WebKit2.CacheModel.WEB_BROWSER)
    cookies_file_path = GLib.get_user_data_dir() + '/cookies'
    cookie_manager = WebKit2.WebContext.get_cookie_manager(web_context)
    cookie_manager.set_accept_policy(WebKit2.CookieAcceptPolicy.ALWAYS)
    cookie_manager.set_persistent_storage(cookies_file_path, WebKit2.CookiePersistentStorage.TEXT)

    actions = [ ('prefs', self._prefs_cb, ('<Ctrl>E',)),
                ('shortcuts', self._shortcuts_cb, ('<Ctrl>F1',)),
                ('about', self._about_cb, None) ]

    for action, callback, accel in actions:
      simple_action = Gio.SimpleAction.new(action, None)
      simple_action.connect('activate', callback)
      self.add_action(simple_action)
      if accel: self.set_accels_for_action('app.' + action, accel)

  # Create main window and connect delete event

  def do_activate(self):
    if not self._window:
      self._window = Window(self)
      self._window.connect('delete-event',self._window_delete_cb)
      self._window.show_all()
    else:
      self._window.present()

  # Show Preferences window

  def _prefs_cb(self, action, parameter):
    prefs_window = PrefsWindow()
    prefs_window.set_transient_for(self._window)
    prefs_window.show()

  # Show Shortcuts window

  def _shortcuts_cb(self, action, parameter):
    builder = Gtk.Builder()
    builder.add_from_resource("/com/github/hugolabe/Wike/ui/shortcuts.ui")
    shortcuts_window = builder.get_object("shortcuts_window")
    shortcuts_window.set_transient_for(self._window)
    shortcuts_window.show()

  # Show About dialog

  def _about_cb(self, action, parameter):
    builder = Gtk.Builder()
    builder.add_from_resource("/com/github/hugolabe/Wike/ui/about.ui")
    about_dialog = builder.get_object("about_dialog")
    about_dialog.set_transient_for(self._window)
    about_dialog.run()
    about_dialog.destroy()

  # Save settings and data and quit app

  def _window_delete_cb(self, window, event):
    if window.is_maximized():
      settings.set_boolean('window-max', True)
    else:
      settings.set_boolean('window-max', False)
      size = window.get_size()
      settings.set_int('window-width', size[0])
      settings.set_int('window-height', size[1])

    if wikiview.is_local():
      settings.set_string('last-uri', '')
    else:
      settings.set_string('last-uri', wikiview.get_base_uri())

    settings.sync()
    languages.save()
    if not settings.get_boolean('keep-historic'):
      historic.clear()
    historic.save()
    if settings.get_boolean('clear-bookmarks'):
      bookmarks.clear()
    bookmarks.save()

    self.quit()


# Run app

def main(version):
  app = Application()
  return app.run(sys.argv)

