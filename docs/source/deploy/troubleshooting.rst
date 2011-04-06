Lock Problems
-------------

If you are experiencing

 WARNING: Couldn't flush user prefs: java.util.prefs.BackingStoreException: Couldn't get file lock.
 Apr 6, 2011 12:06:46 AM java.util.prefs.FileSystemPreferences checkLockFile0ErrorCode
 WARNING: Could not lock User prefs.  Unix error code 2.
 Apr 6, 2011 12:06:46 AM java.util.prefs.FileSystemPreferences syncWorld


Delete these two files

 /var/lib/tomcat6/webapps/geonetwork/WEB-INF/db/data/DefaultDatabase.lock

 /var/lib/tomcat6/webapps/geonetwork/WEB-INF/lucene/nonspatial/write.lock
