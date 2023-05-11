# This file is part of Wike (com.github.hugolabe.Wike)
# SPDX-FileCopyrightText: 2021-23 Hugo Olabera <hugolabe@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later


from gi.repository import Gtk, Adw

from wike.data import settings


# Languages window to choose user languages

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/ui/projects.ui')
class ProjectsWindow(Adw.Window):

  __gtype_name__ = 'ProjectsWindow'

  projects_list = Gtk.Template.Child()

  # Initialize and connect signals

  def __init__(self):
    super().__init__()

    self.project_selected = 'wikipedia'
    self._populate()

    self.projects_list.connect('row-activated', self._project_selected_cb)
    self.connect('close-request', self._window_close_cb)

  # Populate list of available languages

  def _populate(self):
    projects_name = ("wikipedia", "wiktionary", "wikinews")
    for project_name in projects_name:
      row = ProjectsRow(project_name)
      self.projects_list.append(row)

  # Set languages changed variable on radio button changed

  def _project_selected_cb(self, projects_list, row):
    self.project_selected = row.project_name

  # On window close refresh languages list (if changed)

  def _window_close_cb(self, prefs_window):
    settings.set_string("search-project", self.project_selected)
    
    window = self.get_transient_for()
    window.headerbar.search_box.settings_popover.populate_list()
    return False

# Row in languages list

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/ui/projects-row.ui')
class ProjectsRow(Gtk.ListBoxRow):

  __gtype_name__ = 'ProjectsRow'

  name_label = Gtk.Template.Child()

  # Set row values

  def __init__(self, project_name):
    super().__init__()

    self.project_name = project_name
    self.name_label.set_label(project_name)


