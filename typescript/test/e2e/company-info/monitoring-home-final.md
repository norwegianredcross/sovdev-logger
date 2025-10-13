# Network Monitoring and Smart Home Hub Project Specification

## Document Status
- **Version**: 2.1 (Draft)
- **Date**: 2025-10-11
- **Status**: Specification Phase - Awaiting Approval
- **Next Step**: Review specification and create detailed architectural plan

---

## Table of Contents

1. [Document Status](#document-status)
2. [Executive Summary](#executive-summary)
3. [Solution Requirements](#solution-requirements)
4. [Monitoring Goals](#monitoring-goals)
5. [Network Topology & Problem Statement](#network-topology--problem-statement)
6. [Goal 1: Network Monitoring & Diagnostics](#goal-1-network-monitoring--diagnostics)
7. [Goal 2: Smart Home Hub with Home Assistant](#goal-2-smart-home-hub-with-home-assistant)
8. [Goal 3: User-Friendly Status Display](#goal-3-user-friendly-status-display)
9. [Goal 4: Secure Remote Access](#goal-4-secure-remote-access)
10. [Solution Options to Evaluate](#solution-options-to-evaluate)
11. [Key Architectural Challenges](#key-architectural-challenges)
12. [Questions Requiring Decisions](#questions-requiring-decisions-must-be-decided-before-any-implementation)
13. [Implementation Approach](#implementation-approach)
14. [Next Steps](#next-steps)
15. [Document Revision History](#document-revision-history)
16. [Approval](#approval)

---

## Executive Summary

This project aims to diagnose intermittent network connectivity issues by implementing a comprehensive monitoring solution using a Raspberry Pi 4B positioned outside the home network. The system will monitor ISP connection quality, WiFi router performance, and inter-router connectivity to identify the root cause of network problems. Additionally, the Raspberry Pi will serve as a smart home hub integrating various communication protocols.

**Key Goals:**
1. Identify whether connectivity issues originate from ISP, Kitchen WiFi router, Office WiFi router, or the connection between routers
2. Provide continuous monitoring with external data backup for ISP troubleshooting
3. Create user-friendly network status displays for non-technical family members
4. Integrate smart home devices using Home Assistant
5. Enable secure remote access from anywhere

**Important Note**: This specification focuses on **requirements and goals**, not specific technology solutions. We are open to any approach that meets our needs, including ready-made systems (like Zabbix, LibreNMS, Uptime Kuma, etc.) or custom-built solutions, as long as they are **open source and free**.

---

## Solution Requirements

### Mandatory Requirements

**CRITICAL: All solutions must be open source and/or free software.**

Any proposed solution must meet the following requirements:

1. **Open Source / Free Software**
   - Must be open source (OSI-approved license) OR completely free to use
   - No vendor lock-in
   - No licensing costs
   - Community-supported or self-hostable

2. **Functional Requirements**
   - Must meet all monitoring goals defined in this document
   - Must support the four main goals (monitoring, smart home, display, remote access)
   - Must work with available hardware (Raspberry Pi 4B, Proxmox server)

3. **Technical Requirements**
   - Must support Linux (Raspberry Pi OS, Ubuntu, or similar)
   - Must be maintainable long-term
   - Must have good documentation
   - Should have active community or development

4. **Operational Requirements**
   - Must be reliable enough for 24/7 operation
   - Must support backup and recovery
   - Should support phased implementation
   - Must support secure remote access

### Evaluation Criteria

When evaluating solutions, we will consider:
- **Ease of setup and configuration**
- **Maintenance burden** (how much ongoing work is required?)
- **Flexibility** (can it adapt to our specific needs?)
- **Feature completeness** (does it do everything we need?)
- **Resource usage** (will it run well on Raspberry Pi 4B?)
- **Integration capabilities** (can it work with other tools if needed?)
- **Community support and documentation**

---

## Monitoring Goals

### Primary Objectives

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

## Goal 1: Network Monitoring & Diagnostics

### Hardware Available for This Project

- **Raspberry Pi 4B** (positioned outside home network, connected directly to HUB) - **resource-limited, monitoring role**
- Two WiFi routers in cascade: Office -> Kitchen -> HUB
- **Thinkcentre PC running Proxmox** (on Office WiFi) - available for heavy workloads, **can deploy new VMs/containers if needed**
- Network HUB connecting everything to ISP
- **Firestick** (on Kitchen WiFi, connected to TV) - potential display device
- **Apple TV** (likely on Kitchen WiFi, connected to TV) - potential display device

**Note:** There is an existing Raspberry Pi with Ubuntu/microk8s on the Office network, but it's **running a separate project with frequently changing software and is NOT available or reliable for this project**.

### Current Technical Experience & Available Infrastructure

**Note:** This section describes existing knowledge and infrastructure, but does NOT prescribe the solution. These are resources that COULD be leveraged IF the chosen solution uses them, but we are open to any approach that meets our requirements.

**Technical Experience:**
- Familiar with Kubernetes - can leverage for orchestration if beneficial
- Familiar with Grafana/Tempo/Prometheus/Loki observability stack - already using in another project
- Familiar with Tailscale and Cloudflared for secure remote access
- Experience with Proxmox virtualization
- Experience with Docker and containerization

**Available Infrastructure:**
- Proxmox server capable of running VMs or containers
- Multiple domains available (some with Cloudflare DNS, some with local DNS provider)
- Google Workspace account for external data storage
- Can deploy Kubernetes (microk8s) on Proxmox if the chosen solution benefits from it

### Key Devices on Office WiFi Network (monitoring targets)

- Tellstick (RF 433 MHz gateway)
- Thinkcentre PC running Proxmox (hosting various services)
- Other smart home devices

### Key Devices on Kitchen WiFi Network (monitoring targets)

- Firestick (also potential display device)
- Apple TV (also potential display device)
- Other devices

### Required Capabilities for Data & Reporting

Any solution must provide these capabilities (not prescribing HOW):

#### Data Collection Capabilities
- Collect network performance metrics (latency, packet loss, jitter, bandwidth)
- Monitor DNS resolution (success/failure, response times)
- Track device availability and response times
- Monitor connection state changes (when connections drop/recover)
- Capture sufficient data to diagnose network issues

#### Data Storage Capabilities
- Store historical data for trend analysis
- Retain data long enough to identify patterns (at least several weeks)
- Handle data collection even during network interruptions (buffering)
- Efficient storage given Raspberry Pi resource constraints

#### Visualization & Dashboard Capabilities
- Display real-time network status
- Show historical trends and patterns
- Provide multiple views:
  - Technical dashboards for detailed analysis
  - Simplified dashboards for non-technical users
- Compare metrics across different network segments (ISP, Kitchen WiFi, Office WiFi)
- Visualize where problems occur in the network topology

#### Reporting & Export Capabilities
- Generate automated reports on network performance
- Export reports/dashboards to Google Drive
- Make reports accessible via shareable links (bit.ly or similar)
- Ensure reports are created even during network outages

#### Alerting Capabilities
- Alert when network issues are detected
- Notify when connections drop
- Alert on DNS failures or high latency
- Configurable alert thresholds and conditions

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

### Requirements for Smart Home Integration

Any solution must:
- Support Home Assistant OR provide equivalent smart home hub functionality
- Work with USB devices (Zigbee, Z-Wave, SDR) connected to the Raspberry Pi
- Integrate with WiFi-connected gateways (LoRaWAN, Tellstick)
- Allow control and monitoring of smart home devices
- Optionally integrate smart home metrics into network monitoring dashboards

### Deployment Considerations
- Could run Home Assistant on monitoring Pi (keeps USB devices directly connected)
- Could run Home Assistant on Proxmox (needs USB device passthrough strategy)
- Could use hybrid approach with distributed components
- Should consider resource usage on Raspberry Pi 4B

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

### Capabilities Needed
- Web-based dashboard that can be displayed in a browser
- Large, readable fonts and icons suitable for TV viewing
- Automatic refresh without user interaction
- Simple color-coding for status (green=good, yellow=warning, red=problem)
- Minimal or no authentication required for family viewing within home network

---

## Goal 4: Secure Remote Access

### Requirements
- Secure access to monitoring system from **internet** (when away from home)
- Secure access to monitoring system from **internal network** (when home)
- Secure access to dashboards, reports, and configuration
- **Access to user-friendly status display from anywhere** (via web link)
- All access must be properly secured given the Pi's position outside the home network

### Available Infrastructure
- Familiar with and actively use: **Tailscale** and **Cloudflared**
- Multiple domains available
  - Some with DNS managed in **Cloudflare**
  - Some with DNS at **local DNS provider**
- Proxmox server available for hosting services

### Required Capabilities
- Support for VPN or secure tunnel solutions (Tailscale, Cloudflared, WireGuard, etc.)
- Web-based interface accessible via HTTPS
- Authentication and access control
- Ability to expose specific dashboards publicly (for family) while securing admin functions
- Works with existing domain infrastructure

---

## Solution Options to Evaluate

**Note:** This is not an exhaustive list, and we are open to other suggestions. All options must meet the requirement of being **open source and/or free**.

### Ready-Made Network Monitoring Systems

#### Zabbix
- **Pros**: Comprehensive monitoring, mature project, powerful alerting, good documentation
- **Cons**: Can be complex to set up, heavier resource usage
- **Evaluation needed**: Can it run efficiently on Raspberry Pi 4B? Does it meet all our monitoring goals?

#### LibreNMS
- **Pros**: Network-focused, auto-discovery, good visualization, active community
- **Cons**: Primarily SNMP-focused (do our routers support SNMP?)
- **Evaluation needed**: Can it do the multi-level testing we need?

#### Cacti
- **Pros**: Excellent graphing, long-established, lightweight
- **Cons**: Older interface, less modern features
- **Evaluation needed**: Does it provide the capabilities we need?

#### Observium
- **Pros**: Network device focused, automatic discovery
- **Cons**: Community edition has limitations
- **Evaluation needed**: Is community edition sufficient? Resource requirements?

#### Netdata
- **Pros**: Real-time monitoring, beautiful dashboards, very lightweight
- **Cons**: Primarily for system monitoring, may need extension for network monitoring
- **Evaluation needed**: Can it be extended for our network monitoring needs?

#### Icinga2
- **Pros**: Monitoring and alerting, scalable, good API
- **Cons**: Requires more setup, multiple components
- **Evaluation needed**: Complexity vs. benefits?

#### Uptime Kuma
- **Pros**: Very easy to set up, beautiful modern UI, lightweight, Docker-ready, status pages, multi-notification support, great for uptime monitoring
- **Cons**: More focused on uptime/availability monitoring than comprehensive network metrics, newer project (less mature)
- **Evaluation needed**: Does it provide enough depth for network diagnostics? Can it handle multi-level testing? Can it monitor network segments separately?

### Custom-Built Solutions

#### Prometheus + Grafana + Exporters
- **Pros**: Highly flexible, excellent visualization, large ecosystem of exporters
- **Cons**: Requires more manual setup and configuration
- **Evaluation needed**: Worth the setup effort? Resource usage on Pi?

#### InfluxDB + Telegraf + Grafana
- **Pros**: Time-series optimized, efficient, flexible
- **Cons**: Multiple components to manage
- **Evaluation needed**: Better or worse than Prometheus stack?

### Hybrid Approaches

#### Home Assistant + Add-ons
- **Pros**: Already planning to use Home Assistant, has network monitoring add-ons/integrations
- **Cons**: May not be as comprehensive as dedicated network monitoring tools
- **Evaluation needed**: Can Home Assistant do everything we need? What add-ons exist?

#### Combination Solutions
- Use ready-made tool for network monitoring
- Use Home Assistant for smart home
- Integrate them together
- **Evaluation needed**: Which combinations work well? Added complexity?

### Questions to Answer During Evaluation

For each potential solution:
1. **Does it meet all our monitoring goals?**
2. **Can it run on Raspberry Pi 4B without performance issues?**
3. **How difficult is setup and configuration?**
4. **What is the ongoing maintenance burden?**
5. **Does it support our required capabilities (data collection, storage, visualization, reporting, alerting)?**
6. **Can it integrate with Google Drive for external backups?**
7. **Does it support secure remote access (VPN, tunnels, authentication)?**
8. **Can it create user-friendly displays for non-technical users?**
9. **Is it actively maintained? How good is the documentation and community support?**
10. **What is the learning curve?**

---

## Key Architectural Challenges

1. **External Position Security**: Pi sits outside home network but needs secure access to internal devices
2. **Continuous Data Push**: Need continuous external data push even during connection failures
3. **Multi-Interface Management**: Multiple network interfaces with different roles (monitoring ISP, testing Kitchen WiFi, monitoring Office devices)
4. **Security Hardening**: Security hardening essential given exposed position
5. **WiFi Connectivity Conflicts**: Pi may need to switch between monitoring Kitchen WiFi and communicating with Office devices
6. **USB Device Access**: Home Assistant USB devices need direct hardware access (how to handle if Home Assistant runs on Proxmox?)
7. **Resource Distribution**: Balance workload between resource-limited monitoring Pi and capable Proxmox server
8. **Dependency Management**: What happens if Proxmox goes offline? Monitoring Pi should continue and buffer data
9. **Storage Constraints**: Data retention on resource-limited Raspberry Pi (if running there)
10. **Solution Selection**: Choosing between ready-made vs. custom solutions - complexity vs. flexibility
11. **User Experience**: Making technical network monitoring data accessible and understandable to non-technical users
12. **Display Device Management**: Ensuring Firestick/Apple TV reliably displays status and auto-refreshes
13. **Self-Monitoring**: Firestick and Apple TV themselves are on Kitchen WiFi and can be monitored as health indicators
14. **Integration**: If using multiple tools (e.g., separate network monitoring + Home Assistant), how do they integrate?

---

## Questions Requiring Decisions (MUST BE DECIDED BEFORE ANY IMPLEMENTATION)

### Solution Selection (MOST IMPORTANT)

#### What solution(s) should we use for network monitoring?
- **Ready-made system** (Zabbix, LibreNMS, Uptime Kuma, Netdata, etc.)?
- **Custom-built stack** (Prometheus/Grafana, InfluxDB/Grafana, etc.)?
- **Home Assistant-based** (can HA + add-ons do everything)?
- **Hybrid approach** (different tools for different purposes)?

**Evaluation criteria:**
- Does it meet all requirements and goals?
- Open source / free?
- Ease of setup vs. flexibility
- Maintenance burden
- Resource usage on Raspberry Pi 4B
- Community support and documentation
- Integration capabilities

#### If using ready-made solution:
- Which specific product/project?
- Can it do everything we need, or do we need supplementary tools?
- What are the resource requirements?
- How do we handle customization needs?

#### If using custom-built solution:
- Which components (Prometheus? InfluxDB? Grafana? Loki? Tempo?)?
- Is the added complexity and setup time worth the flexibility?
- Do we have time to maintain a custom solution?

#### Solution deployment architecture:
- Where does each component run (Raspberry Pi vs. Proxmox)?
- How do components communicate with each other?
- What happens if one component fails?

### Architecture Decisions

#### Where should services run?
- All on monitoring Pi (simpler, single device, but resource-constrained)
- All on Proxmox (more resources, but monitoring Pi only collects data)
- Hybrid split (collectors on Pi, storage/processing on Proxmox)

#### Containerization / Orchestration?
- Docker Compose (simpler)?
- Kubernetes/microk8s (more complex, but potentially easier management)?
- Native systemd services (most lightweight)?
- **Decision depends on chosen solution**

#### Security architecture
- Tailscale vs. Cloudflared vs. combination for remote access?
- How to leverage existing domains
- Firewall rules and network segmentation
- How to secure Pi given its position outside home network

#### Data flow architecture
- How does data flow from Pi to backend to Google Drive?
- What happens when connectivity breaks?
- Buffering and retry strategies

### Network Monitoring Decisions

#### What monitoring agents/exporters to run on monitoring Pi?
- **Depends on chosen solution**
- For ICMP/ping monitoring?
- For DNS monitoring?
- For bandwidth testing?
- For packet capture (if needed)?
- How to test from multiple network segments?

#### Data collection configuration
- What metrics to collect for network diagnostics
- Collection intervals for different types of checks
- How to minimize resource usage on Pi
- Storage and retention policies

#### Visualization and dashboards
- Technical dashboards for detailed analysis
- **Simplified dashboard for non-technical users**
- How to visualize multi-level network testing
- Comparison views (wired vs Kitchen WiFi vs Office)
- DNS monitoring dashboards
- Alert rules and thresholds

#### Reporting
- How to generate automated reports
- How to export to Google Drive
- What format (PDF, HTML, JSON)?
- Scheduling (daily, weekly, on-demand)?

#### Network traffic analysis
- Do we need packet capture capabilities?
- How to capture and analyze traffic from the HUB?
- Tools needed (tcpdump, Wireshark, etc.)?

### User-Friendly Status Display Decisions

#### Display solution
- Can chosen monitoring solution provide simplified dashboard?
- Need custom dashboard creation?
- Use Home Assistant dashboard if available?

#### Display implementation
- Which device is better: Firestick or Apple TV?
- Web browser in kiosk mode?
- Dedicated app if available?
- Auto-start and auto-refresh configuration

#### Dashboard design for non-technical users
- Simple color-coded status indicators (red/yellow/green)
- Large, readable fonts and icons
- Minimal technical jargon
- What key information to display

#### Hosting and access
- Where to host the simplified dashboard (Pi, Proxmox, same as monitoring system)?
- Authentication requirements (public within home network vs. secured)?
- How to make it accessible but still secure from external access?

### Smart Home Hub Decisions

#### Where should Home Assistant run?
- On monitoring Pi (keeps USB devices connected, simpler)
- On Proxmox (needs USB device passthrough/forwarding strategy)
- Does the chosen monitoring solution affect this decision?

#### Integration questions
- If on Proxmox, how to handle USB device access from monitoring Pi?
- Could Home Assistant's dashboard replace the need for a separate display solution?
- How to integrate Home Assistant metrics into network monitoring dashboards?
- Should Home Assistant be THE monitoring solution, or supplementary?

#### Device configuration
- Configuration for USB devices (Zigbee, Z-Wave, SDR)
- Integration with WiFi-connected gateways (LoRaWAN, Tellstick on Office network)
- How to utilize the SDR dongle (additional RF monitoring?)
- How Home Assistant will communicate with devices on Office WiFi while monitoring Pi may be on Kitchen WiFi

### Security & Access Decisions

#### Overall security architecture
- Secure architecture given Pi's position outside home network with access to internal network
- Firewall rules and network segmentation strategy
- Best approach for remote access: Tailscale vs. Cloudflared vs. combination
- How to leverage existing domains and Cloudflare infrastructure
- How to secure the user-friendly status display (accessible to family but not internet)

#### Authentication and access control
- Authentication strategy for monitoring system
- Should the simplified dashboard be behind auth or publicly accessible within home network?
- Securing admin interfaces
- Access control: different permissions for internal vs. external access
- Secure communication between monitoring Pi and backend services
- Secure communication between Pi and internal smart home gateways

### System Architecture Decisions

#### Network interface configuration on monitoring Pi
- Wired (eth0) for ISP monitoring and traffic capture
- WiFi for connecting to Kitchen router and monitoring Office devices
- How to manage switching between network connections?

#### Storage strategy
- Local storage on Pi vs. on Proxmox
- Network storage (NFS from Proxmox)?
- Storage requirements for chosen solution
- Data retention policies

#### Operational considerations
- Backup and recovery strategy
- What happens when network connectivity is broken?
- Configuration management (infrastructure as code?)
- Update strategy that doesn't compromise security or monitoring uptime

### Implementation Stage Refinement
- Refine the proposed stage structure based on chosen solution
- Define detailed verification criteria for each stage
- Identify dependencies between stages
- Create rollback procedures for each stage
- Estimate time and effort for each stage

---

## Implementation Approach

### CRITICAL: Phased Implementation with Verification

**No implementation before specification agreement:**
- Complete overall specification must be agreed upon before writing ANY code or configuration
- **Solution must be selected and approved**
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

### Proposed Stage Structure (to be refined after solution selection)

**Note:** The exact stages will depend on the chosen solution. Below is a generic framework that will be adapted.

#### Stage 0: Planning & Specification (CURRENT)
- Evaluate solution options
- Choose solution(s) and justify decision
- Finalize architecture decisions
- Define all stages and verification criteria
- Create detailed specification document
- **Verification**: Specification reviewed and approved, solution selected

#### Stage 1: Basic Setup and Security Hardening
- Set up monitoring Pi with OS
- Implement security hardening
- Set up basic connectivity (wired and WiFi)
- **Verification**: Pi is secure, connected, and accessible

#### Stage 2: Basic ISP Monitoring
- Install and configure chosen monitoring solution (basic setup)
- Implement direct ISP connection monitoring
- Basic metrics collection (ping, DNS, connectivity)
- **Verification**: Can reliably detect when ISP connection drops

#### Stage 3: Backend Infrastructure and Visualization
- Set up data storage (on Pi or Proxmox - depends on architecture)
- Set up visualization/dashboard system
- Configure secure access (Tailscale/Cloudflared)
- **Verification**: Metrics are being stored and can be visualized

#### Stage 4: Multi-level Network Testing
- Add WiFi connection testing (Kitchen and Office)
- Monitor devices on Office network from Kitchen WiFi
- Implement router-to-router monitoring
- **Verification**: Can identify where connectivity issues occur (ISP, Kitchen, Office, or between routers)

#### Stage 5: External Data Backup
- Implement Google Drive integration
- Set up automated report generation
- Create shareable links
- **Verification**: Reports are successfully uploaded and accessible even during outages

#### Stage 6: User-Friendly Display
- Create simplified status dashboard
- Configure Firestick or Apple TV display
- Implement auto-refresh and kiosk mode
- **Verification**: Non-technical users can understand network status at a glance

#### Stage 7: Smart Home Integration
- Deploy Home Assistant (or integrate if solution already includes it)
- Configure USB devices (Zigbee, Z-Wave, SDR)
- Integrate with WiFi gateways (LoRaWAN, Tellstick)
- **Verification**: All smart home devices are accessible and controllable

#### Stage 8: Advanced Monitoring & Alerting
- Implement advanced metrics and logging
- Set up alerting rules and notifications
- Fine-tune dashboards based on real-world usage
- **Verification**: System reliably alerts on issues and provides actionable data

#### Stage 9: Documentation & Handoff
- Complete system documentation
- Create user guides for family members
- Document maintenance procedures
- Create troubleshooting guide
- **Verification**: System is fully documented and maintainable

**Note:** These stages are preliminary and will be significantly refined once we select a solution.

---

## Next Steps

1. **Review this specification document** - ensure it accurately captures all requirements
2. **Evaluate solution options** - research and compare the solutions listed (and any others discovered)
3. **Select solution(s)** - make decision on which solution(s) to use based on evaluation criteria
4. **Get LLM assistance to create detailed architectural plan** for the chosen solution, addressing all remaining questions
5. **Review and approve the architectural plan** - make any necessary adjustments
6. **Define detailed implementation stages** with verification criteria specific to chosen solution
7. **Begin Stage 1 implementation** only after all specifications are approved

**NO CODE OR CONFIGURATION WILL BE WRITTEN UNTIL:**
- We have selected a solution
- We have a complete, agreed-upon specification for that solution
- All architectural decisions are documented and approved

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 (Draft) | 2025-10-11 | Initial | Initial specification document with reorganized structure |
| 2.0 (Draft) | 2025-10-11 | Update | Made solution-agnostic, added emphasis on open source/free requirement, added solution evaluation section |
| 2.1 (Draft) | 2025-10-11 | Update | Added Uptime Kuma to solution evaluation list |

---

## Approval

- [ ] Technical requirements reviewed and approved
- [ ] Solution requirements agreed upon (open source/free)
- [ ] Solution options evaluated
- [ ] Solution selected and justified
- [ ] Architecture decisions documented
- [ ] Security considerations addressed
- [ ] Implementation stages defined
- [ ] Ready to proceed to detailed architectural planning

**Signatures/Approvals:**
- Project Owner: _________________ Date: _________
- Technical Lead: _________________ Date: _________
