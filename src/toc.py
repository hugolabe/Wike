# toc.py
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
from gi.repository import Gio, GLib, Gtk


# Popover class for TOC
# Show table of contents for current page

class TocPopover(Gtk.Popover):

  # Initialize popover and set actions

  def __init__(self, window):
    super().__init__()
    self.set_size_request(300, -1)

    self._window = window

    actions = Gio.SimpleActionGroup()
    action = Gio.SimpleAction.new('section', GLib.VariantType('s'))
    action.connect('activate', self._section_activate_cb)
    actions.add_action(action)
    self.insert_action_group('toc_popover', actions)

  # Create toc menu and populate

  def populate(self, toc):
    self._toc = toc
    menu = Gio.Menu()
    self.bind_model(menu, None)
    if toc != None:
      self._fill_menu(menu, toc, 0)

  # Fill toc menu and submenus

  def _fill_menu(self, menu, toc, index):
    level = toc[index]['toclevel']

    if index > 0:
      action_string = 'toc_popover.section(\'' + str(index-1) + '\')'
      text = toc[index-1]['anchor'].replace('_', ' ')
      if len(text) > 45:
        text = text[0:44] + '...'
      button = Gio.MenuItem.new(text, action_string)
      menu.append_item(button)

    while index < len(toc) - 1:
      leap = level - toc[index+1]['toclevel']
      text = toc[index]['anchor'].replace('_', ' ')
      if len(text) > 45:
        text = text[0:44] + '...'

      if leap >= 0:
        action_string = 'toc_popover.section(\'' + str(index) + '\')'
        button = Gio.MenuItem.new(text, action_string)
        menu.append_item(button)
        index += 1
        if leap > 0:
          return index
      elif leap < 0:
        submenu = Gio.Menu()
        menu.append_submenu(text, submenu)
        index = self._fill_menu(submenu, toc, index+1)
        if toc[index]['toclevel'] < level:
          return index

    if toc[index]['toclevel'] == level:
      action_string = 'toc_popover.section(\'' + str(index) + '\')'
      text = toc[index]['anchor'].replace('_', ' ')
      if len(text) > 45:
        text = text[0:44] + '...'
      button = Gio.MenuItem.new(text, action_string)
      menu.append_item(button)
      return index

    return index

  # On menu activated load section

  def _section_activate_cb(self, action, parameter):
    index = int(parameter.unpack())
    anchor = self._toc[index]['anchor']
    self._window.page.wikiview.load_section(anchor)

