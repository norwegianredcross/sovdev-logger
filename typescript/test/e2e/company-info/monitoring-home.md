# Network Monitoring and Smart Home Hub Project Specification

## Document Status
- **Version**: 1.0 (Draft)
- **Date**: 2025-10-11
- **Status**: Specification Phase - Awaiting Approval
- **Next Step**: Review specification and create detailed architectural plan

---

## Executive Summary

This project aims to diagnose intermittent network connectivity issues by implementing a comprehensive monitoring solution using a Raspberry Pi 4B positioned outside the home network. The system will monitor ISP connection quality, WiFi router performance, and inter-router connectivity to identify the root cause of network problems. Additionally, the Raspberry Pi will serve as a smart home hub integrating various communication protocols.

**Key Goals:**
1. Identify whether connectivity issues originate from ISP, Kitchen WiFi router, Office WiFi router, or the connection between routers
2. Provide continuous monitoring with external data backup for ISP troubleshooting
3. Create user-friendly network status displays for non-technical family members
4. Integrate smart home devices using Home Assistant
5. Enable secure remote access from anywhere

---

## Network Topology & Problem Statement

### Physical Setup
```
ISP <---> HUB <---> Raspberry Pi 4B (OUTSIDE home network) - MONITORING/SMART HOME
              <---> Kitchen WiFi Router <---> Office WiFi Router
                    └─> Firestick (TV display)         └─> Tellstick
                    └─> Apple TV (TV display)          └─> Thinkcentre PC (Proxmox)
                                                        └─> [Raspberry Pi with microk8s - SEPARATE PROJECT, NOT PART OF THIS]
```

### Critical Security Consideration
The Raspberry Pi sits OUTSIDE the home WiFi network but has access to it, creating a potential security vulnerability. All access and communications must be properly secured.

### Problem Statement
Experiencing intermittent connectivity issues (broken connections, dropped traffic) and need to determine whether the root cause is:
1. ISP's connection quality
2. Home WiFi network (routers: "Office" and "Kitchen")
3. **The connection BETWEEN Kitchen and Office routers**
4. DNS resolution failures

### ISP Troubleshooting Challenge
When calling the ISP, they check the line and report it's "OK," but since the connection drops and reconnects intermittently, they can't catch it during a problem. Continuous monitoring with data pushed externally is required for historical analysis.

---

## Implementation Approach

### CRITICAL: Phased Implementation with Verification

**No implementation before specification agreement:**
- Complete overall specification must be agreed upon before writing ANY code or configuration
- All architectural decisions must be documented and approved
- Technology stack must be finalized
- Data flows and integrations must be mapped out

**Phased Implementation Requirements:**
- Project broken down into discrete stages
- Each stage must have:
  - Clear objectives and deliverables
  - Defined success criteria
  - Verification/testing procedures
  - Rollback plan if issues arise
- Each stage must be completed and verified before moving to the next

**Stage Verification:**
- Each stage must pass verification tests before proceeding
- Verification includes:
  - Functional testing (does it work as expected?)
  - Security validation (is it secure?)
  - Performance testing (does it meet requirements?)
  - Documentation (is everything documented?)
- No moving to next stage until current stage is approved

**Documentation Throughout:**
- Each stage will be documented with:
  - What was implemented
  - How to verify it works
  - Configuration details
  - Troubleshooting notes

### Proposed Stage Structure (to be refined)

#### Stage 0: Planning & Specification (CURRENT)
- Finalize architecture decisions
- Choose technology stack
- Define all stages and verification criteria
- Create detailed specification document
- **Verification**: Specification reviewed and approved

#### Stage 1: Basic Network Monitoring (ISP Connection)
- Set up monitoring Pi with basic OS and security hardening
- Implement direct ISP connection monitoring
- Basic metrics collection (ping, DNS, bandwidth)
- **Verification**: Can reliably detect when ISP connection drops

#### Stage 2: Backend Infrastructure
- Deploy Prometheus/Loki/Grafana (on Pi or Proxmox - to be decided)
- Set up secure access (Tailscale/Cloudflared)
- Configure data persistence
- **Verification**: Metrics are being stored and can be visualized

#### Stage 3: Multi-level Network Testing
- Add WiFi connection testing (Kitchen and Office)
- Monitor devices on Office network from Kitchen WiFi
- Implement router-to-router monitoring
- **Verification**: Can identify where connectivity issues occur

