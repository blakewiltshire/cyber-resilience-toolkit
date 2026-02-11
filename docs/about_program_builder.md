# 🎛 About This App — Programme Builder & AI Export

The **🎛 Programme Builder & AI Export** module assembles **programme artefacts** from your selected governance context and optional operational inputs.

It exists to produce **clean, portable outputs** for review, archiving, export, and (optionally) structured AI handoff.

---

## What this module is

A **builder + packaging layer** that creates:

- **Manifests** — compact, human-facing build summaries
- **Bundles** — normalised structural containers (entities + relationships + metadata)
- **Verified artefacts** — export-ready copies of a built artefact
- **AI handoffs** — wrappers that package a verified artefact into SYSTEM + USER + JSON

---

## What this module is not

This module does **not**:

- Provide advice (security, operational, or otherwise)
- Provide configuration guidance or step-by-step implementation
- Provide assurance, certification, or compliance claims
- Edit catalogues, lenses, or org profiles
- Run AI inside build/verify logic (AI handoff is packaging only)

---

## How the flow fits together

1) **Org Governance Profiles + Governance Setup**  
   Your organisation profile and governance catalogues provide context:
   - CRT-REQ (Requirements)
   - CRT-LR (Legal & Regulatory)

2) **Operational Extensions (catalogues)**  
   Your operational surface (org-specific catalogues) can be extended via:
   - CRT-AS (Assets & Technology)
   - CRT-D (Data & Classification)
   - CRT-I (Identity Zones & Trust Anchors)
   - CRT-SC (Supply Chain & Vendors)
   - CRT-T (Telemetry & Signal Sources)

3) **Structural Lenses (optional bundles)**  
   The lens modules can save **lens bundles** (inputs) which may be attached to a programme build:
   - 🧩 Attack Surface Mapper (CRT-AS)
   - 🧮 Data Classification Registry (CRT-D)
   - 🔐 Identity Access Lens (CRT-I)
   - 🛰️ Supply Chain Exposure Scanner (CRT-SC)
   - 📡 Telemetry Signal Console (CRT-T)

4) **Programme Builder outputs**  
   - **Task Builder** creates **manifest + bundle**
   - **Templates** shape the output format (built-in or user-defined)
   - **Verify** produces a **verified artefact** for export
   - **AI Prompt & Response** packages a verified artefact into an **AI handoff** (SYSTEM + USER + JSON)

---

## 🎛 Task Builder

Builds a programme artefact from:

- Selected **Org Governance Profile**
- Active governance catalogues (CRT-REQ / CRT-LR)
- Optional **lens bundles** (DCR / ASM / IAL / SCES / TSC)

Outputs:
- **Manifest** (summary)
- **Bundle** (structural container)

---

## 🧱 User Templates

Templates allow you to shape exported outputs into consistent layouts.

- Built-in defaults provide a baseline structure
- User templates allow custom sections/ordering for downstream consumption
- Templates do not change underlying artefact data — they shape presentation/output structure

---

## 🔍 Verify

Verify creates an export-ready **verified artefact**:

- A clean, stable copy intended for sharing and downstream tooling
- Restore behaviour (where enabled) restores from a verified artefact back into the current session

---

## 🧠 AI Prompt & Response

This step packages a **verified artefact** into a structured handoff:

- **SYSTEM**: fixed boundaries and handling rules
- **USER**: operator intent and any manual notes
- **JSON**: the verified artefact payload

This module does not generate advice or perform analysis by itself — it produces the handoff container used by the AI Observation Console or external tools.

---

## 🧹 Maintenance

Maintenance provides safe housekeeping across:

- Org profiles
- Active catalogues (governance + operational extensions)
- Lens bundles
- Programme artefacts (manifests, bundles, verified, AI handoffs)
- User templates
- Session hygiene

---

## Notes

The intent is repeatable, auditable structure:

**Build once → place on the shelf → reuse or export when needed.**
