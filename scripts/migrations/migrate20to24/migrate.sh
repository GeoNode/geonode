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
python $DIR/create_auth_group_and_update_res.py
# here add your script to migrate other resourcebase based models
# now contacts, tags, regions and permissions
python $DIR/migrate_contactroles.py
python $DIR/migrate_tags.py
python $DIR/migrate_regions.py
python $DIR/migrate_user_permissions.py
python $DIR/migrate_group_permissions.py

# things not being migrated, PR are welcome :)
# actstream, agon_ratings, announcements, dialogos, notifications, messages