#### Stage 4: External Data Backup
- Implement Google Drive integration
- Set up automated report generation
- Create shareable links
- **Verification**: Reports are successfully uploaded and accessible

#### Stage 5: User-Friendly Display
- Create simplified status dashboard
- Configure Firestick or Apple TV display
- Implement auto-refresh and kiosk mode
- **Verification**: Non-technical users can understand network status

#### Stage 6: Smart Home Integration
- Deploy Home Assistant
- Configure USB devices (Zigbee, Z-Wave, SDR)
- Integrate with WiFi gateways (LoRaWAN, Tellstick)
- **Verification**: All smart home devices are accessible and controllable

#### Stage 7: Advanced Monitoring & Alerting
- Implement advanced metrics and logging
- Set up alerting rules
- Fine-tune dashboards
- **Verification**: System reliably alerts on issues and provides actionable data

#### Stage 8: Documentation & Handoff
- Complete system documentation
- Create user guides
- Document maintenance procedures
- **Verification**: System is fully documented and maintainable

**Note:** These stages are preliminary and will be refined once we finalize the overall specification.

---

## Goal 1: Network Monitoring & Diagnostics

### Hardware Available for This Project

- **Raspberry Pi 4B** (positioned outside home network, connected directly to HUB) - **resource-limited, monitoring role**
- Two WiFi routers in cascade: Office -> Kitchen -> HUB
- **Thinkcentre PC running Proxmox** (on Office WiFi) - available for heavy workloads, **can deploy new microk8s instance if needed**
- Network HUB connecting everything to ISP
- **Firestick** (on Kitchen WiFi, connected to TV) - potential display device
- **Apple TV** (likely on Kitchen WiFi, connected to TV) - potential display device

**Note:** There is an existing Raspberry Pi with Ubuntu/microk8s on the Office network, but it's **running a separate project with frequently changing software and is NOT available or reliable for this project**.

### Available Kubernetes & Observability Infrastructure

- **Can deploy**: Fresh microk8s instance on Proxmox (VMs or containers) if Kubernetes architecture is beneficial
- **Familiar with Kubernetes** - can leverage for orchestration, service mesh, distributed architecture
- **Familiar with Grafana/Tempo/Prometheus/Loki stack** - already using in another project
  - Grafana for dashboards and visualization
  - Prometheus for metrics collection and storage
  - Loki for log aggregation
  - Tempo for distributed tracing (may be useful for tracking network flows)

### Key Devices on Office WiFi Network (monitoring targets)

- Tellstick (RF 433 MHz gateway)
- Thinkcentre PC running Proxmox (hosting various services)
- Other smart home devices

### Key Devices on Kitchen WiFi Network (monitoring targets)

- Firestick (also potential display device)
- Apple TV (also potential display device)
- Other devices

### Monitoring Goals

1. **ISP Connection Quality**: Monitor the direct connection from Raspberry Pi to ISP to establish a baseline for "good" connectivity
   
2. **Traffic Comparison**: Capture/monitor traffic passing through the HUB to compare:
   - Traffic from WiFi network heading to ISP
   - Direct traffic from Raspberry Pi to ISP
   
3. **Multi-level Testing**: Have Raspberry Pi test connectivity at different network levels:
   - **Direct to ISP** (via wired connection to HUB)
   - **Via Kitchen WiFi** (connect Pi WiFi to Kitchen router, test internet)
   - **Kitchen to Office** (connect Pi to Kitchen WiFi, monitor devices on Office WiFi)
   - Compare results to isolate where drops occur (ISP, Kitchen router, or Office router)

4. **Office Network Device Monitoring**: While connected to Kitchen WiFi, continuously monitor:
   - Tellstick availability and response
   - Thinkcentre PC/Proxmox services availability
   - Other devices on Office network
   - This helps identify if problems are between the two routers

5. **Kitchen Network Device Monitoring**: Monitor devices on Kitchen WiFi:
   - Firestick availability
   - Apple TV availability
   - Can serve as indicators of Kitchen WiFi health

6. **DNS-Specific Monitoring**: Track DNS lookup failures separately, as this could be a distinct issue

### Data Persistence & Reporting Architecture

Given the Raspberry Pi's resource limitations and available **Grafana/Prometheus/Loki** stack, use a **distributed cloud-native observability architecture**:

