# This file is part of Wike (com.github.hugolabe.Wike)
# SPDX-FileCopyrightText: 2021-25 Hugo Olabera
# SPDX-License-Identifier: GPL-3.0-or-later


import os

from gi.repository import GLib, Gio, Gdk, Gtk, Adw, WebKit

from wike.data import settings
from wike.bookmarks import BookmarksPanel
from wike.history import HistoryPanel
from wike.langlinks import LanglinksPanel
from wike.menu import ArticleMenuPopover, MainMenuPopover, ViewMenuPopover
from wike.page import PageBox
from wike.search import SearchPanel
from wike.toc import TocPanel


# Main window

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/gtk/window.ui')
class Window(Adw.ApplicationWindow):

  __gtype_name__ = 'Window'

  breakpoint_window_medium = Gtk.Template.Child()
  breakpoint_window_small = Gtk.Template.Child()
  breakpoint_content = Gtk.Template.Child()
  toast_overlay = Gtk.Template.Child()
  main_button = Gtk.Template.Child()
  search_button = Gtk.Template.Child()
  toc_button = Gtk.Template.Child()
  langlinks_button = Gtk.Template.Child()
  bookmarks_button = Gtk.Template.Child()
  history_button = Gtk.Template.Child()
  panel_button = Gtk.Template.Child()
  panel_split = Gtk.Template.Child()
  panel_stack = Gtk.Template.Child()
  main_button_mob = Gtk.Template.Child()
  close_panel_button_mob = Gtk.Template.Child()
  headerbar = Gtk.Template.Child()
  newtab_button = Gtk.Template.Child()
  tabs_button = Gtk.Template.Child()
  article_button = Gtk.Template.Child()
  view_button = Gtk.Template.Child()
  panel_button_mob = Gtk.Template.Child()
  article_button_mob = Gtk.Template.Child()
  view_button_mob = Gtk.Template.Child()
  tabbar = Gtk.Template.Child()
  tabview = Gtk.Template.Child()
  taboverview = Gtk.Template.Child()

  # Initialize window, set actions and connect signals

  def __init__(self, app, launch_uri):
    super().__init__(application=app)

    width = settings.get_int('window-width')
    height = settings.get_int('window-height')

    self.set_default_size(width, height)
    if settings.get_boolean('window-max'):
      self.maximize()

    self._print_settings = Gtk.PrintSettings()

    self.main_menu_popover = MainMenuPopover()
    self.main_button.set_popover(self.main_menu_popover)

    self.article_menu_popover = ArticleMenuPopover()
    self.article_button.set_popover(self.article_menu_popover)

    self.view_menu_popover = ViewMenuPopover(self)
    self.view_button.set_popover(self.view_menu_popover)

    self.search_panel = SearchPanel(self)
    search_stack_page = self.panel_stack.add_named(self.search_panel, 'search')

    self.toc_panel = TocPanel(self)
    toc_stack_page = self.panel_stack.add_named(self.toc_panel, 'toc')

    self.langlinks_panel = LanglinksPanel(self)
    langlinks_stack_page = self.panel_stack.add_named(self.langlinks_panel, 'langlinks')

    self.bookmarks_panel = BookmarksPanel(self)
    bookmarks_stack_page = self.panel_stack.add_named(self.bookmarks_panel, 'bookmarks')
    
    self.history_panel = HistoryPanel(self)
    history_stack_page = self.panel_stack.add_named(self.history_panel, 'history')

    self.page = PageBox(self, None)

    if launch_uri != '':
      tabpage = self.tabview.append(self.page)
      if launch_uri == 'notfound':
        self.page.wikiview.load_message(launch_uri)
      else:
        self.page.wikiview.load_wiki(launch_uri)
    else:
      on_start = settings.get_int('on-start-load')
      last_uri = settings.get_string('last-uri')
      if on_start != 3:
        tabpage = self.tabview.append(self.page)
        match on_start:
          case 0:
            self.page.wikiview.load_main()
          case 1:
            self.page.wikiview.load_random()
          case 2:
            if last_uri != '':
              self.page.wikiview.load_wiki(last_uri)
            else:
              self.page.wikiview.load_message('blank')
      else:
        tabs_data = settings.get_value('last-tabs').unpack()
        if len(tabs_data) > 0:
          for uri, title in tabs_data.items():
            if last_uri == uri:
              tabpage = self.tabview.append(self.page)
              self.tabview.set_selected_page(tabpage)
              self.page.wikiview.load_wiki(last_uri)
            else:
              self.new_lazy_page(uri, title, None)
          if not last_uri in tabs_data:
            tabpage = self.tabview.get_nth_page(0)
            self.tabview.set_selected_page(tabpage)
            self.page = tabpage.get_child()
            self.page.load_now()
        else:
          tabpage = self.tabview.append(self.page)
          self.page.wikiview.load_message('blank')

    settings.bind('panel-pinned', self.panel_button, 'active', Gio.SettingsBindFlags.DEFAULT)
    settings.bind('panel-page', self.panel_stack, 'visible-child-name', Gio.SettingsBindFlags.DEFAULT)

    self._set_actions(app)

    self.breakpoint_window_medium.connect('apply', self._breakpoint_medium_apply_cb)
    self.breakpoint_window_medium.connect('unapply', self._breakpoint_medium_unapply_cb)
    self.breakpoint_window_small.connect('apply', self._breakpoint_small_apply_cb)
    self.breakpoint_window_small.connect('unapply', self._breakpoint_small_unapply_cb)
    self.breakpoint_content.connect('apply', self._breakpoint_content_apply_cb)
    self.breakpoint_content.connect('unapply', self._breakpoint_content_unapply_cb)
    settings.connect('changed::hide-tabs', self._settings_hide_tabs_changed_cb)

    self.handler_selpage = self.tabview.connect('notify::selected-page', self._tabview_selected_page_cb)
    self.tabview.connect('close-page', self._tabview_close_page_cb)
    self.taboverview.connect('create-tab', self._taboverview_create_tab_cb)

    self.toc_button.connect('toggled', self._bar_selector_button_toggled_cb, 'toc')
    self.search_button.connect('toggled', self._bar_selector_button_toggled_cb, 'search')
    self.langlinks_button.connect('toggled', self._bar_selector_button_toggled_cb, 'langlinks')
    self.bookmarks_button.connect('toggled', self._bar_selector_button_toggled_cb, 'bookmarks')
    self.history_button.connect('toggled', self._bar_selector_button_toggled_cb, 'history')
    self.panel_split.connect('notify::show-sidebar', self._panel_split_show_cb)
    self.close_panel_button_mob.connect('clicked', self._close_panel_button_mob_cb)

    gesture = Gtk.GestureClick(button=0, propagation_phase=Gtk.PropagationPhase.CAPTURE)
    self.add_controller(gesture)
    gesture.connect('pressed', self._gesture_click_cb)

    self._panel_split_show_cb(self.panel_split, None)
    if settings.get_boolean('hide-tabs'):
      self._hide_tabs(True)

  # Set actions for window

  def _set_actions(self, app):
    actions = [ ('prev-page', self._prev_page_cb, ('<Alt>Left',)),
                ('next-page', self._next_page_cb, ('<Alt>Right',)),
                ('new-tab', self._new_tab_cb, ('<Ctrl>T',)),
                ('close-tab', self._close_tab_cb, ('<Ctrl>W',)),
                ('next-tab', self._next_tab_cb, ('<Ctrl>Tab',)),
                ('prev-tab', self._prev_tab_cb, ('<Shift><Ctrl>Tab',)),
                ('toggle-overview', self._toggle_overview_cb, ('F4', '<Alt>T',)),
                ('add-bookmark', self._add_bookmark_cb, ('<Ctrl>D',)),
                ('show-search', self._show_search_cb, ('F2', '<Ctrl>K',)),
                ('show-toc', self._show_toc_cb, ('<Ctrl>I',)),
                ('show-langlinks', self._show_langlinks_cb, ('<Ctrl>L',)),
                ('show-bookmarks', self._show_bookmarks_cb, ('<Ctrl>B',)),
                ('show-history', self._show_history_cb, ('<Ctrl>H',)),
                ('main-page', self._main_page_cb, ('<Alt>Home',)),
                ('random-article', self._random_article_cb, ('<Alt>R',)),
                ('open-link', self._open_link_cb, ('<Alt>L',)),
                ('reload-page', self._reload_page_cb, ('F5', '<Ctrl>R',)),
                ('search-text', self._search_text_cb, ('<Ctrl>F',)),
                ('print-page', self._print_page_cb, ('<Ctrl>P',)),
                ('open-browser', self._open_browser_cb, None),
                ('copy-link', self._copy_url_cb, ('<Ctrl>U',)) ]

    for action, callback, accel in actions:
      simple_action = Gio.SimpleAction.new(action, None)
      simple_action.connect('activate', callback)
      self.add_action(simple_action)
      if accel:
        app.set_accels_for_action('win.' + action, accel)

    pin_panel_action = Gio.SimpleAction.new_stateful('pin-panel', None, GLib.Variant.new_boolean(False))
    pin_panel_action.connect('change-state', self._pin_panel_cb)
    self.add_action(pin_panel_action)
    app.set_accels_for_action('win.pin-panel', ('F9',))

    if settings.get_boolean('panel-pinned'):
      pin_panel_action.change_state(GLib.Variant.new_boolean(True))

  # On breakpoint window medium apply

  def _breakpoint_medium_apply_cb(self, break_point):
    self.panel_split.set_collapsed(True)

    pin_panel_action = self.lookup_action('pin-panel')
    pin_panel_action.set_enabled(False)

  # On breakpoint window medium unapply

  def _breakpoint_medium_unapply_cb(self, break_point):
    pin_panel_action = self.lookup_action('pin-panel')
    pin_panel_action.set_enabled(True)

    if self.panel_button.get_active():
      self.panel_split.set_collapsed(False)

  # On breakpoint window small apply

  def _breakpoint_small_apply_cb(self, break_point):
    self.main_button.set_popover(None)
    self.main_button_mob.set_popover(self.main_menu_popover)

    pin_panel_action = self.lookup_action('pin-panel')
    pin_panel_action.set_enabled(False)

  # On breakpoint window small unapply

  def _breakpoint_small_unapply_cb(self, break_point):
    self.main_button_mob.set_popover(None)
    self.main_button.set_popover(self.main_menu_popover)

    pin_panel_action = self.lookup_action('pin-panel')
    pin_panel_action.set_enabled(True)

  # On breakpoint content apply

  def _breakpoint_content_apply_cb(self, break_point):
    self._hide_tabs(True)

    self.article_button.set_popover(None)
    self.article_button_mob.set_popover(self.article_menu_popover)
    self.view_button.set_popover(None)
    self.view_button_mob.set_popover(self.view_menu_popover)

  # On breakpoint content unapply

  def _breakpoint_content_unapply_cb(self, break_point):
    if not settings.get_boolean('hide-tabs'):
      self._hide_tabs(False)

    self.article_button_mob.set_popover(None)
    self.article_button.set_popover(self.article_menu_popover)
    self.view_button_mob.set_popover(None)
    self.view_button.set_popover(self.view_menu_popover)

  # Settings hide tabs changed event

  def _settings_hide_tabs_changed_cb(self, settings, key):
    if settings.get_boolean('hide-tabs'):
      self._hide_tabs(True)
    else:
      if self.main_button.get_visible():
        self._hide_tabs(False)

  # Hide or show tabbar and related buttons

  def _hide_tabs(self, hide):
    if hide:
      self.tabbar.set_visible(False)
      self.newtab_button.set_visible(False)
      self.tabs_button.set_visible(True)
    else:
      self.tabbar.set_visible(True)
      self.newtab_button.set_visible(True)
      self.tabs_button.set_visible(False)

  # On selector button toggled change panel view

  def _bar_selector_button_toggled_cb(self, button, name):
    if button.get_active():
      self.panel_stack.set_visible_child_name(name)
      if not self.panel_split.get_show_sidebar():
        self.panel_split.set_show_sidebar(True)
      if name=='search':
        self.search_panel.search_entry.grab_focus()

  # Panel show state changed

  def _panel_split_show_cb(self, panel_split, param):
    if panel_split.get_show_sidebar():
      panel_page = self.panel_stack.get_visible_child_name()
      match panel_page:
        case 'search':
          self.search_button.set_active(True)
        case 'toc':
          self.toc_button.set_active(True)
        case 'langlinks':
          self.langlinks_button.set_active(True)
        case 'bookmarks':
          self.bookmarks_button.set_active(True)
        case 'history':
          self.history_button.set_active(True)
    else:
      self.search_button.set_active(False)
      self.toc_button.set_active(False)
      self.langlinks_button.set_active(False)
      self.bookmarks_button.set_active(False)
      self.history_button.set_active(False)
      self.page.set_focus()

  # On close panel button clicked hide panel

  def _close_panel_button_mob_cb(self, button):
    self.panel_button_mob.set_active(False)

  # Select search in panel

  def _show_search_cb(self, action, parameter):
    self.search_button.set_active(True)

  # Select toc in panel

  def _show_toc_cb(self, action, parameter):
    self.toc_button.set_active(True)

  # Select langlinks in panel

  def _show_langlinks_cb(self, action, parameter):
    self.langlinks_button.set_active(True)

  # Select bookmarks in panel

  def _show_bookmarks_cb(self, action, parameter):
    self.bookmarks_button.set_active(True)

  # Select history in panel

  def _show_history_cb(self, action, parameter):
    self.history_button.set_active(True)

  # On pin panel action set collapsed state

  def _pin_panel_cb(self, action, parameter):
    action.set_state(parameter)
    if parameter:
      self.panel_split.set_collapsed(False)
    else:
      self.panel_split.set_collapsed(True)

  # Handle mouse clicks with buttons 8 and 9

  def _gesture_click_cb(self, gesture, n_press, x, y):
    button = gesture.get_current_button()
    prev_page_action = self.lookup_action('prev-page')
    next_page_action = self.lookup_action('next-page')

    match button:
      case 8:
        gesture.set_state(Gtk.EventSequenceState.CLAIMED)
        prev_page_action.activate()
      case 9:
        gesture.set_state(Gtk.EventSequenceState.CLAIMED)
        next_page_action.activate()

  # Create new tab with a page

  def new_page(self, uri, parent, select):
    page = PageBox(self, None)
    tabpage = self.tabview.add_page(page, parent)
    tabpage.set_live_thumbnail(True)

    match uri:
      case 'main':
        page.wikiview.load_main()
      case 'random':
        page.wikiview.load_random()
      case 'blank' | 'notfound':
        page.wikiview.load_message(uri)
      case _:
        page.wikiview.load_wiki(uri)

    if select:
      self.tabview.set_selected_page(tabpage)

    return tabpage

  # New empty tab with a title for lazy-loading

  def new_lazy_page(self, uri, title, parent):
    page = PageBox(self, [uri,title])
    tabpage = self.tabview.add_page(page, parent)
    tabpage.set_live_thumbnail(True)
    tabpage.set_title(title)

    return tabpage

  # New empty tab

  def _new_tab_cb(self, action, parameter):
    self.new_page('blank', None, True)

  # Close current tab

  def _close_tab_cb(self, action, parameter):
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

  # Open/close taboverview

  def _toggle_overview_cb(self, action, parameter):
    self.taboverview.set_open(not self.taboverview.get_open())

  # On tab selected event refresh headerbar and sidebar, and force loading

  def _tabview_selected_page_cb(self, tabview, value):
    tabpage = tabview.get_selected_page()
    if not tabpage:
      return

    self.page = tabpage.get_child()
    if self.page.lazy_load:
      self.page.load_now()
    else:
      self.refresh_nav_actions(self.page.wikiview)
      self.refresh_menu_actions(self.page.wikiview.is_local())
      self.set_title(self.page.wikiview.title)
      self.toc_panel.populate(self.page.wikiview.title, self.page.wikiview.sections)
      self.langlinks_panel.populate(self.page.wikiview.langlinks)
      self.bookmarks_panel.refresh_buttons()

  # On tab closed event destroy wikiview and confirm

  def _tabview_close_page_cb(self, tabview, tabpage):
    page = tabpage.get_child()
    wikiview = page.wikiview

    if self.tabview.get_n_pages() > 1:
      page.view_stack.remove(wikiview)
      wikiview.run_dispose()
      tabview.close_page_finish(tabpage, True)
    else:
      if self.taboverview.get_open():
        self.taboverview.set_open(False)
      wikiview.load_message('blank')
      tabview.close_page_finish(tabpage, False)

    return True

  # Create new tab on taboverview button clicked

  def _taboverview_create_tab_cb(self, taboverview):
    tabpage = self.new_page('blank', None, True)
    return tabpage

  # Go to previous page

  def _prev_page_cb(self, action, parameter):
    if self.page.wikiview.can_go_back():
      self.page.wikiview.go_back()

  # Go to next page

  def _next_page_cb(self, action, parameter):
    if self.page.wikiview.can_go_forward():
      self.page.wikiview.go_forward()

  # Add page to bookmarks

  def _add_bookmark_cb(self, action, parameter):
    if not self.page.wikiview.is_local():
      uri = self.page.wikiview.get_base_uri()
      title = self.page.wikiview.title
      lang = self.page.wikiview.get_lang()
      if self.bookmarks_panel.add_bookmark(uri, title, lang):
        message = _('Bookmark added: ') + title
        self.send_notification(message)

  # Show Wikipedia main page

  def _main_page_cb(self, action, parameter):
    self.page.wikiview.load_main()

  # Show Wikipedia random article

  def _random_article_cb(self, action, parameter):
    self.page.wikiview.load_random()

  # Show open link dialog

  def _open_link_cb(self, action, parameter):
    builder = Gtk.Builder()
    builder.add_from_resource('/com/github/hugolabe/Wike/gtk/dialogs.ui')
    open_link_dialog = builder.get_object('open_link_dialog')
    link_entry = builder.get_object('link_entry')

    link_entry.connect('apply', self._link_entry_apply_cb, open_link_dialog)
    link_entry.connect('changed', self._link_entry_changed_cb, open_link_dialog)

    open_link_dialog.present(self)

  # On entry apply load link if valid

  def _link_entry_apply_cb(self, link_entry, open_link_dialog):
    text = link_entry.get_text()
    link = self.page.wikiview.is_wiki_uri(text)

    if link != '':
      open_link_dialog.close()
      self.page.wikiview.load_wiki(link)
    else:
      link_entry.set_show_apply_button(False)
      link_entry.set_show_apply_button(True)
      link_entry.add_css_class('error')


  # On entry changes check input

  def _link_entry_changed_cb(self, link_entry, open_link_dialog):
    text = link_entry.get_text()

    if len(text) == 0:
      link_entry.set_show_apply_button(False)
      link_entry.set_show_apply_button(True)

    if link_entry.has_css_class('error'):
      link_entry.remove_css_class('error')

  # Reload article view

  def _reload_page_cb(self, action, parameter):
    self.page.wikiview.reload()

  # Show text search bar

  def _search_text_cb(self, action, parameter):
    if not self.page.search_bar.get_search_mode():
      self.page.search_bar.set_search_mode(True)
    else:
      self.page.search_entry.grab_focus()

  # Print current page

  def _print_page_cb(self, action, parameter):
    print_operation = WebKit.PrintOperation.new(self.page.wikiview)
    self._print_set_settings(print_operation)

    result = print_operation.run_dialog(self)
    if result == WebKit.PrintOperationResponse.PRINT:
      handler_finished = print_operation.connect('finished', self._print_operation_finished)
      print_operation.connect('failed', self._print_operation_failed, handler_finished)

  # Set print operation settings

  def _print_set_settings(self, print_operation):
    output_uri = self._print_settings.get('output-uri')
    if output_uri:
      output_dir = os.path.dirname(output_uri)
    else:
      output_dir = 'file://' + os.path.expanduser('~')

    output_name = self.page.wikiview.title + '.pdf'
    output_name = output_name.replace('/', '-')

    output_uri = os.path.join(output_dir, output_name)
    self._print_settings.set('output-uri', output_uri)
    print_operation.set_print_settings(self._print_settings)

  # Show a notification when print operation is finished

  def _print_operation_finished(self, print_operation):
    self._print_settings = print_operation.get_print_settings()
    self.send_notification(_('Print operation completed'))

  # Show a notification when print operation failed

  def _print_operation_failed(self, print_operation, error, handler_finished):
    print_operation.disconnect(handler_finished)
    self.send_notification(_('Print operation failed'))

  # Open article in external browser

  def _open_browser_cb(self, action, parameter):
    uri = self.page.wikiview.get_base_uri()

    uri_launcher = Gtk.UriLauncher.new(uri)
    uri_launcher.launch(self, None, None, None)

  # Copy article URL to clipboard

  def _copy_url_cb(self, action, parameter):
    uri = self.page.wikiview.get_base_uri()
    clipboard = Gdk.Display.get_default().get_clipboard()
    clipboard.set(uri)

    self.send_notification(_('Link copied to clipboard'))

  # Refresh navigation actions state

  def refresh_nav_actions(self, wikiview):
    prev_page_action = self.lookup_action('prev-page')
    next_page_action = self.lookup_action('next-page')

    if wikiview.can_go_back():
      prev_page_action.set_enabled(True)
    else:
      prev_page_action.set_enabled(False)
    if wikiview.can_go_forward():
      next_page_action.set_enabled(True)
    else:
      next_page_action.set_enabled(False)

  # Refresh page actions state

  def refresh_menu_actions(self, is_local):
    search_text_action = self.lookup_action('search-text')
    print_page_action = self.lookup_action('print-page')
    open_browser_action = self.lookup_action('open-browser')
    copy_url_action = self.lookup_action('copy-link')

    if is_local:
      search_text_action.set_enabled(False)
      print_page_action.set_enabled(False)
      open_browser_action.set_enabled(False)
      copy_url_action.set_enabled(False)
    else:
      search_text_action.set_enabled(True)
      print_page_action.set_enabled(True)
      open_browser_action.set_enabled(True)
      copy_url_action.set_enabled(True)

  # Show notification with provided message

  def send_notification(self, message):
    toast = Adw.Toast.new(message)
    toast.set_timeout(3)
    self.toast_overlay.add_toast(toast)
