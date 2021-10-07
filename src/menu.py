# menu.py
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
from gi.repository import Gio, Gdk, Gtk

from wike.data import settings


# Popover class for main menu
# Show and manage main menu

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/ui/menu.ui')
class MenuPopover(Gtk.Popover):

  __gtype_name__ = 'MenuPopover'
  
  light_button = Gtk.Template.Child()
  sepia_button = Gtk.Template.Child()
  dark_button = Gtk.Template.Child()

  # Load custom css for theme buttons and connect signals

  def __init__(self, window):
    super().__init__()

    self._window = window
    
    gfile = Gio.File.new_for_uri('resource:///com/github/hugolabe/Wike/ui/menu.css')
    css_provider = Gtk.CssProvider()
    css_provider.load_from_file(gfile)
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)
    
    if settings.get_int('theme') == 1:
      self.dark_button.set_active(True)
    elif settings.get_int('theme') == 2:
      self.sepia_button.set_active(True)

    self.light_button.connect('toggled', self._light_button_toggled_cb)
    self.sepia_button.connect('toggled', self._sepia_button_toggled_cb)
    self.dark_button.connect('toggled', self._dark_button_toggled_cb)
  
  # Change to light theme on button toggle
  
  def _light_button_toggled_cb(self, button):
    if button.get_active():
      app = self._window.get_application()
      theme_action = app.lookup_action('theme_light')
      theme_action.activate()

  # Change to sepia theme on button toggle
  
  def _sepia_button_toggled_cb(self, button):
    if button.get_active():
      app = self._window.get_application()
      theme_action = app.lookup_action('theme_sepia')
      theme_action.activate()

  # Change to dark theme on button toggle
  
  def _dark_button_toggled_cb(self, button):
    if button.get_active():
      app = self._window.get_application()
      theme_action = app.lookup_action('theme_dark')
      theme_action.activate()
    
