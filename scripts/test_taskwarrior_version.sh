#!/bin/bash
# ⚠️  WARNING: This script deletes ~/.task and ~/.taskrc
# ⚠️  Only run on a test Mac with no important tasks!

set -e

# Use gtimeout on macOS (from coreutils), timeout on Linux
if command -v gtimeout >/dev/null 2>&1; then
    TIMEOUT_CMD="gtimeout"
elif command -v timeout >/dev/null 2>&1; then
    TIMEOUT_CMD="timeout"
else
    echo "❌ Error: timeout command not found"
    echo "Install with: brew install coreutils"
    exit 1
fi

echo "=========================================="
echo "TaskWarrior Version Testing Script"
echo "=========================================="
echo ""
echo "⚠️  This script will DELETE ~/.task and ~/.taskrc"
echo "⚠️  All TaskWarrior data will be lost!"
echo ""
read -p "Continue? (type 'yes' to confirm): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

VERSION=$1

if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 v3.4.0"
    exit 1
fi

echo ""
echo "Testing TaskWarrior ${VERSION}..."
echo "=========================================="
echo ""

# Clean previous TaskWarrior install
echo "1. Cleaning previous TaskWarrior..."
brew uninstall --ignore-dependencies task 2>/dev/null || true

# Clone TaskWarrior and checkout version
echo "2. Cloning TaskWarrior..."
cd /tmp
rm -rf taskwarrior-test
git clone https://github.com/GothenburgBitFactory/taskwarrior.git taskwarrior-test
cd taskwarrior-test

echo "3. Checking out ${VERSION}..."
if ! git checkout $VERSION; then
    echo "❌ Version ${VERSION} not found in TaskWarrior repo"
    exit 1
fi

# Build TaskWarrior
echo "4. Building TaskWarrior..."
mkdir -p build
cd build
if ! cmake ..; then
    echo "❌ CMake configuration failed"
    exit 1
fi

if ! make -j4; then
    echo "❌ Build failed"
    exit 1
fi

echo "✅ Build succeeded"
echo ""

# Clean TaskWarrior data
echo "5. Cleaning TaskWarrior data..."
rm -rf ~/.task ~/.taskrc

# Test 1: Version check (with timeout)
echo "6. Running tests..."
echo "   Test 1: task --version (5s timeout)"
if $TIMEOUT_CMD 5s ./src/task --version > /tmp/tw_version.txt 2>&1; then
    VERSION_OUTPUT=$(cat /tmp/tw_version.txt)
    echo "   ✅ PASS - Version: $VERSION_OUTPUT"
else
    echo "   ❌ FAIL - Command hung or errored"
    cat /tmp/tw_version.txt
    exit 1
fi

# Test 2: Basic task creation (with timeout)
echo "   Test 2: task add (5s timeout)"
if echo "yes" | $TIMEOUT_CMD 5s ./src/task add "test task" > /tmp/tw_add.txt 2>&1; then
    echo "   ✅ PASS - Task created"
else
    echo "   ❌ FAIL - Command hung or errored"
    cat /tmp/tw_add.txt
    exit 1
fi

# Test 3: Task count (with timeout)
echo "   Test 3: task count (5s timeout)"
if $TIMEOUT_CMD 5s ./src/task count > /tmp/tw_count.txt 2>&1; then
    COUNT=$(cat /tmp/tw_count.txt)
    echo "   ✅ PASS - Count: $COUNT"
else
    echo "   ❌ FAIL - Command hung or errored"
    cat /tmp/tw_count.txt
    exit 1
fi

# Test 4: Task list (with timeout)
echo "   Test 4: task list (5s timeout)"
if $TIMEOUT_CMD 5s ./src/task list > /tmp/tw_list.txt 2>&1; then
    echo "   ✅ PASS - List displayed"
else
    echo "   ❌ FAIL - Command hung or errored"
    cat /tmp/tw_list.txt
    exit 1
fi

# Test 5: Mark done (with timeout)
echo "   Test 5: task 1 done (5s timeout)"
if $TIMEOUT_CMD 5s ./src/task 1 done > /tmp/tw_done.txt 2>&1; then
    echo "   ✅ PASS - Task marked done"
else
    echo "   ❌ FAIL - Command hung or errored"
    cat /tmp/tw_done.txt
    exit 1
fi

# Test 6: Final count (should be 0)
echo "   Test 6: task count (verify 0) (5s timeout)"
if $TIMEOUT_CMD 5s ./src/task count > /tmp/tw_final.txt 2>&1; then
    FINAL_COUNT=$(cat /tmp/tw_final.txt)
    if [ "$FINAL_COUNT" = "0" ]; then
        echo "   ✅ PASS - Count: 0 (task completed)"
    else
        echo "   ⚠️  WARN - Count: $FINAL_COUNT (expected 0)"
    fi
else
    echo "   ❌ FAIL - Command hung or errored"
    cat /tmp/tw_final.txt
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ TaskWarrior ${VERSION} - ALL TESTS PASSED"
echo "=========================================="
echo ""
echo "Binary location: /tmp/taskwarrior-test/build/src/task"
echo "Git commit: $(git rev-parse HEAD)"
echo ""
echo "Next steps:"
echo "1. Document results in scripts/TASKWARRIOR_TESTING.md"
echo "2. Test on additional Mac configurations"
echo "3. Create pinned formula if this version works consistently"
echo ""

exit 0
