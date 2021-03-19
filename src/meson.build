conf = configuration_data()
conf.set('PYTHON', python.find_installation().path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'wike.in',
  output: 'wike',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

wike_sources = [
  '__init__.py',
  'application.py',
  'bookmarks.py',
  'data.py',
  'header.py',
  'langlinks.py',
  'prefs.py',
  'search.py',
  'toc.py',
  'view.py',
  'wikipedia.py',
  'window.py'
]

install_data(wike_sources, install_dir: moduledir)

