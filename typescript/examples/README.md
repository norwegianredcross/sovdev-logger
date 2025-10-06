# sovdev-logger Examples

This directory contains real-world usage examples of the sovdev-logger library.

## What are Examples?

Examples are **copy-pasteable starter code** showing how to integrate sovdev-logger into your applications. They demonstrate common use cases and best practices.

## Installation

After the library is published to npm, install it with:

```bash
npm install @sovdev/logger
```

For now (development), examples use the local source via `file:../..` in package.json.

## Available Examples

### 01. Basic Usage (`basic/`)

**What it shows:**
- Minimal setup to get started
- Simple initialization with `sovdevInitialize()`
- Basic logging with different log levels
- Console and file output

**Run it:**
```bash
cd examples/basic
npm install
npm start
```

**When to use:**
- Your first time using sovdev-logger
- Simple console applications
- Quick prototyping

---

### Future Examples (To Be Added)

#### 02. Peer Services (`peer-services/`) - Coming Soon

**What it will show:**
- Creating peer service mappings with `createPeerServices()`
- Tracking calls to external systems (APIs, databases)
- Using CMDB system IDs for correlation
- Distinguishing internal vs external operations

**Use case:** Microservices calling external systems

---

#### 03. Express API (`express-api/`) - Coming Soon

**What it will show:**
- Integration with Express.js
- Request/response logging middleware
- Automatic traceId propagation
- Error handling

**Use case:** REST API services

---

#### 04. Batch Job Processing (`batch-job/`) - Coming Soon

**What it will show:**
- Job lifecycle logging (Started, Progress, Completed)
- Progress tracking with `sovdevLogJobProgress()`
- Error handling in batch operations
- Dual traceId strategy (batch-level + item-level)

**Use case:** ETL jobs, data processing pipelines

---

#### 05. OTLP Integration (`otlp-integration/`) - Coming Soon

**What it will show:**
- Configuring OTLP endpoints
- Environment variable setup
- Sending logs to Grafana Cloud / Azure Application Insights
- Verifying logs in observability platform

**Use case:** Production deployments with centralized logging

---

## Example Structure

Each example follows this structure:

```
examples/XX-example-name/
├── README.md              # Detailed explanation
├── package.json           # Dependencies (file:../.. or ^1.0.0)
├── .env.example           # Environment variables template
├── tsconfig.json          # TypeScript configuration
└── index.ts               # Main example code
```

## Running Examples

### During Development (before npm publish)

Examples use local source code:

```bash
cd examples/basic
npm install          # Links to file:../..
npm start            # Runs the example
```

### After Publishing to npm

Users will install from npm:

```bash
mkdir my-project
cd my-project
npm install @sovdev/logger
# Copy example code from docs
npm start
```

## Difference from Tests

| Examples | Tests (test/e2e/) |
|----------|-------------------|
| Show **how to use** the library | Verify the library **works correctly** |
| Copy-paste starter code | Automated verification |
| Minimal, focused code | Comprehensive scenarios |
| Always use published package (or file link during dev) | Always use local source |
| User-facing documentation | Developer tool |

**Examples** are for users learning the library.
**Tests** are for developers verifying the library.

## Best Practices for Examples

### Keep them Simple

✅ **Good Example:**
```typescript
import { sovdevInitialize, sovdevLog, SOVDEV_LOGLEVELS } from '@sovdev/logger';

sovdevInitialize('my-app');
sovdevLog(SOVDEV_LOGLEVELS.INFO, 'main', 'Application started', null, null);
```

❌ **Bad Example** (too complex):
```typescript
// Don't: Add complex business logic, error handling, etc.
// Examples should be minimal and focused
```

### Include README.md

Every example should have a README explaining:
1. **What it demonstrates**
2. **How to run it**
3. **What output to expect**
4. **When to use this pattern**

### Use .env.example

Show users what environment variables are needed:

```bash
# .env.example
LOG_TO_CONSOLE=true
LOG_TO_FILE=true
NODE_ENV=development
```

### Keep Dependencies Minimal

Only include packages required for the example:
- ✅ `@sovdev/logger` (the library)
- ✅ `tsx` or `ts-node` (to run TypeScript)
- ✅ `express` (if showing Express integration)
- ❌ Don't add testing frameworks, linters, etc.

## Adding a New Example

1. **Create directory:**
   ```bash
   mkdir examples/05-my-new-example
   cd examples/05-my-new-example
   ```

2. **Create package.json:**
   ```json
   {
     "name": "sovdev-logger-example-my-new-example",
     "version": "1.0.0",
     "private": true,
     "type": "module",
     "scripts": {
       "start": "tsx index.ts"
     },
     "dependencies": {
       "@sovdev/logger": "file:../.."
     },
     "devDependencies": {
       "tsx": "^4.19.2",
       "typescript": "^5.7.2"
     }
   }
   ```

3. **Create index.ts** with focused example code

4. **Create README.md** explaining the example

5. **Create .env.example** with required environment variables

6. **Test it:**
   ```bash
   npm install
   npm start
   ```

7. **Update this README** to list your new example

## Documentation

Examples should be referenced in the main documentation:

- **typescript/README.md** - Links to examples for quick start
- **docs/README-configuration.md** - References examples for configuration patterns
- **docs/logging-data.md** - Links to batch-job example for pattern explanation

## Why Examples Use `file:../..` (Important!)

### The Pattern

All examples in this directory use local source linking:

```json
{
  "dependencies": {
    "@sovdev/logger": "file:../.."
  }
}
```

### Why We Do This (Industry Best Practice)

This is the **standard approach** used by popular libraries (Winston, Express, Pino, OpenTelemetry):

1. ✅ **Examples always test current code** - No version lag between source and examples
2. ✅ **Works before publishing** - Examples work even if package isn't on npm yet
3. ✅ **Catches regressions** - If you break the API, examples break immediately
4. ✅ **No version management** - Don't need to update example versions after each release

### What This Means for Different Users

| User Type | What You Do | Why |
|-----------|-------------|-----|
| **Library User** | `npm install @sovdev/logger` | Get the published package |
| **Library Developer** | Clone repo, examples use `file:../..` | Test against current source |
| **Example Copier** | Copy `.ts` files, NOT package.json | Start fresh with npm install |

### Important: Don't Copy package.json to Your Project!

When using these examples as a starting point for your own project:

```bash
# ❌ DON'T DO THIS
cp -r examples/basic/* my-project/
# This copies package.json with "file:../.." which won't work in your project

# ✅ DO THIS INSTEAD
mkdir my-project
cd my-project
npm init -y
npm install @sovdev/logger
# Copy only the .ts files
cp ../sovdev-logger/typescript/examples/basic/*.ts .
```

### After Publishing to npm

**We keep `file:../..` in examples** even after publishing because:
- Examples continue to test latest code
- Library developers get immediate feedback
- No maintenance burden updating versions
- Users who need the npm package know to run `npm install @sovdev/logger`

**This is not a bug or oversight** - it's intentional and follows industry standards.

## Getting Help

If an example doesn't work:
1. Check the example's README.md for prerequisites
2. Verify you ran `npm install` in the example directory
3. Check environment variables in .env.example
4. Review the main sovdev-logger documentation
5. Open an issue on GitHub

## Contributing

To contribute a new example:
1. Follow the structure above
2. Keep it simple and focused
3. Test it thoroughly
4. Document it well
5. Submit a pull request
