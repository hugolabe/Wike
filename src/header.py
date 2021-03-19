# header.py
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
from gi.repository import Gtk

from wike.data import settings, historic
from wike.bookmarks import BookmarksPopover
from wike.langlinks import LanglinksPopover
from wike.search import SearchEntry
from wike.toc import TocPopover
from wike.view import wikiview


# Headerbar for main window
# Contains widgets for manage searchs, navigation and popovers

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/ui/header.ui')
class HeaderBar(Gtk.HeaderBar):

  __gtype_name__ = 'HeaderBar'

  search_button = Gtk.Template.Child()
  menu_button = Gtk.Template.Child()
  bookmarks_button = Gtk.Template.Child()
  langlinks_button = Gtk.Template.Child()
  toc_button = Gtk.Template.Child()

  # Set main menu and connect signals and actions

  def __init__(self):
    super().__init__()

    builder_menu = Gtk.Builder()
    builder_menu.add_from_resource("/com/github/hugolabe/Wike/ui/menu.ui")
    menu = builder_menu.get_object("menu")

    builder_spinner = Gtk.Builder()
    builder_spinner.add_from_resource("/com/github/hugolabe/Wike/ui/header-spinner.ui")
    self._spinner_box = builder_spinner.get_object("spinner_box")
    self._spinner = builder_spinner.get_object("spinner")

    self.search_entry = SearchEntry(self.search_button)
    self.bookmarks_popover = BookmarksPopover()
    self.langlinks_popover = LanglinksPopover()
    self.toc_popover = TocPopover()

    self.menu_button.set_menu_model(menu)
    self.menu_button.get_popover().set_size_request(280, -1)
    self.bookmarks_button.set_popover(self.bookmarks_popover)
    self.langlinks_button.set_popover(self.langlinks_popover)
    self.toc_button.set_popover(self.toc_popover)

    self.search_button.connect('clicked', self._search_button_cb)
    self.menu_button.connect('toggled', self._menu_button_cb)

  # Show headerbar spinner and disable search button

  def show_spinner(self):
    if self.search_button.get_active():
      self.search_button.set_active(False)
    self.set_custom_title(self._spinner_box)
    self.search_button.set_sensitive(False)
    self._spinner.start()

  # Hide headerbar spinner and enable search button

  def hide_spinner(self):
    if self.search_button.get_active():
      self.search_button.set_active(False)
    self.search_button.set_sensitive(True)
    self._spinner.stop()
    self.set_title(wikiview.get_title())
    self.set_custom_title(None)

  # Set menus for toc and langlinks

  def set_page_menus(self, props):
    if props == None:
      self.toc_popover.populate(None)
      self.langlinks_popover.populate(None)
    else:
      sections = props['sections']
      langlinks = props['langlinks']
      if len(sections) > 0:
        self.toc_popover.populate(sections)
        self.toc_button.set_sensitive(True)
      else:
        self.toc_popover.populate(None)
      if len(langlinks) > 0:
        if self.langlinks_popover.populate(langlinks):
          self.langlinks_button.set_sensitive(True)
      else:
        self.langlinks_popover.populate(None)
      if len(props['redirects']) > 0:
        self.set_title(props['title'])

  # Refresh_languages for settings and langlinks popovers

  def refresh_langs(self):
    self.search_entry.settings_popover.populate_list()
    if self.search_entry.settings_popover.is_visible():
      self.search_entry.settings_popover.show_all()

    if self.langlinks_popover.refresh():
      if not self.langlinks_button.get_sensitive():
        self.langlinks_button.set_sensitive(True)
      if self.langlinks_popover.is_visible():
        self.langlinks_popover.show_all()
    else:
      if self.langlinks_popover.is_visible():
        self.langlinks_popover.hide()
      self.langlinks_button.set_sensitive(False)

  # Show search entry on button toggled

  def _search_button_cb(self, search_button):
    if search_button.get_active():
      self.set_custom_title(self.search_entry)
      self.search_entry.show()
      self.search_entry.grab_focus()
    else:
      self.search_entry.hide()
      self.set_custom_title(None)

  # Enable or disable menu items on button toggled

  def _menu_button_cb(self, menu_button):
    if menu_button.get_active():
      window = self.get_parent()
      show_historic_action = window.lookup_action('show_historic')
      open_browser_action = window.lookup_action('open_browser')
      copy_url_action = window.lookup_action('copy_url')

      if wikiview.is_local():
        open_browser_action.set_enabled(False)
        copy_url_action.set_enabled(False)
      else:
        open_browser_action.set_enabled(True)
        copy_url_action.set_enabled(True)
      if settings.get_boolean('keep-historic') and len(historic.items) > 0:
        show_historic_action.set_enabled(True)
      else:
        show_historic_action.set_enabled(False)

