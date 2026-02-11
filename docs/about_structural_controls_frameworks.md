# 📂 Structural Controls & Frameworks  
### About This App

This module is the **command centre** of the Cyber Resilience Toolkit (CRT).

It unifies:

- the **core CRT backbone**,  
- your **governance inputs**,  
- your **operational extensions**, and  
- a **structural mapping layer**.

Together, these form the deterministic substrate the platform uses to generate **programme artefacts** such as:

- policies and standards  
- architecture views  
- risk and resilience reviews  
- incident response plans  
- continuity and scenario packets  
- awareness and training materials  
- exception modelling structures  

This app does **not** provide configuration, advice, or assurance.  
It provides **structure**.

---

## 🧭 Framing: Depth, Aperture, Platinum

- **Depth = CRT-C**  
  The structural control catalogue is the objective spine of the programme.

- **Aperture = CRT-C + Extensions**  
  N / F / LR / REQ / POL / STD / AS / D / I / SC / T widen the frame safely and without drift.

- **Platinum = Both, simultaneously, without bias**  
  This app is where **depth** and **aperture** are aligned and inspectable.

---

## 🚀 Flow Overview

1. **Org Governance Profile — define organisation profiles (industry, jurisdictions, frameworks, obligations).**  
2. **CRT Defaults Browser — inspect the CRT backbone and all shipped catalogues.**  
3. **Governance Setup — onboard your own requirements and obligations (CRT-REQ / CRT-LR).**  
4. **Operational Extensions — extend assets, data, identity, supply-chain, telemetry.**  
5. **Mapping Explorer — inspect structural relationships.**

Each step builds on the previous one:

- Org Governance Profile sets the **context lens**.  
- CRT Defaults Browser exposes the **backbone and overlays**.  
- Governance Setup and Operational Extensions add **your organisation’s overlays and surface**.  
- Mapping Explorer lets you **inspect how it all connects**.

---

## 🗂️ View Options

Use the view selector to choose:

- **Org Governance Profile (Org & Scope)**  
- **CRT Defaults Browser**  
- **Governance Setup (Framework Onboarding)**  
- **Operational Extensions (Org-Specific)**  
- **Mapping Explorer**

Each view is a different **structural lens** over the same CRT backbone.

---

## 1. Org Governance Profile (Org & Scope)

This panel defines the **organisational context container** that underpins every other CRT module.

It captures **who you are**:

- primary industry / sector  
- operational environment (cloud, hybrid, on-prem)  
- jurisdictions and regions in scope  
- frameworks and requirement sets adopted (from **CRT-REQ**)  
- legal and regulatory obligations in scope (from **CRT-LR**)  
- organisation size and key context notes  

The Org Governance Profile is:

- a **read-only context object** (it does not modify CRT catalogues),  
- a **scope builder** for frameworks and obligations,  
- a **lens** that downstream modules use when assembling bundles for AI.

Saving a profile builds an **Org Governance Scope Bundle** (JSON) that other modules (e.g. 🧭 Governance Orchestration, 🧱 Security Architecture Workspace, 📊 Incident Simulation Engine) can consume to keep outputs aligned with your organisational frame.

This profile **frames** interpretation; it does **not** validate compliance or make decisions.

---

## 2. CRT Defaults Browser — Full Catalogue View (Depth)

The CRT ships with three catalogue families, all visible in a unified, read-only **Defaults Browser**.

### 🧱 Core CRT Series (Locked Backbone)

Canonical and **read-only**:

- 📘 **CRT-G — Domains**  
- 🧱 **CRT-C — Controls**  
- ⚠️ **CRT-F — Failures**  
- 🧩 **CRT-N — Compensations**

This is the raw backbone.  
Everything else connects into it.

---

### 📋 Governance Catalogues (Overlays)

These ship with baseline entries and can be extended via **Framework Onboarding** or **Policy & Standard Orchestration**:

- 📋 **CRT-REQ — Requirements**  
- 📜 **CRT-POL — Policies**  
- 📏 **CRT-STD — Standards**  
- ⚖️ **CRT-LR — Obligations**

