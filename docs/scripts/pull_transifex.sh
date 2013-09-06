LOCALES='fr it de es'

for LOCALE in ${LOCALES}
do
  for FILE in `find translations/ -type f -name "*.po"`
  do
    INDIR=$(dirname $FILE)
    FILENAME=$(basename $FILE)
    echo "Copying file ${FILENAME} from ${INDIR} to ... as ..."
  done
done
