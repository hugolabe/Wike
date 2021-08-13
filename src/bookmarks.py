# bookmarks.py
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

from wike.data import languages, bookmarks
from wike.view import wikiview


# Popover class for bookmarks
# View and manage list of bookmarks

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/ui/bookmarks.ui')
class BookmarksPopover(Gtk.Popover):

  __gtype_name__ = 'BookmarksPopover'

  bookmarks_list = Gtk.Template.Child()
  add_button = Gtk.Template.Child()
  clear_button = Gtk.Template.Child()
  placeholder_label = Gtk.Template.Child()

  # Initialize popover and connect signals

  def __init__(self):
    super().__init__()

    placeholder_text = _("<b>No Bookmarks</b>\n\n<small>Use the <i>Add Bookmark</i> button\nor click a link with the middle mouse button\nto add bookmarks to the list</small>")
    self.placeholder_label.set_markup(placeholder_text)

    self.bookmarks_list.set_sort_func(self._sort_list)
    self.bookmarks_list.set_header_func(self._set_row_separator)
    self._populate()

    self.bookmarks_list.connect('row-activated', self._list_activated_cb)
    self.bookmarks_list.connect('add', self._list_changed_cb)
    self.bookmarks_list.connect('remove', self._list_changed_cb)
    self.add_button.connect('clicked', self._add_button_clicked_cb)
    self.clear_button.connect('clicked', self._clear_button_clicked_cb)
    self.connect('show', self._popover_show_cb)

  # Sort list alphabetically

  def _sort_list(self, row1, row2):
    if row1.title > row2.title:
      return 1
    elif row1.title < row2.title:
      return -1
    else:
      if row1.lang > row2.lang:
        return 1
      elif row1.lang < row2.lang:
        return -1
      else:
        return 0

  # Set bookmark row separator

  def _set_row_separator(self, row, before):
    if before and not row.get_header():
      separator = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)
      row.set_header(separator)

  # Populate bookmarks list

  def _populate(self):
    for bookmark in bookmarks.items:
      title = bookmarks.items[bookmark][0]
      lang = bookmarks.items[bookmark][1]
      if lang in languages.wikilangs:
        lang_name = languages.wikilangs[lang].capitalize()
      else:
        lang_name = lang
      row = BookmarkBoxRow(bookmark, title, lang, lang_name)
      self.bookmarks_list.add(row)

  # Refresh sensitivity of add and clear buttons

  def _refresh_buttons(self):
    if len(self.bookmarks_list.get_children()) == 0:
      self.clear_button.set_sensitive(False)
    else:
      self.clear_button.set_sensitive(True)
    if wikiview.get_base_uri() in bookmarks.items or wikiview.is_local():
      self.add_button.set_sensitive(False)
    else:
      self.add_button.set_sensitive(True)

  # Add bookmark with uri, title and lang

  def add_bookmark(self, uri, title, lang):
    if bookmarks.add(uri, title, lang):
      if lang in languages.wikilangs:
        lang_name = languages.wikilangs[lang].capitalize()
      else:
        lang_name = lang
      row = BookmarkBoxRow(uri, title, lang, lang_name)
      self.bookmarks_list.add(row)
      return True
    else:
      return False

  # Add item on button clicked

  def _add_button_clicked_cb(self, add_button):
    uri = wikiview.get_base_uri()
    title = wikiview.get_title()
    lang = wikiview.get_lang()
    if self.add_bookmark(uri, title, lang):
      self.bookmarks_list.show_all()

  # Clear list on button clicked

  def _clear_button_clicked_cb(self, clear_button):
    clear_dialog = Gtk.MessageDialog(self.get_toplevel(),
                                     Gtk.DialogFlags.MODAL,
                                     Gtk.MessageType.WARNING,
                                     Gtk.ButtonsType.CANCEL,
                                     _('Clear Bookmarks List?'))
    clear_dialog.set_property('secondary-text', _('All bookmarks in the list will be removed permanently.'))
    clear_dialog.add_buttons(_('Clear List'), Gtk.ResponseType.YES)

    response = clear_dialog.run()
    clear_dialog.destroy()
    if response == Gtk.ResponseType.CANCEL:
      return

    bookmarks.clear()
    rows = self.bookmarks_list.get_children()
    for row in rows:
      self.bookmarks_list.remove(row)

  # Load article in view on list activated

  def _list_activated_cb(self, bookmarks_list, row):
    self.hide()
    wikiview.load_wiki(row.uri)

  # Refresh buttons state on list changed

  def _list_changed_cb(self, bookmarks_list, row):
    self._refresh_buttons()

  # Populate list and show popover

  def _popover_show_cb(self, popover):
    self.bookmarks_list.show_all()
    self.bookmarks_list.unselect_all()
    self._refresh_buttons()


# Class for row in bookmarks list
# Create row from URL, title and article language

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/ui/bookmarks-row.ui')
class BookmarkBoxRow(Gtk.ListBoxRow):

  __gtype_name__ = 'BookmarkBoxRow'

  article_title = Gtk.Template.Child()
  article_lang = Gtk.Template.Child()
  remove_button = Gtk.Template.Child()

  # Set values and connect signals

  def __init__(self, uri, title, lang, lang_name):
    super().__init__()

    self.uri = uri
    self.title = title
    self.lang = lang

    self.article_title.set_label(title)
    self.article_lang.set_markup('<small>' + lang_name + '</small>')

    self.remove_button.connect('clicked', self._remove_button_clicked_cb)

  # Remove bookmark on buttom clicked

  def _remove_button_clicked_cb(self, remove_button):
    bookmarks.remove(self.uri)
    bookmarks_list = self.get_parent()
    bookmarks_list.remove(self)