They act as **overlays** that bind into CRT-C using `mapped_control_ids`.  
They do **not** modify CRT-G / CRT-C / CRT-F / CRT-N.

---

### 🛰 Operational Structure (Org-Specific)

These catalogues describe **your real environment**:

- 🛰 **CRT-AS — Asset & technology landscape**  
- 📦 **CRT-D — Data & classification catalogue**  
- 🔐 **CRT-I — Identity zones & trust anchors**  
- 🚢 **CRT-SC — Supply-chain & vendor catalogue**  
- 📡 **CRT-T — Telemetry & signal sources**

They connect back into CRT-D and CRT-C and underpin downstream modules.

The Defaults Browser shows every shipped catalogue in one place — **read-only, searchable, and downloadable**.

---

## 3. Governance Setup — Framework Onboarding

This panel allows you to extend:

- **CRT-REQ — Requirements**  
- **CRT-LR — Legal & Regulatory Obligations**

These catalogues act as **governance overlays**:

- they connect into the backbone via **CRT-C controls**,  
- they do **not** modify CRT-G, CRT-C, CRT-F, or CRT-N.

Use this area to incorporate:

- regulatory expectations and supervisory rules  
- internal governance elements and committees  
- sector-specific requirements  
- jurisdictional obligations  

You may append new rows to CRT-REQ and CRT-LR at any time.  
If mistakes occur, restore the default catalogues from the `/defaults` folder.

---

## 4. Operational Extensions — Org-Specific Catalogues

This panel allows you to extend the **operational surface** of your programme by appending rows to:

- **CRT-AS** — Asset & technology landscape  
- **CRT-D** — Data & classification catalogue  
- **CRT-I** — Identity zones & trust anchors  
- **CRT-SC** — Supply-chain & vendor catalogue  
- **CRT-T** — Telemetry & signal sources  

These catalogues:

- describe **your actual assets, data, identities, vendors, and signals**, and  
- connect back into **CRT-D** and **CRT-C** via mappings such as `mapped_data_class_ids` and `mapped_control_ids`.

They underpin the downstream modules for:

- architecture and control layering  
- risk and resilience views  
- incident response preparation  
- continuity and scenario modelling  
- awareness and training content  
- exception modelling and review  

You may append organisation-specific rows at any time.  
If mistakes occur, restore the default catalogues from the `/defaults` folder.

---

## 5. Structural Mapping Explorer — Requirements, Policies, Standards, Obligations

The **Mapping Explorer** provides a read-only, structural lens over how governance items connect to CRT controls.

It offers four anchor lenses:

- 📋 **Requirements Lens** (CRT-REQ as anchor)  
- 📜 **Policy Lens** (CRT-POL as anchor)  
- 📏 **Standard Lens** (CRT-STD as anchor)  
- ⚖️ **Obligation Lens** (CRT-LR as anchor)

Each lens lets you:

- select a requirement, policy, standard, or obligation, and  
- inspect the connected **CRT-C control bundle** and its related:

  - CRT-F failure modes  
  - CRT-N compensations  
  - other requirements, policies, standards, and obligations mapped to the same controls  

This view is:

- **structural and conceptual only**,  
- **not** advisory, configuration, or assurance.

Operational catalogues (AS / D / I / SC / T) do **not** appear directly in this Explorer by design.  
Their mappings are consumed in the architecture, risk, IR, continuity, and awareness modules where they gain practical meaning.

---

## 🎯 Why This App Matters

This app aligns:

- **Inputs (Org-Specific)**  
  - AS / D / I / SC / T  

- **Spine (CRT Native)**  
  - C → F → N → LR → REQ → POL → STD  

- **Lenses (Modules)**  
  - Orchestration, Architecture, IAM, Mapper, Scanner, Dashboard, Simulation, IR, Continuity, Awareness  

This alignment enables the platform to generate **programme artefacts** that are:

- structurally consistent  
- environment-aware  
- bounded by CRT  
- free from uncontrolled drift  
