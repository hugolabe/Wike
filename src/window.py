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
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gio, GLib, Gdk, Gtk, Adw

from wike.data import settings
from wike.header import HeaderBar
from wike.page import PageBox


# Application main window
# Contains a page and a headerbar

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/ui/window.ui')
class Window(Adw.ApplicationWindow):

  __gtype_name__ = 'Window'

  window_box = Gtk.Template.Child()
  tabbar = Gtk.Template.Child()
  tabview = Gtk.Template.Child()
  notification = Gtk.Template.Child()
  notification_label = Gtk.Template.Child()
  notification_close_button = Gtk.Template.Child()

  # Initialize window, set actions and connect signals

  def __init__(self, app, launch_uri):
    super().__init__(title='Wike', application=app)

    # Set default window icon name for XFCE, LXQt, MATE
    self.set_default_icon_name('com.github.hugolabe.Wike')

    self.set_default_size(settings.get_int('window-width'), settings.get_int('window-height'))
    if settings.get_boolean('window-max'):
      self.maximize()

    self.page = PageBox(self)
    tabpage = self.tabview.append(self.page)

    self.headerbar = HeaderBar(self)
    self.window_box.prepend(self.headerbar)

    actions = [ ('prev_page', self._prev_page_cb, ('<Alt>Left',)),
                ('next_page', self._next_page_cb, ('<Alt>Right',)),
                ('new_tab', self._new_tab_cb, ('<Ctrl>N',)),
                ('close_tab', self._close_tab_cb, ('<Ctrl>W',)),
                ('next_tab', self._next_tab_cb, ('<Ctrl>Tab',)),
                ('prev_tab', self._prev_tab_cb, ('<Shift><Ctrl>Tab',)),
                ('show_search', self._show_search_cb, ('F2', '<Ctrl>K',)),
                ('show_menu', self._show_menu_cb, ('F10',)),
                ('show_bookmarks', self._show_bookmarks_cb, ('<Ctrl>B',)),
                ('add_bookmark', self._add_bookmark_cb, ('<Ctrl>D',)),
                ('show_langlinks', self._show_langlinks_cb, ('<Ctrl>L',)),
                ('show_toc', self._show_toc_cb, ('<Ctrl>T',)),
                ('main_page', self._main_page_cb, ('<Alt>Home',)),
                ('random_article', self._random_article_cb, None),
                ('show_historic', self._show_historic_cb, ('<Ctrl>H',)),
                ('reload_page', self._reload_page_cb, ('F5', '<Ctrl>R',)),
                ('search_text', self._search_text_cb, ('<Ctrl>F',)),
                ('open_browser', self._open_browser_cb, None),
                ('copy_url', self._copy_url_cb, ('<Ctrl>U',)) ]

    for action, callback, accel in actions:
      simple_action = Gio.SimpleAction.new(action, None)
      simple_action.connect('activate', callback)
      self.add_action(simple_action)
      if accel:
        app.set_accels_for_action('win.' + action, accel)

    self.handler_selpage = self.tabview.connect('notify::selected-page', self._tabview_selected_page_cb)
    self.tabview.connect('close-page', self._tabview_close_page_cb)
    self.notification_close_button.connect('clicked', self._hide_notification_cb)

    if launch_uri == 'notfound':
      self.page.wikiview.load_message(launch_uri, None)
    else:
      if launch_uri != '':
        self.page.wikiview.load_wiki(launch_uri)
      else:
        if settings.get_int('on-start-load') == 0:
          self.page.wikiview.load_main()
        elif settings.get_int('on-start-load') == 1:
          self.page.wikiview.load_random()
        else:
          if settings.get_string('last-uri'):
            self.page.wikiview.load_wiki(settings.get_string('last-uri'))
          else:
            self.page.wikiview.load_main()

  # Create new tab with a page

  def new_page(self, uri, parent, select):
    page = PageBox(self)
    tabpage = self.tabview.add_page(page, parent)
    if uri == 'blank' or uri == 'notfound':
      page.wikiview.load_message(uri, None)
    else:
      page.wikiview.load_wiki(uri)

    if select:
      self.tabview.set_selected_page(tabpage)

  # New empty tab

  def _new_tab_cb(self, action, parameter):
    self.new_page('blank', None, True)

  # Close current tab

  def _close_tab_cb(self, action, parameter):
    if self.tabview.get_n_pages() > 1:
      tabpage = self.tabview.get_selected_page()
      self.tabview.close_page(tabpage)

  # Go to next tab

  def _next_tab_cb(self, action, parameter):
    num_pages = self.tabview.get_n_pages()
    if num_pages == 1:
      return

    tabpage = self.tabview.get_selected_page()
    if self.tabview.get_page_position(tabpage) < num_pages - 1:
      self.tabview.select_next_page()
    else:
      tabpage = self.tabview.get_nth_page(0)
      self.tabview.set_selected_page(tabpage)

  # Go to previous tab

  def _prev_tab_cb(self, action, parameter):
    num_pages = self.tabview.get_n_pages()
    if num_pages == 1:
      return

    tabpage = self.tabview.get_selected_page()
    if self.tabview.get_page_position(tabpage) > 0:
      self.tabview.select_previous_page()
    else:
      tabpage = self.tabview.get_nth_page(num_pages - 1)
      self.tabview.set_selected_page(tabpage)

  # On tab selected event refresh headerbar controls

  def _tabview_selected_page_cb(self, tabview, value):
    tabpage = tabview.get_selected_page()
    if not tabpage:
      return

    self.page = tabpage.get_child()
    self.refresh_nav_buttons(self.page.wikiview)
    self.headerbar.set_title(self.page.wikiview.title)
    self.headerbar.toc_button.set_sensitive(False)
    self.headerbar.langlinks_button.set_sensitive(False)
    self.headerbar.set_toc(self.page.wikiview.sections)
    self.headerbar.set_langlinks(self.page.wikiview.langlinks)

  # On tab closed event destroy wikiview and confirm

  def _tabview_close_page_cb(self, tabview, tabpage):
    page = tabpage.get_child()
    page.wikiview.destroy()
    tabview.close_page_finish(tabpage, True)
    return True

  # Go to previous page

  def _prev_page_cb(self, action, parameter):
    if self.page.wikiview.can_go_back():
      self.page.wikiview.go_back()

  # Go to next page

  def _next_page_cb(self, action, parameter):
    if self.page.wikiview.can_go_forward():
      self.page.wikiview.go_forward()

  # Show search entry

  def _show_search_cb(self, action, parameter):
    self.headerbar.search_button.set_active(not self.headerbar.search_button.get_active())

  # Show main menu

  def _show_menu_cb(self, action, parameter):
    self.headerbar.menu_button.set_active(not self.headerbar.menu_button.get_active())

  # Show bookmarks popover

  def _show_bookmarks_cb(self, action, parameter):
    if not self.headerbar.bookmarks_button.get_active():
      self.headerbar.bookmarks_button.set_active(True)

  # Add current page to bookmarks

  def _add_bookmark_cb(self, action, parameter):
    if not self.page.wikiview.is_local():
      uri = self.page.wikiview.get_base_uri()
      title = self.page.wikiview.title
      lang = self.page.wikiview.get_lang()
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
    self.page.wikiview.load_main()

  # Show Wikipedia random article

  def _random_article_cb(self, action, parameter):
    self.page.wikiview.load_random()

  # Show historic

  def _show_historic_cb(self, action, parameter):
    self.page.wikiview.load_historic()

  # Reload article view

  def _reload_page_cb(self, action, parameter):
    self.page.wikiview.reload()

  # Show text search bar

  def _search_text_cb(self, action, parameter):
    if not self.page.search_bar.get_search_mode():
      self.page.search_bar.set_search_mode(True)
    else:
      self.page.textsearch_entry.grab_focus()

  # Open article in external browser

  def _open_browser_cb(self, action, parameter):
    uri = self.page.wikiview.get_base_uri()
    Gtk.show_uri(None, uri, Gdk.CURRENT_TIME)

  # Copy article URL to clipboard

  def _copy_url_cb(self, action, parameter):
    uri = self.page.wikiview.get_base_uri()
    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
    clipboard.set_text(uri, -1)

    self.show_notification(_('Wikipedia URL copied to clipboard'))

  # Refresh navigation buttons state

  def refresh_nav_buttons(self, wikiview):
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

