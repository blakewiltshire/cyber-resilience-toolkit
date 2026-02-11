# 🧮 About This App — Data Classification Registry

The **Data Classification Registry** provides the structural foundation for how data behaves across
the Cyber Resilience Toolkit (CRT).
It defines **data tiers**, **categories**, **environments**, and **propagation rules**, allowing the CRT to
represent how information travels across technological, organisational, and behavioural systems.

This is not a policy engine or compliance wizard.
It is a **structural registry** that supports reasoning about how different classes of data influence:

- exposure paths
- control inheritance
- boundary transitions
- propagation loops
- resilience geometry

By anchoring data to a defined tier and category, the CRT can trace how disruption, misuse, or
compromise propagates across the wider system.

---

## Why a Data Classification Registry Matters

In real-world environments, **propagation begins with data**.
The sensitivity and context of a dataset determines the impact of:

- system failures
- control thinness
- vendor exposure
- identity boundary shifts
- automation drift
- behavioural workarounds

Propagation loops described in the companion guide (“data ↔ process ↔ decision ↔ impact”) can only
be modelled when the underlying data class is known.

The registry therefore acts as a **structural anchor**, not a set of prescriptive requirements.

---

## Baseline vs User-Defined Classifications

The CRT provides a **baseline catalogue (CRT-D.csv)** that reflects common data classes found across
small, medium, and large organisations.
These entries are neutral and structural — not organisation-specific — and can be:

- extended,
- reduced,
- overridden, or
- replaced entirely.

### SMEs and Minimal Models

Smaller organisations often operate a simpler classification framework:

- **Confidential**
- **Non-Confidential**
- Optional: **Personal Data (GDPR)**
- Optional: **Operational Logs**

The Data Classification Registry is designed to support **minimal** and **complex** models equally.
Organisations can upload their own classification CSV and the registry will adapt automatically.

This ensures the CRT remains relevant across:

- cloud-native SMEs,
- hybrid mid-market environments, and
- large multi-vendor ecosystems.

---

## What This App Provides

- A unified view of baseline or user-supplied data tiers and categories
- Propagation rules describing how each class travels across boundaries
- Linked CRT-C controls that follow or protect each data class
- A structural lens for later modules (Attack Surface, Supply-Chain, Simulation, Metrics)

The registry does not enforce policy or validate compliance; it surfaces **structure**, allowing
reasoning about where data originates, how it moves, and which controls inherit downstream.

---

## How It Fits Into the CRT System

Several modules directly depend on data classification:

- **🧩 Attack Surface Mapper**
  Ingress and egress surfaces differ by data class.

- **🛰️ Supply-Chain Exposure Scanner**
  Vendor propagation depends on data type and sensitivity.

- **🔐 Identity & Access Lens**
  Privilege boundaries are shaped by data tier and category.

- **📊 Incident Simulation Engine**
  Blast-radius analysis requires knowing what information is at risk.

- **📈 Resilience Metrics Dashboard**
  Data-domain fragility contributes to overall structural indices.

- **🧱 Control Architecture Viewer**
  Classification determines which CRT-C controls follow which assets.

The registry is therefore **foundational**, enabling structural reasoning across the entire CRT.

---

## Adding or Replacing Your Own Catalogue

You can provide your own CSV file containing data tiers, categories, environments, or propagation
rules.
When uploaded, the CRT will:

- merge your entries with the baseline,
- or replace the baseline entirely (depending on your selection),
- automatically detect column names,
- and integrate data classes into downstream modules.

This allows alignment with sector-specific obligations such as:

- GDPR
- FCA / FINRA data obligations
- HIPAA / PHI constraints
- Local data residency requirements
- Industry classification schemes

The CRT keeps all structural mapping internal — no external frameworks are ingested unless you
supply them.

---

## Notes

- The registry reads its entries from **CRT-D.csv** in the catalogue directory, or from a user-uploaded file.
- Columns are detected dynamically; only the structural patterns matter, not exact labels.
- Propagation rules may be simple or detailed — both support structural analysis.
- Linked controls help trace which CRT-C controls should inherit across data flows.

The goal is resilience through **structural clarity**, not compliance scoring.
Data classes provide the first node in the propagation chain, enabling the CRT to model how systems
contain or amplify risk.
