## 1. Implement missing file comparison in install_file()
- [ ] 1.1 Check if destination file exists
- [ ] 1.2 Use existing `compare_files()` function to check if source and destination match
- [ ] 1.3 Skip copy operation if files are identical (implement spec requirement)
- [ ] 1.4 Return operation status: "installed" (new), "updated" (changed), "unchanged" (skipped)
- [ ] 1.5 Preserve file permissions (st_mode) - already implemented
- [ ] 1.6 Preserve file timestamp (st_mtime) - currently missing
- [ ] 1.7 Preserve existing binary file detection logic

## 2. Add comprehensive tests for install_file()
- [ ] 2.1 Test install_file() installs new file and returns "installed"
- [ ] 2.2 Test install_file() updates changed file and returns "updated"
- [ ] 2.3 Test install_file() skips unchanged file and returns "unchanged"
- [ ] 2.4 Test install_file() skips binary files
- [ ] 2.5 Test install_file() preserves file permissions
- [ ] 2.6 Test install_file() preserves file timestamp (mtime)

## 3. Add E2E tests for install command
- [ ] 3.1 Test running install twice doesn't recopy unchanged files
- [ ] 3.2 Test install reports correct statistics on first run
- [ ] 3.3 Test install reports correct statistics on second run (all unchanged)
- [ ] 3.4 Test install detects and updates changed files
- [ ] 3.5 Test install creates new files correctly

## 4. Update install_templates() to track statistics
- [ ] 4.1 Collect return values from all `install_file()` calls
- [ ] 4.2 Count operations by status (installed/updated/unchanged)
- [ ] 4.3 Return dict with counts: `{"installed": X, "updated": Y, "unchanged": Z}`
- [ ] 4.4 Remove incorrect `files_installed` count

## 5. Update update_templates() statistics format
- [ ] 5.1 Map existing stats (replaced/patched/skipped/conflict) to new format
- [ ] 5.2 Return consistent dict format: `{"installed": X, "updated": Y, "unchanged": Z, "conflicts": W}`
- [ ] 5.3 Ensure backward compatibility with existing behavior

## 6. Add --quiet flag to CLI
- [ ] 6.1 Add `-q`/`--quiet` flag to `mcp-guide-install` command
- [ ] 6.2 Pass quiet flag through to output logic
- [ ] 6.3 Suppress statistics output when quiet=True
- [ ] 6.4 Ensure errors and warnings still display in quiet mode

## 7. Update output formatting
- [ ] 7.1 Format statistics as "X files installed, Y files updated, Z files unchanged"
- [ ] 7.2 Handle singular/plural correctly (1 file vs 2 files)
- [ ] 7.3 Only show non-zero counts in output
- [ ] 7.4 Add conflict reporting for update command if applicable
- [ ] 7.5 Respect quiet flag in all output paths

## 8. Verify all existing tests pass
- [ ] 8.1 Run full test suite
- [ ] 8.2 Verify no regressions in existing installer tests
- [ ] 8.3 Verify no regressions in CLI tests

## 9. Update documentation
- [ ] 9.1 Update CLI help text for --quiet flag
- [ ] 9.2 Update installation documentation with new output format
- [ ] 9.3 Document that unchanged files are skipped in install command
- [ ] 9.4 Clarify difference between install (simple compare) and update (smart diff/patch)
- [ ] 9.5 Add note about bug fix in changelog
