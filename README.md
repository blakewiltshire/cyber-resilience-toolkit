# Cyber Resilience Toolkit (CRT) — Structural Governance Environment

The Cyber Resilience Toolkit (CRT) is a catalogue-driven environment for examining cyber resilience through a shared structural model spanning governance intent, controls, architecture, identity, supply-chain relationships, telemetry, and regulatory obligations.

CRT provides consistent structure and traceability across these domains so that material can be examined, aligned, and carried forward into documentation, programmes, or downstream reasoning workflows.

---

## Python Version

Python 3.11–3.12 (tested on 3.12.x)

---

## Quick Start

### 1. Clone

```bash
git clone https://github.com/blakewiltshire/cyber-resilience-toolkit.git
cd cyber-resilience-toolkit
```

### 2. Create a Virtual Environment

```bash
python3 -m venv .venv
```

If `python3` is not available on your system, try:

```bash
python -m venv .venv
```

### 3. Activate the Environment

**macOS / Linux**

```bash
source .venv/bin/activate
```

**Windows (PowerShell)**

```powershell
.\.venv\Scripts\Activate.ps1
```

**Windows (cmd)**

```bat
.\.venv\Scripts\activate.bat
```

### 4. Install Requirements

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Run the Application

```bash
streamlit run app.py
```

The application will launch at:

http://localhost:8501

---

## What This Is (and Isn’t)

**Is:**  
A structural, catalogue-first environment for exploring how governance, controls, architecture, data, identity, suppliers, and operational signals relate within a cyber-resilience context.

**Isn’t:**  
An assessment engine, automated assurance tool, configuration system, or advisory product. CRT does not provide recommendations, scores, compliance outcomes, or operational instructions.

---

## Screenshots

---

### Portal Home — Structural Orientation

![CRT Portal](docs/screenshots/01-portal.png)

The portal establishes the shared structural model and clarifies:

- What the CRT brings into view  
- What the environment produces  
- How modules interrelate  

This is the conceptual anchor before moving into structured views.

---

### Structural Controls & Frameworks — Model Backbone

![Structural Controls](docs/screenshots/02-structural-controls.png)

The backbone of CRT’s shared model:

- Control architecture (CRT-C / CRT-F / CRT-N)  
- Governance intent and policy alignment  
- Requirements and structural mapping  
- Consistent catalogue relationships  

This module provides the structural grounding for downstream artefacts.

---

### Identity & Access Lens — Structural Lens

![Structural Lenses](docs/screenshots/03-identity-lens.png)

A structural view across identities, privilege tiers, and trust anchors:

- Identity zones and access boundaries  
- Trust anchors and privilege structures  
- Linkage to control frameworks (where recorded)  
- Optional scoped identity context  

This lens produces a normalised identity context for downstream use.

---

### Programme Builder — Artefact Assembly

![Programme Builder](docs/screenshots/04-programme-builder.png)

The Programme Builder assembles structured artefacts from governance context and optional operational inputs.

Outputs include:

- Manifests (summary views)  
- Bundles (structured containers)  

All outputs preserve lineage to the underlying CRT catalogues.

---

### Verify & AI Handoff — Output Preparation

![Programme Builder - Verify](docs/screenshots/05-programme-verify.png)

The verification stage prepares artefacts for export and downstream use:

- Verified artefacts (stable, shareable outputs)  
- Restore behaviour (where enabled)  
- Structured AI handoff packaging  

This stage produces clean, portable outputs for review, archiving, or external tooling.

---

## Where to Start

- **Structural Controls & Frameworks** — the backbone view of CRT’s shared model  
- **Programme Builder & Export** — assemble structured governance or architecture artefacts  
- **Structural Lenses** — examine assets, data, identity, suppliers, and signals  
- **Reference & Integration** — explore catalogues and trusted reference material  

Each module presents a different perspective on the same underlying structure, without fragmenting or redefining it.

---

## Structure (High-Level)

```
cyber-resilience-toolkit/
  apps/          # Canonical catalogues, defaults, and samples
  core/          # Shared structural logic and helpers
  pages/         # Streamlit modules (views and builders)
  docs/          # Reference notes and bundled documentation
  brand/         # Visual assets
  data/          # Optional local context
  images/        # App images
  app.py         # Streamlit launcher
  LICENSE
  requirements.txt
  README.md
```

Canonical catalogues live alongside the modules that use them.  
Generated artefacts are produced locally during use.

---

## License & Use

Free to read and use as provided.

All content and outputs are structural and conceptual in nature.  
No configuration, assurance, or advisory services are provided.

Refer to LICENSE for details.

---

## Ecosystem Context

The Cyber Resilience Toolkit forms part of a broader independent framework studio exploring complex systems through structured guides, modular tools, and applied insight.

CRT aligns with the architectural concepts presented in:

*Cyber Resilience in the Information Age* — a system-level exploration of resilience, governance, and adaptive control in interconnected digital environments.

The toolkit can be used independently.  
The guide provides deeper architectural framing for those exploring the underlying structural model.

Further context:  
www.blakewiltshire.com

---

Cyber Resilience Toolkit by Blake Wiltshire  
© Blake Media Ltd.
