project('wike',
  version: '3.2.0',
  license: 'GPL3+',
  meson_version: '>= 0.60',
  default_options: [ 'warning_level=2', ],
)

gnome = import('gnome')
i18n = import('i18n')
python = import('python')

pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, meson.project_name())

conf = configuration_data()
conf.set('PYTHON', python.find_installation().full_path())
conf.set('VERSION', meson.project_version())
conf.set('BIN', join_paths(get_option('prefix'), get_option('bindir'), meson.project_name()))
conf.set('pkgdatadir', pkgdatadir)
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))

subdir('data')
subdir('src')
subdir('po')

gnome.post_install(
  glib_compile_schemas: true,
  gtk_update_icon_cache: true,
  update_desktop_database: true,
)
