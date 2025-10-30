#!/bin/bash

# verify-kubectl-setup.sh
# Verifies kubectl configuration and provides guidance if not available
#
# Exit codes:
#   0 - kubectl fully configured and working
#   1 - kubectl not installed
#   2 - kubectl installed but cannot connect to cluster
#   3 - kubectl connected but cannot access monitoring namespace

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "\n${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  kubectl Setup Verification${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_header

# Test 1: Check if kubectl is installed
echo "Test 1: Checking if kubectl is installed..."
if ! command -v kubectl &> /dev/null; then
    print_error "kubectl is not installed"
    echo ""
    print_warning "kubectl is OPTIONAL for sovdev-logger validation"
    echo ""
    print_info "You have two options:"
    echo ""
    echo "  Option A: Use Grafana queries instead (RECOMMENDED)"
    echo "  ----------------------------------------"
    echo "  • Open http://grafana.localhost in your browser"
    echo "  • Navigate to 'Structured Logging Testing Dashboard'"
    echo "  • Verify all panels show data for your language"
    echo "  • Use query-grafana-*.sh scripts for programmatic queries:"
    echo "    - ./query-grafana-loki.sh <service-name>"
    echo "    - ./query-grafana-prometheus.sh <metric-name>"
    echo "    - ./query-grafana-tempo.sh <trace-id>"
    echo ""
    echo "  Option B: Install kubectl (if you need direct pod access)"
    echo "  ----------------------------------------"
    echo "  • Follow: https://kubernetes.io/docs/tasks/tools/"
    echo "  • Configure kubeconfig: export KUBECONFIG=/path/to/config"
    echo "  • Re-run this script to verify"
    echo ""
    exit 1
fi
print_success "kubectl is installed: $(kubectl version --client --short 2>/dev/null | head -1)"

# Test 2: Check if kubectl can connect to cluster
echo ""
echo "Test 2: Checking kubectl connection to cluster..."
if ! kubectl cluster-info &> /dev/null; then
    print_error "kubectl cannot connect to Kubernetes cluster"
    echo ""
    print_warning "kubectl is OPTIONAL for sovdev-logger validation"
    echo ""
    print_info "Common causes:"
    echo "  • KUBECONFIG not set or pointing to wrong file"
    echo "  • Cluster is not running"
    echo "  • Network connectivity issues"
    echo ""
    print_info "You have two options:"
    echo ""
    echo "  Option A: Use Grafana queries instead (RECOMMENDED)"
    echo "  ----------------------------------------"
    echo "  • Grafana is the authoritative validation source"
    echo "  • Open http://grafana.localhost"
    echo "  • Use query-grafana-*.sh scripts"
    echo ""
    echo "  Option B: Fix kubectl connection"
    echo "  ----------------------------------------"
    echo "  • Check KUBECONFIG: echo \$KUBECONFIG"
    echo "  • Verify cluster is running: docker ps | grep k3s"
    echo "  • Test connection: kubectl get nodes"
    echo ""
    exit 2
fi
print_success "kubectl connected to cluster"

# Test 3: Check if monitoring namespace exists
echo ""
echo "Test 3: Checking access to monitoring namespace..."
if ! kubectl get namespace monitoring &> /dev/null; then
    print_error "Cannot access monitoring namespace"
    echo ""
    print_warning "The monitoring namespace might not exist or you don't have permissions"
    echo ""
    print_info "You have two options:"
    echo ""
    echo "  Option A: Use Grafana queries instead (RECOMMENDED)"
    echo "  ----------------------------------------"
    echo "  • Grafana queries work regardless of kubectl access"
    echo "  • Use query-grafana-*.sh scripts"
    echo ""
    echo "  Option B: Check namespace"
    echo "  ----------------------------------------"
    echo "  • List namespaces: kubectl get namespaces"
    echo "  • Check if monitoring exists in the list"
    echo ""
    exit 3
fi
print_success "Monitoring namespace accessible"

# Test 4: Check if specific pods are accessible
echo ""
echo "Test 4: Checking access to monitoring pods..."
PODS_CHECKED=0
PODS_ACCESSIBLE=0

# Check Loki
if kubectl get pod -n monitoring loki-0 &> /dev/null; then
    print_success "Loki pod accessible (loki-0)"
    PODS_ACCESSIBLE=$((PODS_ACCESSIBLE + 1))
else
    print_warning "Loki pod not accessible (loki-0)"
fi
PODS_CHECKED=$((PODS_CHECKED + 1))

# Check Prometheus
if kubectl get svc -n monitoring prometheus-server &> /dev/null; then
    print_success "Prometheus service accessible (prometheus-server)"
    PODS_ACCESSIBLE=$((PODS_ACCESSIBLE + 1))
else
    print_warning "Prometheus service not accessible (prometheus-server)"
fi
PODS_CHECKED=$((PODS_CHECKED + 1))

# Check Tempo
if kubectl get svc -n monitoring tempo &> /dev/null; then
    print_success "Tempo service accessible (tempo)"
    PODS_ACCESSIBLE=$((PODS_ACCESSIBLE + 1))
else
    print_warning "Tempo service not accessible (tempo)"
fi
PODS_CHECKED=$((PODS_CHECKED + 1))

# Test 5: Check if kubectl exec works
echo ""
echo "Test 5: Checking kubectl exec capability..."
if kubectl exec -n monitoring loki-0 -- echo "test" &> /dev/null; then
    print_success "kubectl exec works (can run commands in pods)"
else
    print_warning "kubectl exec does not work (may need additional permissions)"
fi

# Final summary
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Summary${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""

if [ $PODS_ACCESSIBLE -eq $PODS_CHECKED ]; then
    print_success "kubectl is fully configured and working!"
    echo ""
    print_info "You can use ALL validation tools:"
    echo "  • query-loki.sh - Direct query to Loki pod"
    echo "  • query-prometheus.sh - Direct query to Prometheus"
    echo "  • query-tempo.sh - Direct query to Tempo"
    echo "  • query-grafana-*.sh - Queries via Grafana proxy"
    echo "  • run-full-validation.sh - Complete automated validation"
    echo ""
    exit 0
elif [ $PODS_ACCESSIBLE -gt 0 ]; then
    print_warning "kubectl is partially working ($PODS_ACCESSIBLE/$PODS_CHECKED pods accessible)"
    echo ""
    print_info "Some direct query tools may not work. Recommendation:"
    echo "  • Use query-grafana-*.sh scripts (work without kubectl)"
    echo "  • Use Grafana dashboard for validation"
    echo ""
    exit 0
else
    print_warning "kubectl is connected but cannot access monitoring pods"
    echo ""
    print_info "Use Grafana-based validation instead:"
    echo "  • query-grafana-loki.sh <service-name>"
    echo "  • query-grafana-prometheus.sh <metric-name>"
    echo "  • query-grafana-tempo.sh <trace-id>"
    echo "  • Grafana dashboard: http://grafana.localhost"
    echo ""
    exit 3
fi
