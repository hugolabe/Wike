# This file is part of Wike (com.github.hugolabe.Wike)
# SPDX-FileCopyrightText: 2021-24 Hugo Olabera <hugolabe@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later


import urllib.parse

from gi.repository import GLib, GObject, Gio, Gdk, Gtk, Adw, WebKit

from wike import wikipedia
from wike.data import settings, languages, bookmarks


# Initialize network session with cookie manager

network_session = WebKit.NetworkSession.get_default()
cookies_file_path = GLib.get_user_data_dir() + '/cookies'
cookie_manager = WebKit.NetworkSession.get_cookie_manager(network_session)
cookie_manager.set_accept_policy(WebKit.CookieAcceptPolicy.ALWAYS)
cookie_manager.set_persistent_storage(cookies_file_path, WebKit.CookiePersistentStorage.TEXT)


# Settings and user content with custom css for wikiviews

class ViewSettings:

  web_settings = WebKit.Settings()
  user_content = WebKit.UserContentManager()
  _style_manager = Adw.StyleManager.get_default()

  # Load custom css and connect view settings signals

  def __init__(self):
    self.web_settings.set_default_font_size(settings.get_int('font-size'))
    self.web_settings.set_enable_back_forward_navigation_gestures(True)

    gfile = Gio.File.new_for_uri('resource:///com/github/hugolabe/Wike/styles/view.min.css')
    try:
      gfile_contents = gfile.load_contents(None)
    except:
      print('Can\'t load view css file from resources')
      self._css_view = ''
    else:
      self._css_view = gfile_contents[1].decode('utf-8')

    gfile = Gio.File.new_for_uri('resource:///com/github/hugolabe/Wike/styles/dark.min.css')
    try:
      gfile_contents = gfile.load_contents(None)
    except:
      print('Can\'t load dark css file from resources')
      self._css_dark = ''
    else:
      self._css_dark = gfile_contents[1].decode('utf-8')

    gfile = Gio.File.new_for_uri('resource:///com/github/hugolabe/Wike/styles/sepia.min.css')
    try:
      gfile_contents = gfile.load_contents(None)
    except:
      print('Can\'t load sepia css file from resources')
      self._css_sepia = ''
    else:
      self._css_sepia = gfile_contents[1].decode('utf-8')

    self.set_style()

    settings.connect('changed::font-family', self._settings_font_family_changed_cb)
    settings.connect('changed::font-size', self._settings_font_size_changed_cb)
    settings.connect('changed::preview-popups', self._settings_preview_popups_changed_cb)
    settings.connect('changed::theme', self._settings_theme_changed_cb)
    self._style_manager.connect('notify::dark', self._system_theme_changed_cb)

  # Settings font family changed event

  def _settings_font_family_changed_cb(self, settings, key):
    self.set_style()

  # Settings font-size changed event

  def _settings_font_size_changed_cb(self, settings, key):
    self.web_settings.set_default_font_size(settings.get_int('font-size'))

  # Settings preview popups changed event

  def _settings_preview_popups_changed_cb(self, settings, key):
    self.set_style()

  # Settings theme changed event

  def _settings_theme_changed_cb(self, settings, key):
    self.set_style()

  # System theme changed event

  def _system_theme_changed_cb(self, style_manager, dark):
    self.set_style()

  # Inject stylesheets for customize article view

  def set_style(self):
    data_manager = network_session.get_website_data_manager()
    data_manager.clear(WebKit.WebsiteDataTypes.MEMORY_CACHE , 0, None, None, None)
    self.user_content.remove_all_style_sheets()

    style_view = WebKit.UserStyleSheet(self._css_view, WebKit.UserContentInjectedFrames.ALL_FRAMES, WebKit.UserStyleLevel.USER, None, None)
    self.user_content.add_style_sheet(style_view)

    css_font = 'body,h1,h2{font-family:"' + settings.get_string('font-family') + '"!important}'
    style_font = WebKit.UserStyleSheet(css_font, WebKit.UserContentInjectedFrames.ALL_FRAMES, WebKit.UserStyleLevel.USER, None, None)
    self.user_content.add_style_sheet(style_font)

    theme = settings.get_int('theme')
    match theme:
      case 1:
        style_dark = WebKit.UserStyleSheet(self._css_dark, WebKit.UserContentInjectedFrames.ALL_FRAMES, WebKit.UserStyleLevel.USER, None, None)
        self.user_content.add_style_sheet(style_dark)
      case 2:
        style_sepia = WebKit.UserStyleSheet(self._css_sepia, WebKit.UserContentInjectedFrames.ALL_FRAMES, WebKit.UserStyleLevel.USER, None, None)
        self.user_content.add_style_sheet(style_sepia)
      case 3:
        if self._style_manager.get_dark():
          style_dark = WebKit.UserStyleSheet(self._css_dark, WebKit.UserContentInjectedFrames.ALL_FRAMES, WebKit.UserStyleLevel.USER, None, None)
          self.user_content.add_style_sheet(style_dark)

    if not settings.get_boolean('preview-popups'):
      css_previews = '.mwe-popups{display:none!important}'
      style_previews = WebKit.UserStyleSheet(css_previews, WebKit.UserContentInjectedFrames.ALL_FRAMES, WebKit.UserStyleLevel.USER, None, None)
      self.user_content.add_style_sheet(style_previews)


