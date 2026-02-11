### 🛰 Operational Extensions — Org-Specific Catalogues

This section lets you describe **your environment** using the CRT operational catalogues:

- 🛰 **CRT-AS — Asset Surface Catalogue**
- 📦 **CRT-D — Data & Classification Catalogue**
- 🔐 **CRT-I — Identity Zones & Trust Anchors**
- 🚢 **CRT-SC — Supply-Chain & Vendor Catalogue**
- 📡 **CRT-T — Telemetry & Signal Sources**

The CRT ships with a **baseline** set of rows for each catalogue.  
You can extend these catalogues to reflect your own assets, data, identity structure, vendors, and telemetry.

If you **cannot confidently describe and map your environment**, keep the defaults and use the modules to explore controls instead.

---

### 📘 What You Can Add Here

You may **append organisation-specific rows** to each catalogue.  
You should **not modify or remove** CRT baseline rows.

---

### 🛰 CRT-AS — Asset Surface Catalogue

Use this to reflect your **real assets and technical surface**:

- applications (public, internal, admin)
- infrastructure components (firewalls, gateways, DBaaS, queues, Kubernetes control plane, etc.)
- security services (SIEM, WAF, PAM, ZTNA, AI gateways, etc.)

Key fields you control on new rows:

- `asset_id` → must follow format `AS-xxxx` (e.g., `AS-1000`, `AS-1001`)
- `asset_name` → free text (“Customer Portal”, “SIEM Platform”)
- `asset_type` → short type (“Web Application”, “Database Service”, “Gateway Service”, “Security Service”, “Object Storage”)
- `environment` → where it runs (Prod, Dev, Corp, Cloud, DR, etc.)
- `exposure_type` → `Remote` | `Local` | `Hybrid` | `Cloud` (how it’s exposed)
- `vendor` → short label (`Internal`, `CloudProvider`, `SecurityVendor`, `CRMVendor`, etc.)
- `trust_boundary` → boundary phrase (“Internet Boundary”, “Perimeter Boundary”, “Cloud Boundary”, “Analytics Boundary”, etc.)
- `entry_points` → protocols/interfaces (“HTTPS; REST API”, “SMTP; HTTPS”, “RDP over HTTPS”)
- `logical_data_classes` → short data labels (“Customer Profiles; Session Tokens; Security Telemetry”)
- `description` → brief explanation of what this asset does
- `notes` → optional free text
- **`mapped_data_class_ids` → semicolon list of CRT-D IDs (required)**
- **`mapped_control_ids` → semicolon list of CRT-C IDs (required)**

> **If you append new assets, both mappings are required.**  
> Without `mapped_data_class_ids` → CRT-D, the system cannot determine exposure.  
> Without `mapped_control_ids` → CRT-C, downstream modules cannot evaluate or visualise the asset.

---

### 📦 CRT-D — Data & Classification Catalogue

Use this to model your **data classes and sensitivity**:

- customer data, employee records, trading logs  
- telemetry archives, model features, AI training data  
- internal reports, legal records, financials, etc.

Key fields you control on new rows:

