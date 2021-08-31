gnome.compile_resources(
  meson.project_name(),
  'com.github.hugolabe.Wike.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir
)

desktop_file = i18n.merge_file(
  input: 'com.github.hugolabe.Wike.desktop.in',
  output: 'com.github.hugolabe.Wike.desktop',
  type: 'desktop',
  po_dir: '../po',
  install: true,
  install_dir: join_paths(get_option('datadir'), 'applications')
)

desktop_utils = find_program('desktop-file-validate', required: false)
if desktop_utils.found()
  test('Validate desktop file', desktop_utils,
    args: [desktop_file]
  )
endif

appstream_file = i18n.merge_file(
  input: 'com.github.hugolabe.Wike.metainfo.xml.in',
  output: 'com.github.hugolabe.Wike.metainfo.xml',
  po_dir: '../po',
  install: true,
  install_dir: join_paths(get_option('datadir'), 'metainfo')
)

appstream_util = find_program('appstream-util', required: false)
if appstream_util.found()
  test('Validate appstream file', appstream_util,
    args: ['validate', appstream_file]
  )
endif

install_data('com.github.hugolabe.Wike.gschema.xml',
  install_dir: join_paths(get_option('datadir'), 'glib-2.0/schemas')
)

compile_schemas = find_program('glib-compile-schemas', required: false)
if compile_schemas.found()
  test('Validate schema file', compile_schemas,
    args: ['--strict', '--dry-run', meson.current_source_dir()]
  )
endif

install_data(
  'com.github.hugolabe.Wike.SearchProvider.ini',
  install_dir: join_paths(get_option('prefix'), get_option('datadir'), 'gnome-shell', 'search-providers')
)

configure_file(
  input: 'com.github.hugolabe.Wike.SearchProvider.service.in',
  output: 'com.github.hugolabe.Wike.SearchProvider.service',
  configuration: conf,
  install: true,
  install_dir: join_paths(get_option('prefix'), get_option('datadir'), 'dbus-1', 'services')
)

icondir = join_paths(get_option('prefix'), get_option('datadir'), 'icons', 'hicolor')
install_data('icons/com.github.hugolabe.Wike.svg', install_dir: join_paths(icondir, 'scalable/apps'))
install_data('icons/com.github.hugolabe.Wike-symbolic.svg', install_dir: join_paths(icondir, 'symbolic/apps'))
install_data('icons/wike-dice-symbolic.svg', install_dir: join_paths(icondir, 'scalable/actions'))
install_data('icons/wike-flag-symbolic.svg', install_dir: join_paths(icondir, 'scalable/actions'))