# Create view_settings object

view_settings = ViewSettings()


# Webview for Wikipedia views

class WikiView(WebKit.WebView):

  __gsignals__ = { 'new-page': (GObject.SIGNAL_RUN_FIRST, None, (str,)),
                   'add-bookmark': (GObject.SIGNAL_RUN_FIRST, None, (str, str, str,)) }

  title = 'Wike'
  sections = None
  langlinks = None

  fail_uri = None

  # Initialize view with user content and web settings

  def __init__(self):
    super().__init__(settings=view_settings.web_settings, user_content_manager=view_settings.user_content)

    theme = settings.get_int('theme')
    match theme:
      case 1:
        self.set_background_color(Gdk.RGBA(0.141, 0.141, 0.141, 1))
      case 2:
        self.set_background_color(Gdk.RGBA(0.976, 0.953, 0.914, 1))
      case _:
        self.set_background_color(Gdk.RGBA(1, 1, 1, 1))

    self.set_zoom_level(settings.get_int('zoom-level') / 100)

    settings.connect('changed::zoom-level', self._zoom_level_changed_cb)

  # Settings zoom level changed event

  def _zoom_level_changed_cb(self, settings, key):
    self.set_zoom_level(settings.get_int('zoom-level') / 100)

  # Load Wikipedia article by URI

  def load_wiki(self, uri):
    self.stop_loading()
    if uri.find('.m.') == -1:
      uri = uri.replace('.wikipedia.org', '.m.wikipedia.org')
    self.load_uri(uri)

  # Go to section in page

  def load_section(self, anchor):
    section = urllib.parse.quote(anchor)
    uri = self.get_uri()
    uri_elements = urllib.parse.urlparse(uri)
    if uri_elements[5] != section:
      section_uri_elements = (uri_elements[0], uri_elements[1], uri_elements[2], uri_elements[3], uri_elements[4], section)
      section_uri = urllib.parse.urlunparse(section_uri_elements)
      self.load_uri(section_uri)

  # Load Wikipedia main page

  def load_main(self):
    uri = 'https://' + settings.get_string('search-language') + '.m.wikipedia.org'
    self.load_wiki(uri)

  # Load Wikipedia random article

  def load_random(self):
    try:
      uri = wikipedia.get_random(settings.get_string('search-language'))
      self.load_wiki(uri)
    except:
      self.load_message('error')

  # Load void html for status page

  def load_message(self, message_type):
    uri = 'about:' + message_type
    self.load_html('', uri)

  # Get base uri for current article

  def get_base_uri(self):
    uri = self.get_uri().replace('.m.', '.')
    uri_elements = urllib.parse.urlparse(uri)
    if uri_elements[5]:
      base_uri_elements = (uri_elements[0], uri_elements[1], uri_elements[2], '', '', '')
      base_uri = urllib.parse.urlunparse(base_uri_elements)
      return base_uri
    else:
      return uri

  # Get language for current article

  def get_lang(self):
    uri = self.get_uri()
    uri_elements = urllib.parse.urlparse(uri)
    uri_scheme = uri_elements[0]
    uri_netloc = uri_elements[1]

    if uri_scheme == 'about':
      return None
    else:
      lang = uri_netloc.split('.', 1)[0]
      return lang

  # Set toc, langlinks and title for current article

  def set_props(self):
    uri = self.get_uri()
    uri_elements = urllib.parse.urlparse(uri)
    uri_scheme = uri_elements[0]
    uri_netloc = uri_elements[1]
    uri_path = uri_elements[2]

    props = None
    self.title = 'Wike'
    self.sections = None
    self.langlinks = None

    if uri_scheme == 'about':
      if uri_path == 'notfound':
        self.title = _('Article not found')
      elif uri_path == 'error':
        self.title = _('Can\'t access Wikipedia')
      return
    else:
      page = uri_path.replace('/wiki/', '', 1)
      lang = uri_netloc.split('.', 1)[0]
      try:
        props = wikipedia.get_properties(page, lang)
      except:
        props = None

    if props:
      self.title = props['title']
      self.sections = props['sections']
      self.langlinks = props['langlinks']
    else:
      title_raw = page.replace('_', ' ')
      self.title = urllib.parse.unquote(title_raw)

  # Check if current page is local (status page)

  def is_local(self):
    uri = self.get_uri()
    uri_elements = urllib.parse.urlparse(uri)
    uri_scheme = uri_elements[0]

    if uri_scheme == 'about':
      return True
    else:
      return False

  # Check if uri is a valid Wikipedia URL

  def _is_wiki_uri(self, uri):
    uri_elements = urllib.parse.urlparse(uri)
    uri_scheme = uri_elements[0]
    uri_netloc = uri_elements[1]
    uri_path = uri_elements[2]

    if uri_netloc.endswith('.wikipedia.org') and (uri_path.startswith('/wiki/') or uri_path == '/'):
      base_uri_elements = (uri_scheme, uri_netloc.replace('.m.', '.'), uri_path, '', '', '')
      base_uri = urllib.parse.urlunparse(base_uri_elements)
      return base_uri
    else:
      return ''

  # Webview load error event

  def do_load_failed(self, event, uri, error):
    self.fail_uri = uri
    self.load_message('error')
    return True

  # Webview decision policy event

  def do_decide_policy(self, decision, decision_type):
    if decision_type == WebKit.PolicyDecisionType.NAVIGATION_ACTION or decision_type == WebKit.PolicyDecisionType.NEW_WINDOW_ACTION:
      nav_action = decision.get_navigation_action()
      nav_type = nav_action.get_navigation_type()
      mouse_button = nav_action.get_mouse_button()
      uri = nav_action.get_request().get_uri()
      uri_elements = urllib.parse.urlparse(uri)
      uri_scheme = uri_elements[0]
      uri_netloc = uri_elements[1]
      uri_path = uri_elements[2]
      uri_fragment = uri_elements[5]
      match nav_type:
        case WebKit.NavigationType.LINK_CLICKED:
          if uri_netloc.endswith('.wikipedia.org') and (uri_path.startswith('/wiki/') or uri_path == '/'):
            base_uri_elements = (uri_elements[0], uri_elements[1].replace('.m.', '.'), uri_elements[2], '', '', '')
            base_uri = urllib.parse.urlunparse(base_uri_elements)
            if mouse_button == 2:
              decision.ignore()
              self.emit('new-page', base_uri)
            else:
              if base_uri != self.get_base_uri():
                decision.ignore()
                self.load_wiki(uri)
          else:
            decision.ignore()
            Gtk.show_uri(None, uri, Gdk.CURRENT_TIME)
        case WebKit.NavigationType.RELOAD | WebKit.NavigationType.BACK_FORWARD:
          if uri_scheme == 'about':
            decision.ignore()
        case WebKit.NavigationType.OTHER:
          if uri_netloc.startswith('upload.'):
            decision.ignore()
    return True

  # Manage webview context menu

  def do_context_menu(self, menu, hit_test):
    if hit_test.context_is_editable() or hit_test.context_is_media() or hit_test.context_is_scrollbar():
      return True

    action_tab = Gio.SimpleAction.new('new-tab', GLib.VariantType('s'))
    action_tab.connect('activate', self._new_tab_cb)
    action_browser = Gio.SimpleAction.new('open-browser', GLib.VariantType('s'))
    action_browser.connect('activate', self._open_browser_cb)
    action_bookmark = Gio.SimpleAction.new('add-bookmark', GLib.VariantType('s'))
    action_bookmark.connect('activate', self._add_bookmark_cb)
    action_clipboard = Gio.SimpleAction.new('copy-link', GLib.VariantType('s'))
    action_clipboard.connect('activate', self._copy_link_cb)

    if hit_test.get_context() == WebKit.HitTestResultContext.DOCUMENT:
      base_uri = self.get_base_uri()
      uri = self._is_wiki_uri(base_uri)
      if uri == '':
        action_bookmark.set_enabled(False)

      item = WebKit.ContextMenuItem.new_separator()
      menu.append(item)
      item = WebKit.ContextMenuItem.new_from_gaction(action_bookmark, _('Add Bookmark'), GLib.Variant.new_string(uri))
      menu.append(item)

    if hit_test.context_is_link() and not hit_test.context_is_image():
      link = hit_test.get_link_uri()
      uri = self._is_wiki_uri(link)
      if uri == '':
        action_bookmark.set_enabled(False)
        action_tab.set_enabled(False)

      if uri != '':
        link = uri
      item = WebKit.ContextMenuItem.new_from_gaction(action_tab, _('Open Link in New Tab'), GLib.Variant.new_string(uri))
      menu.append(item)
      item = WebKit.ContextMenuItem.new_from_gaction(action_browser, _('Open Link in Browser'), GLib.Variant.new_string(link))
      menu.append(item)
      item = WebKit.ContextMenuItem.new_separator()
      menu.append(item)
      item = WebKit.ContextMenuItem.new_from_gaction(action_bookmark, _('Add Link to Bookmarks'), GLib.Variant.new_string(uri))
      menu.append(item)
      item = WebKit.ContextMenuItem.new_from_gaction(action_clipboard, _('Copy Link to Clipboard'), GLib.Variant.new_string(link))
      menu.append(item)

    allowed_actions = (WebKit.ContextMenuAction.NO_ACTION,
                       WebKit.ContextMenuAction.CUSTOM,
                       WebKit.ContextMenuAction.GO_BACK,
                       WebKit.ContextMenuAction.GO_FORWARD,
                       WebKit.ContextMenuAction.RELOAD,
                       WebKit.ContextMenuAction.COPY,
                       WebKit.ContextMenuAction.COPY_IMAGE_TO_CLIPBOARD,
                       WebKit.ContextMenuAction.COPY_IMAGE_URL_TO_CLIPBOARD)

    items = menu.get_items()
    for item in items:
      if not item.get_stock_action() in allowed_actions:
        menu.remove(item)

    return False

  # On context menu activated open link in new tab

  def _new_tab_cb(self, action, parameter):
    uri = parameter.get_string()
    self.emit('new-page', uri)

  # On context menu activated open link in browser

  def _open_browser_cb(self, action, parameter):
    uri = parameter.get_string()
    Gtk.show_uri(None, uri, Gdk.CURRENT_TIME)

  # On context menu activated add bookmark

  def _add_bookmark_cb(self, action, parameter):
    uri = parameter.get_string()
    uri_elements = urllib.parse.urlparse(uri)
    uri_netloc = uri_elements[1]
    uri_path = uri_elements[2]

    page = uri_path.replace('/wiki/', '', 1)
    title_raw = page.replace('_', ' ')
    title = urllib.parse.unquote(title_raw)
    lang = uri_netloc.split('.', 1)[0]

    self.emit('add-bookmark', uri, title, lang)

  # On context menu activated copy link to clipboard

  def _copy_link_cb(self, action, parameter):
    uri = parameter.get_string()
    clipboard = Gdk.Display.get_default().get_clipboard()
    clipboard.set(uri)
