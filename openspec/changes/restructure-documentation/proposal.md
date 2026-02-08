# Change: Restructure documentation for clarity and PyPI visibility

## Why

Current documentation mixes informative and instructive content in README.md, making it:
- Too long and overwhelming for new users
- Not optimized for PyPI display where it's most visible
- Lacking a cohesive structure that links user docs, setup guides, and release notes

Need to separate concerns:
- README.md should be informative (what/why) and PyPI-suitable
- Setup/configuration docs should be instructive (how)
- CHANGELOG.md should provide feature-based release notes

## What Changes

- Create CHANGELOG.md with initial 1.0.0 release notes
  - Brief overview of mcp-guide capabilities
  - Transport modes (STDIO, HTTP, HTTPS)
  - Key features list
  - Not user documentation, but a succinct snapshot
- Refactor README.md to be informative, not instructive
  - Elevator pitch and key features
  - Brief installation and quick example
  - Links to detailed documentation
  - Suitable for PyPI display
- Create docs/SETUP.md or docs/GETTING-STARTED.md
  - Detailed installation and configuration
  - Transport mode setup guides
  - Docker deployment instructions
  - Environment variables reference
  - Troubleshooting
- Link all documentation together cohesively
  - Cross-reference between README, setup docs, and user docs
  - Integrate with existing user-documentation-updates content

## Impact

- Affected specs: documentation
- Affected code: None (documentation only)
- Dependencies: Should be done after user-documentation-updates for cohesive linking
- Users get clearer, better-organized documentation
- PyPI page becomes more effective for discovery
- Release notes provide feature-based summaries
