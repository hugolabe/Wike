# This file is part of Wike (com.github.hugolabe.Wike)
# SPDX-FileCopyrightText: 2021-23 Hugo Olabera <hugolabe@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later


import sys

import gi
gi.require_version('Gdk', '4.0')
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('WebKit', '6.0')
from gi.repository import GLib, Gio, Gdk, Gtk, Adw, WebKit

from wike.data import settings, languages, history, bookmarks
from wike.prefs import PrefsWindow
from wike.window import Window
from wike.view import network_session


# Main application class for Wike

class Application(Adw.Application):

  # Initialize app

  def __init__(self):
    super().__init__(application_id='com.github.hugolabe.Wike', flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)

    self._window = None
    self._launch_uri = ''

    self.add_main_option('url', b'u', GLib.OptionFlags.NONE, GLib.OptionArg.STRING, 'Open Wikipedia URL', None)

  # Load custom css and set actions

  def do_startup(self):
    Adw.Application.do_startup(self)

    css_widgets = Gtk.CssProvider()
    css_widgets.load_from_resource('/com/github/hugolabe/Wike/ui/widgets.css')
    self._css_sepia = Gtk.CssProvider()
    self._css_sepia.load_from_resource('/com/github/hugolabe/Wike/ui/sepia.css')
    Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css_widgets, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    self._style_manager = Adw.StyleManager.get_default()
    if settings.get_int('theme') == 0:
      self._style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
    elif settings.get_int('theme') == 1:
      self._style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
    elif settings.get_int('theme') == 2:
      self._style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
      Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), self._css_sepia, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    elif settings.get_int('theme') == 3:
      self._style_manager.set_color_scheme(Adw.ColorScheme.PREFER_LIGHT)

    action = Gio.SimpleAction.new('prefs', None)
    action.connect('activate', self._prefs_cb)
    self.add_action(action)
    self.set_accels_for_action('app.prefs', ('<Ctrl>comma',))

    action = Gio.SimpleAction.new('theme-system', None)
    action.connect('activate', self._theme_system)
    self.add_action(action)

    action = Gio.SimpleAction.new('theme-light', None)
    action.connect('activate', self._theme_light)
    self.add_action(action)

    action = Gio.SimpleAction.new('theme-sepia', None)
    action.connect('activate', self._theme_sepia)
    self.add_action(action)

    action = Gio.SimpleAction.new('theme-dark', None)
    action.connect('activate', self._theme_dark)
    self.add_action(action)

    action = Gio.SimpleAction.new('about', None)
    action.connect('activate', self._about_cb)
    self.add_action(action)

    action = Gio.SimpleAction.new('quit', None)
    action.connect('activate', self._quit_cb)
    self.add_action(action)
    self.set_accels_for_action('app.quit', ('<Ctrl>Q',))

  # Manage command line options

  def do_command_line(self, command_line):
    options = command_line.get_options_dict().end().unpack()

    if 'url' in options:
      self._launch_uri = options['url']

    if self._window:
      self._window.new_page(self._launch_uri, None, True)
      return 0

    self.activate()
    return 0

  # Create main window and connect close event

  def do_activate(self):
    if not self._window:
      self._window = Window(self, self._launch_uri)
      self._window.connect('close-request',self._window_close_cb)

      self._window.present()

  # Set theme system

  def _theme_system(self, action, parameter):
    self._style_manager.set_color_scheme(Adw.ColorScheme.PREFER_LIGHT)
    Gtk.StyleContext.remove_provider_for_display(Gdk.Display.get_default(), self._css_sepia)
    settings.set_int('theme', 3)

  # Set theme light

  def _theme_light(self, action, parameter):
    self._style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
    Gtk.StyleContext.remove_provider_for_display(Gdk.Display.get_default(), self._css_sepia)
    settings.set_int('theme', 0)

  # Set theme sepia

  def _theme_sepia(self, action, parameter):
    self._style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
    Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), self._css_sepia, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    settings.set_int('theme', 2)

  # Set theme dark

  def _theme_dark(self, action, parameter):
    self._style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
    Gtk.StyleContext.remove_provider_for_display(Gdk.Display.get_default(), self._css_sepia)
    settings.set_int('theme', 1)

  # Show preferences window

  def _prefs_cb(self, action, parameter):
    prefs_window = PrefsWindow()
    prefs_window.set_transient_for(self._window)

    prefs_window.show()

  # Show about window

  def _about_cb(self, action, parameter):
    builder = Gtk.Builder()
    builder.add_from_resource('/com/github/hugolabe/Wike/ui/about.ui')
    about_window = builder.get_object('about_window')
    about_window.set_transient_for(self._window)

    about_window.add_link(_('Source Code'), 'https://github.com/hugolabe/Wike')
    about_window.add_link(_('Report an Issue'), 'https://github.com/hugolabe/Wike/issues')
    about_window.add_link(_('Help Translating'), 'https://poeditor.com/join/project?hash=kNgJu4MAum')
    about_window.set_developers(['Hugo Olabera <hugolabe@gmail.com>', _('Contributors') + ' https://github.com/hugolabe/Wike/graphs/contributors',])
    about_window.add_credit_section(_('Flag Icons'), ['HatScripts https://github.com/HatScripts/',])
    about_window.add_legal_section('Wikipedia', _('All content from Wikipedia.org and available under CC BY-SA 3.0 unless otherwise noted.\n\nWike is an independent development not endorsed by or affiliated with the Wikimedia Foundation.'), Gtk.License.UNKNOWN, None)
    about_window.add_legal_section('Circle Flags', 'Copyright © 2022 HatScripts', Gtk.License.MIT_X11, None)

    about_window.show()

  # On window close quit app

  def _window_close_cb(self, window):
    window.tabview.disconnect(window.handler_selpage)
    quit_action = self.lookup_action('quit')
    quit_action.activate()

  # Save settings and data and quit app

  def _quit_cb(self, action, parameter):
    if self._window.is_maximized():
      settings.set_boolean('window-max', True)
    else:
      settings.set_boolean('window-max', False)
      size = self._window.get_default_size()
      settings.set_int('window-width', size[0])
      settings.set_int('window-height', size[1])

    if self._window.page.wikiview.is_local():
      settings.set_string('last-uri', '')
    else:
      settings.set_string('last-uri', self._window.page.wikiview.get_base_uri())

    settings.sync()
    languages.save()
    if not settings.get_boolean('keep-history'):
      history.clear()
    if settings.get_boolean('clear-data-on-close'):
      data_manager = network_session.get_website_data_manager()
      data_manager.clear(WebKit.WebsiteDataTypes.ALL, 0, None, None, None)

    history.save()
    bookmarks.save()

    self.quit()


# Run app

def main(version):
  app = Application()
  return app.run(sys.argv)
