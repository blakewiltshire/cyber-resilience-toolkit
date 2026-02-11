# Cyber Resilience Toolkit (CRT) — Quick Start

This guide covers first-run setup and initial orientation.

---

## 1) Clone and set up

```bash
git clone https://github.com/your-org/cyber-resilience-toolkit.git
cd cyber-resilience-toolkit
python -m venv env
source env/bin/activate
pip install -r requirements.txt
```

## 2) Launch

```bash
streamlit run app.py
```

Open http://localhost:8501

## 3) First orientation

Start with Structural Controls & Frameworks to understand the CRT backbone.

Core CRT catalogues are read-only by design.

Governance and operational catalogues may be extended locally where enabled.

## 4) Outputs

Selected modules produce structured CSV/JSON artefacts suitable for
documentation, review, or downstream reasoning workflows.

> Note: CRT writes local artefacts (backups, JSON views, bundles) into the
project directory. These are intended for local use and are not persisted
across deployments.

Cyber Resilience Toolkit by Blake Wiltshire
© Blake Media Ltd.