- `data_id` → must follow format `D-xxxx` (e.g., `D-1000`, `D-1001`)
- `data_name` → free text (“Employee Data”, “Operational Logs”)
- `definition` → short meaning of the data class
- `data_tier` → `Public` | `Internal` | `Confidential` | `Restricted` | `Critical`
- `classification_level` → same as `data_tier` (kept separate for orgs with dual models)
- `data_category` → short label (“Operational Logs”, “Financial Records”, “Analytics Outputs”
- `environment` → where it primarily lives (“Prod”, “HR Systems”, “Analytics”, “Cloud”, etc.)
- `description` → brief operational description
- `examples` → a few sample items (“API logs”, “parquet snapshots”, “JWT tokens”)
- `propagation_rules` → semicolon or underscore chain (“App _ SIEM _ Archive”)
- `confidentiality_impact` → `low` | `medium` | `high`
- `integrity_impact` → `low` | `medium` | `high`
- `availability_impact` → `low` | `medium` | `high`
- `notes` → optional free text
- **`mapped_control_ids` → semicolon list of CRT-C IDs (required)**

> **If you append new data classes, you MUST map them to CRT-C** via `mapped_control_ids`.  
> Without this, the control architecture view and downstream modules cannot understand how those data classes are governed.

---

### 🔐 CRT-I — Identity Zones & Trust Anchors

Use this to describe your **identity architecture**:

- IdPs, directories, and SSO layers  
- PAM vaults and admin identity anchors  
- device-trust evaluators and token issuers  

Key fields you control on new rows:

- `identity_id` → must follow format `I-xxxx` (e.g., `I-1000`, `I-1001`)
- `name` → free text (“PAM Vault”, “Finance User”, “Root CA”)
- `type` → `user` | `service` | `machine`
- `zone` → `critical` | `sensitive` | `operational` | `external`
- `trust_anchor` → `yes` | `no` (is this an anchor of identity trust?)
- `policy_anchor` → free text (e.g., `MFA`, `hardware-token`, `pam-control`)
- `privilege_level` → `high` | `medium` | `low`
- `associated_assets` → short tag (“erp”, “ci-cd”, “net-edge”, “prod-app”)
- `notes` → optional free text
- `source_ref` → `baseline` or brief lineage
- **`mapped_control_ids` → semicolon list of CRT-C IDs (required)**

> **If you append new identity zones or trust anchors, you MUST map them to CRT-C.**  
> This preserves the link between identity architecture and access / governance controls.

---

### 🚢 CRT-SC — Supply-Chain & Vendor Catalogue

Use this to reflect your **real suppliers and dependencies**:

- cloud / hosting providers  
- SaaS platforms  
- payment processors and critical service providers  
- security vendors, monitoring platforms, integrators  

Key fields you control on new rows:

- `vendor_id` → must follow format `SC-xxxx` (e.g., `SC-1000`, `SC-1001`)
- `service_type` → free text (“SaaS”, “IaaS”, “MSP”, “CPaaS”)
- `dependency_type` → `direct` | `indirect` | `transitive`
- `criticality` → `High` | `Medium` | `Low`
- `region` → short label (e.g., `global`, `US`, `UK`, `EU`)
- `contract_tier` → `enhanced` | `standard` | `regulated`
- `data_access_level` → `full` | `limited` | `none`
- `failure_modes` → semicolon list (e.g., `outage;auth-failure`)
- `vendor_archetype` → brief category (“Identity Provider”, “SaaS Suite”)
- `example_vendors` → optional examples (“Okta”, “AWS”, “Salesforce”)
- `notes` → optional free text
- `source_ref` → `baseline` or brief lineage
- **`mapped_control_ids` → semicolon list of CRT-C IDs (required)**

> **If you append new vendors, you MUST map them to CRT-C.**  
> These mappings are used by the Supply-Chain Exposure Scanner and structural views to identify which controls govern each dependency.

---

### 📡 CRT-T — Telemetry & Signal Sources

Use this to describe **where your signals come from**:

- IdP authentication logs  
- SIEM feeds  
- endpoint telemetry, network flows, DNS  
- cloud provider logs, model telemetry, AI audit logs  

Key fields you control on new rows:

- `telemetry_id` → must follow format `T-xxxx` (e.g., `T-1000`, `T-1001`)
- `source_name` → free text (e.g., “API Gateway Logs”)
- `channel` → `logs` | `metrics` | `events` | `traces`
- `signal_class` → `auth` | `endpoint` | `network` | `cloud` | `api` | `application` | `database` | `model` | `generic`
- `retention_days` → number (e.g., `30`, `90`, `180`, `365`)
- `parsing_status` → `native` | `partial` | `custom-parsed` | `raw`
- `linked_zones` → semicolon-separated (e.g., `corp;cloud;prod;edge;iot-zone`)
- `enrichment_ready` → `yes` | `no`
- `notes` → optional free text
- `source_ref` → `baseline` or brief lineage
- **`mapped_control_ids` → semicolon list of CRT-C IDs (required)**

> **If you append new telemetry sources, you MUST map them to CRT-C.**  
> This is how the Telemetry & Signal Console understands which controls are being evidenced by which signals.

---

### 🛡️ Safe Extension Model

The operational catalogues are **extension points**, not places to rewrite the CRT backbone.

- You may **append** rows to:
  - `CRT-AS.csv`, `CRT-D.csv`, `CRT-I.csv`, `CRT-SC.csv`, `CRT-T.csv`
- Keep the **column structure identical** when adding new entries.
- If files become inconsistent, restore the defaults from `/defaults`.
- Baseline CRT rows (shipped with the toolkit) should be treated as **reference examples**.
- **New rows must be mapped**:
  - to CRT-D (for assets → `mapped_data_class_ids`), and
  - to CRT-C (for all catalogues → `mapped_control_ids`).

If you cannot describe and map an item correctly:

> Do not add the row.  
> Use the defaults, and work with the modules to select controls and structures instead.

---

### 🧠 AI-Assisted Mapping to CRT-C (Optional & Bounded)

AI can assist with **choosing CRT-C control IDs** for new rows.  
It must **not** invent your environment, or new CRT catalogues.

You define your environment.  
AI only assists with **linking** that environment to CRT-C.

A safe pattern:

1. **Provide a bounded CRT-C list**  
   - Include only `control_id`, `control_name`, and a short `description`.  
   - Example (short extract):

     - `CRT-C-0001` — Data Classification Framework  
     - `CRT-C-0002` — Data Encryption (At Rest)  
     - `CRT-C-0003` — Data Encryption (In Transit)  
     - `CRT-C-0010` — Privileged Access Management (PAM)  
     - `CRT-C-0049` — Security Monitoring and Anomaly Detection  

   AI should only ever select from what you provide.

2. **Provide a small batch of catalogue rows to map**  
   - 3–10 entries from a single catalogue (AS / D / I / SC / T).  
   - Keep descriptions truthful and specific.  
   - Example (assets):

     - `AS-CUST-API` — “Public-facing API entry point for customer profile updates and account actions.”  
     - `AS-AI-GW` — “Internal API surface brokering requests to external LLM provider; handles sensitive prompts and derived outputs.”

3. **Apply strict mapping rules in your prompt**  
   - Ask AI to propose **0–3 candidate CRT-C IDs** per item.  
   - Require “NO GOOD MATCH” when nothing fits.  
   - Explicitly state:

     - Use **only** the CRT-C IDs listed above.  
     - **Never** invent or guess new CRT-C IDs.  
     - **Never** reference other frameworks (ISO, NIST, PCI) in IDs.  
     - Output format, for example:

       - `Item ID: <ID>`  
       - `Candidate Controls: <CRT-C IDs or NO GOOD MATCH>`  
       - `Reasoning: <one sentence>`

4. **Review suggestions as the decision-maker**  
   - Does each suggested control genuinely apply?  
   - Is anything obviously missing?  
   - Would the mapping make sense to an architect or auditor?

5. **Update the CSVs manually**  
   - Only copy the CRT-C IDs you accept into `mapped_control_ids` on:

     - `CRT-AS.csv`  
     - `CRT-D.csv`  
     - `CRT-I.csv`  
     - `CRT-SC.csv`  
     - `CRT-T.csv`

   - For assets, also ensure `mapped_data_class_ids` refer to the correct CRT-D rows.

---

### ⚠️ Drift Risk (Why the Constraints Matter)

Without these constraints, AI (or manual edits) can:

- invent control IDs or names  
- drift into ISO / NIST / PCI identifiers instead of CRT  
- produce inconsistent mappings across runs  
- break alignment between:
  - controls (CRT-C)
  - failures (CRT-F)
  - compensations (CRT-N)
  - obligations (CRT-LR / CRT-REQ)
  - operational catalogues (AS / D / I / SC / T)

The pattern above keeps mappings **bounded, explainable, and structurally consistent**.
