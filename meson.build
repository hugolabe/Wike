project('wike',
  version: '1.5.4',
  license: 'GPL3+',
  meson_version: '>= 0.50.0',
  default_options: [ 'warning_level=2', ],
)

gnome = import('gnome')
i18n = import('i18n')
python = import('python')

pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, meson.project_name())

conf = configuration_data()
conf.set('PYTHON', python.find_installation().path())
conf.set('VERSION', meson.project_version())
conf.set('BIN', join_paths(get_option('prefix'), get_option('bindir'), meson.project_name()))
conf.set('pkgdatadir', pkgdatadir)
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))

subdir('data')
subdir('src')
subdir('po')

meson.add_install_script('build-aux/meson/postinstall.py')
