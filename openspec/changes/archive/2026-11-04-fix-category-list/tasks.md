# Tasks

## 1. Fix file discovery

- [x] 1.1 Make `discover_document_files` return an empty `FileInfoList` with a debug log when the base directory is missing or not a directory, while retaining the absolute-path `ValueError` and errors on existing unreadable directories.
