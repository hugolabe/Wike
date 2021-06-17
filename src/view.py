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
gi.require_version('WebKit2', '4.0')
from gi.repository import Gio, GObject, Gdk, Gtk, WebKit2

from wike import wikipedia
from wike.data import settings, languages, historic, bookmarks


# Webview class for Wikipedia view
# Show Wikipedia pages with custom css and manage decision policy

class WikiView(WebKit2.WebView):

  __gsignals__ = { 'load-wiki': (GObject.SIGNAL_RUN_FIRST, None, ()),
                   'add-bookmark': (GObject.SIGNAL_RUN_FIRST, None, (str, str, str,)) }

  # Initialize view with user content and web settings

  def __init__(self):
    user_content = WebKit2.UserContentManager()
    super().__init__(user_content_manager=user_content)

    web_settings = self.get_settings()
    web_settings.set_default_font_size(settings.get_int('font-size'))
    settings.connect('changed::font-size', self._settings_font_size_changed_cb, web_settings)
    settings.connect('changed::custom-font', self._settings_custom_font_changed_cb)
    settings.connect('changed::font-family', self._settings_custom_font_changed_cb)

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

    self.set_style()

  # Settings font-size changed event

  def _settings_font_size_changed_cb(self, settings, key, web_settings):
    web_settings.set_default_font_size(settings.get_int('font-size'))

  # Settings custom font changed event

  def _settings_custom_font_changed_cb(self, settings, key):
    self.set_style()

  # Inyect stylesheet for customize article view

  def set_style(self):
    user_content =  self.get_user_content_manager()
    user_content.remove_all_style_sheets()

    style_view = WebKit2.UserStyleSheet(self._css_view, WebKit2.UserContentInjectedFrames.ALL_FRAMES, WebKit2.UserStyleLevel.USER, None, None)
    user_content.add_style_sheet(style_view)

    if settings.get_boolean('dark-mode'):
      self.set_background_color(Gdk.RGBA(0.1, 0.1, 0.1, 1))
      style_dark = WebKit2.UserStyleSheet(self._css_dark, WebKit2.UserContentInjectedFrames.ALL_FRAMES, WebKit2.UserStyleLevel.USER, None, None)
      user_content.add_style_sheet(style_dark)
    else:
      self.set_background_color(Gdk.RGBA(1, 1, 1, 1))

    if settings.get_boolean('custom-font'):
      css_font = 'body,h1,h2{font-family:"' + settings.get_string('font-family') + '"!important}'
      style_font = WebKit2.UserStyleSheet(css_font, WebKit2.UserContentInjectedFrames.ALL_FRAMES, WebKit2.UserStyleLevel.USER, None, None)
      user_content.add_style_sheet(style_font)

  # Check connection and load Wikipedia article by URI

  def load_wiki(self, uri):
    self.stop_loading()
    if uri.find('.m.') == -1:
      uri = uri.replace('.wikipedia.org', '.m.wikipedia.org')
    self.emit('load-wiki')
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
      uri = wikipedia.get_random()
      self.load_wiki(uri)
    except:
      self.load_message('notfound', None)

  # Create and load html for message page

  def load_message(self, message_type, fail_uri):
    self.emit('load-wiki')

    if message_type == 'notfound':
      title = _('Article not found')
      message = _('Can\'t find any results for requested query')
    else:
      title = _('Can\'t access Wikipedia')
      message = _('Check your Internet connection and try again')

    if fail_uri:
      button = '<a href="' + fail_uri + '" class="btn">' + _('Try again') + '</a>\n'
    else:
      button = ''

    html = '<!DOCTYPE html>\n<html>\n<head>\n<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />\n<title>Wike</title>\n</head>\n\
<body class="wike-body">\n<div id="wike-message">\n<h1>:-(</h1>\n<h3>' + title + '</h3>\n<p>' + message + '</p>\n' + button + '</div>\n</body>\n</html>\n'

    uri = 'about:' + message_type
    self.load_html(html, uri)

  # Create and load html for historic page

  def load_historic(self):
    self.emit('load-wiki')

    html_top = '<!DOCTYPE html>\n<html>\n<head>\n<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />\n<title>Wike</title>\n</head>\n\
<body class="wike-body">\n<div id="wike-historic">\n'

    html_bottom = '</div>\n</body>\n</html>\n'

    html_body = ''
    for date in sorted(historic.items, reverse=True):
      html_body = html_body + '<h3>' + date + '</h3>\n'
      historic_item = historic.items[date]
      for uri in sorted(historic_item, key=historic_item.get, reverse=True):
        time = historic_item[uri][0]
        title = historic_item[uri][1]
        lang = historic_item[uri][2]
        if lang in languages.wikilangs: lang = languages.wikilangs[lang].capitalize()
        html_body = html_body + '<div class="wike-hist-item">' + time.rsplit(':', 1)[0] + '<a href="' + uri + '">' + title + '</a><span class="wike-hist-lang">' + lang + '</span></div>\n'

    html = html_top + html_body + html_bottom

    uri = 'about:historic'
    self.load_alternate_html(html, uri, uri)

  # Check connection and reload Wikipedia article or local page

  def reload(self):
    self.stop_loading()
    uri = self.get_uri()
    if self.is_local():
      uri_elements = urllib.parse.urlparse(uri)
      uri_path = uri_elements[2]
      if uri_path == 'historic':
        self.load_historic()
    else:
      self.emit('load-wiki')
      self.reload_bypass_cache()

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

  # Get title for current article

  def get_title(self):
    uri = self.get_uri()
    uri_elements = urllib.parse.urlparse(uri)
    uri_scheme = uri_elements[0]
    uri_path = uri_elements[2]

    if uri_scheme == 'about':
      if uri_path == 'historic':
        return _('Recent articles')
      else:
        return 'Wike'
    else:
      title = uri_path.replace('/wiki/', '', 1).replace('_', ' ')
      return urllib.parse.unquote(title)

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

  # Get table of contents and langlinks for current article

  def get_props(self):
    uri = self.get_uri()
    uri_elements = urllib.parse.urlparse(uri)
    uri_scheme = uri_elements[0]
    uri_netloc = uri_elements[1]
    uri_path = uri_elements[2]

    if uri_scheme == 'about':
      return None
    else:
      page = uri_path.replace('/wiki/', '', 1)
      lang = uri_netloc.split('.', 1)[0]
      try:
        props = wikipedia.get_properties(page, lang)
      except:
        props = None
      return props

  # Check if current page is local (message page or historic)

  def is_local(self):
    uri = self.get_uri()
    uri_elements = urllib.parse.urlparse(uri)
    uri_scheme = uri_elements[0]

    if uri_scheme == 'about':
      return True
    else:
      return False

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
            title = uri_path.replace('/wiki/', '', 1).replace('_', ' ')
            title = urllib.parse.unquote(title)
            lang = uri_netloc.split('.', 1)[0]
            self.emit('add-bookmark', base_uri, title, lang)
          else:
            if base_uri == self.get_base_uri():
              decision.use()
            else:
              decision.ignore()
              self.load_wiki(uri)
        else:
          decision.ignore()
          Gtk.show_uri(None, uri, Gdk.CURRENT_TIME)
      elif nav_type == WebKit2.NavigationType.RELOAD or nav_type == WebKit2.NavigationType.BACK_FORWARD:
        if uri_scheme == 'about' and uri_path == 'historic':
          self.load_historic()
      elif nav_type == WebKit2.NavigationType.OTHER:
        if uri_netloc.startswith('upload.'): decision.ignore()
    return True

  # Deactivate webview context menu

  def do_context_menu(self, menu, event, hit_test_result):
    return True


# Create wikiview global object

wikiview = WikiView()

