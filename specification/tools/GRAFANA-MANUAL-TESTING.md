# Grafana Manual UI Testing Checklist (Task 3.5)

**Purpose**: Visual confirmation that Grafana dashboards correctly display data using snake_case field names

**Duration**: ~15 minutes

**Prerequisites**:
- Monitoring stack deployed and running
- Test data generated (run `./run-full-validation.sh typescript`)
- Grafana accessible at http://grafana.localhost

---

## Access Grafana

1. Open browser: http://grafana.localhost
2. Login with admin credentials (if required)
3. Verify Grafana UI loads correctly

---

## Test 1: Explore View - Loki Datasource

**Purpose**: Verify Loki queries work with snake_case field names

### Steps:

1. Navigate to **Explore** (compass icon in left sidebar)
2. Select **Loki** datasource from dropdown
3. Test the following queries:

#### Query 1: Filter by service_name
```logql
{service_name="sovdev-test-company-lookup-typescript"}
```
**Expected Result**:
- ✅ Query executes without errors
- ✅ Log entries are displayed
- ✅ Timestamp, log level, and message visible

#### Query 2: Filter by function_name
```logql
{service_name="sovdev-test-company-lookup-typescript"} | json | function_name="main"
```
**Expected Result**:
- ✅ Query executes without errors
- ✅ Only logs from "main" function displayed
- ✅ JSON parser works correctly

#### Query 3: Filter by log_type
```logql
{service_name="sovdev-test-company-lookup-typescript"} | json | log_type="transaction"
```
**Expected Result**:
- ✅ Query executes without errors
- ✅ Only transaction logs displayed

#### Query 4: Filter by session_id (NEW FIELD)
```logql
{session_id=~".+"}
```
**Expected Result**:
- ✅ Query executes without errors
- ✅ Logs grouped by session_id
- ✅ All logs from same test run have same session_id

#### Query 5: Display formatted output
```logql
{service_name="sovdev-test-company-lookup-typescript"}
  | json
  | line_format "{{.level}} | {{.function_name}} | {{.log_type}} | {{.message}}"
```
**Expected Result**:
- ✅ Query executes without errors
- ✅ Log lines formatted with fields extracted correctly
- ✅ All field names work (level, function_name, log_type, message)

### Verification Checklist:
- [ ] All 5 Loki queries execute successfully
- [ ] No errors about "unknown field" or "invalid field name"
- [ ] Log data is displayed correctly
- [ ] snake_case field names work in queries (service_name, function_name, log_type)
- [ ] JSON parser extracts fields correctly

---

## Test 2: Explore View - Prometheus Datasource

**Purpose**: Verify Prometheus queries work with snake_case label names

### Steps:

1. In **Explore**, switch to **Prometheus** datasource
2. Test the following queries:

#### Query 1: Filter by service_name label
```promql
sovdev_operations_total{service_name="sovdev-test-company-lookup-typescript"}
```
**Expected Result**:
- ✅ Query executes without errors
- ✅ Metric series are displayed
- ✅ Operation counts visible

#### Query 2: Filter by log_level label
```promql
sovdev_operations_total{service_name="sovdev-test-company-lookup-typescript", log_level="info"}
```
**Expected Result**:
- ✅ Query executes without errors
- ✅ Only info-level operation metrics displayed

#### Query 3: Filter by log_type label
```promql
sovdev_operations_total{service_name="sovdev-test-company-lookup-typescript", log_type="transaction"}
```
**Expected Result**:
- ✅ Query executes without errors
- ✅ Only transaction operation metrics displayed

#### Query 4: Aggregate by peer_service
```promql
sum by (peer_service) (sovdev_operations_total{service_name="sovdev-test-company-lookup-typescript"})
```
**Expected Result**:
- ✅ Query executes without errors
- ✅ Metrics grouped by peer_service
- ✅ Shows breakdown by target system

### Verification Checklist:
- [ ] All 4 Prometheus queries execute successfully
- [ ] No errors about "unknown label" or "invalid label name"
- [ ] Metric data is displayed correctly
- [ ] snake_case label names work in queries (service_name, log_level, log_type, peer_service)
- [ ] Aggregation functions work with snake_case labels

---

## Test 3: Explore View - Tempo Datasource

**Purpose**: Verify Tempo queries work and can find traces

### Steps:

1. In **Explore**, switch to **Tempo** datasource
2. Test trace search:

#### Search 1: Search by service name
- Set **Service Name** filter to: `sovdev-test-company-lookup-typescript`
- Click **Run Query**

**Expected Result**:
- ✅ Query executes without errors
- ✅ Trace list is displayed
- ✅ Recent traces from test run are visible

#### Search 2: View trace details
- Click on a trace from the results
- Examine trace spans

**Expected Result**:
- ✅ Trace visualization loads
- ✅ Spans are displayed in timeline
- ✅ Span details show attributes with snake_case names
- ✅ Attributes like service_name, function_name are visible

### Verification Checklist:
- [ ] Tempo search executes successfully
- [ ] Traces are found and displayed
- [ ] Trace details load correctly
- [ ] Span attributes use snake_case naming

---

## Test 4: Dashboard View (If dashboards are configured)

**Purpose**: Verify existing dashboards display data correctly with snake_case fields

### Steps:

