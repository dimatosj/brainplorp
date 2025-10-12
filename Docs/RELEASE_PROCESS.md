# brainplorp Release Process

This document describes how to create a new release of brainplorp.

## Prerequisites

- Maintainer access to both repositories:
  - `dimatosj/brainplorp` (main repo)
  - `dimatosj/homebrew-brainplorp` (Homebrew tap)
- GitHub CLI (`gh`) installed (optional, can use GitHub UI)
- All tests passing on `master` branch

---

## Current Release Process (Sprint 10.1+ Wheel-Based)

Starting with v1.6.1, brainplorp uses GitHub Actions to build wheels automatically on version tags.
Maintainer only needs to update version, tag, and update Homebrew formula.

### Step-by-Step

**1. Update Version Numbers**

Edit these files with new version (e.g., `1.6.1`):

```bash
# src/brainplorp/__init__.py
__version__ = "1.6.1"

# pyproject.toml
version = "1.6.1"

# tests/test_smoke.py (update version assertion if present)
assert __version__ == "1.6.1"

# tests/test_cli.py (update version check if present)
assert "1.6.1" in result.output
```

**2. Commit and Tag**

```bash
VERSION="1.6.1"
git add src/brainplorp/__init__.py pyproject.toml tests/test_*.py
git commit -m "Bump version to ${VERSION}"
git tag -a "v${VERSION}" -m "Sprint 10.1: Wheel-based Homebrew distribution"
git push origin master
git push origin "v${VERSION}"
```

**3. Wait for GitHub Actions**

- Go to: https://github.com/dimatosj/brainplorp/actions
- Watch "Release" workflow (triggered by tag push)
- Wait ~2 minutes for wheel to build
- Workflow creates GitHub Release automatically
- Wheel uploaded as release asset: `brainplorp-1.6.1-py3-none-any.whl`

**4. Get Wheel SHA256**

Option A - From GitHub Actions output:
- Click on the "Release" workflow run
- Expand "Calculate SHA256" step
- Copy SHA256 hash from output

Option B - Download and calculate locally:
```bash
VERSION="1.6.1"
curl -L -o brainplorp-${VERSION}-py3-none-any.whl \
  "https://github.com/dimatosj/brainplorp/releases/download/v${VERSION}/brainplorp-${VERSION}-py3-none-any.whl"

shasum -a 256 brainplorp-${VERSION}-py3-none-any.whl
# Output: abc123def456... brainplorp-1.6.1-py3-none-any.whl
```

**5. Update Homebrew Formula**

```bash
cd /opt/homebrew/Library/Taps/dimatosj/homebrew-brainplorp
# OR: cd ~/repos/homebrew-brainplorp

# Edit Formula/brainplorp.rb
vim Formula/brainplorp.rb
```

Update these two lines:
```ruby
url "https://github.com/dimatosj/brainplorp/releases/download/v1.6.1/brainplorp-1.6.1-py3-none-any.whl"
sha256 "abc123def456..."  # SHA256 from step 4
```

Commit and push:
```bash
git add Formula/brainplorp.rb
git commit -m "brainplorp ${VERSION} - Wheel-based distribution"
git push origin master
```

**6. Test Installation**

```bash
# On clean Mac or fresh user account
brew update
brew untap dimatosj/brainplorp  # Clear cache
brew tap dimatosj/brainplorp
brew install brainplorp

# Verify
brainplorp --version  # Should show: brainplorp v1.6.1
brainplorp setup      # Should run without errors
brainplorp mcp        # Should configure Claude Desktop
```

**7. Update CHANGELOG**

```bash
cd ~/repos/brainplorp  # Or wherever brainplorp repo is

vim CHANGELOG.md
```

Example entry:
```markdown
## [1.6.1] - 2025-10-12

### Fixed
- Fixed Homebrew installation hanging on Macs with conda/miniconda
- Switched to wheel-based distribution (5-10x faster installation)

[1.6.1]: https://github.com/dimatosj/brainplorp/releases/tag/v1.6.1
```

Commit:
```bash
git add CHANGELOG.md
git commit -m "Update CHANGELOG for v${VERSION}"
git push origin master
```