#### Monitoring Pi Role (outside network): Lightweight data collection
- Run Prometheus node exporter for system metrics
- Run custom network monitoring exporters (blackbox exporter, smokeping exporter, etc.)
- Run Promtail for shipping logs to Loki
- Possibly run lightweight packet capture and export to Tempo for tracing network flows
- Send all telemetry data to backend services (on Proxmox or monitoring Pi itself)

#### Backend Services (options to decide)

**Option A: Run on Monitoring Pi itself** (simpler, single device)
- Lighter weight, but resource-constrained

**Option B: Deploy on Proxmox** (more resources available)
- Could use Docker Compose, systemd services, or deploy microk8s
- Better performance and scalability

**Option C: Hybrid** - collectors on Pi, heavy services on Proxmox

#### Services Needed
- **Prometheus** for metrics storage (network latency, packet loss, DNS response times, etc.)
- **Loki** for centralized log aggregation (connection logs, error logs, monitoring agent logs)
- **Tempo** for distributed tracing (optional - trace network request flows through different segments)
- **Grafana** for unified dashboards showing:
  - ISP connection quality over time
  - Kitchen WiFi performance
  - Office WiFi performance
  - Inter-router connectivity
  - DNS resolution success/failure rates
  - Device availability on Office and Kitchen networks
- CronJobs/scheduled tasks for automated report generation
- Alerting via Grafana (alert when connection drops detected)

#### External Backup: Google Drive (via Google Workspace)
- Scheduled job to export Grafana dashboards/reports to PDF
- Export critical Prometheus/Loki data periodically
- Publicly accessible folder for reports/dashboards
- Link shortener (bit.ly) for easy access
- Ensures data survives even if entire home network goes down

---

## Goal 2: Smart Home Hub with Home Assistant

### Communication Devices Connected to Raspberry Pi

**Built-in:**
- Bluetooth
- WiFi

**Connected via USB:**
- Zigbee coordinator/stick
- Z-Wave controller/stick
- SDR (Software Defined Radio) dongle

**Connected via Gateway on Internal WiFi Network:**
- LoRaWAN gateway
- Tellstick (for RF 433 MHz temperature sensors) - on Office WiFi

### Deployment Options
- Run Home Assistant on monitoring Pi (outside network) - keeps USB devices directly connected
- Run Home Assistant on Proxmox (inside network) - better for updates/reliability but needs USB device passthrough strategy
- Hybrid approach with distributed components
- **Integration with Grafana**: Home Assistant can export metrics to Prometheus for unified monitoring

---

## Goal 3: User-Friendly Status Display

### Requirements
- **Non-technical users** (family members) should be able to easily see network status
- Display should show simplified, color-coded information (e.g., red/yellow/green status)
- Should be visible on TV via Firestick or Apple TV
- Auto-refresh to show current status
- Simple indicators like:
  - "Internet: ✓ Working" or "Internet: ✗ Down"
  - "Kitchen WiFi: Good/Slow/Down"
  - "Office WiFi: Good/Slow/Down"
  - Last updated timestamp
  - Maybe simple graphs showing recent history

### Available Display Devices
- **Firestick** (connected to Kitchen WiFi) - can run web browser apps, kiosk-style displays
- **Apple TV** (connected to Kitchen WiFi) - can run apps or display via AirPlay

### Display Options to Consider
- Simplified Grafana dashboard in kiosk mode
- Custom web dashboard with large, color-coded status indicators
- Home Assistant dashboard (if HA is deployed)
- Dedicated status page app

---

## Goal 4: Secure Remote Access

### Requirements
- Secure access to Raspberry Pi from **internet** (when away from home)
- Secure access to Raspberry Pi from **internal network** (when home)
- Secure access to backend services (Grafana dashboards, Prometheus, databases) whether on Pi or Proxmox
- **Access to user-friendly status display from anywhere** (via web link)
- All access must be properly secured given the Pi's position outside the home network

### Available Infrastructure
- Familiar with and actively use: **Tailscale** and **Cloudflared**
- Multiple domains available
  - Some with DNS managed in **Cloudflare**
  - Some with DNS at **local DNS provider**
- Proxmox server available for hosting services
- **Can deploy Kubernetes** (microk8s) on Proxmox if the orchestration benefits outweigh complexity
- **Grafana** already provides authentication and can be exposed securely

---

## Questions Requiring Decisions (MUST BE DECIDED BEFORE ANY IMPLEMENTATION)

### Architecture Decisions

#### Should we use Kubernetes (microk8s on Proxmox) or simpler Docker Compose/systemd services?
- Pros/cons for this use case
- Does the observability stack (Grafana/Prometheus/Loki) benefit enough from K8s to justify complexity?
- Resource requirements on Proxmox for microk8s vs. standalone services

