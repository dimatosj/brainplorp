# Sprint 5 Q&A Resolution Summary

**Date:** October 6, 2025
**Sprint:** Sprint 5 (Note Linking)
**Total Questions:** 13
**Status:** All RESOLVED ✅

---

## Summary

All 13 engineering questions for Sprint 5 have been resolved with detailed implementation guidance. The decisions balance:
- **User experience** (clear errors, helpful messages)
- **Data integrity** (validation, no broken links)
- **Cross-platform compatibility** (Windows path handling)
- **Consistency** (with Sprint 3 and Sprint 4 patterns)
- **Simplicity** (start simple, enhance later if needed)

---

## Decisions Summary

### Engineering Decisions (Made by PM/Architect)

**Q5: Path normalization** → YES, normalize paths
- Use `.as_posix()` for forward slashes
- Handle `./notes/` vs `notes/` variations

**Q6: Error handling** → Document common exceptions, let others propagate
- Document `FileNotFoundError` in docstrings
- Trust Python's error messages for edge cases

**Q8: Notes outside vault** → Refuse to link with clear error
- Only allow notes inside vault
- Resolve symlinks first

**Q10: Testing Sprint 4** → Mock for unit tests
- Let Python ImportError happen naturally if Sprint 4 incomplete

**Q13: Sprint 4 verification** → Assume complete, fail naturally
- No custom verification needed

---

### PM/Product Decisions (Using Recommendations)

**Q1: YAML formatting** → Block style, preserve order, keep BaseLoader
- Consistency with Sprint 3
- More readable in Obsidian

**Q2: Front matter creation** → No default fields, no blank line
- Minimal approach
- Consistent with Sprint 4

**Q3: UUID validation** → YES, validate
- Prevents broken links
- Clear errors immediately
- Data integrity > speed

**Q4: Annotation prefix** → Use `"plorp:note:"`
- Prevents conflicts with user annotations
- Clear namespace ownership
- Forward slashes for cross-platform

**Q7: Note types** → Document from Sprint 4
- meeting → vault/meetings/
- others → vault/notes/

**Q9: Unlinking warning** → YES, print warning
- Sets expectations
- Provides instructions
- Better UX

**Q11: Title sanitization** → Sanitize (replace unsafe chars with `-`)
- Just works, no friction
- Cross-platform safety
- User informed if changed

**Q12: Field naming** → Keep `tasks`
- Simple and clear
- Low conflict risk
- Can namespace later if needed

---

## Key Implementation Patterns Established

### 1. Annotation Format
```python
# TaskWarrior annotations use:
"plorp:note:path/to/note.md"

# Parsing:
if annotation.startswith('plorp:note:'):
    relative_path = annotation[11:]  # Remove prefix
```

### 2. Path Normalization
```python
# Always use forward slashes
normalized_path = str(relative_path.as_posix())

# Compare normalized paths for duplicates
```

### 3. UUID Validation
```python
# Validate before adding to front matter
task = get_task_info(task_uuid)
if not task:
    raise ValueError(f"Task not found: {task_uuid}")
```

### 4. Title Sanitization
```python
# Replace unsafe chars
unsafe_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
for char in unsafe_chars:
    title = title.replace(char, '-')
```

### 5. YAML Handling
```python
# Consistent with Sprint 3
yaml.dump(fm, default_flow_style=False, sort_keys=False)
yaml.load(parts[1], Loader=yaml.BaseLoader)
```

---

## Cross-Sprint Consistency

### Maintained from Previous Sprints:

**From Sprint 3:**
- YAML handling with BaseLoader
- Block style formatting
- No field sorting

**From Sprint 4:**
- Note directory structure (meetings/ vs notes/)
- Front matter format
- Auto-creation patterns

---

## For Sprint 5 Engineering Instance

All questions resolved with implementation code. Key points:

1. **Validate UUIDs** before adding to notes (Q3)
2. **Use `plorp:note:` prefix** for annotations (Q4)
3. **Normalize paths** to forward slashes (Q4, Q5)
4. **Sanitize titles** in CLI (Q11)
5. **Print warning** when unlinking (Q9)
6. **Keep front matter minimal** (Q2)
7. **Use `tasks` field name** (Q12)
8. **Refuse notes outside vault** (Q8)

All implementation details are in the Sprint 5 Q&A section with code examples.

---

## Ready for Implementation

Sprint 5 spec is complete with:
- ✅ All 13 questions resolved
- ✅ Implementation code provided
- ✅ Rationale documented
- ✅ Cross-platform considerations addressed
- ✅ Consistency with previous sprints maintained
- ✅ Sprint 4 verified complete (149 tests passing, 91% coverage)

**Sprint 5 can begin immediately.**

---

**Document Version:** 1.0
**Last Updated:** October 6, 2025
