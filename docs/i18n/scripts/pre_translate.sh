LOCALES='fr it de es'

sphinx-build -b gettext . i18n/pot

# Now iteratively update the locale specific .po files with any new strings needed translation

for LOCALE in ${LOCALES}
do
  # Merge or copy all the updated pot files over to locale specific po files
  for FILE in `find i18n/pot/ -type f -name "*.pot"`
  do
    POTFILE=${FILE}
    POFILE=`echo ${POTFILE} | sed -e 's,\.pot,\.po,' | sed -e 's,pot,'${LOCALE}'/LC_MESSAGES,'`
    if [ -f $POFILE ];
    then
      echo "Updating strings for ${POFILE}"
      msgmerge -U ${POFILE} ${POTFILE}
    else
      echo "Creating ${POFILE}"
      mkdir -p `echo $(dirname ${POFILE})`
      cp ${POTFILE} ${POFILE} 
    fi
  done
done
