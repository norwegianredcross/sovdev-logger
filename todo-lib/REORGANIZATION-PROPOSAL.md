# todo-lib Reorganization Proposal

**Problem**: Current structure assumes todo-lib is Python-only
**Goal**: Make it easy to create implementation guides for PHP, C#, Go, Rust, Java

---

## Proposed Structure

```
todo-lib/
├── README.md                           # Index of all language guides
├── TEMPLATE.md                         # Guide for creating new language guides
│
├── python/
│   ├── README.md                       # Python guide index
│   ├── QUICK-START.md                  # Step-by-step checklist (4-8 hours)
│   ├── implementation-guide.md         # Complete technical reference
│   ├── otel-research.md                # OpenTelemetry research for Python
│   └── specification-gaps.md           # Gaps identified and resolved
│
├── php/
│   ├── README.md
│   ├── QUICK-START.md
│   ├── implementation-guide.md
│   ├── otel-research.md
│   └── specification-gaps.md
│
├── csharp/
│   ├── README.md
│   ├── QUICK-START.md
│   ├── implementation-guide.md
│   ├── otel-research.md
│   └── specification-gaps.md
│
├── go/
│   ├── README.md
│   ├── QUICK-START.md
│   ├── implementation-guide.md
│   ├── otel-research.md
│   └── specification-gaps.md
│
├── rust/
│   └── (same structure)
│
└── java/
    └── (same structure)
```

---

## Document Templates

### 1. README.md (Language-specific index)

**Purpose**: Overview of implementation guides for a specific language

**Content**:
- Documents in this folder
- Implementation workflow
- Key decisions made (logging library, flush pattern, etc.)
- Dependencies
- Time estimates
- References to specification

**Example**: Current `python/README.md`

---

### 2. QUICK-START.md (Execution checklist)

**Purpose**: Step-by-step implementation checklist with time estimates

**Content**:
- Pre-implementation checklist
- Phase 1: Setup (30 min)
- Phase 2: Core Implementation (4-6 hours)
- Phase 3: Testing (1-2 hours)
- Phase 4: Package and Documentation (1 hour)
- Completion checklist
- Time tracking table
- References to detailed guides

**Key principle**: Pure checklist, references other documents for details

**Example**: Current `python/QUICK-START.md`

---

### 3. implementation-guide.md (Complete technical reference)

**Purpose**: Comprehensive technical reference with all code examples

**Content**:
1. Overview (goals, key differences from other languages)
2. Dependencies (packages, versions, installation)
3. Architecture (triple output pattern)
4. OpenTelemetry Integration (provider initialization)
5. Logging Library Selection (rationale and setup)
6. API Signatures (language-specific types and examples)
7. Module Structure (how to organize code)
8. Implementation Patterns (common code patterns)
9. File Rotation (language-specific approach)
10. Exception Handling (language-specific patterns)
11. Testing (test structure and E2E example code)
12. Complete Example (full implementation skeleton)

**Key principle**: Self-contained technical reference

**Example**: Current `python/python-implementation-guide.md`

---

### 4. otel-research.md (OpenTelemetry research)

**Purpose**: Document research on OpenTelemetry SDK for this language

**Content**:
- Executive summary (key findings)
- OpenTelemetry SDK overview (version, installation, patterns)
- Logging library comparison (equivalent to Winston/pino/etc.)
- Integration patterns (how professionals use OTEL in this language)
- Provider initialization patterns
- Flush patterns (async vs sync)
- Performance considerations
- Decision rationale (why we chose specific approaches)

**Key principle**: Documents WHY, not just WHAT

**Example**: Current `python/python-otel-research.md`

---

### 5. specification-gaps.md (Gap analysis)

**Purpose**: Document specification gaps identified during research

**Content**:
- Executive summary (how many gaps, all resolved?)
- Gap 1: [Issue] - Resolution
- Gap 2: [Issue] - Resolution
- ...
- Specification updates needed
- Language-specific notes

**Key principle**: Historical record of decisions

**Example**: Current `python/python-specification-gaps.md`

---

## Top-Level README.md

**Purpose**: Index all language implementation guides