**8. Announce Release**

- Post in community channels
- Notify testers of new version
- Update README if needed

### Troubleshooting (Wheel-Based Process)

**Wheel build fails in GitHub Actions:**
- Check Actions logs for Python errors
- Verify `pyproject.toml` is valid
- Ensure all dependencies are in `[project.dependencies]`
- Test locally: `python -m build --wheel`

**Homebrew install fails:**
- Double-check SHA256 matches wheel file exactly
- Verify wheel URL is accessible (test in browser)
- Check formula syntax: `brew audit dimatosj/brainplorp/brainplorp`
- Clear Homebrew cache: `rm -rf ~/Library/Caches/Homebrew/downloads/*brainplorp*`

**Version mismatch:**
- Ensure all 4 files have same version (`__init__.py`, `pyproject.toml`, test files)
- Re-tag if version was wrong:
  ```bash
  git tag -d "v${VERSION}"
  git push origin --delete "v${VERSION}"
  # Fix version, then re-tag
  ```

**Dependencies missing after install:**
- Wheel should include dependency metadata (check `METADATA` file in wheel)
- Homebrew formula installs dependencies via pip automatically
- If missing, verify wheel built correctly: `unzip -l dist/*.whl | grep METADATA`

---

## Legacy Release Process (v1.6.0 and Earlier - Source-Based)

**Note:** This process is deprecated as of Sprint 10.1. Use wheel-based process above for v1.6.1+.

<details>
<summary>Click to expand old source-based release process</summary>

## Release Checklist

### 1. Pre-Release Verification

```bash
# Ensure you're on master and up to date
git checkout master
git pull origin master

# Run full test suite
pytest tests/ -v

# Verify all tests pass (should see 537+)
# Check that version is bumped in both files:
grep "__version__" src/brainplorp/__init__.py
grep "version" pyproject.toml
# Both should show the new version (e.g., "1.6.0")
```

### 2. Create Git Tag

```bash
# Format: vMAJOR.MINOR.PATCH (e.g., v1.6.0)
VERSION="1.6.0"
git tag -a "v${VERSION}" -m "Sprint 10: Mac Installation & Multi-Computer Sync"
git push origin "v${VERSION}"
```

### 3. Create GitHub Release

```bash
# Create release with auto-generated notes
gh release create "v${VERSION}" \
  --title "brainplorp v${VERSION}" \
  --notes "See [CHANGELOG.md](CHANGELOG.md) for details." \
  --verify-tag
```

**Or manually via GitHub UI:**
1. Go to https://github.com/dimatosj/brainplorp/releases/new
2. Choose tag: `v1.6.0`
3. Title: `brainplorp v1.6.0`
4. Description: Link to CHANGELOG.md or paste release notes
5. Click "Publish release"

### 4. Calculate SHA256 for Homebrew Formula

```bash
# Download the release tarball
VERSION="1.6.0"
curl -L "https://github.com/dimatosj/brainplorp/archive/refs/tags/v${VERSION}.tar.gz" -o brainplorp-${VERSION}.tar.gz

# Calculate SHA256
shasum -a 256 brainplorp-${VERSION}.tar.gz

# Output will be something like:
# abc123def456... brainplorp-1.6.0.tar.gz

# Copy the hash (first part before the filename)
```

### 5. Update Homebrew Formula

```bash
# Clone tap repo (if not already cloned)
cd ~/repos  # Or wherever you keep repos
git clone https://github.com/dimatosj/homebrew-brainplorp.git
cd homebrew-brainplorp

# Edit formula
vim Formula/brainplorp.rb
```

**Update these lines:**
```ruby
url "https://github.com/dimatosj/brainplorp/archive/refs/tags/v1.6.0.tar.gz"
sha256 "abc123def456..."  # Paste SHA256 from step 4
```

**Commit and push:**
```bash
git add Formula/brainplorp.rb
git commit -m "brainplorp ${VERSION}"
git push origin master
```

### 6. Test Homebrew Installation

```bash
# On a clean Mac or fresh user account:
brew update
brew tap dimatosj/brainplorp
brew install brainplorp

# Verify
brainplorp --version  # Should print v1.6.0
brainplorp setup      # Should run without errors
```

