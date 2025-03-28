# This file is part of Wike (com.github.hugolabe.Wike)
# SPDX-FileCopyrightText: 2021-24 Hugo Olabera <hugolabe@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later


import json, urllib.parse

from gi.repository import Gtk, Adw


# TOC (table of contents) panel for sidebar

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/gtk/toc.ui')
class TocPanel(Adw.Bin):

  __gtype_name__ = 'TocPanel'

  title_label = Gtk.Template.Child()
  toc_list = Gtk.Template.Child()

  # Initialize widgets and connect signals

  def __init__(self, window):
    super().__init__()

    self._window = window
    
    self.toc_list.connect('row-activated', self._list_activated_cb)
    
  # Populate toc list

  def populate(self, title, sections):
    self.toc_list.remove_all()

    if sections:
      self.title_label.set_label(title)
      for section in sections:
        row = TocBoxRow(section['anchor'].replace('_', ' '), section['anchor'], section['toclevel'])
        self.toc_list.append(row)
    else:
      self.title_label.set_label('')

  # On list activated load section

  def _list_activated_cb(self, toc_list, row):
    if self._window.panel_split.get_collapsed():
      self._window.panel_split.set_show_sidebar(False)

    self._window.page.wikiview.load_section(row.anchor)


# Section row in toc list

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/gtk/toc-row.ui')
class TocBoxRow(Gtk.ListBoxRow):

  __gtype_name__ = 'TocBoxRow'

  section_label = Gtk.Template.Child()

  # Set label text and indent

  def __init__(self, section, anchor, level):
    super().__init__()
    
    self.anchor = anchor

    if level > 1:
      self.section_label.add_css_class('caption')
    self.section_label.set_label(section)
    self.section_label.set_margin_start(3 + (level - 1) * 15)