1. Navigate to **Dashboards** (four squares icon in left sidebar)
2. Open any dashboards that use sovdev-logger data

### For each dashboard panel:

#### Visual checks:
- [ ] Panel loads without errors
- [ ] Data is displayed (graphs, tables, logs)
- [ ] No "No data" errors
- [ ] Time series show recent data points
- [ ] Legends show correct labels

#### Query inspection:
- [ ] Click panel title → **Edit**
- [ ] Review query in panel editor
- [ ] Verify query uses snake_case field names
- [ ] Verify no old field names (functionName, logType, service.name)

### Common dashboard panel types:

**Log panels**:
- [ ] Loki query uses snake_case fields
- [ ] Log lines display correctly
- [ ] Filters work (service_name, function_name, log_type)

**Metric panels**:
- [ ] Prometheus query uses snake_case labels
- [ ] Graphs show data points
- [ ] Legend shows correct service/function names

**Trace panels** (if any):
- [ ] Tempo queries execute
- [ ] Trace data is linked correctly

---

## Test 5: Query Builder (Visual query editor)

**Purpose**: Verify Grafana's visual query builder recognizes snake_case fields

### Steps:

1. In **Explore**, use **Builder** mode (not Code mode)
2. For **Loki**:
   - Click **+ Label filter**
   - Verify dropdown shows: service_name, function_name, log_type, peer_service
   - Select `service_name` → `=` → `sovdev-test-company-lookup-typescript`
   - Click **Run query**

**Expected Result**:
- ✅ Label filter dropdown shows snake_case field names
- ✅ Query executes successfully
- ✅ Builder generates correct query syntax

3. For **Prometheus**:
   - Select metric: `sovdev_operations_total`
   - Click **+ Label filter**
   - Verify dropdown shows: service_name, log_level, log_type, peer_service
   - Select filters and run query

**Expected Result**:
- ✅ Label filter dropdown shows snake_case label names
- ✅ Query executes successfully
- ✅ Builder generates correct PromQL syntax

### Verification Checklist:
- [ ] Query builder shows snake_case field names in dropdowns
- [ ] No old field names visible (functionName, logType, etc.)
- [ ] Builder-generated queries work correctly
- [ ] Switching between Builder and Code mode preserves field names

---

## Test 6: Variables (Dashboard variables if configured)

**Purpose**: Verify dashboard variables work with snake_case field names

### Steps:

1. Open a dashboard with variables (if any)
2. Check variable dropdowns at top of dashboard

### For each variable:
- [ ] Variable dropdown populates correctly
- [ ] Options are loaded from query
- [ ] Selecting different option updates panels
- [ ] Query behind variable uses snake_case fields

### Example variables to check:
- Service selector: `label_values(sovdev_operations_total, service_name)`
- Function selector: `label_values({service_name="..."}, function_name)`
- Peer service selector: `label_values(sovdev_operations_total, peer_service)`

---

## Test 7: Alerting Rules (If configured)

**Purpose**: Verify alert rules work with snake_case field names

### Steps:

1. Navigate to **Alerting** → **Alert rules**
2. Check any rules related to sovdev-logger

### For each alert rule:
- [ ] Rule evaluation shows "Normal" or appropriate state
- [ ] Query uses snake_case field names
- [ ] No errors in rule evaluation
- [ ] Alert conditions reference correct fields

---

## Final Verification Summary

### Critical success criteria:

✅ **All queries execute without "unknown field" errors**
✅ **Data is displayed correctly in all views**
✅ **snake_case field names work in queries (service_name, function_name, log_type, peer_service)**
✅ **Query builder recognizes snake_case fields**
✅ **No references to old field names (functionName, logType, service.name, peer.service)**
✅ **session_id field is queryable and visible**

### If any test fails:

1. **Document the failure**:
   - Which test failed?
   - What error message appeared?
   - What was expected vs. actual result?

2. **Check for issues**:
   - Are datasources configured correctly?
   - Do backend queries work directly (Loki, Prometheus, Tempo)?
   - Are field names correct in backend data?

3. **Report findings**:
   - Create issue with test results
   - Include screenshots of errors
   - Include failed query text

---

## Evidence Collection (Optional)

To document successful validation:

1. **Screenshots**:
   - Successful Loki query with results
   - Successful Prometheus query with graph
   - Tempo trace details showing snake_case attributes
   - Dashboard showing data

2. **Export queries**:
   - Save working query examples
   - Document any dashboard JSON updates needed

3. **Validation report**:
   - Date tested
   - Grafana version
   - Test results summary
   - Any issues found and resolved

---

## Completion Checklist

Before marking Task 3.5 complete, verify:

- [ ] All Loki queries in Test 1 work (5/5)
- [ ] All Prometheus queries in Test 2 work (4/4)
- [ ] Tempo search and trace details work (Test 3)
- [ ] Query builder shows snake_case fields (Test 5)
- [ ] No "unknown field" or "invalid field name" errors anywhere
- [ ] Visual confirmation that data displays correctly
- [ ] Documentation updated if any issues found

**Task 3.5 Status**: ⏳ Ready for manual testing

**Time to complete**: ~15 minutes

**Tester**: [Your name]

**Date tested**: [Date]

**Results**: [PASS/FAIL with notes]
