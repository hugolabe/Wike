# This file is part of Wike (com.github.hugolabe.Wike)
# SPDX-FileCopyrightText: 2021-23 Hugo Olabera <hugolabe@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later


from gi.repository import GLib, Gio, Gtk, Pango

from wike.data import settings


# Popover for main menu

class MainMenuPopover(Gtk.PopoverMenu):

  # Set menu model

  def __init__(self):
    super().__init__()

    builder_menu = Gtk.Builder()
    builder_menu.add_from_resource('/com/github/hugolabe/Wike/ui/menu-main.ui')
    main_menu = builder_menu.get_object('main_menu')
    self.set_menu_model(main_menu)


# Popover for view menu

class ViewMenuPopover(Gtk.PopoverMenu):

  # Set menu model and add theme switcher and zoom level widgets

  def __init__(self, window):
    super().__init__()

    self._window = window

    builder_menu = Gtk.Builder()
    builder_menu.add_from_resource('/com/github/hugolabe/Wike/ui/menu-view.ui')
    self.view_menu = builder_menu.get_object('view_menu')
    self.set_menu_model(self.view_menu)
    
    theme_switcher = ThemeSwitcher(window)
    self.add_child(theme_switcher, 'theme_switcher')

    zoom_level = ZoomLevel()
    self.add_child(zoom_level, 'zoom_level')

    if not settings.get_boolean('custom-font'):
      pango_context = self.get_pango_context()
      font_family = pango_context.get_font_description().get_family()
      settings.set_string('font-family', font_family)

    self._add_section_font()

    actions = Gio.SimpleActionGroup()
    action = Gio.SimpleAction.new_stateful('show-flags', None, GLib.Variant.new_boolean(settings.get_boolean('show-flags')))
    action.connect('change-state', self._show_flags_cb)
    actions.add_action(action)
    action = Gio.SimpleAction.new_stateful('preview-popups', None, GLib.Variant.new_boolean(settings.get_boolean('preview-popups')))
    action.connect('change-state', self._preview_popups_cb)
    actions.add_action(action)
    action = Gio.SimpleAction.new('set-font', None)
    action.connect('activate', self._set_font_cb)
    actions.add_action(action)
    self.insert_action_group('view', actions)

  # Show/hide flags for language lists

  def _show_flags_cb(self, action, parameter):
    action.set_state(parameter)
    settings.set_boolean('show-flags', parameter)

  # Show/hide previews for article links

  def _preview_popups_cb(self, action, parameter):
    action.set_state(parameter)
    settings.set_boolean('preview-popups', parameter)

  # Show choose font dialog

  def _set_font_cb(self, action, parameter):
    font_desc = Pango.FontDescription()
    font_desc.set_family(settings.get_string('font-family'))
    font_desc.set_absolute_size(settings.get_int('font-size') * Pango.SCALE)

    font_dialog = Gtk.FontChooserDialog.new(_('Pick a Font'), self._window)
    font_dialog.set_font_desc(font_desc)
    font_dialog.set_level(Gtk.FontChooserLevel.SIZE)
    font_dialog.set_modal(True)
    font_dialog.show()
    font_dialog.connect('response', self._font_dialog_cb)

  # On dialog response set font and refresh menu

  def _font_dialog_cb(self, font_dialog, response):
    if response == Gtk.ResponseType.OK:
      font_desc = font_dialog.get_font_desc()
      font_family = font_desc.get_family()
      font_size = font_desc.get_size() / Pango.SCALE
      settings.set_boolean('custom-font', True)
      settings.set_string('font-family', font_family)
      settings.set_int('font-size', font_size)
      self.view_menu.remove(3)
      self._add_section_font()
      font_dialog.destroy()
    else:
      font_dialog.destroy()

  # Add menu section to choose font

  def _add_section_font(self):
    font_label = settings.get_string('font-family') + ' ' + str(settings.get_int('font-size'))
    font_section = Gio.Menu()
    font_section.append(font_label, 'view.set-font')
    self.view_menu.append_section(_('Font'), font_section)


