# view.py
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


import urllib.parse

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
from gi.repository import Gio, GLib, GObject, Gdk, Gtk, Handy, WebKit2

from wike import wikipedia
from wike.data import settings, languages, historic, bookmarks


# Initialize webcontext with cookie manager

web_context = WebKit2.WebContext.get_default()
web_context.set_cache_model(WebKit2.CacheModel.WEB_BROWSER)
cookies_file_path = GLib.get_user_data_dir() + '/cookies'
cookie_manager = WebKit2.WebContext.get_cookie_manager(web_context)
cookie_manager.set_accept_policy(WebKit2.CookieAcceptPolicy.ALWAYS)
cookie_manager.set_persistent_storage(cookies_file_path, WebKit2.CookiePersistentStorage.TEXT)


# Settings class for Wikipedia views
# Create settings and user content with custom css for wikiviews

class ViewSettings:

  web_settings = WebKit2.Settings()
  user_content = WebKit2.UserContentManager()
  style_manager = Handy.StyleManager.get_default()

  # Load custom css and connect view settings signals

  def __init__(self):
    self.web_settings.set_default_font_size(settings.get_int('font-size'))

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

    settings.connect('changed::font-size', self._settings_font_size_changed_cb)
    settings.connect('changed::custom-font', self._settings_custom_font_changed_cb)
    settings.connect('changed::font-family', self._settings_custom_font_changed_cb)
    settings.connect('changed::preview-popups', self._settings_preview_popups_changed_cb)
    settings.connect('changed::theme', self._settings_theme_changed_cb)
    self.style_manager.connect('notify::dark', self._system_theme_changed_cb)

  # Settings font-size changed event

  def _settings_font_size_changed_cb(self, settings, key):
    self.web_settings.set_default_font_size(settings.get_int('font-size'))

  # Settings custom font changed event

  def _settings_custom_font_changed_cb(self, settings, key):
    self.set_style()

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
    data_manager = web_context.get_website_data_manager()
    data_manager.clear(WebKit2.WebsiteDataTypes.MEMORY_CACHE , 0, None, None, None)
    self.user_content.remove_all_style_sheets()

    style_view = WebKit2.UserStyleSheet(self._css_view, WebKit2.UserContentInjectedFrames.ALL_FRAMES, WebKit2.UserStyleLevel.USER, None, None)
    self.user_content.add_style_sheet(style_view)

    theme = settings.get_int('theme')
    if theme == 1:
      style_dark = WebKit2.UserStyleSheet(self._css_dark, WebKit2.UserContentInjectedFrames.ALL_FRAMES, WebKit2.UserStyleLevel.USER, None, None)
      self.user_content.add_style_sheet(style_dark)
    elif theme == 2:
      style_sepia = WebKit2.UserStyleSheet(self._css_sepia, WebKit2.UserContentInjectedFrames.ALL_FRAMES, WebKit2.UserStyleLevel.USER, None, None)
      self.user_content.add_style_sheet(style_sepia)
    elif theme == 3:
      if self.style_manager.get_dark():
        style_dark = WebKit2.UserStyleSheet(self._css_dark, WebKit2.UserContentInjectedFrames.ALL_FRAMES, WebKit2.UserStyleLevel.USER, None, None)
        self.user_content.add_style_sheet(style_dark)

    if settings.get_boolean('custom-font'):
      css_font = 'body,h1,h2{font-family:"' + settings.get_string('font-family') + '"!important}'
      style_font = WebKit2.UserStyleSheet(css_font, WebKit2.UserContentInjectedFrames.ALL_FRAMES, WebKit2.UserStyleLevel.USER, None, None)
      self.user_content.add_style_sheet(style_font)

    if not settings.get_boolean('preview-popups'):
      css_previews = '.mwe-popups{display:none!important}'
      style_previews = WebKit2.UserStyleSheet(css_previews, WebKit2.UserContentInjectedFrames.ALL_FRAMES, WebKit2.UserStyleLevel.USER, None, None)
      self.user_content.add_style_sheet(style_previews)


# Create view_settings object

view_settings = ViewSettings()


