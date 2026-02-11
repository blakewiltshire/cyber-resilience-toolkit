# 📖 About This App

## 📚 Reference Data & Trusted Sources (CRT)

The **📚 Reference Data & Trusted Sources** hub provides structural access to
core reference components within the **Cyber Resilience Toolkit (CRT)**.

Rather than implementing controls or processing telemetry directly, this app
offers **non-interactive scaffolding** for:

- locating authoritative external references
- interpreting CRT control catalogues and resilience frameworks
- understanding AI persona roles in cyber and operational contexts
- cross-referencing concepts, chapters, and control families

It is designed as a **reference and orientation layer**, not a configuration
console or policy engine.

---

## 🌐 Cyber Resilience Reference Directory

A curated directory of external frameworks, standards, and institutional
reference points relevant to cybersecurity, operational resilience, and digital
governance.

**Purpose:**

- Locate authoritative frameworks, guidance, and baseline standards
- Support mapping between CRT controls and external obligations
- Provide stable anchor points for strategy, architecture, and assurance work

**Scope includes:**

- International standards (e.g. ISO/IEC 27000-series, ISO 22301)
- Regulatory and supervisory references (e.g. DORA, NIS2, NIST publications)
- Multilateral and regional initiatives (e.g. ENISA, OECD, WEF, ITU)

All entries are **outbound references** only — no API integrations, downloads,
or in-app content scraping.

---

## 📂 Structural Controls & Frameworks

A structural view of the **CRT control catalogue** and related framework
mappings, focused on architectural coherence rather than configuration detail.

**Purpose:**

- Provide an at-a-glance understanding of CRT control families (CRT-C)
- Anchor CRT-F and CRT-N mappings to well-known frameworks and standards
- Support reasoning about Prevent / Detect / Respond / Recover structures

**Scope includes:**

- Control families and series from the CRT-C catalogue
- High-level alignment to NIST CSF and related frameworks (CRT-N)
- Structural groupings used in the **Technical Controls Index**

This view is intended for **control architecture interpretation** — not for
defining rule sets, playbooks, or product-specific policies.

---

## 🧠 AI Persona Reference

A centralised repository of **role-aligned AI persona definitions** used across
the CRT and its companion materials.

**Purpose:**

- Describe how different roles frame cyber, operational, and governance
  questions
- Provide neutral, non-advisory scaffolds for reflective exploration
- Support consistent use of personas within the CRT and related guides

**Scope includes:**

- Cyber risk strategy, security architecture, threat intelligence, resilience,
  governance, supply-chain, and behavioural resilience roles
- YAML-backed persona metadata stored in
  `docs/catalogues/ai_personas_cyber.yaml` (or equivalent)
- Integration points with the **Triangular Navigation** structures where
  relevant

Personas provide **perspectives, not prescriptions**. They do not make
decisions, recommend actions, or override organisational governance.

---

## 🗂️ Index & Controls Viewer

A combined viewer for **concepts** and **technical control families** used in
the CRT ecosystem and the *Cyber Resilience in the Information Age* guide.

**Two primary layers:**

1. **Concept Index (A–Z)**
   - Structural terminology, analytical language, and thematic concepts
   - References to chapters and structural themes where appropriate
   - Backed by `docs/catalogues/index_glossary_cyber.yaml`

2. **Technical Controls Index (CRT-C / CRT-F / CRT-N Families)**
   - Architectural control families (e.g. Identity & Access, Data Security,
     Incident Response, Supply-Chain, Physical Security, Emerging Technologies)
   - Full listing of associated CRT-C control IDs per family
   - Links to CRT modules where a family is prominently expressed

This module is designed for **orientation and cross-referencing**, not for
editing catalogues or managing policies.

---

## Developer Notes

- This app is composed of **non-interactive reference modules** only.  
  It does not execute controls, process telemetry, or integrate live data feeds.

- YAML catalogues are stored under `docs/catalogues/` and are shared across
  CRT submodules where appropriate.

- Updates to reference data (e.g., adding a new control family, external
  framework, or persona) should be made by editing the relevant YAML files  
  and reloading the app.

- This module provides **structural and conceptual framing only**.  
  It does **not** provide security configuration guidance, operational
  procedures, or implementation instructions.