#### Where should services run?
- All on monitoring Pi (simpler, single device, but resource-constrained)
- All on Proxmox (more resources, but monitoring Pi only collects data)
- Hybrid split (collectors on Pi, storage/processing on Proxmox)

#### Security architecture
- Tailscale vs. Cloudflared vs. combination for remote access?
- How to leverage existing domains
- Firewall rules and network segmentation

#### Data flow architecture
- How does data flow from Pi to backend to Google Drive?
- What happens when connectivity breaks?
- Buffering and retry strategies

### Network Monitoring Decisions

#### What network monitoring exporters/collectors to run on monitoring Pi?
- Blackbox exporter for HTTP/ICMP/DNS probes?
- Smokeping exporter for latency graphs?
- Custom exporters for specific network tests?
- SNMP exporter for router metrics?
- Packet capture tools that can export to Prometheus/Loki?

#### Prometheus configuration for network monitoring
- What metrics to collect for network diagnostics
- Scrape intervals for different types of checks
- Recording rules for aggregations
- Retention policies given storage constraints
- Remote write to Proxmox vs. local storage on Pi?

#### Loki configuration for log collection
- What logs to collect from monitoring Pi
- Log parsing and labeling strategies
- Retention and storage
- Push to Proxmox vs. run on Pi?

#### Tempo configuration (if useful)
- Can distributed tracing help visualize network request flows?
- Trace network requests from Pi → Kitchen → Office → Internet
- Worth the complexity for this use case?

#### Grafana dashboard design
- Technical dashboards for detailed analysis
- **Simplified dashboard for non-technical users**
- Key metrics to display for ISP connection quality
- How to visualize multi-level network testing
- Comparison dashboards (wired vs Kitchen WiFi vs Office)
- DNS monitoring dashboards
- Alert rules for connection drops

#### Additional monitoring questions
- How to capture and analyze traffic from the HUB
- Communication between monitoring Pi and backend services (on Proxmox or Pi itself)
- How to identify whether issues originate from ISP, Kitchen router, Office router, or between routers
- Scheduled jobs for automated report generation and Google Drive export

### User-Friendly Status Display Decisions

#### Display solution choice
- Grafana kiosk mode vs. custom web dashboard?
- Which device is better: Firestick or Apple TV?
- Should we use Home Assistant's built-in dashboard capabilities?

#### Dashboard design for non-technical users
- Simple color-coded status indicators (red/yellow/green)
- Large, readable fonts and icons
- Minimal technical jargon
- Auto-refresh mechanism
- What key information to display (ISP status, WiFi status, device availability)

#### Technical implementation
- How to display on Firestick (web browser in kiosk mode, dedicated app?)
- How to display on Apple TV (web browser, AirPlay from another device?)
- Auto-start and auto-refresh configuration
- Fallback if display device loses connection

#### Hosting
- Where to host the simplified dashboard (Pi, Proxmox, separate web server?)
- How to make it accessible without authentication (for family use)
- But still secure it from external access

### Smart Home Hub Decisions

#### Where should Home Assistant run?
- On monitoring Pi (keeps USB devices connected, simpler)
- On Proxmox (needs USB device passthrough/forwarding strategy)
- Distributed architecture

#### Integration questions
- If on Proxmox, how to handle USB device access from monitoring Pi?
- Could Home Assistant's dashboard replace the need for a custom display solution?
- How to integrate Home Assistant metrics into Prometheus
- How to visualize Home Assistant data alongside network monitoring in Grafana

#### Device configuration
- Configuration for USB devices (Zigbee, Z-Wave, SDR)
- Integration with WiFi-connected gateways (LoRaWAN, Tellstick on Office network)
- How to utilize the SDR dongle
- How Home Assistant will communicate with devices on Office WiFi while monitoring Pi may be on Kitchen WiFi

### Security & Access Decisions

#### Overall security architecture
- Secure architecture given Pi's position outside home network with access to internal network
- Firewall rules and network segmentation strategy
- Best approach for remote access to Grafana/services: Tailscale vs. Cloudflared vs. combination
- How to leverage existing domains and Cloudflare infrastructure
- How to secure the user-friendly status display (accessible to family but not internet)

#### If using Kubernetes
- Ingress controller configuration (Traefik, Nginx?)
- Service mesh mTLS configuration