# Webview class for Wikipedia views
# Show Wikipedia pages and manage decision policy

class WikiView(WebKit2.WebView):

  __gsignals__ = { 'new-page': (GObject.SIGNAL_RUN_FIRST, None, (str, )),
                   'add-bookmark': (GObject.SIGNAL_RUN_FIRST, None, (str, str, str,)) }

  title = 'Wike'
  sections = None
  langlinks = None

  # Initialize view with user content and web settings

  def __init__(self):
    super().__init__(settings=view_settings.web_settings, user_content_manager=view_settings.user_content)

    theme = settings.get_int('theme')
    if theme == 1:
      self.set_background_color(Gdk.RGBA(0.1, 0.1, 0.1, 1))
    elif theme == 2:
      self.set_background_color(Gdk.RGBA(0.976, 0.953, 0.914, 1))
    elif theme == 3:
      if view_settings.style_manager.get_dark():
        self.set_background_color(Gdk.RGBA(0.1, 0.1, 0.1, 1))
      else:
        self.set_background_color(Gdk.RGBA(1, 1, 1, 1))
    else:
      self.set_background_color(Gdk.RGBA(1, 1, 1, 1))

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
      self.load_message('notfound', None)

  # Create and load html for message page

  def load_message(self, message_type, fail_uri):
    if message_type == 'blank':
      title = 'Wike'
      subtitle = _('Search and read Wikipedia articles')
      message = _('Click the search button or press F2 to search articles in Wikipedia. You can also use the main menu to open Wikipedia main page, the list of recent articles or get a random article.')
    elif message_type == 'notfound':
      title = ':-('
      subtitle = _('Article not found')
      message = _('Can\'t find any results for requested query')
    else:
      title = ':-('
      subtitle = _('Can\'t access Wikipedia')
      message = _('Check your Internet connection and try again')

    if fail_uri:
      button = '<a href="' + fail_uri + '" class="btn">' + _('Try Again') + '</a>\n'
    else:
      button = ''

    html = '<!DOCTYPE html>\n<html>\n<head>\n<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />\n<title>Wike</title>\n</head>\n\
<body class="wike-body">\n<div id="wike-message">\n<h1>' + title + '</h1>\n<h3>' + subtitle + '</h3>\n<p>' + message + '</p>\n' + button + '</div>\n</body>\n</html>\n'

    uri = 'about:' + message_type
    self.load_html(html, uri)

  # Create and load html for historic page

  def load_historic(self):
    html_top = '<!DOCTYPE html>\n<html>\n<head>\n<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />\n<title>Wike</title>\n</head>\n\
<body class="wike-body">\n<div id="wike-historic">\n'

    html_bottom = '</div>\n</body>\n</html>\n'

    html_body = ''
    for date in sorted(historic.items, reverse=True):
      html_body = html_body + '<h3>' + date + '</h3>\n<table>\n'
      historic_item = historic.items[date]
      for uri in sorted(historic_item, key=historic_item.get, reverse=True):
        time = historic_item[uri][0]
        title = historic_item[uri][1]
        lang = historic_item[uri][2]
        if lang in languages.wikilangs:
          lang = languages.wikilangs[lang].capitalize()
        html_body = html_body + '<tr>\n<td class="wike-hist-time">' + time.rsplit(':', 1)[0] + '</td>\n<td class="wike-hist-link">' + '<a href="' + uri + '">' + title + '</a></td>\n<td class="wike-hist-lang">' + lang + '</td>\n</tr>\n'
      html_body = html_body + '</table>\n'

    html = html_top + html_body + html_bottom

    uri = 'about:historic'
    self.load_alternate_html(html, uri, uri)

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

  # Set TOC, langlinks and title for current article

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
      if uri_path == 'historic':
        self.title = _('Recent Articles')
      elif uri_path == 'notfound':
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

  # Check if current page is local (message page or historic)

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

  # Webview decision policy event

  def do_decide_policy(self, decision, decision_type):
    if decision_type == WebKit2.PolicyDecisionType.NAVIGATION_ACTION or decision_type == WebKit2.PolicyDecisionType.NEW_WINDOW_ACTION:
      nav_action = decision.get_navigation_action()
      nav_type = nav_action.get_navigation_type()
      mouse_button = nav_action.get_mouse_button()
      uri = nav_action.get_request().get_uri()
      uri_elements = urllib.parse.urlparse(uri)
      uri_scheme = uri_elements[0]
      uri_netloc = uri_elements[1]
      uri_path = uri_elements[2]
      uri_fragment = uri_elements[5]
      if nav_type == WebKit2.NavigationType.LINK_CLICKED:
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
      elif nav_type == WebKit2.NavigationType.RELOAD or nav_type == WebKit2.NavigationType.BACK_FORWARD:
        if uri_scheme == 'about':
          decision.ignore()
          if uri_path == 'historic':
            self.load_historic()
      elif nav_type == WebKit2.NavigationType.OTHER:
        if uri_netloc.startswith('upload.'):
          decision.ignore()
    return True

  # Manage webview context menu

  def do_context_menu(self, menu, event, hit_test):
    if hit_test.context_is_editable() or hit_test.context_is_media() or hit_test.context_is_scrollbar():
      return True

    action_tab = Gio.SimpleAction.new('new_tab', GLib.VariantType('s'))
    action_tab.connect('activate', self._new_tab_cb)
    action_browser = Gio.SimpleAction.new('open_browser', GLib.VariantType('s'))
    action_browser.connect('activate', self._open_browser_cb)
    action_bookmark = Gio.SimpleAction.new('add_bookmark', GLib.VariantType('s'))
    action_bookmark.connect('activate', self._add_bookmark_cb)
    action_clipboard = Gio.SimpleAction.new('copy_link', GLib.VariantType('s'))
    action_clipboard.connect('activate', self._copy_link_cb)

    if hit_test.get_context() == WebKit2.HitTestResultContext.DOCUMENT:
      base_uri = self.get_base_uri()
      uri = self._is_wiki_uri(base_uri)
      if uri == '' or uri in bookmarks.items:
        action_bookmark.set_enabled(False)

      item = WebKit2.ContextMenuItem.new_separator()
      menu.append(item)
      item = WebKit2.ContextMenuItem.new_from_gaction(action_bookmark, _('Add Bookmark'), GLib.Variant.new_string(uri))
      menu.append(item)

    if hit_test.context_is_link() and not hit_test.context_is_image():
      link = hit_test.get_link_uri()
      uri = self._is_wiki_uri(link)
      if uri == '':
        action_bookmark.set_enabled(False)
        action_tab.set_enabled(False)
      else:
        if uri in bookmarks.items:
          action_bookmark.set_enabled(False)

      if uri != '':
        link = uri
      item = WebKit2.ContextMenuItem.new_from_gaction(action_tab, _('Open Link in New Tab'), GLib.Variant.new_string(uri))
      menu.append(item)
      item = WebKit2.ContextMenuItem.new_from_gaction(action_browser, _('Open Link in Browser'), GLib.Variant.new_string(link))
      menu.append(item)
      item = WebKit2.ContextMenuItem.new_separator()
      menu.append(item)
      item = WebKit2.ContextMenuItem.new_from_gaction(action_bookmark, _('Add Link to Bookmarks'), GLib.Variant.new_string(uri))
      menu.append(item)
      item = WebKit2.ContextMenuItem.new_from_gaction(action_clipboard, _('Copy Link to Clipboard'), GLib.Variant.new_string(link))
      menu.append(item)

    allowed_actions = (WebKit2.ContextMenuAction.NO_ACTION,
                       WebKit2.ContextMenuAction.CUSTOM,
                       WebKit2.ContextMenuAction.GO_BACK,
                       WebKit2.ContextMenuAction.GO_FORWARD,
                       WebKit2.ContextMenuAction.RELOAD,
                       WebKit2.ContextMenuAction.COPY,
                       WebKit2.ContextMenuAction.COPY_IMAGE_TO_CLIPBOARD,
                       WebKit2.ContextMenuAction.COPY_IMAGE_URL_TO_CLIPBOARD)

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
    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
    clipboard.set_text(uri, -1)

