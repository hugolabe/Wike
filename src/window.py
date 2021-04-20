# window.py
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
gi.require_version('Handy', '1')
from gi.repository import Gio, GLib, Gdk, Gtk, Handy, WebKit2

from wike.data import settings, historic
from wike.header import HeaderBar
from wike.view import wikiview


# Application main window
# Contains a webview, a search bar and a headerbar

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/ui/window.ui')
class Window(Handy.ApplicationWindow):

  __gtype_name__ = 'Window'

  window_box = Gtk.Template.Child()
  content_box = Gtk.Template.Child()
  search_bar = Gtk.Template.Child()
  textsearch_entry = Gtk.Template.Child()
  textsearch_prev_button = Gtk.Template.Child()
  textsearch_next_button = Gtk.Template.Child()
  textsearch_matches_label = Gtk.Template.Child()
  notification = Gtk.Template.Child()
  notification_label = Gtk.Template.Child()
  notification_close_button = Gtk.Template.Child()

  # Initialize window, set actions and connect signals

  def __init__(self, app):
    super().__init__(title='Wike', application=app)

    self.set_default_size(settings.get_int('window-width'), settings.get_int('window-height'))
    if settings.get_boolean('window-max'): self.maximize()

    self.content_box.pack_end(wikiview, True, True, 0)

    self.headerbar = HeaderBar()
    self.window_box.pack_start(self.headerbar, False, True, 0)

    actions = [ ('prev_page', self._prev_page_cb, ('<Alt>Left',)),
                ('next_page', self._next_page_cb, ('<Alt>Right',)),
                ('show_search', self._show_search_cb, ('F2',)),
                ('show_bookmarks', self._show_bookmarks_cb, ('<Ctrl>B',)),
                ('add_bookmark', self._add_bookmark_cb, ('<Ctrl>D',)),
                ('show_langlinks', self._show_langlinks_cb, ('<Ctrl>L',)),
                ('show_toc', self._show_toc_cb, ('<Ctrl>T',)),
                ('main_page', self._main_page_cb, ('<Alt>Home',)),
                ('random_article', self._random_article_cb, None),
                ('show_historic', self._show_historic_cb, ('<Ctrl>H',)),
                ('reload_page', self._reload_page_cb, ('F5',)),
                ('search_text', self._search_text_cb, ('<Ctrl>F',)),
                ('open_browser', self._open_browser_cb, None),
                ('copy_url', self._copy_url_cb, ('<Ctrl>U',)) ]

    for action, callback, accel in actions:
      simple_action = Gio.SimpleAction.new(action, None)
      simple_action.connect('activate', callback)
      self.add_action(simple_action)
      if accel: app.set_accels_for_action('win.' + action, accel)

    find_controller = wikiview.get_find_controller()
    nav_list = wikiview.get_back_forward_list()
    self.search_bar.connect_entry(self.textsearch_entry)

    wikiview.connect('load-wiki', self._wikiview_load_wiki_cb)
    wikiview.connect('load-changed', self._wikiview_load_changed_cb)
    wikiview.connect('load-failed', self._wikiview_load_failed_cb)
    wikiview.connect('add-bookmark', self._wikiview_add_bookmark_cb)
    self.textsearch_entry.connect('changed', self._textsearch_entry_changed_cb, find_controller)
    self.textsearch_entry.connect('activate', self._textsearch_entry_activate_cb, find_controller)
    self.textsearch_prev_button.connect('clicked', self._textsearch_prev_button_clicked_cb, find_controller)
    self.textsearch_next_button.connect('clicked', self._textsearch_next_button_clicked_cb, find_controller)
    find_controller.connect('found-text', self._find_controller_found_cb)
    find_controller.connect('failed-to-find-text', self._find_controller_not_found_cb)
    find_controller.connect('counted-matches', self._find_controller_matches_cb)
    nav_list.connect('changed', self._nav_list_changed_cb)
    self.notification_close_button.connect('clicked', self._hide_notification_cb)

    if settings.get_string('on-start-load') == 'main':
      wikiview.load_main()
    elif settings.get_string('on-start-load') == 'random':
      wikiview.load_random()
    else:
      if settings.get_string('last-uri'):
        wikiview.load_wiki(settings.get_string('last-uri'))
      else:
        wikiview.load_main()

  # Show spinner on wikiview load started

  def _wikiview_load_wiki_cb(self, wikiview):
    self.headerbar.show_spinner()

  # Manage wikiview load page events

  def _wikiview_load_changed_cb(self, wikiview, event):
    if event == WebKit2.LoadEvent.STARTED:
      if self.search_bar.get_search_mode(): self.search_bar.set_search_mode(False)
      self.headerbar.toc_button.set_sensitive(False)
      self.headerbar.langlinks_button.set_sensitive(False)
    elif event == WebKit2.LoadEvent.FINISHED:
      self.headerbar.hide_spinner()
      props = wikiview.get_props()
      self.headerbar.set_page_menus(props)
      if settings.get_boolean('keep-historic') and not wikiview.is_local():
        historic.add(wikiview.get_base_uri(), wikiview.get_title(), wikiview.get_lang())

  # If wikiview load failed show error

  def _wikiview_load_failed_cb(self, wikiview, event, uri, error):
    if not wikiview.is_loading():
      wikiview.load_message('error')
    return True

  # On webview bookmark added show notification

  def _wikiview_add_bookmark_cb(self, wikiview, uri, title, lang):
    if self.headerbar.bookmarks_popover.add_bookmark(uri, title, lang):
      message = _('New bookmark: ') + title
      self.show_notification(message)

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
    prev_page_action = self.lookup_action('prev_page')
    next_page_action = self.lookup_action('next_page')

    if wikiview.can_go_back():
      prev_page_action.set_enabled(True)
    else:
      prev_page_action.set_enabled(False)
    if wikiview.can_go_forward():
      next_page_action.set_enabled(True)
    else:
      next_page_action.set_enabled(False)

  # Go to previous page

  def _prev_page_cb(self, action, parameter):
    if wikiview.can_go_back():
      wikiview.go_back()
      self.headerbar.hide_spinner()

  # Go to next page

  def _next_page_cb(self, action, parameter):
    if wikiview.can_go_forward():
      wikiview.go_forward()
      self.headerbar.hide_spinner()

  # Show search entry

  def _show_search_cb(self, action, parameter):
    self.headerbar.search_button.set_active(not self.headerbar.search_button.get_active())

  # Show bookmarks popover

  def _show_bookmarks_cb(self, action, parameter):
    if not self.headerbar.bookmarks_button.get_active():
      self.headerbar.bookmarks_button.set_active(True)

  # Add current page to bookmarks

  def _add_bookmark_cb(self, action, parameter):
    if not wikiview.is_local():
      uri = wikiview.get_base_uri()
      title = wikiview.get_title()
      lang = wikiview.get_lang()
      if self.headerbar.bookmarks_popover.add_bookmark(uri, title, lang):
        if self.headerbar.bookmarks_popover.is_visible():
          self.headerbar.bookmarks_popover.bookmarks_list.show_all()
        else:
          message = _('New bookmark: ') + title
          self.show_notification(message)

  # Show langlinks popover

  def _show_langlinks_cb(self, action, parameter):
    if self.headerbar.langlinks_button.get_sensitive():
      if not self.headerbar.langlinks_button.get_active():
        self.headerbar.langlinks_button.set_active(True)

  # Show toc popover

  def _show_toc_cb(self, action, parameter):
    if self.headerbar.toc_button.get_sensitive():
      if not self.headerbar.toc_button.get_active():
        self.headerbar.toc_button.set_active(True)

  # Show Wikipedia main page

  def _main_page_cb(self, action, parameter):
    wikiview.load_main()

  # Show Wikipedia random article

  def _random_article_cb(self, action, parameter):
    wikiview.load_random()

  # Show historic

  def _show_historic_cb(self, action, parameter):
    wikiview.load_historic()

  # Reload article view

  def _reload_page_cb(self, action, parameter):
    wikiview.reload()

  # Show text search bar

  def _search_text_cb(self, action, parameter):
    if not self.search_bar.get_search_mode():
      self.search_bar.set_search_mode(True)
    else:
      self.textsearch_entry.grab_focus()

  # Open article in external browser

  def _open_browser_cb(self, action, parameter):
    uri = wikiview.get_base_uri()
    Gtk.show_uri(None, uri, Gdk.CURRENT_TIME)

  # Copy article URL to clipboard

  def _copy_url_cb(self, action, parameter):
    uri = wikiview.get_base_uri()
    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
    clipboard.set_text(uri, -1)

    self.show_notification(_('Wikipedia URL copied to clipboard'))

  # Show notification with provided message

  def show_notification(self, message):
    self.notification_label.set_label(message)
    self.notification.set_reveal_child(True)
    GLib.timeout_add_seconds(3, self._hide_notification_cb, None)

  # Hide notification on button clicked or time expired

  def _hide_notification_cb(self, close_button):
    if self.notification.get_reveal_child():
      self.notification.set_reveal_child(False)
    return False

