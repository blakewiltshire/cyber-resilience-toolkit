# 🔄 System Integrator Hub (SIH)

The **System Integrator Hub (SIH)** is the *registry-level hub* for the Cyber Resilience Toolkit (CRT).
It provides a **single, read-only integration layer** over all CRT catalogues and exposes them in a
consistent way to every module in the app suite.

---

## 1. Purpose and Scope

The SIH exists to:

- Load and validate all CRT catalogues from a single location (`apps/data_sources/crt_catalogues`).
- Enforce the distinction between:
  - **Backbone catalogues** (authoritative, not modified by the app).
  - **Append-only catalogues** (org-specific extensions added via the toolkit).
- Provide a **stable API** for other modules:
  - `get_catalogue(name)` – retrieve a full catalogue as a DataFrame.
  - `resolve_entity(catalogue, id)` – look up a single row using the catalogue's primary ID field.
  - `build_relationships(entity)` – (optional) construct structural views across catalogues.

SIH is **read-only**: it never writes to CSVs, never merges files, and never updates schemas.
All changes happen upstream (e.g. via Structural Controls & Frameworks) and are then *re-read* by SIH.

---

## 2. Catalogues managed by SIH

SIH currently manages the following CRT catalogues:

**Backbone catalogues**

- `CRT-C` – Controls catalogue (core control statements).
- `CRT-F` – Failure modes / risk conditions catalogue.
- `CRT-N` – Compensating controls catalogue.
- `CRT-POL` – Policy catalogue (policy-level intent).
- `CRT-STD` – Standard catalogue (supporting standards and patterns).

These are treated as **authoritative**. The program does not alter these catalogues.

**Append-only catalogues**

- `CRT-LR`  – Legal / regulatory obligations.
- `CRT-REQ` – Requirements (internal / external, including stacked frameworks such as NIST SP 800-53).
- `CRT-D`   – Data & classification registry.
- `CRT-AS`  – Asset & surface catalogue.
- `CRT-I`   – Identity & trust anchors.
- `CRT-SC`  – Supply-chain & vendor catalogue.
- `CRT-T`   – Telemetry & signal sources.
- `CRT-G`   – Control groups / domains.

These catalogues may be extended by the organisation (e.g. via **Operational Extensions**), but SIH always
treats them as **append-only registries**. It never changes existing rows.

---

## 3. Relationship to other modules

The SIH sits at the centre of the CRT architecture and is used by multiple modules:

### 📂 Structural Controls & Frameworks

- Reads `CRT-C`, `CRT-F`, `CRT-N`, `CRT-G`, and select append-only catalogues via SIH.
- Presents a structured view of:
  - Control groups and domains.
  - Cross-mappings between controls, failures, and compensations.
- Acts as the **primary entry point** for extending catalogues (e.g. via Governance Setup and Operational Extensions).

### 🧮 Data Classification Registry (DCR)

- Uses SIH to read `CRT-D`, `CRT-C`, and other relevant catalogues.
- Builds **bundles** that link data sets, classifications, and control sets for downstream AI usage.
- Bundles are **runtime objects or exports**, not new catalogues. They are *not* currently stored back into SIH.

### 🧭 Policy & Standards Orchestration

- Uses SIH to read `CRT-POL`, `CRT-STD`, `CRT-C`, `CRT-LR`, and `CRT-REQ`.
- Accepts bundles (e.g. generated in DCR) as **inputs** for AI context and orchestration flows.
- Again, bundles are not catalogues; they are *consumer payloads* built on top of SIH-backed data.

### Other Structural Lenses and AI Context Modules

- Attack Surface Mapper, Identity & Access Lens, Supply-Chain Exposure Scanner, Telemetry Console, etc.
- All read their underlying catalogues via SIH (e.g. `CRT-AS`, `CRT-I`, `CRT-SC`, `CRT-T`).
- Where they produce AI-ready bundles, those bundles are **module-specific outputs**, not registry entries.

---

## 4. What SIH does *not* do

To keep the architecture clean, SIH **does not**:

- Store or list **AI bundles** created by other modules.
- Maintain a history of exports or user selections.
- Provide write or merge operations on any catalogue.
- Replace the "Per-module AI Bundle View" concept. Each module remains responsible for its own bundle exports.

If bundle persistence is required in future, it will be introduced as a **separate registry** (e.g. a
bundle index or log) that SIH can load, rather than overloading the existing CRT catalogues.

---

## 5. How to interpret the SIH console

The SIH Streamlit console provides three perspectives:

1. **📊 Catalogue Health Overview**
   - Quickly validate which catalogues are loaded and how many rows / columns each has.
   - Check:
     - Backbone vs append-only flags.
     - Whether any catalogue is unexpectedly empty.
     - Likely ID columns (e.g. `policy_id`, `standard_id`, `requirement_id`).

2. **🗂️ Catalogue Explorer**
   - Inspect schema and sample records for a single catalogue.
   - Confirm that append-only extensions are visible to all modules.

3. **🧪 Entity & Relationship Probe** *(optional, if implemented)*
   - Look up a single entity (e.g. control, requirement, policy) using its ID.
   - Explore structural relationships if `build_relationships` is implemented in SIH.

These views are designed for **verification and structural insight**, not configuration.
They help ensure that the CRT backbone and your organisation-specific extensions are correctly loaded before
those catalogues are used by DCR, Policy Orchestration, and other modules.