#### Authentication and access control
- Authentication strategy (Grafana native, OAuth, SSO?)
- Should the simplified dashboard be behind auth or publicly accessible within home network?
- Securing Prometheus endpoints
- Access control: different permissions for internal vs. external access
- Secure communication between monitoring Pi and backend services (Proxmox or Pi)
- Secure communication between Pi and internal smart home gateways

### System Architecture Decisions

#### Deployment architecture
- Standalone services (Docker Compose, systemd) vs. Kubernetes on Proxmox
- Resource allocation for Grafana/Prometheus/Loki/Tempo stack
- Storage requirements for metrics/logs retention

#### Network interface configuration on monitoring Pi
- Wired (eth0) for ISP monitoring and traffic capture
- WiFi for connecting to Kitchen router and monitoring Office devices

#### Data flow architecture
- Monitoring Pi → Backend (Prometheus remote write or scrape? Promtail push or pull?)
- Grafana → Export → Google Drive
- Grafana/Custom Dashboard → Firestick/Apple TV

#### Storage strategy
- Local storage on Pi vs. on Proxmox
- Network storage (NFS from Proxmox)?
- Prometheus local storage vs. remote storage (Thanos, Cortex?)
- Loki storage backend

#### Operational considerations
- Backup and recovery strategy
- What happens when network connectivity is broken (Prometheus remote write queue, Promtail buffering?)
- Configuration management (dashboards as code, IaC for Proxmox deployments)
- Update strategy that doesn't compromise security or monitoring uptime
- **Observability stack sizing**: Resource requirements for this specific network monitoring use case

### Grafana/Prometheus/Loki Specific

Can leverage existing knowledge but need guidance on:
- Network-specific exporters and metrics
- Dashboard templates for network monitoring
- **Simplified dashboard templates for non-technical users**
- Alert rules for network issues
- Log parsing for network logs
- Integration with Google Drive for report export
- Kiosk mode configuration for TV display

### Implementation Stage Refinement
- Refine the proposed stage structure
- Define detailed verification criteria for each stage
- Identify dependencies between stages
- Create rollback procedures for each stage
- Estimate time and effort for each stage

---

## Key Architectural Challenges

1. Pi sits outside home network but needs secure access to internal devices
2. Need continuous external data push even during connection failures
3. Multiple network interfaces with different roles (monitoring ISP, testing Kitchen WiFi, monitoring Office devices)
4. Security hardening essential given exposed position
5. **WiFi connectivity conflicts**: Pi may need to switch between monitoring Kitchen WiFi and communicating with Office devices
6. Home Assistant USB devices need direct hardware access (conflicts with Proxmox deployment unless USB forwarding is set up)
7. **Resource distribution**: Balance workload between resource-limited monitoring Pi and capable Proxmox server
8. **Dependency management**: What happens if Proxmox goes offline? Monitoring Pi should continue and buffer data
9. **Storage constraints**: Prometheus/Loki retention on resource-limited Raspberry Pi (if running there)
10. **Adapting observability stack**: Using Grafana/Prometheus/Loki for network monitoring vs. traditional application monitoring
11. **User experience**: Making technical network monitoring data accessible and understandable to non-technical users
12. **Display device management**: Ensuring Firestick/Apple TV reliably displays status and auto-refreshes
13. **Monitoring the monitors**: Firestick and Apple TV themselves are on Kitchen WiFi and can be monitored as health indicators
14. **Architecture complexity vs. simplicity**: Kubernetes adds orchestration benefits but also complexity - is it worth it for this project?

---

## Next Steps

1. **Review this specification document** - ensure it accurately captures all requirements
2. **Get LLM assistance to create detailed architectural plan** addressing all the questions above
3. **Review and approve the architectural plan** - make any necessary adjustments
4. **Define detailed implementation stages** with verification criteria
5. **Begin Stage 1 implementation** only after all specifications are approved

**NO CODE OR CONFIGURATION WILL BE WRITTEN UNTIL WE HAVE A COMPLETE, AGREED-UPON SPECIFICATION.**

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 (Draft) | 2025-10-11 | Initial | Initial specification document |

---

## Approval

- [ ] Technical requirements reviewed and approved
- [ ] Architecture decisions documented
- [ ] Security considerations addressed
- [ ] Implementation stages defined
- [ ] Ready to proceed to detailed architectural planning

**Signatures/Approvals:**
- Project Owner: _________________ Date: _________
- Technical Lead: _________________ Date: _________
