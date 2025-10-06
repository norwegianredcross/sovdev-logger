# Terchris Workflow Rules

## Purpose

This document defines workflow rules for working on this repository, including LLM assistant guidelines and personal workspace organization.

**Location:** `.terchris/rules-terchris.md` (tracked in git)
**Personal workspace:** `terchris/` directory (never tracked by git)

## Rules for LLMs Working on This Repository

### 1. Never Commit Files from terchris/

**Rule**: The `terchris/` directory must be in `.gitignore` and never committed to the repository.

**Why**: This is a personal workspace for temporary files, experiments, and backups that should not pollute the git history.

**Actions**:
- ✅ Always check `.gitignore` includes `terchris/`
- ✅ If creating backup files, place them in `terchris/backups/`
- ❌ Never use `.backup` extensions in tracked directories (like `docs/file.md.backup`)

### 2. Use terchris/ for Backups

**Rule**: When making risky changes to important files, create backups in `terchris/backups/` first.

**Example**:
```bash
# ❌ DON'T DO THIS (creates tracked backup)
cp docs/logging-data.md docs/logging-data.md.backup

# ✅ DO THIS INSTEAD (untracked backup)
mkdir -p terchris/backups
cp docs/logging-data.md terchris/backups/logging-data.md.backup-2025-10-06
```

**Naming convention for backups**:
- Include date: `filename.ext.backup-YYYY-MM-DD`
- Include purpose if needed: `filename.ext.backup-before-refactor`

### 3. terchris/ Subdirectory Structure

**Suggested organization**:

```
terchris/
├── rules-terchris.md          # This file - workflow rules
├── backups/                   # File backups before major changes
│   ├── logging-data.md.backup-2025-10-06
│   └── logger.ts.backup-before-refactor
├── experiments/               # Code experiments and prototypes
│   ├── new-feature-test/
│   └── alternative-approach/
├── notes/                     # Personal development notes
│   ├── refactoring-plan.md
│   └── api-design-thoughts.md
├── plans-current/             # Current/active planning documents
│   ├── 0summary-plan.md       # MUST be kept up to date
│   ├── github-plan.md
│   └── pivot-dashboards-plan.md
├── plans-archive/             # Completed plans
│   ├── 0summary-archive.md    # Index of archived plans
│   ├── implementation-stages.md
│   └── changes-plan.md
├── temp/                      # Temporary files (can be deleted anytime)
│   ├── test-output.json
│   └── scratch.ts
└── archive/                   # Old work that might be useful later
    └── 2025-10-06-documentation-review/
```

### 4. When to Use terchris/

**Use terchris/ for**:
- ✅ Backup files before major refactoring
- ✅ Experimental code that isn't ready for the main codebase
- ✅ Personal notes and planning documents
- ✅ Implementation plans and status tracking (place in `plans/`)
- ✅ Temporary test files
- ✅ Downloaded resources or references
- ✅ Work-in-progress that might span multiple sessions

**Don't use terchris/ for**:
- ❌ Code that should be committed (use proper directories)
- ❌ Shared documentation (use `docs/`)
- ❌ Test files that should be in version control (use `test/`)
- ❌ Examples for users (use `examples/`)

**Special note on planning documents**:
- Active plans go in `terchris/plans-current/`
- The file `terchris/plans-current/0summary-plan.md` **MUST be kept up to date** at all times
- When a plan is completed, move it to `terchris/plans-archive/` and update both summary files
- Plans useful for all developers can be moved to `docs/` or relevant directory
- Keep work-in-progress plans in `terchris/plans-current/` to avoid cluttering the tracked repository

### 5. Cleanup Policy

**Rule**: Files in `terchris/` can be deleted at any time. Don't rely on them being permanent.

**Organization**:
- `temp/` - Can be cleaned up daily
- `backups/` - Keep for current feature work, clean up after merge
- `experiments/` - Keep until experiment concludes
- `notes/` - Keep as long as useful
- `plans-current/` - Active plans, update `0summary-plan.md` when adding/removing plans
- `plans-archive/` - Completed plans, update `0summary-archive.md` when archiving
- `archive/` - Organize by date, review periodically

