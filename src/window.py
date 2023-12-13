# This file is part of Wike (com.github.hugolabe.Wike)
# SPDX-FileCopyrightText: 2021-23 Hugo Olabera <hugolabe@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later


import os

from gi.repository import GLib, GObject, Gio, Gdk, Gtk, Adw, WebKit

from wike.data import settings
from wike.bookmarks import BookmarksBox
from wike.header import HeaderBar, ActionBar
from wike.history import HistoryPanel
from wike.langlinks import LanglinksPanel
from wike.page import PageBox
from wike.toc import TocPanel


# Main window with a flap a headerbar and an actionbar

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/ui/window.ui')
class Window(Adw.ApplicationWindow):

  __gtype_name__ = 'Window'

  window_box = Gtk.Template.Child()
  toast_overlay = Gtk.Template.Child()
  flap = Gtk.Template.Child()
  flap_stack = Gtk.Template.Child()
  flap_pin_revealer = Gtk.Template.Child()
  flap_pin_button = Gtk.Template.Child()
  flap_toc_button = Gtk.Template.Child()
  flap_langlinks_button = Gtk.Template.Child()
  flap_bookmarks_button = Gtk.Template.Child()
  flap_history_button = Gtk.Template.Child()
  tabbar = Gtk.Template.Child()
  tabview = Gtk.Template.Child()
  taboverview = Gtk.Template.Child()
  
  mobile_layout = False
  
  # Initialize window, set actions and connect signals

  def __init__(self, app, launch_uri):
    super().__init__(application=app)

    width = settings.get_int('window-width')
    height = settings.get_int('window-height')

    if width < 720:
      self.mobile_layout = True

    self.set_default_size(width, height)
    if settings.get_boolean('window-max'):
      self.maximize()

    self._print_settings = Gtk.PrintSettings()

    self.actionbar = ActionBar()
    self.window_box.append(self.actionbar)
    
    self.headerbar = HeaderBar(self)
    self.window_box.prepend(self.headerbar)

    self.toc_panel = TocPanel(self)
    toc_stack_page = self.flap_stack.add_named(self.toc_panel, 'toc')
    
    self.langlinks_panel = LanglinksPanel(self)
    langlinks_stack_page = self.flap_stack.add_named(self.langlinks_panel, 'langlinks')
    
    self.bookmarks_box = BookmarksBox(self)
    bookmarks_stack_page = self.flap_stack.add_named(self.bookmarks_box, 'bookmarks')
    
    self.history_panel = HistoryPanel(self)
    history_stack_page = self.flap_stack.add_named(self.history_panel, 'history')

    flap_page = settings.get_string('flap-page')
    match flap_page:
      case 'langlinks':
        self.flap_langlinks_button.set_active(True)
      case 'bookmarks':
        self.flap_bookmarks_button.set_active(True)
      case 'history':
        self.flap_history_button.set_active(True)
      case _:
        self.flap_toc_button.set_active(True)

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

    settings.bind('flap-pinned', self.flap_pin_button, 'active', Gio.SettingsBindFlags.DEFAULT)
    settings.bind('flap-page', self.flap_stack, 'visible-child-name', Gio.SettingsBindFlags.DEFAULT)

    self._set_actions(app)
    self._set_layout()

    self.handler_selpage = self.tabview.connect('notify::selected-page', self._tabview_selected_page_cb)
    self.tabview.connect('close-page', self._tabview_close_page_cb)
    self.taboverview.connect('create-tab', self._taboverview_create_tab_cb)

    self.flap_toc_button.connect('toggled', self._flap_switcher_button_cb, 'toc')
    self.flap_langlinks_button.connect('toggled', self._flap_switcher_button_cb, 'langlinks')
    self.flap_bookmarks_button.connect('toggled', self._flap_switcher_button_cb, 'bookmarks')
    self.flap_history_button.connect('toggled', self._flap_switcher_button_cb, 'history')

    gesture = Gtk.GestureClick(button=0, propagation_phase=Gtk.PropagationPhase.CAPTURE)
    self.add_controller(gesture)
    gesture.connect('pressed', self._gesture_click_cb)

  # Set actions for window
  
  def _set_actions(self, app):
    actions = [ ('prev-page', self._prev_page_cb, ('<Alt>Left',)),
                ('next-page', self._next_page_cb, ('<Alt>Right',)),
                ('new-tab', self._new_tab_cb, ('<Ctrl>T',)),
                ('close-tab', self._close_tab_cb, ('<Ctrl>W',)),
                ('next-tab', self._next_tab_cb, ('<Ctrl>Tab',)),
                ('prev-tab', self._prev_tab_cb, ('<Shift><Ctrl>Tab',)),
                ('toggle-overview', self._toggle_overview_cb, ('F4', '<Alt>T',)),
                ('go-search', self._go_search_cb, ('F2', '<Ctrl>K',)),
                ('add-bookmark', self._add_bookmark_cb, ('<Ctrl>D',)),
                ('show-toc', self._show_toc_cb, ('<Ctrl>I',)),
                ('show-langlinks', self._show_langlinks_cb, ('<Ctrl>L',)),
                ('show-bookmarks', self._show_bookmarks_cb, ('<Ctrl>B',)),
                ('show-history', self._show_history_cb, ('<Ctrl>H',)),
                ('main-page', self._main_page_cb, ('<Alt>Home',)),
                ('random-article', self._random_article_cb, ('<Alt>R',)),
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

    toggle_sidebar_action = Gio.SimpleAction.new_stateful('toggle-sidebar', None, GLib.Variant.new_boolean(False))
    toggle_sidebar_action.connect('change-state', self._toggle_sidebar_cb)
    self.add_action(toggle_sidebar_action)
    app.set_accels_for_action('win.toggle-sidebar', ('F9',))

    pin_sidebar_action = Gio.SimpleAction.new_stateful('pin-sidebar', None, GLib.Variant.new_boolean(False))
    pin_sidebar_action.connect('change-state', self._pin_sidebar_cb)
    pin_sidebar_action.bind_property('enabled', self.flap_pin_revealer, 'reveal-child',  GObject.BindingFlags.SYNC_CREATE)
    self.add_action(pin_sidebar_action)
    
    self.flap.connect('notify::reveal-flap', self._flap_reveal_cb)
    
    if settings.get_boolean('flap-pinned'):
      pin_sidebar_action.change_state(GLib.Variant.new_boolean(True))

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

  # If window size changed set layout

  def do_size_allocate(self, width, height, baseline):
    if width < 720:
      if self.mobile_layout == False:
        self.mobile_layout = True
        self._set_layout()
    else:
      if self.mobile_layout == True:
        self.mobile_layout = False
        self._set_layout()

    Adw.ApplicationWindow.do_size_allocate(self, width, height, baseline)

  # Set layout for mobile or desktop
  
  def _set_layout (self):
    pin_sidebar_action = self.lookup_action('pin-sidebar')

    self.headerbar.set_mobile(self.mobile_layout)
    pin_sidebar_action.set_enabled(not self.mobile_layout)

    self._update_sidebar_policy(pin_sidebar_action)

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
      self.toc_panel.populate(self.page.wikiview.title, self.page.wikiview.sections)
      self.langlinks_panel.populate(self.page.wikiview.langlinks)
      self.bookmarks_box.refresh_buttons()

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

  # On flap switcher button toggled change panel view

  def _flap_switcher_button_cb(self, button, name):
    if button.get_active():
      self.flap_stack.set_visible_child_name(name)

  # Go to previous page

  def _prev_page_cb(self, action, parameter):
    if self.page.wikiview.can_go_back():
      self.page.wikiview.go_back()

  # Go to next page

  def _next_page_cb(self, action, parameter):
    if self.page.wikiview.can_go_forward():
      self.page.wikiview.go_forward()

  # Go to search entry

  def _go_search_cb(self, action, parameter):
    self.headerbar.search_box.search_entry.grab_focus()

  # Add page to bookmarks

  def _add_bookmark_cb(self, action, parameter):
    if not self.page.wikiview.is_local():
      uri = self.page.wikiview.get_base_uri()
      title = self.page.wikiview.title
      lang = self.page.wikiview.get_lang()
      if self.bookmarks_box.add_bookmark(uri, title, lang):
        message = _('Bookmark added: ') + title
        self.send_notification(message)

  # Show/hide sidebar (flap)

  def _toggle_sidebar_cb(self, action, parameter):
    action.set_state(parameter)
    
    if parameter:
      self.flap.set_reveal_flap(True)
    else:
      self.flap.set_reveal_flap(False)
  
  # On pin sidebar action set state and update sidebar
  
  def _pin_sidebar_cb(self, action, parameter):
    action.set_state(parameter)
    self._update_sidebar_policy(action)

  # Update sidebar policy

  def _update_sidebar_policy(self, action):
    prefer_pinned = action.get_state().get_boolean()
    if prefer_pinned and not self.mobile_layout:
      self.flap.set_fold_policy(Adw.FlapFoldPolicy.NEVER)
    else:
      self.flap.set_fold_policy(Adw.FlapFoldPolicy.ALWAYS)

  # On flap reveal changed set action state
  
  def _flap_reveal_cb(self, flap, parameter):
    reveal_state = GLib.Variant.new_boolean(flap.get_reveal_flap())
    toggle_sidebar_action = self.lookup_action('toggle-sidebar')
    
    if toggle_sidebar_action.get_state() != reveal_state:
      toggle_sidebar_action.set_state(reveal_state)
    
  # Show toc in sidebar

  def _show_toc_cb(self, action, parameter):
    self.flap_toc_button.set_active(True)
    if self.flap.get_fold_policy() == Adw.FlapFoldPolicy.ALWAYS:
      self.flap.set_reveal_flap(True)

  # Show langlinks in sidebar

  def _show_langlinks_cb(self, action, parameter):
    self.flap_langlinks_button.set_active(True)
    if self.flap.get_fold_policy() == Adw.FlapFoldPolicy.ALWAYS:
      self.flap.set_reveal_flap(True)

  # Show bookmarks in sidebar

  def _show_bookmarks_cb(self, action, parameter):
    self.flap_bookmarks_button.set_active(True)
    if self.flap.get_fold_policy() == Adw.FlapFoldPolicy.ALWAYS:
      self.flap.set_reveal_flap(True)

  # Show history in sidebar

  def _show_history_cb(self, action, parameter):
    self.flap_history_button.set_active(True)
    if self.flap.get_fold_policy() == Adw.FlapFoldPolicy.ALWAYS:
      self.flap.set_reveal_flap(True)

  # Show Wikipedia main page

  def _main_page_cb(self, action, parameter):
    self.page.wikiview.load_main()

  # Show Wikipedia random article

  def _random_article_cb(self, action, parameter):
    self.page.wikiview.load_random()

  # Reload article view

  def _reload_page_cb(self, action, parameter):
    self.page.wikiview.reload()

  # Show text search bar

  def _search_text_cb(self, action, parameter):
    if not self.page.search_bar.get_search_mode():
      self.page.search_bar.set_search_mode(True)
    else:
      self.page.textsearch_entry.grab_focus()

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
      output_dir = 'file://' + GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD)

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
    Gtk.show_uri(None, uri, Gdk.CURRENT_TIME)

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