### 7. Post-Release

**Update CHANGELOG.md:**
```bash
cd ~/repos/brainplorp

# Edit CHANGELOG.md to document release
vim CHANGELOG.md
```

**Example entry:**
```markdown
## [1.6.0] - 2025-10-11

### Added
- Interactive setup wizard (`brainplorp setup`)
- Multi-computer sync support (TaskChampion + iCloud)
- Config validation command (`brainplorp config validate`)
- Homebrew tap for easy installation
- Comprehensive documentation for testers and multi-computer usage

### Changed
- Improved error messages in CLI
- Better vault detection logic

### Fixed
- None

[1.6.0]: https://github.com/dimatosj/brainplorp/releases/tag/v1.6.0
```

**Commit changelog:**
```bash
git add CHANGELOG.md
git commit -m "Update CHANGELOG for v${VERSION}"
git push origin master
```

## Version Numbering

brainplorp follows [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.x.x): Breaking changes
- **MINOR** (x.1.x): New features, backwards compatible
- **PATCH** (x.x.1): Bug fixes only

**Sprint-to-version mapping:**
- Major sprints (8, 9, 10) → MINOR bump (1.4.0 → 1.5.0 → 1.6.0)
- Minor sprints (9.1, 9.2, 9.3) → PATCH bump (1.5.0 → 1.5.1 → 1.5.2)

## Troubleshooting

### Formula fails to install

**Problem:** `brew install brainplorp` fails with SHA256 mismatch

**Solution:**
1. Re-download tarball: `curl -L "https://github.com/dimatosj/brainplorp/archive/refs/tags/v${VERSION}.tar.gz" -o test.tar.gz`
2. Recalculate SHA: `shasum -a 256 test.tar.gz`
3. Update formula with correct SHA
4. Force update: `brew update && brew reinstall brainplorp`

### Version mismatch

**Problem:** `brainplorp --version` shows wrong version after release

**Solution:**
1. Verify version in `src/brainplorp/__init__.py`
2. Verify version in `pyproject.toml`
3. Ensure tag was created from correct commit
4. Reinstall: `brew reinstall brainplorp`

### Dependencies not installing

**Problem:** Homebrew doesn't install Python dependencies

**Solution:**
1. Check `pyproject.toml` has correct dependencies listed
2. Verify formula uses `virtualenv_install_with_resources`
3. May need to add explicit `resource` blocks in formula for each dependency

## Quick Reference

```bash
# Full release in one script
VERSION="1.6.0"

# 1. Tag and release
git tag -a "v${VERSION}" -m "Sprint 10: Mac Installation & Multi-Computer Sync"
git push origin "v${VERSION}"
gh release create "v${VERSION}" --title "brainplorp v${VERSION}" --notes "See CHANGELOG.md"

# 2. Get SHA
curl -L "https://github.com/dimatosj/brainplorp/archive/refs/tags/v${VERSION}.tar.gz" | shasum -a 256

# 3. Update formula (manual)
cd ../homebrew-brainplorp
vim Formula/brainplorp.rb  # Update URL and SHA256
git commit -am "brainplorp ${VERSION}"
git push

# 4. Test
brew update && brew reinstall brainplorp
brainplorp --version
```

## Emergency Rollback

If a release has critical bugs:

```bash
# 1. Delete GitHub release
gh release delete "v${VERSION}" --yes

# 2. Delete tag
git push origin --delete "v${VERSION}"
git tag -d "v${VERSION}"

# 3. Revert Homebrew formula
cd ../homebrew-brainplorp
git revert HEAD
git push

# 4. Fix bugs, then re-release as PATCH version
# e.g., 1.6.0 had bugs → fix and release as 1.6.1
```

## Notes

- **Never force-push tags** - tags are immutable by convention
- **Test on clean Mac** before announcing release publicly
- **Update docs first** - release process assumes docs are ready
- **Homebrew caches** - use `brew update` to refresh tap

</details>

---

**Last Updated:** 2025-10-12 (Sprint 10.1 - Wheel-based distribution)
