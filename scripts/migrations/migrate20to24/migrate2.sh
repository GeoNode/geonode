python $DIR/create_auth_group_and_update_res.py
# here add your script to migrate other resourcebase based models
# now contacts, tags, regions and permissions
python $DIR/migrate_tags.py
python $DIR/migrate_regions.py
python $DIR/migrate_user_permissions.py
python $DIR/migrate_group_permissions.py
