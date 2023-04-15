# This file is part of Wike (com.github.hugolabe.Wike)
# SPDX-FileCopyrightText: 2021-23 Hugo Olabera <hugolabe@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later


import json, urllib.parse

from gi.repository import GLib, Gtk, Adw


# Box for toc (table of contents) in sidebar

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/ui/toc.ui')
class TocBox(Gtk.Box):

  __gtype_name__ = 'TocBox'

  title_label = Gtk.Template.Child()
  toc_list = Gtk.Template.Child()
  toc_scroller = Gtk.Template.Child()
  toc_separator = Gtk.Template.Child()
  
  # Initialize widgets and connect signals

  def __init__(self, window):
    super().__init__()

    self._window = window
    
    self.toc_list.connect('row-activated', self._list_activated_cb)
    self.toc_scroller.get_vadjustment().connect('value-changed', self._toc_scrolled_cb)
    
  # Populate toc list

  def populate(self, title, sections):
    self.toc_scroller.get_vadjustment().set_value(0)
    self.title_label.set_markup('<big>' + GLib.markup_escape_text(title, -1) + '</big>')

    while True:
      row = self.toc_list.get_row_at_index(0)
      if row:
        self.toc_list.remove(row)
      else:
        break

    if sections:
      self.title_label.set_visible(True)
      for section in sections:
        row = TocBoxRow(section['anchor'].replace('_', ' '), section['anchor'], section['toclevel'])
        self.toc_list.append(row)
    else:
      self.title_label.set_visible(False)

  # On list activated load section

  def _list_activated_cb(self, toc_list, row):
    if self._window.flap.get_fold_policy() == Adw.FlapFoldPolicy.ALWAYS:
      self._window.flap.set_reveal_flap(False)

    self._window.page.wikiview.load_section(row.anchor)

  # Show/hide separator on scroll

  def _toc_scrolled_cb(self, adjustment):
    if adjustment.get_value() > 0:
      self.toc_separator.set_visible(True)
    else:
      self.toc_separator.set_visible(False)


# Section row in toc list

@Gtk.Template(resource_path='/com/github/hugolabe/Wike/ui/toc-row.ui')
class TocBoxRow(Gtk.ListBoxRow):

  __gtype_name__ = 'TocBoxRow'

  section_label = Gtk.Template.Child()

  # Set label text and indent

  def __init__(self, section, anchor, level):
    super().__init__()
    
    self.anchor = anchor
    section_markup = GLib.markup_escape_text(section, -1)

    if level > 1:
      section_markup = '<small>' + section_markup + '</small>'
    self.section_label.set_markup(section_markup)
    self.section_label.set_margin_start(3 + (level - 1) * 15)
