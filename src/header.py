# This file is part of Wike (com.github.hugolabe.Wike)
# SPDX-FileCopyrightText: 2021-23 Hugo Olabera <hugolabe@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later


from gi.repository import Gtk

from wike.menu import MainMenuPopover, ViewMenuPopover
from wike.search import SearchBox


# Headerbar for main window

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/ui/headerbar.ui')
class HeaderBar(Gtk.HeaderBar):

  __gtype_name__ = 'HeaderBar'

  prev_button = Gtk.Template.Child()
  next_button = Gtk.Template.Child()
  newtab_button = Gtk.Template.Child()
  tabs_button = Gtk.Template.Child()
  menu_button = Gtk.Template.Child()
  view_button = Gtk.Template.Child()
  flap_button = Gtk.Template.Child()

  # Set main menu popover and searchbox as custom title

  def __init__(self, window):
    super().__init__()

    self._window = window
    self._actionbar = window.actionbar
    
    self.tabs_button.set_view(window.tabview)

    self.main_menu_popover = MainMenuPopover()
    self.menu_button.set_popover(self.main_menu_popover)

    self.search_box = SearchBox(window)
    self.set_title_widget(self.search_box)

    self.set_mobile(True)
  
  # Set headerbar for mobile or desktop
  
  def set_mobile(self, mobile_layout):
    if mobile_layout:
      self.prev_button.set_visible(False)
      self.next_button.set_visible(False)
      self.newtab_button.set_visible(False)
      self.tabs_button.set_visible(True)
      self.flap_button.set_visible(False)
      self.view_button.set_visible(False)
      self.search_box.set_size_request(-1, -1)
      view_menu_popover = self.view_button.get_popover()
      if view_menu_popover:
        self.view_button.set_popover(None)
        view_menu_popover.run_dispose()
      if not self._actionbar.view_button.get_popover():
        self._actionbar.view_button.set_popover(ViewMenuPopover(self._window))
      self._actionbar.set_reveal_child(True)
      self._window.tabbar.set_visible(False)
    else:
      self.prev_button.set_visible(True)
      self.next_button.set_visible(True)
      self.newtab_button.set_visible(True)
      self.tabs_button.set_visible(False)
      self.flap_button.set_visible(True)
      self.view_button.set_visible(True)
      self.search_box.set_size_request(320, -1)
      view_menu_popover = self._actionbar.view_button.get_popover()
      if view_menu_popover:
        self._actionbar.view_button.set_popover(None)
        view_menu_popover.run_dispose()
      if not self.view_button.get_popover():
        self.view_button.set_popover(ViewMenuPopover(self._window))
      self._actionbar.set_reveal_child(False)
      self._window.tabbar.set_visible(True)


# Actionbar for main window and mobile layout

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/ui/actionbar.ui')
class ActionBar(Gtk.Revealer):

  __gtype_name__ = 'ActionBar'

  view_button = Gtk.Template.Child()

  # Initialize

  def __init__(self):
    super().__init__()