### 6. .gitignore Entry

**Required entry** in `.gitignore`:

```gitignore
# Terchris personal working directory (never commit)
terchris/
```

**Verification**:
```bash
# Check terchris is ignored
git check-ignore terchris/
# Should output: terchris/

# Verify nothing from terchris/ is tracked
git ls-files | grep terchris
# Should output nothing
```

### 7. Special Cases

#### Creating Summary Documents

When creating analysis or summary documents during work:

**Option A**: Document is temporary (just for current session)
```bash
# Place in temp/
echo "Summary..." > terchris/temp/documentation-review-summary.md
```

**Option B**: Document is useful reference for repository
```bash
# Create in docs/ if it benefits all developers
echo "Summary..." > docs/MIGRATION-GUIDE.md
git add docs/MIGRATION-GUIDE.md
```

#### Moving Backups to terchris/

If backup files were mistakenly created in tracked directories:

```bash
# Find and move them
find . -name "*.backup" -not -path "./terchris/*" -exec mv {} terchris/backups/ \;

# Or for specific files
mv docs/logging-data.md.backup terchris/backups/
```

### 8. Communication with Developers

**If asked to create backups**:
```markdown
I've created a backup in `terchris/backups/filename.ext.backup-YYYY-MM-DD` before making changes.
```

**If asked where working files are**:
```markdown
Working files are in `terchris/experiments/feature-name/`. These are not tracked by git.
```

**If suggesting cleanup**:
```markdown
Note: The following temporary files in `terchris/temp/` can be deleted:
- file1.txt
- file2.json
Would you like me to clean them up?
```

### 9. Plan Management Workflow

**Rule**: All planning documents must follow a strict archival workflow.

#### Active Plans (plans-current/)

**Requirements**:
- `0summary-plan.md` **MUST be kept up to date** at all times
- Every plan file must have an entry in the summary
- Summary shows: status, purpose, last updated date
- Add new plans → update summary immediately
- Update existing plan → update summary timestamp

#### Archiving Completed Plans

**When to archive**:
- Plan status changes to "COMPLETE"
- All tasks/stages are finished
- No longer actively referenced

**Archive process**:
1. Move plan file: `plans-current/plan-name.md` → `plans-archive/plan-name.md`
2. Add entry to `plans-archive/0summary-archive.md` (most recent first)
3. Remove entry from `plans-current/0summary-plan.md`
4. Update any cross-references in remaining current plans

**Archive entry format**:
```markdown
### [Plan Name] - Archived YYYY-MM-DD
**Original File:** filename.md
**Status:** ✅ Complete
**Completion Date:** YYYY-MM-DD
**What was accomplished:**
- Key achievement 1
- Key achievement 2
**Related Plans:** (if any)
```

#### Example Workflow

```bash
# User completes implementation-stages.md plan
# 1. Move to archive
mv terchris/plans-current/implementation-stages.md terchris/plans-archive/

# 2. Update archive index
# Edit terchris/plans-archive/0summary-archive.md - add entry at top

# 3. Update current plans summary
# Edit terchris/plans-current/0summary-plan.md - remove entry

# 4. Verify
ls terchris/plans-current/   # Should not contain implementation-stages.md
ls terchris/plans-archive/   # Should contain implementation-stages.md
```

## Summary for LLMs

1. **Always use `terchris/` for temporary/personal files**
2. **Never commit anything from `terchris/`**
3. **Create backups in `terchris/backups/` not `*.backup` in tracked dirs**
4. **Verify `.gitignore` includes `terchris/`**
5. **Ask user before deleting files from `terchris/`**
6. **Keep `0summary-plan.md` up to date** - update whenever plans change
7. **Archive completed plans** - move to plans-archive/ and update both summaries

## Repository Context

**Repository**: sovdev-logger
**Purpose**: Multi-language structured logging library
**Owner**: terchris (Terje Christensen)
**Organization**: Norwegian Red Cross (redcross-public)

---

**Note:** This file is tracked in git at `.terchris/rules-terchris.md`. The `terchris/` working directory referenced in these rules is NOT tracked by git.