**Content**:
```markdown
# Implementation Guides (todo-lib)

This folder contains language-specific implementation guides for sovdev-logger.

## Available Languages

| Language | Status | Time Estimate | Key Library |
|----------|--------|---------------|-------------|
| [Python](python/) | ✅ Complete | 8-10 hours | stdlib logging + python-json-logger |
| [TypeScript](typescript/) | ✅ Complete | 6-8 hours | Winston |
| [PHP](php/) | 🚧 In Progress | 8-10 hours | Monolog + OpenTelemetry |
| [C#](csharp/) | 📝 Planned | 8-10 hours | Microsoft.Extensions.Logging |
| [Go](go/) | 📝 Planned | 6-8 hours | slog + OpenTelemetry |
| [Rust](rust/) | 📝 Planned | 8-10 hours | tracing + opentelemetry |
| [Java](java/) | 📝 Planned | 8-10 hours | Log4j2 + OpenTelemetry |

## How to Use These Guides

1. **Read the specification first**: `specification/` folder contains language-agnostic concepts
2. **Choose your language**: Navigate to `{language}/` folder
3. **Start with QUICK-START.md**: Follow the step-by-step checklist
4. **Reference implementation-guide.md**: For detailed technical information
5. **Test with specification tools**: Use `specification/tools/` for validation

## Creating a New Language Guide

See [TEMPLATE.md](TEMPLATE.md) for instructions on creating implementation guides for new languages.

## Key Principles

- ✅ **Specification is source of truth**: Language guides reference specification, don't duplicate
- ✅ **Language-specific only**: Only document what's different for this language
- ✅ **Research before implementation**: Understand OpenTelemetry SDK patterns for the language
- ✅ **Professional patterns**: Use logging libraries and patterns that professional developers use
- ✅ **Tested and validated**: All guides include E2E tests and validation with specification tools
```

---

## TEMPLATE.md (Guide for creating new language guides)

**Purpose**: Step-by-step process for creating implementation guides for a new language