# Theme switcher widget for view menu

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/ui/theme-switcher.ui')
class ThemeSwitcher(Gtk.Box):

  __gtype_name__ = 'ThemeSwitcher'

  system_button = Gtk.Template.Child()
  light_button = Gtk.Template.Child()
  sepia_button = Gtk.Template.Child()
  dark_button = Gtk.Template.Child()

  # Set button theme active and connect signals

  def __init__(self, window):
    super().__init__()

    self._window = window

    theme = settings.get_int('theme')
    match theme:
      case 0:
        self.light_button.set_active(True)
      case 1:
        self.dark_button.set_active(True)
      case 2:
        self.sepia_button.set_active(True)
      case 3:
        self.system_button.set_active(True)

    self.system_button.connect('toggled', self._system_button_toggled_cb)
    self.light_button.connect('toggled', self._light_button_toggled_cb)
    self.sepia_button.connect('toggled', self._sepia_button_toggled_cb)
    self.dark_button.connect('toggled', self._dark_button_toggled_cb)

  # On button toggle change to system theme

  def _system_button_toggled_cb(self, button):
    if button.get_active():
      app = self._window.get_application()
      theme_action = app.lookup_action('theme-system')
      theme_action.activate()

  # On button toggle change to light theme

  def _light_button_toggled_cb(self, button):
    if button.get_active():
      app = self._window.get_application()
      theme_action = app.lookup_action('theme-light')
      theme_action.activate()

  # On button toggle change to sepia theme

  def _sepia_button_toggled_cb(self, button):
    if button.get_active():
      app = self._window.get_application()
      theme_action = app.lookup_action('theme-sepia')
      theme_action.activate()

  # On button toggle change to dark theme

  def _dark_button_toggled_cb(self, button):
    if button.get_active():
      app = self._window.get_application()
      theme_action = app.lookup_action('theme-dark')
      theme_action.activate()


# Zoom level widget for view menu

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/ui/zoom-level.ui')
class ZoomLevel(Gtk.Box):

  __gtype_name__ = 'ZoomLevel'

  zoom_value_button = Gtk.Template.Child()
  zoom_in_button = Gtk.Template.Child()
  zoom_out_button = Gtk.Template.Child()

  # Set buttons status and connect signals

  def __init__(self):
    super().__init__()

    self._set_buttons()

    self.zoom_value_button.connect('clicked', self._zoom_value_clicked)
    self.zoom_in_button.connect('clicked', self._zoom_in_clicked)
    self.zoom_out_button.connect('clicked', self._zoom_out_clicked)
    settings.connect('changed::zoom-level', self._zoom_level_changed_cb)

  # Set buttons sensitivity for current zoom level value

  def _set_buttons(self):
    zoom_value = settings.get_int('zoom-level')
    self.zoom_value_button.set_label(str(zoom_value) + '%')

    if zoom_value == 100:
      self.zoom_value_button.set_sensitive(False)
      self.zoom_in_button.set_sensitive(True)
      self.zoom_out_button.set_sensitive(True)
    else:
      self.zoom_value_button.set_sensitive(True)
      if zoom_value >= 200:
        self.zoom_in_button.set_sensitive(False)
        self.zoom_out_button.set_sensitive(True)
      elif zoom_value <= 50:
        self.zoom_in_button.set_sensitive(True)
        self.zoom_out_button.set_sensitive(False)
      else:
        self.zoom_in_button.set_sensitive(True)
        self.zoom_out_button.set_sensitive(True)

  # On button clicked set zoom level to 100%

  def _zoom_value_clicked(self, zoom_value_button):
    settings.set_int('zoom-level', 100)

  # On button clicked increase zoom level

  def _zoom_in_clicked(self, zoom_in_button):
    zoom_level = settings.get_int('zoom-level')
    if zoom_level < 200:
      zoom_level += 10
      settings.set_int('zoom-level', zoom_level)

  # On button clicked reduce zoom level

  def _zoom_out_clicked(self, zoom_out_button):
    zoom_level = settings.get_int('zoom-level')
    if zoom_level > 50:
      zoom_level -= 10
      settings.set_int('zoom-level', zoom_level)

  # On zoom level changed refresh buttons

  def _zoom_level_changed_cb(self, settings, key):
    self._set_buttons()
