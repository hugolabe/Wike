# This file is part of Wike (com.github.hugolabe.Wike)
# SPDX-FileCopyrightText: 2021-23 Hugo Olabera <hugolabe@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later


from gi.repository import GObject, Gio, Gtk, Adw, Pango

from wike.data import languages, bookmarks


# Box bookmarks in sidebar

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/ui/bookmarks.ui')
class BookmarksBox(Gtk.Box):

  __gtype_name__ = 'BookmarksBox'

  booklists_dropdown = Gtk.Template.Child()
  menu_button = Gtk.Template.Child()
  bookmarks_list = Gtk.Template.Child()
  bookmarks_scroller = Gtk.Template.Child()
  bookmarks_separator = Gtk.Template.Child()

  # Initialize widgets and connect signals

  def __init__(self, window):
    super().__init__()

    self._window = window
    self._booklist = None
    self._booklist_default = _('Reading list')

    menu_popover = BookmarksMenuPopover(self)
    self.menu_button.set_popover(menu_popover)

    self.booklists_model = Gio.ListStore(item_type=Booklist)
    self.booklists_model.append(Booklist(self._booklist_default))
    for list_name in bookmarks.lists.keys():
      self.booklists_model.append(Booklist(list_name))

    self.booklists_model.sort(self._sort_booklists)

    booklists_factory = Gtk.SignalListItemFactory()
    booklists_factory.connect('setup', self._booklists_factory_setup)
    booklists_factory.connect('bind', self._booklists_factory_bind)

    self.booklists_dropdown.set_model(self.booklists_model)
    self.booklists_dropdown.set_factory(booklists_factory)

    self.bookmarks_list.set_sort_func(self._sort_list)
    self._populate(None)

    self._set_actions()

    self.booklists_dropdown.connect('notify::selected', self._booklists_dropdown_selected_cb)
    self.booklists_model.connect('items-changed', self._booklists_model_changed_cb)
    self.bookmarks_list.connect('row-activated', self._list_activated_cb)
    self.bookmarks_scroller.get_vadjustment().connect('value-changed', self._bookmarks_scrolled_cb)

  # Set actions for bookmarks menu

  def _set_actions(self):
    actions = [ ('create-list', self._create_booklist_cb),
                ('rename-list', self._rename_booklist_cb),
                ('clear-list', self._clear_booklist_cb) ]

    self.actions_group = Gio.SimpleActionGroup()

    for name, callback in actions:
      action = Gio.SimpleAction.new(name, None)
      action.connect('activate', callback)
      self.actions_group.add_action(action)

    self.insert_action_group('bookmarks', self.actions_group)

  # Setup booklist item with a label

  def _booklists_factory_setup(self, factory, list_item):
    label = Gtk.Label()
    label.set_xalign(0)
    label.set_max_width_chars(15)
    label.set_ellipsize(Pango.EllipsizeMode.END)
    list_item.set_child(label)

  # Bind label property for booklist item

  def _booklists_factory_bind(self, factory, list_item):
    label = list_item.get_child()
    booklist = list_item.get_item()
    booklist.bind_property('name', label, 'label', GObject.BindingFlags.SYNC_CREATE)

  # Sort booklists dropdown alphabetically

  def _sort_booklists(self, row1, row2):
    if row1.name == self._booklist_default:
      return 0

    if row1.name > row2.name:
      return 1
    elif row1.name < row2.name:
      return -1
    else:
      return 0

  # Sort bookmarks list alphabetically

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

  # Populate bookmarks list

  def _populate(self, list_name):
    if list_name:
      bookmarks_items = bookmarks.lists[list_name]
    else:
      bookmarks_items = bookmarks.items

    for bookmark in bookmarks_items:
      title = bookmarks_items[bookmark][0]
      lang = bookmarks_items[bookmark][1]
      row = BookmarksRow(bookmark, title, lang)
      self.bookmarks_list.append(row)
      row.remove_button.connect('clicked', self._row_remove_button_cb, row)

  # Clear bookmarks list

  def _clear(self):
    while True:
      row = self.bookmarks_list.get_row_at_index(0)
      if row:
        self.bookmarks_list.remove(row)
      else:
        break

  # Refresh status of headerbar bookmark buttons

  def refresh_buttons(self):
    add_bookmark_action = self._window.lookup_action('add-bookmark')

    if self._window.page.wikiview.is_local():
      add_bookmark_action.set_enabled(False)
      return

    if self._booklist:
      bookmarks_items = bookmarks.lists[self._booklist]
    else:
      bookmarks_items = bookmarks.items

    if self._window.page.wikiview.get_base_uri() in bookmarks_items:
      add_bookmark_action.set_enabled(False)
    else:
      add_bookmark_action.set_enabled(True)

  # Add bookmark with uri, title and lang in current list

  def add_bookmark(self, uri, title, lang):
    if bookmarks.add(uri, title, lang, self._booklist):
      row = BookmarksRow(uri, title, lang)
      self.bookmarks_list.append(row)
      row.remove_button.connect('clicked', self._row_remove_button_cb, row)
      self.refresh_buttons()
      return True
    else:
      return False

  # Remove bookmark from current list
  
  def remove_bookmark(self, uri):
    if bookmarks.remove(uri, self._booklist):
      i = 0
      while True:
        row = self.bookmarks_list.get_row_at_index(i)
        if row.uri == uri:
          self.bookmarks_list.remove(row)
          break
        else:
          i += 1
      self.refresh_buttons()
      return True
    else:
      return False

  # Show create bookmarks list dialog

  def _create_booklist_cb(self, action, parameter):
    builder = Gtk.Builder()
    builder.add_from_resource('/com/github/hugolabe/Wike/ui/dialogs.ui')
    new_booklist_dialog = builder.get_object('new_booklist_dialog')
    name_entry = builder.get_object('name_entry')
    new_booklist_dialog.set_transient_for(self._window)

    new_booklist_dialog.connect('response', self._create_booklist_response_cb, name_entry)
    name_entry.connect('changed', self._create_entry_changed_cb, new_booklist_dialog)

    new_booklist_dialog.show()

  # On response create bookmarks list

  def _create_booklist_response_cb(self, new_booklist_dialog, response, name_entry):
    if response == 'create':
      list_name = name_entry.get_text()
      if bookmarks.new_list(list_name):
        self.booklists_model.append(Booklist(list_name))
        self.booklists_model.sort(self._sort_booklists)

  # On entry changes check input

  def _create_entry_changed_cb(self, name_entry, new_booklist_dialog):
    text = name_entry.get_text()

    if len(text) == 0:
      new_booklist_dialog.set_response_enabled('create', False)
      name_entry.remove_css_class('error')
    else:
      if text == self._booklist_default or text in bookmarks.lists:
        new_booklist_dialog.set_response_enabled('create', False)
        name_entry.add_css_class('error')
      else:
        new_booklist_dialog.set_response_enabled('create', True)
        name_entry.remove_css_class('error')

  # Show rename bookmarks list dialog

  def _rename_booklist_cb(self, action, parameter):
    builder = Gtk.Builder()
    builder.add_from_resource('/com/github/hugolabe/Wike/ui/dialogs.ui')
    rename_booklist_dialog = builder.get_object('rename_booklist_dialog')
    rename_entry = builder.get_object('rename_entry')
    rename_booklist_dialog.set_transient_for(self._window)

    rename_entry.set_text(self._booklist)

    rename_booklist_dialog.connect('response', self._rename_booklist_response_cb, rename_entry)
    rename_entry.connect('changed', self._rename_entry_changed_cb, rename_booklist_dialog)

    rename_booklist_dialog.show()

  # On response rename bookmarks list

  def _rename_booklist_response_cb(self, rename_booklist_dialog, response, rename_entry):
    if response == 'rename':
      new_name = rename_entry.get_text()
      if bookmarks.rename_list(self._booklist, new_name):
        position = self.booklists_dropdown.get_selected()
        self.booklists_model.remove(position)
        self.booklists_model.append(Booklist(new_name))
        self.booklists_model.sort(self._sort_booklists)

  # On entry changes check input

  def _rename_entry_changed_cb(self, rename_entry, rename_booklist_dialog):
    text = rename_entry.get_text()

    if len(text) == 0:
      rename_booklist_dialog.set_response_enabled('rename', False)
      rename_entry.remove_css_class('error')
    else:
      if text == self._booklist:
        rename_booklist_dialog.set_response_enabled('rename', False)
        rename_entry.remove_css_class('error')
      elif text == self._booklist_default or text in bookmarks.lists:
        rename_booklist_dialog.set_response_enabled('rename', False)
        rename_entry.add_css_class('error')
      else:
        rename_booklist_dialog.set_response_enabled('rename', True)
        rename_entry.remove_css_class('error')

  # Show clear bookmarks list dialog

  def _clear_booklist_cb(self, action, parameter):
    builder = Gtk.Builder()
    builder.add_from_resource('/com/github/hugolabe/Wike/ui/dialogs.ui')
    clear_booklist_dialog = builder.get_object('clear_booklist_dialog')
    delete_booklist_check = builder.get_object('delete_booklist_check')
    clear_booklist_dialog.set_transient_for(self._window)

    if self.booklists_dropdown.get_selected() == 0:
      delete_booklist_check.set_sensitive(False)

    clear_booklist_dialog.connect('response', self._clear_booklist_response_cb, delete_booklist_check)

    clear_booklist_dialog.show()

  # On response clear all bookmarks of current list
  
  def _clear_booklist_response_cb(self, dialog, response, delete_booklist_check):
    if response == 'clear':
      if delete_booklist_check.get_active():
        if bookmarks.remove_list(self._booklist):
          self.booklists_model.remove(self.booklists_dropdown.get_selected())
      else:
        bookmarks.clear_list(self._booklist)
        self._clear()
        self.refresh_buttons()

  # Dropdown list selected changed

  def _booklists_dropdown_selected_cb(self, booklists_dropdown, selected):
    position = booklists_dropdown.get_selected()
    list_name = booklists_dropdown.get_selected_item().name
    if position == 0:
      self._booklist = None
    else:
      self._booklist = list_name

    self._clear()
    self._populate(self._booklist)
    self.refresh_buttons()

  # Dropdown list items changed

  def _booklists_model_changed_cb(self, booklists_model, position, removed, added):
    if added == 1:
      self.booklists_dropdown.set_selected(position)
    else:
      if removed == 1:
        self.booklists_dropdown.set_selected(0)

  # On list activated load article in view

  def _list_activated_cb(self, bookmarks_list, row):
    if self._window.flap.get_fold_policy() == Adw.FlapFoldPolicy.ALWAYS and not self._window._ctrl_pressed:
      self._window.flap.set_reveal_flap(False)

    if self._window._ctrl_pressed:
      self._window.new_lazy_page(row.uri, row.title, None)
    else:
      self._window.page.wikiview.load_wiki(row.uri)

  # On row button remove bookmark and refresh buttons state
  
  def _row_remove_button_cb(self, remove_button, row):
    if bookmarks.remove(row.uri, self._booklist):
      self.bookmarks_list.remove(row)

    self.refresh_buttons()

  # Show/hide separator on scroll

  def _bookmarks_scrolled_cb(self, adjustment):
    if adjustment.get_value() > 0:
      self.bookmarks_separator.set_visible(True)
    else:
      self.bookmarks_separator.set_visible(False)