**Content**:
```markdown
# Creating Implementation Guides for New Languages

This document explains how to create a complete set of implementation guides for a new language.

## Process Overview

**Time estimate**: 2-3 days (research + writing)

1. Research Phase (4-6 hours)
2. Gap Analysis (2-3 hours)
3. Guide Writing (8-10 hours)
4. Validation (2-3 hours)

---

## Step 1: Research Phase

**Goal**: Understand how professional developers use OpenTelemetry in this language

### 1.1 OpenTelemetry SDK Research

**Research questions:**
- What is the latest OpenTelemetry SDK version?
- What are the required packages?
- How do professionals initialize providers (Logs, Metrics, Traces)?
- Is flush() async or sync?
- What is the default batch size and timeout?
- How do you parse OTLP headers from environment variables?

**Resources:**
- OpenTelemetry official documentation
- GitHub examples in opentelemetry-{language}
- Stack Overflow patterns
- Real-world projects using OpenTelemetry

**Document findings in**: `{language}/otel-research.md`

### 1.2 Logging Library Research

**Research questions:**
- What is the equivalent of Winston/pino in this language?
- What logging libraries are most popular?
- Which library has native OpenTelemetry integration?
- Does it support structured logging (JSON)?
- Does it support file rotation?
- Can it output to multiple destinations simultaneously?

**Comparison matrix:**
| Library | OTEL Integration | JSON Support | File Rotation | Popularity | Learning Curve |
|---------|------------------|--------------|---------------|------------|----------------|
| Library A | ✅ Native | ✅ Built-in | ✅ Built-in | Very High | Low |
| Library B | ⚠️ Manual | ✅ Plugin | ❌ Manual | High | Medium |
| Library C | ❌ None | ✅ Built-in | ✅ Built-in | Medium | High |

**Decision criteria:**
1. Native OpenTelemetry integration (highest priority)
2. JSON support for structured logging
3. File rotation (or easy to add)
4. Familiarity to developers in this language
5. Active maintenance and community

**Document findings in**: `{language}/otel-research.md`

### 1.3 Language Patterns Research

**Research questions:**
- Module system: How do you export functions? (exports, __all__, pub, etc.)
- Async patterns: Does this language prefer async/sync for IO operations?
- Error handling: Exceptions vs Result types vs error returns?
- Type system: Static typing with inference? Duck typing? Explicit types?
- Naming conventions: camelCase, snake_case, PascalCase?

**Document findings in**: `{language}/otel-research.md`

---

## Step 2: Gap Analysis

**Goal**: Identify what the specification doesn't cover for this language

### 2.1 Read Specification with Language Lens

Read these specification files:
- `specification/01-api-contract.md`
- `specification/02-field-definitions.md`
- `specification/06-test-scenarios.md`

For each section, ask:
- ❓ "How would this work in {language}?"
- ❓ "Does the specification explain this for {language}?"
- ❓ "What language-specific details are missing?"

### 2.2 Common Gaps

**Typical gaps found:**
1. **Async vs Sync**: Is sovdev_flush() async or sync?
2. **Error Types**: What exception type to use?
3. **Module Pattern**: How to structure module exports?
4. **Type Annotations**: What type hints to use?
5. **Null Handling**: How to represent "null" in JSON serialization?
6. **File Rotation**: What library or pattern to use?
7. **OpenTelemetry Headers**: How to parse JSON from env var?
8. **Naming Convention**: camelCase vs snake_case for function names?

### 2.3 Document Gaps

**For each gap, document:**
- Gap title (brief)
- Why it's a gap (what's unclear)
- Research finding (what you discovered)
- Resolution (decision made)
- Code example (if applicable)

**Document in**: `{language}/specification-gaps.md`

---

## Step 3: Write Implementation Guide

**Goal**: Create comprehensive technical reference

### 3.1 implementation-guide.md Structure

Use this exact structure (see `python/implementation-guide.md` as template):

1. **Overview**
   - Goals
   - Key differences from TypeScript (table format)

2. **Dependencies**
   - Required packages with versions
   - Installation commands
   - Version support (minimum, recommended)

3. **Architecture**
   - Triple output pattern diagram
   - Benefits

4. **OpenTelemetry Integration**
   - Provider initialization code
   - Resource configuration
   - Batch processing setup

5. **Logging Library Selection**
   - Decision and rationale
   - Setup pattern code

6. **API Signatures**
   - Language-specific type signatures
   - Docstrings with examples

7. **Module Structure**
   - Pattern explanation (exports, module-level functions, etc.)
   - Complete code example

8. **Implementation Patterns**
   - create_peer_services pattern
   - JSON serialization
   - Peer service resolution

9. **File Rotation**
   - Configuration code
   - Rotation behavior explanation

10. **Exception Handling**
    - Exception processing code
    - Credential removal patterns
    - Stack trace limiting

11. **Testing**
    - Test structure
    - E2E test code example
    - Reference to specification tools

12. **Complete Example**
    - Full implementation skeleton
    - Ready-to-use code

**Key principle**: Every section must have CODE EXAMPLES

### 3.2 QUICK-START.md Structure

Transform implementation-guide into a step-by-step checklist:

**Phase 1: Setup (30 min)**
- [ ] Task 1
- [ ] Task 2
- Reference: See section X in implementation-guide

**Phase 2: Core Implementation (4-6 hours)**
- [ ] Step 1: Create logger class (2-3 hours)
  - Reference: Section Y
- [ ] Step 2: Module-level API (1 hour)
  - Reference: Section Z

**Phase 3: Testing (1-2 hours)**
- [ ] Create test files
- [ ] Run validation tools
- Reference: specification/06-test-scenarios.md

**Phase 4: Package (1 hour)**
- [ ] Create package files
- [ ] Verify installation

**Key principle**: Pure checklist with time estimates and references

### 3.3 README.md Structure

Create language-specific index:

**Documents in This Folder:**
- 🚀 QUICK-START.md (START HERE)
- 📖 implementation-guide.md (MAIN REFERENCE)
- 🔬 otel-research.md (BACKGROUND)
- 🔧 specification-gaps.md (REFERENCE)

**Implementation Workflow:**
- Phase 1: Setup (30 min)
- Phase 2: Core (4-6 hours)
- Phase 3: Testing (1-2 hours)
- Phase 4: Package (1 hour)

**Key Decisions Made:**
- Logging library: {choice} (rationale)
- Flush pattern: {async/sync} (rationale)
- Module structure: {pattern} (rationale)

**Dependencies:** (list key packages)

**Time Estimate:** 8-10 hours

---

## Step 4: Validation

**Goal**: Verify guides are complete and accurate

### 4.1 Implementation Test

**Test the guides by implementing:**
1. Follow QUICK-START.md exactly
2. Reference implementation-guide.md as needed
3. Note any unclear sections
4. Time each phase

### 4.2 Validation Checklist

- [ ] All 7 API functions documented
- [ ] Complete code skeleton provided
- [ ] E2E test example included
- [ ] Testing references specification tools
- [ ] No duplication of specification content
- [ ] Time estimates realistic
- [ ] All code examples compile/run

### 4.3 Specification Tools Validation

Run these commands:
```bash
./specification/tools/validate-log-format.sh {language}/test/e2e/company-lookup/logs/dev.log
./specification/tools/run-company-lookup.sh {language}
./specification/tools/run-company-lookup-validate.sh {language}
```

All must pass ✅

---

## Language-Specific Considerations

### PHP
- **Logging library**: Monolog (industry standard)
- **OTEL integration**: Manual LoggerProvider setup
- **Async**: PHP has limited async support, use sync
- **Naming**: snake_case for functions
- **Module pattern**: Namespaces and classes

### C# (.NET)
- **Logging library**: Microsoft.Extensions.Logging (official)
- **OTEL integration**: Native via OpenTelemetry.Instrumentation
- **Async**: async/await pattern (async Task)
- **Naming**: PascalCase for public methods
- **Module pattern**: Namespaces and static classes

### Go
- **Logging library**: slog (stdlib, Go 1.21+)
- **OTEL integration**: Official opentelemetry-go
- **Async**: Goroutines, but flush is synchronous
- **Naming**: CamelCase for exported functions
- **Module pattern**: Package-level functions
- **Error handling**: Return error values, not exceptions

### Rust
- **Logging library**: tracing (ecosystem standard)
- **OTEL integration**: opentelemetry-rust + tracing-opentelemetry
- **Async**: async/await with tokio runtime
- **Naming**: snake_case for functions
- **Module pattern**: pub mod and pub fn
- **Error handling**: Result<T, E> types

### Java
- **Logging library**: Log4j2 or SLF4J + Logback
- **OTEL integration**: opentelemetry-java + instrumentation
- **Async**: CompletableFuture or sync
- **Naming**: camelCase for methods
- **Module pattern**: Static factory methods or singleton
- **Error handling**: Exceptions (checked and unchecked)

---

## Checklist: Complete Language Guide

- [ ] `{language}/README.md` created (index and overview)
- [ ] `{language}/QUICK-START.md` created (execution checklist)
- [ ] `{language}/implementation-guide.md` created (technical reference)
- [ ] `{language}/otel-research.md` created (research findings)
- [ ] `{language}/specification-gaps.md` created (gap analysis)
- [ ] Top-level `README.md` updated (add language to table)
- [ ] E2E test implemented and passing
- [ ] All specification tools pass
- [ ] Time estimates validated

---

## Time Breakdown

| Phase | Activity | Time |
|-------|----------|------|
| 1 | OpenTelemetry SDK research | 2-3 hours |
| 1 | Logging library research | 2-3 hours |
| 2 | Gap analysis | 2-3 hours |
| 3 | Write implementation-guide.md | 4-6 hours |
| 3 | Write QUICK-START.md | 1-2 hours |
| 3 | Write README.md | 1 hour |
| 3 | Write otel-research.md | 2 hours |
| 3 | Write specification-gaps.md | 1 hour |
| 4 | Implement and validate | 8-10 hours |
| **Total** | | **23-30 hours** |

**Note**: Actual implementation (following the guide) takes 8-10 hours. Creating the guide takes 23-30 hours.

---

**Last updated**: 2025-10-12
**Template version**: 1.0.0
```

