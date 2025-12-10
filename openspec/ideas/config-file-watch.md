Implement a watcher asyncio task that periodically checks the mtime and inode of the
configuration file to detect external changes.

If change is detected it must inform ConfigManager who will then iterate through all
available sessions and notify them also.

This system will require careful thought as it has a potential to cause a "storm" of
configuration file reading from all active sessions.

Perhaps it is better to separate the loading functionality so that while the watcher
is running it caches the config file itself and handles all local reads until the next
change is detected, or the cache is invalidated when the config file is saved.
So, on change, all the sessions will get their data from the cache unless and until
the config file is changed again.

