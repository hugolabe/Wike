configure_file(
  input: 'wike.in',
  output: 'wike',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

configure_file(
  input: 'wike-sp.in',
  output: 'wike-sp',
  configuration: conf,
  install: true,
  install_dir: pkgdatadir
)

wike_sources = [
  '__init__.py',
  'application.py',
  'bookmarks.py',
  'data.py',
  'header.py',
  'langlinks.py',
  'menu.py',
  'page.py',
  'prefs.py',
  'search.py',
  'toc.py',
  'view.py',
  'wikipedia.py',
  'window.py'
]

install_data(wike_sources, install_dir: moduledir)

