# 📖 About This App — Control Architecture Viewer

The **🧱 Control Architecture Viewer** provides a structural lens over the Cyber Resilience Toolkit (CRT) control catalogue.  
It is **not** a checklist, auditor workflow, or compliance dashboard — it is a **structural exploration environment** designed to show how CRT control families behave as an interconnected system.

---

## What this app provides

- A unified view of **CRT-G** domains, **CRT-C** primary controls, **CRT-F** failure modes, and **CRT-N** compensations.  
- Filters to explore controls by **domain**, **control ID**, or **descriptive content**.  
- The ability to surface structural relationships:
  - controls with linked failure modes  
  - controls with compensating measures  
  - controls missing one or both  
- A way to examine the **CRT architecture independently** of organisational checklists or external frameworks.

---

## Why this matters

Most frameworks (SoGP, PCI, ISO 27001, NIS2, DORA) describe **obligations**.  
The CRT describes **structure** — the architecture that underpins resilience as a system property.

This app helps you answer architectural questions such as:

- Where are my control domains strong or thinly supported?  
- Which controls are **structurally fragile** (failures with no compensations)?  
- Which areas rely heavily on compensations rather than primary controls?  
- Where do identity, data, infrastructure, and behavioural controls intersect?

This allows resilience to be analysed as **system geometry**, not as a checklist of requirements.

---

## How external frameworks fit (SoGP, PCI, NIS2, etc.)

External frameworks can be mapped to CRT controls via:

- **📂 Framework Mappings Explorer**  
- **🧭 Policy & Control Tracker**

Once mapped, they can enrich this viewer through lightweight indicators  
(e.g., *controls touched by any external framework*),  
but the viewer remains **CRT-native** and independent of any external licensing.

---

## Intended users

- Security architects  
- Resilience engineers  
- Governance & risk teams  
- CTO / CISO strategic planning  
- Organisations adopting CRT structure alongside existing frameworks  

---

## Notes

- This app reads from structured CSV catalogues: **CRT-G**, **CRT-C**, **CRT-F**, and **CRT-N**.  
- User-defined frameworks can extend analysis via the **Framework Mappings Explorer**.  
- No external framework content is stored unless deliberately supplied by the user.
