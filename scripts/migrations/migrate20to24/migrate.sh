# migration steps
# 1. run migration scripts
# 2. run updatelayers

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

python $DIR/migrate_people.py
python $DIR/migrate_account.py
python $DIR/migrate_avatars.py
python $DIR/migrate_resourcebases.py
python $DIR/migrate_layers.py
python $DIR/migrate_attributes.py
python $DIR/migrate_maps.py
python $DIR/migrate_maplayers.py
python $DIR/migrate_documents.py
python $DIR/migrate_contactroles.py

# things not being migrated, PR are welcome :)
# actstream, agon_ratings, announcements, dialogos, notifications, messages
