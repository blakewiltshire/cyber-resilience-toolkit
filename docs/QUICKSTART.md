# Cyber Resilience Toolkit (CRT) — Quick Start

This guide covers first-run setup and initial orientation.

---

## 1) Clone the Repository

```bash
git clone https://github.com/blakewiltshire/cyber-resilience-toolkit.git
cd cyber-resilience-toolkit
```

---

## 2) Create a Virtual Environment

```bash
python3 -m venv .venv
```

If `python3` is not available on your system, try:

```bash
python -m venv .venv
```

---

## 3) Activate the Environment

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

---

## 4) Install Requirements

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 5) Launch the Application

```bash
streamlit run app.py
```

The application will launch at:

http://localhost:8501

---

## 6) First Orientation

Start with **Structural Controls & Frameworks** to understand the CRT backbone.

Core CRT catalogues are read-only by design.

Governance and operational catalogues may be extended locally where enabled.

---

## 7) Outputs

Selected modules produce structured CSV/JSON artefacts suitable for documentation, review, or AI-assisted interpretation workflows.

> Note: CRT writes local artefacts (backups, JSON views, bundles) into the project directory. These are intended for local use and are not persisted across deployments.

---

Cyber Resilience Toolkit by Blake Wiltshire  
© Blake Media Ltd.
