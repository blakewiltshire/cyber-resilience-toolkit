# 📖 About the Index & Controls Viewer (CRT)

The **🗂️ Index & Controls Viewer** provides two structural reference layers used
throughout the **Cyber Resilience Toolkit (CRT)** and the companion guide
*Cyber Resilience in the Information Age*:

### 1) Concept Index (A–Z)
A consolidated catalogue of structural terminology, analytical language, and
cross-referenced concepts appearing across the guide and CRT ecosystem.
Each entry includes a concise definition and, where relevant, chapter context.

### 2) Technical Controls Index (CRT-C / CRT-F / CRT-N Families)
An architectural overview of control families used within the CRT:
- Data Security & Integrity
- Identity & Access Governance
- Governance & Compliance
- Incident Response & Monitoring
- Supply-Chain Assurance
- Physical & Environmental Controls
- Infrastructure & Connectivity
- Emerging Technologies & Systemic Risk
… and others.

Each family lists its corresponding **CRT-C control IDs**, associated control
series, and relevant CRT modules.

---

## What this module provides
- A referenceable, YAML-backed catalogue stored under
  `docs/catalogues/index_glossary_cyber.yaml` and
  `docs/catalogues/technical_controls_index.yaml`
- Cross-links to CRT modules such as the
  **📡 Telemetry & Signal Console**,
  **🛰️ Supply-Chain Exposure Scanner**, and
  **🔐 Identity & Access Lens**
- A clear separation between conceptual terminology and structured control
families
- A consistent reference model aligned with the CRT control catalogue

---

## How to use this module
- Use the **Concept Index** to interpret terminology, structural language, and
themes discussed across the guide.
- Use the **Technical Controls Index** to explore how CRT-C control families map
to architectural functions in the CRT.
- Filter by **A–Z**, **control family**, or **CRT control ID**.
- Use results as grounding for analysis, scenario interpretation, or module
navigation.

---

## Troubleshooting
- If no entries appear, verify the YAML catalogues exist under
  `docs/catalogues/`.
- If fields display incorrectly, check YAML indentation or list markers.
- To extend the reference, update the YAML files directly.

---

## Notes
This module is a **non-interactive reference**.
It provides conceptual and architectural framing only.
**No configuration guidance, implementation detail, or policy advice is
provided.**
