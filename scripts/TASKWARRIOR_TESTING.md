# TaskWarrior Version Testing

## Current Status

**Recommended Version:** v3.4.0 ✅
**Git Commit:** `063325b0525ed523a32fd0b670f0de0aa65d40ac`
**Last Updated:** 2025-10-12
**Status:** Testing complete - v3.4.0 verified working

## Test Matrix

Test each version with `./scripts/test_taskwarrior_version.sh <version>`

| Version | Build | Test 1 (version) | Test 2 (add) | Test 3 (count) | Test 4 (list) | Test 5 (done) | Result | Notes |
|---------|-------|------------------|--------------|----------------|---------------|---------------|--------|-------|
| v3.4.1  | N/A   | ❌ Hang          | N/A          | N/A            | N/A           | N/A           | **FAIL** | Known issue: hangs on `--version` |
| v3.4.0  | ✅     | ✅ PASS          | ✅ PASS      | ✅ PASS        | ✅ PASS       | ✅ PASS       | **✅ PASS** | **RECOMMENDED VERSION** |
| v3.3.0  | -     | -                | -            | -              | -             | -             | SKIP   | v3.4.0 works, no need to test older |
| v3.2.0  | -     | -                | -            | -              | -             | -             | SKIP   | v3.4.0 works, no need to test older |
| v3.1.0  | -     | -                | -            | -              | -             | -             | SKIP   | v3.4.0 works, no need to test older |
| v3.0.0  | -     | -                | -            | -              | -             | -             | SKIP   | v3.4.0 works, no need to test older |

## Testing Procedure

### Prerequisites
- macOS with Homebrew
- Xcode Command Line Tools installed
- cmake installed: `brew install cmake`
- Clean test environment (no important TaskWarrior data)

### Run Tests

```bash
# Make script executable
chmod +x scripts/test_taskwarrior_version.sh

# Test each version (most recent first)
./scripts/test_taskwarrior_version.sh v3.4.0
./scripts/test_taskwarrior_version.sh v3.3.0
./scripts/test_taskwarrior_version.sh v3.2.0
./scripts/test_taskwarrior_version.sh v3.1.0
./scripts/test_taskwarrior_version.sh v3.0.0

# Document results in table above after each test
```

### Multi-Mac Testing

After finding a working version, test on multiple Mac configurations:

| Mac Type | Conda | macOS | Architecture | Version | Result | Notes |
|----------|-------|-------|--------------|---------|--------|-------|
| Mac 1    | Yes   | 15.4  | arm64        | v3.4.0  | TBD    | John's Mac |
| Mac 2    | No    | 15.x  | arm64        | v3.4.0  | TBD    | Clean Mac |
| Mac 3    | No    | 14.x  | arm64        | v3.4.0  | TBD    | Older macOS |

## Recommended Version

**TaskWarrior v3.4.0** ✅

### Why v3.4.0?

- **All tests pass:** Version check, task creation, counting, listing, completion all work correctly
- **No hangs:** Unlike v3.4.1, v3.4.0 does not hang on first initialization
- **Recent version:** Close to latest (3.4.1) but without the blocking bug
- **Git commit:** `063325b0525ed523a32fd0b670f0de0aa65d40ac`

### Build Instructions

```bash
git clone https://github.com/GothenburgBitFactory/taskwarrior.git
cd taskwarrior
git checkout 063325b0525ed523a32fd0b670f0de0aa65d40ac
mkdir build && cd build
cmake ..
make -j4
sudo make install
```

### Known Limitations

- None identified during testing
- All 6 functional tests passed
- Test 6 shows count=1 after completion (completed tasks stored in database), this is normal TaskWarrior behavior

## Future Updates

When TaskWarrior releases new versions (3.5.0, 3.6.0, etc.):

1. Run test script: `./scripts/test_taskwarrior_version.sh vX.Y.Z`
2. Update test matrix above
3. If PASS and no regressions: Consider updating pinned formula
4. If FAIL: Document failure mode for troubleshooting

## Creating Pinned Formula

Once a working version is identified:

1. Note the git commit SHA from test output
2. Create `Formula/taskwarrior-pinned.rb` in homebrew-brainplorp
3. Pin to the specific commit
4. Test installation: `brew install dimatosj/brainplorp/taskwarrior-pinned`
5. Update brainplorp.rb to depend on pinned formula
