## MODIFIED Requirements
### Requirement: Async File Operations
The system SHALL use `anyio.Path` for all asynchronous file I/O operations.
File reads and writes MUST execute open-read/write-close atomically in a single
thread call to prevent file handle leaks on task cancellation.

The system MUST NOT depend on `aiofiles`.

#### Scenario: Text file read
- **WHEN** a text file is read asynchronously
- **THEN** `anyio.Path.read_text()` is used
- **AND** the file handle is closed atomically within the thread call

#### Scenario: Binary file read
- **WHEN** a binary file is read asynchronously
- **THEN** `anyio.Path.read_bytes()` is used
- **AND** the file handle is closed atomically within the thread call

#### Scenario: File write
- **WHEN** a file is written asynchronously
- **THEN** `anyio.Path.write_text()` or `anyio.Path.write_bytes()` is used
- **AND** the file handle is closed atomically within the thread call

#### Scenario: File stat
- **WHEN** file metadata is queried asynchronously
- **THEN** `anyio.Path.stat()` is used instead of `aiofiles.os.stat()`
