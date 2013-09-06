tx set --auto-local -r geonode-docs-test.index 'i18n/<lang>/LC_MESSAGES/index.po' --source-lang en --source-file i18n/pot/index.pot --execute

tx push -s -t
