## 1. Hash Calculation
- [x] 1.1 Add path hash calculation utility function
- [x] 1.2 Extract full path from MCP list/roots or PWD
- [x] 1.3 Generate SHA256 hash from absolute path
- [x] 1.4 Create short hash (8 characters) for key generation

## 2. Configuration Structure
- [x] 2.1 Update project configuration schema
- [x] 2.2 Add name and hash properties to project objects
- [x] 2.3 Generate keys as `{name}-{short-hash}` format
- [x] 2.4 Maintain backward compatibility for reading

## 3. Project Resolution
- [x] 3.1 Update project lookup to handle hash-suffixed keys
- [x] 3.2 Implement hash verification during project resolution
- [x] 3.3 Support user-friendly project names in commands
- [x] 3.4 Handle hash mismatches (project moved/renamed)

## 4. Migration Logic
- [x] 4.1 Detect legacy configuration format
- [x] 4.2 Calculate hashes for existing projects
- [x] 4.3 Convert dictionary keys to hash-suffixed format
- [x] 4.4 Preserve all existing project data during migration

## 5. Testing
- [x] 5.1 Test hash calculation consistency
- [x] 5.2 Test project resolution with multiple same-named projects
- [x] 5.3 Test migration from legacy format
- [x] 5.4 Test hash verification and mismatch handling
- [x] 5.5 Test user interface remains unchanged
