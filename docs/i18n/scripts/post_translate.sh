LOCALES='fr it de es'

for LOCALE in ${LOCALES}
do
  for POFILE in `find i18n/${LOCALE}/LC_MESSAGES/ -type f -name '*.po'`
  do
    MOFILE=`echo ${POFILE} | sed -e 's,\.po,\.mo,'`
    # Compile the translated strings
    echo "Compiling messages to ${MOFILE}"
    msgfmt --statistics -o ${MOFILE} ${POFILE}
  done
done
