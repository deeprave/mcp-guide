# Implementation Tasks

## 1. Investigation
- [ ] 1.1 Test `guide-agent-install -l` via uvx and document output
- [ ] 1.2 Test `guide-agent-install -l` via direct pip install
- [ ] 1.3 Test `mcp-install` via uvx
- [ ] 1.4 Test `mcp-install` via direct pip install
- [ ] 1.5 Check where agent configuration files are located
- [ ] 1.6 Verify agent configuration files are in package distribution
- [ ] 1.7 Check entry point definitions in `pyproject.toml`
- [ ] 1.8 Trace script execution to find where it fails
- [ ] 1.9 Identify root cause

## 2. Fix Implementation
- [ ] 2.1 Update package data configuration if needed
- [ ] 2.2 Fix entry point definitions if needed
- [ ] 2.3 Fix path resolution in scripts if needed
- [ ] 2.4 Ensure agent config files are included in distribution

## 3. Testing
- [ ] 3.1 Test `guide-agent-install -l` via uvx (should list agents)
- [ ] 3.2 Test `guide-agent-install -l` via pip install
- [ ] 3.3 Test `guide-agent-install <agent>` via uvx
- [ ] 3.4 Test `mcp-install` via uvx
- [ ] 3.5 Test `mcp-install` via pip install
- [ ] 3.6 Verify all installation methods work consistently

## 4. Documentation
- [ ] 4.1 Document correct usage of scripts
- [ ] 4.2 Add troubleshooting section if needed
- [ ] 4.3 Update installation documentation
