# page.py
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
gi.require_version('WebKit2', '4.0')
from gi.repository import Gdk, Gtk, WebKit2

from wike.data import settings, historic
from wike.view import WikiView


# Page box for each tab
# Contains a webview and a search bar

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/ui/page.ui')
class PageBox(Gtk.Box):

  __gtype_name__ = 'PageBox'

  search_bar = Gtk.Template.Child()
  textsearch_entry = Gtk.Template.Child()
  textsearch_prev_button = Gtk.Template.Child()
  textsearch_next_button = Gtk.Template.Child()
  textsearch_matches_label = Gtk.Template.Child()

  # Add wikiview, initialize find controller and connect signals

  def __init__(self, window):
    super().__init__()

    self._window = window

    self.wikiview = WikiView()
    self.pack_end(self.wikiview, True, True, 0)
    self.wikiview.show()

    find_controller = self.wikiview.get_find_controller()
    nav_list = self.wikiview.get_back_forward_list()
    self.search_bar.connect_entry(self.textsearch_entry)

    self.wikiview.connect('load-changed', self._wikiview_load_changed_cb)
    self.wikiview.connect('load-failed', self._wikiview_load_failed_cb)
    self.wikiview.connect('new-page', self._wikiview_new_page_cb)
    self.textsearch_entry.connect('changed', self._textsearch_entry_changed_cb, find_controller)
    self.textsearch_entry.connect('activate', self._textsearch_entry_activate_cb, find_controller)
    self.textsearch_prev_button.connect('clicked', self._textsearch_prev_button_clicked_cb, find_controller)
    self.textsearch_next_button.connect('clicked', self._textsearch_next_button_clicked_cb, find_controller)
    find_controller.connect('found-text', self._find_controller_found_cb)
    find_controller.connect('failed-to-find-text', self._find_controller_not_found_cb)
    find_controller.connect('counted-matches', self._find_controller_matches_cb)
    nav_list.connect('changed', self._nav_list_changed_cb)

  # Manage wikiview load page events

  def _wikiview_load_changed_cb(self, wikiview, event):
    tabpage = self._window.tabview.get_page(self)

    if event == WebKit2.LoadEvent.STARTED:
      if self.search_bar.get_search_mode(): self.search_bar.set_search_mode(False)
      tabpage.set_title(_('Loading Article'))
      tabpage.set_loading(True)
      if tabpage.get_selected():
        self._window.headerbar.set_title('Loading Article')
        self._window.headerbar.toc_button.set_sensitive(False)
        self._window.headerbar.langlinks_button.set_sensitive(False)
        if self._window.headerbar.search_button.get_active():
          self._window.headerbar.search_button.set_active(False)
    elif event == WebKit2.LoadEvent.COMMITTED:
      wikiview.set_props()
      tabpage.set_title(wikiview.title)
      if tabpage.get_selected():
        self._window.headerbar.set_title(wikiview.title)
        self._window.headerbar.set_toc(wikiview.sections)
        self._window.headerbar.set_langlinks(wikiview.langlinks)
    elif event == WebKit2.LoadEvent.FINISHED:
      tabpage.set_loading(False)
      if settings.get_boolean('keep-historic') and not wikiview.is_local():
        historic.add(wikiview.get_base_uri(), wikiview.title, wikiview.get_lang())

  # If wikiview load failed show error

  def _wikiview_load_failed_cb(self, wikiview, event, uri, error):
    if not wikiview.is_loading():
      wikiview.load_message('error', uri)
    return True

  # On webview event create new page

  def _wikiview_new_page_cb(self, wikiview, uri):
    tabpage = self._window.tabview.get_page(self)
    self._window.new_page(uri, tabpage, False)

  # Search text in article when entry changes

  def _textsearch_entry_changed_cb(self, textsearch_entry, find_controller):
    text_length = textsearch_entry.get_text_length()
    if text_length > 2:
      text = textsearch_entry.get_text()
      find_controller.count_matches(text, WebKit2.FindOptions.WRAP_AROUND | WebKit2.FindOptions.CASE_INSENSITIVE, 9999)
      find_controller.search(text, WebKit2.FindOptions.WRAP_AROUND | WebKit2.FindOptions.CASE_INSENSITIVE, 9999)
    else:
      self.textsearch_matches_label.set_label('')
      self.textsearch_prev_button.set_sensitive(False)
      self.textsearch_next_button.set_sensitive(False)
      find_controller.search_finish()

  # On entry activated search next match

  def _textsearch_entry_activate_cb(self, textsearch_entry, find_controller):
    text_length = textsearch_entry.get_text_length()
    if text_length > 2:
      find_controller.search_next()

  # On text search prev button clicked search previous match

  def _textsearch_prev_button_clicked_cb(self, textsearch_prev_button, find_controller):
    find_controller.search_previous()

  # On text search next button clicked search next match

  def _textsearch_next_button_clicked_cb(self, textsearch_next_button, find_controller):
    find_controller.search_next()

  # Found text in article

  def _find_controller_found_cb(self, find_controller, match_count):
    self.textsearch_prev_button.set_sensitive(True)
    self.textsearch_next_button.set_sensitive(True)

  # Not found text in article

  def _find_controller_not_found_cb(self, find_controller):
    self.textsearch_matches_label.set_markup('<span foreground="red">' + str(0) + '</span>')
    self.textsearch_prev_button.set_sensitive(False)
    self.textsearch_next_button.set_sensitive(False)
    find_controller.search_finish()
    Gdk.beep()

  # Show text search matches found

  def _find_controller_matches_cb(self, find_controller, match_count):
    self.textsearch_matches_label.set_label(str(match_count))

  # Refresh navbox state on navlist changed

  def _nav_list_changed_cb(self, nav_list, item_added, item_removed):
    tabpage = self._window.tabview.get_page(self)
    if tabpage.get_selected():
      self._window.refresh_nav_buttons(self.wikiview)