---

## Migration Plan

### Current State
```
todo-lib/
├── README.md
├── QUICK-START.md
├── python-implementation-guide.md
├── python-otel-research.md
└── python-specification-gaps.md
```

### Step 1: Create Structure
```bash
cd todo-lib
mkdir python
```

### Step 2: Move Files
```bash
mv README.md python/
mv QUICK-START.md python/
mv python-implementation-guide.md python/implementation-guide.md
mv python-otel-research.md python/otel-research.md
mv python-specification-gaps.md python/specification-gaps.md
```

### Step 3: Create Top-Level Files
```bash
# Create new top-level README.md (index)
# Create TEMPLATE.md
```

### Step 4: Create Placeholders for Other Languages
```bash
mkdir php csharp go rust java
echo "# Coming Soon" > php/README.md
echo "# Coming Soon" > csharp/README.md
# etc.
```

---

## Benefits of This Structure

1. **Scalable**: Easy to add new languages
2. **Self-contained**: Each language folder is complete
3. **Clear separation**: Language-specific vs language-agnostic
4. **Template-driven**: TEMPLATE.md makes it repeatable
5. **Discoverable**: Top-level README indexes all languages
6. **Maintainable**: Changes to one language don't affect others
7. **Consistent**: Same structure for all languages

---

## Example: Adding PHP Support

```bash
# 1. Research
cd todo-lib/php
# Research OpenTelemetry PHP SDK
# Research Monolog vs other logging libraries
# Document findings in otel-research.md

# 2. Gap Analysis
# Read specification with PHP lens
# Document gaps in specification-gaps.md

# 3. Write Guides
# Create implementation-guide.md (following template)
# Create QUICK-START.md (checklist)
# Create README.md (index)

# 4. Implement
cd ../../php  # Main project
mkdir -p sovdev_logger test/e2e/company-lookup
# Follow QUICK-START.md

# 5. Validate
./specification/tools/validate-log-format.sh php/test/e2e/company-lookup/logs/dev.log
./specification/tools/run-company-lookup.sh php
./specification/tools/run-company-lookup-validate.sh php
```

Total time: 2-3 days (research + guides) + 8-10 hours (implementation)

---

**Status**: Proposal for discussion
**Next steps**: Get approval, then reorganize Python guides as proof of concept
