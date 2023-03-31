# This file is part of Wike (com.github.hugolabe.Wike)
# SPDX-FileCopyrightText: 2021-23 Hugo Olabera <hugolabe@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later


import gi
gi.require_version('Gtk', '4.0')
gi.require_version('WebKit', '6.0')
from gi.repository import Gtk, WebKit

from wike.data import settings
from wike.view import WikiView


# Page box for each tab with webview and search bar

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/ui/page.ui')
class PageBox(Gtk.Box):

  __gtype_name__ = 'PageBox'

  search_bar = Gtk.Template.Child()
  search_entry = Gtk.Template.Child()
  search_prev_button = Gtk.Template.Child()
  search_next_button = Gtk.Template.Child()
  search_matches_label = Gtk.Template.Child()
  view_stack = Gtk.Template.Child()
  status_page = Gtk.Template.Child()
  main_page_button = Gtk.Template.Child()
  random_article_button = Gtk.Template.Child()
  try_again_button = Gtk.Template.Child()

  # Add wikiview, initialize find controller and connect signals

  def __init__(self, window):
    super().__init__()

    self._window = window

    self.wikiview = WikiView()
    self.wikiview.set_vexpand(True)
    self.view_stack.add_named(self.wikiview, 'wikiview')
    self.view_stack.set_visible_child_name('wikiview')

    find_controller = self.wikiview.get_find_controller()
    nav_list = self.wikiview.get_back_forward_list()
    self.search_bar.connect_entry(self.search_entry)

    self.wikiview.connect('load-changed', self._wikiview_load_changed_cb)
    self.wikiview.connect('new-page', self._wikiview_new_page_cb)
    self.wikiview.connect('add_bookmark', self._wikiview_add_bookmark_cb)
    self.try_again_button.connect('clicked', self._try_again_button_cb)
    self.search_entry.connect('search-changed', self._search_entry_changed_cb, find_controller)
    self.search_entry.connect('activate', self._search_entry_activate_cb, find_controller)
    self.search_prev_button.connect('clicked', self._search_prev_button_cb, find_controller)
    self.search_next_button.connect('clicked', self._search_next_button_cb, find_controller)
    find_controller.connect('found-text', self._find_controller_found_cb)
    find_controller.connect('failed-to-find-text', self._find_controller_not_found_cb)
    find_controller.connect('counted-matches', self._find_controller_matches_cb)
    nav_list.connect('changed', self._nav_list_changed_cb)

  # Manage wikiview load page events

  def _wikiview_load_changed_cb(self, wikiview, event):
    tabpage = self._window.tabview.get_page(self)

    if event == WebKit.LoadEvent.STARTED:
      if wikiview.get_uri().endswith('.wikipedia.org/'):
        self._is_main = True
      else:
        self._is_main = False
      if self.search_bar.get_search_mode():
        self.search_bar.set_search_mode(False)
      self.view_stack.set_visible_child_name('wikiview')
      tabpage.set_title(_('Loading'))
      tabpage.set_loading(True)
      if tabpage.get_selected():
        self._window.headerbar.search_box.reset()
        wikiview.grab_focus()

    elif event == WebKit.LoadEvent.COMMITTED:
      wikiview.set_props()
      tabpage.set_title(wikiview.title)
      if tabpage.get_selected():
        self._window.toc_box.populate(wikiview.title, wikiview.sections)
        self._window.langlinks_box.populate(wikiview.langlinks)
      self._window.bookmarks_box.refresh_buttons()
      self._window.refresh_menu_actions(wikiview.is_local())

    elif event == WebKit.LoadEvent.FINISHED:
      tabpage.set_loading(False)
      if wikiview.is_local():
        self._show_status_page(wikiview.get_uri())
      if settings.get_boolean('keep-history'):
        if not self._is_main and not wikiview.is_local():
          self._window.history_box.add_item(wikiview.get_base_uri(), wikiview.title, wikiview.get_lang())

  # If wikiview is local show status page

  def _show_status_page(self, uri):
    if uri == 'about:notfound':
      self.status_page.set_title(_('Article not Found'))
      self.status_page.set_description(_('Can\'t find any results for requested query'))
      self.status_page.set_icon_name('find-location-symbolic')
      self.main_page_button.set_visible(True)
      self.random_article_button.set_visible(False)
      self.try_again_button.set_visible(False)
      self.main_page_button.grab_focus()
    elif uri == 'about:error':
      self.status_page.set_title(_('Can\'t Access Wikipedia'))
      self.status_page.set_description(_('Check your Internet connection and try again'))
      self.status_page.set_icon_name('network-error-symbolic')
      self.main_page_button.set_visible(False)
      self.random_article_button.set_visible(False)
      self.try_again_button.set_visible(True)
      self.try_again_button.grab_focus()
    else:
      self.main_page_button.grab_focus()

    self.view_stack.set_visible_child_name('status')

  # Try again button clicked

  def _try_again_button_cb(self, try_again_button):
    if self.wikiview.fail_uri:
      self.wikiview.load_wiki(self.wikiview.fail_uri)

  # On webview event create new page

  def _wikiview_new_page_cb(self, wikiview, uri):
    tabpage = self._window.tabview.get_page(self)
    self._window.new_page(uri, tabpage, False)

  # On webview event add new bookmark

  def _wikiview_add_bookmark_cb(self, wikiview, uri, title, lang):
    if self._window.bookmarks_box.add_bookmark(uri, title, lang):
      message = _('Bookmark added: ') + title
      self._window.send_notification(message)

  # Search text in article when entry changes

  def _search_entry_changed_cb(self, search_entry, find_controller):
    text = search_entry.get_text()
    if len(text) > 2:
      find_controller.count_matches(text, WebKit.FindOptions.WRAP_AROUND | WebKit.FindOptions.CASE_INSENSITIVE, 9999)
      find_controller.search(text, WebKit.FindOptions.WRAP_AROUND | WebKit.FindOptions.CASE_INSENSITIVE, 9999)
    else:
      self.search_matches_label.set_label('')
      self.search_entry.remove_css_class('error')
      self.search_prev_button.set_sensitive(False)
      self.search_next_button.set_sensitive(False)
      find_controller.search_finish()

  # On entry activated search next match

  def _search_entry_activate_cb(self, search_entry, find_controller):
    text = search_entry.get_text()
    if len(text) > 2:
      find_controller.search_next()

  # On text search prev button clicked search previous match

  def _search_prev_button_cb(self, search_prev_button, find_controller):
    find_controller.search_previous()

  # On text search next button clicked search next match

  def _search_next_button_cb(self, search_next_button, find_controller):
    find_controller.search_next()

  # Found text in article

  def _find_controller_found_cb(self, find_controller, match_count):
    self.search_prev_button.set_sensitive(True)
    self.search_next_button.set_sensitive(True)

  # Not found text in article

  def _find_controller_not_found_cb(self, find_controller):
    self.search_matches_label.set_label('0')
    self.search_entry.add_css_class('error')
    self.search_prev_button.set_sensitive(False)
    self.search_next_button.set_sensitive(False)
    find_controller.search_finish()

  # Show text search matches found

  def _find_controller_matches_cb(self, find_controller, match_count):
    self.search_matches_label.set_label(str(match_count))
    self.search_entry.remove_css_class('error')

  # Refresh navbox state on navlist changed

  def _nav_list_changed_cb(self, nav_list, item_added, item_removed):
    tabpage = self._window.tabview.get_page(self)
    if tabpage.get_selected():
      self._window.refresh_nav_actions(self.wikiview)
