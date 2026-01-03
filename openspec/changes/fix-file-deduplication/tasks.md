## 1. Investigation
- [x] 1.1 Identify the exact location of file deduplication logic
- [x] 1.2 Understand current deduplication key implementation
- [x] 1.3 Create test cases that reproduce the bug

## 2. Implementation
- [x] 2.1 Update deduplication logic to use full relative path instead of basename
- [x] 2.2 Ensure path normalization handles different directory separators
- [x] 2.3 Update any related documentation or comments

## 3. Testing
- [x] 3.1 Add unit tests for deduplication with same basenames from different paths
- [x] 3.2 Test collection processing with overlapping filenames
- [x] 3.3 Verify no regression in existing functionality

## 4. Validation
- [x] 4.1 Test with real collection data that has duplicate basenames
- [x] 4.2 Confirm all expected files are now included in processing
- [x] 4.3 Verify performance impact is minimal
