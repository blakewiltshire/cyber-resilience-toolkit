# 🧩 Attack Surface Mapper  
### Structural Exposure Mapping Across Identities, Services, Integrations, and Vendors

The **Attack Surface Mapper** provides a systemic view of the organisation’s exposure pathways.  
It does not predict compromise, measure vulnerability, or compute exploitability.  
Instead, it reveals **how exposure propagates through the system** — across people, devices, applications, networks, cloud services, and third-party integrations.

---

## What This App Provides

### **A unified structural catalogue**
- Users  
- Devices and endpoints  
- Applications and APIs  
- Network boundaries  
- Cloud services and SaaS platforms  
- Vendor and third-party integrations  
- File transfer points  
- Telemetry and analytics surfaces  

### **System geometry insights**
- Where exposure originates (local / remote / hybrid)  
- How it crosses trust boundaries  
- Which assets carry high data concentration  
- Which surfaces intersect critical controls  
- Where propagation loops may emerge (technology ↔ process ↔ behaviour)  

### **Control / Failure / Compensation overlay**
- Linked CRT-C controls  
- Associated CRT-F failure modes  
- Available CRT-N compensations  
- Surfaces lacking any structural control alignment

---

## Why This Matters

Most organisations define security by *components*  
(firewalls, VPNs, SaaS apps, endpoints),  
but resilience depends on **relationships**.

The Attack Surface Mapper enables analysis of:

### **1. Concentration Risk**
Which services combine:
- sensitive data  
- privileged access  
- vendor dependency  
- limited monitoring  

### **2. Propagation Pathways**
How a failure in one system can transfer risk to:
- integrated platforms  
- identity infrastructure  
- analytics pipelines  
- external vendors  

### **3. Trust-Boundary Distortion**
Where internal assumptions meet external systems, e.g.:
- SaaS → internal data stores  
- File transfer → privileged workflows  
- Market data → trading systems  
- Wi-Fi → internal CRM  

### **4. Control Blind Spots**
Which surfaces have:
- controls linked but insufficient  
- no failure modes mapped  
- compensations without primaries  

This supports structural decision-making without prescribing architecture or maturity levels.

---

## How User Frameworks Fit

Users may upload their own attack surface catalogue to:

- Replace the baseline  
- Extend it  
- Override specific entries  
- Merge organisational records  

This preserves the CRT’s role as **open-architecture scaffolding**,  
not a recommended configuration.

Uploaded catalogues can introduce:
- new SaaS platforms  
- bespoke internal systems  
- industry-specific gateways  
- vendor dependencies  
- IoT and sensor ecosystems  

The CRT does not impose interpretation — it adapts to the organisation’s real geometry.

---

## Intended Users

- Security Architects  
- Resilience Engineers  
- CTO / CISO Strategy Teams  
- Governance & Risk Analysts  
- Organisations aligning CRT structure with internal architecture  

---

## Notes

- This module reads `CRT-AS.csv` and joins it with `CRT-C`, `CRT-D`, and `CRT-F`.  
- User uploads are optional and may extend, override, or replace the baseline.
- No external framework content is stored unless explicitly supplied by the user.