# This object represent a bookmarks list in dropdown

class Booklist(GObject.Object):
  __gtype_name__ = 'Booklist'

  # Set values

  def __init__(self, name):
    super().__init__()

    self._name = name

  # Name of booklist property

  @GObject.Property(type=str)
  def name(self):
    return self._name


# Row on bookmarks list

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/ui/bookmarks-row.ui')
class BookmarksRow(Gtk.ListBoxRow):

  __gtype_name__ = 'BookmarksRow'
  
  title_label = Gtk.Template.Child()
  lang_label = Gtk.Template.Child()
  remove_button = Gtk.Template.Child()

  # Set values and connect signals

  def __init__(self, uri, title, lang):
    super().__init__()

    self.uri = uri
    self.title = title
    self.lang = lang

    if lang in languages.wikilangs:
      lang_name = languages.wikilangs[lang].capitalize()
    else:
      lang_name = lang

    self.title_label.set_label(title)
    self.lang_label.set_markup('<small>' + lang_name + '</small>')


# Popover menu for bookmarks options

class BookmarksMenuPopover(Gtk.PopoverMenu):

  # Set menu model and connect signals

  def __init__(self, bookmarks_box):
    super().__init__()

    builder_menu = Gtk.Builder()
    builder_menu.add_from_resource('/com/github/hugolabe/Wike/ui/bookmarks-menu.ui')
    menu = builder_menu.get_object('bookmarks_menu')
    self.set_menu_model(menu)

    self.connect('show', self._popover_show_cb, bookmarks_box)

  # Enable or disable menu items on popover show

  def _popover_show_cb(self, popover, bookmarks_box):
    rename_list_action = bookmarks_box.actions_group.lookup_action('rename-list')

    if bookmarks_box.booklists_dropdown.get_selected() == 0:
      rename_list_action.set_enabled(False)
    else:
      rename_list_action.set_enabled(True)
