### 📘 What You Can Add Here

The **Requirements (CRT-REQ)** and **Obligations (CRT-LR)** catalogues allow you to incorporate organisational, regulatory, or sector-specific expectations into your governance system.

These inputs may include:

1. **Regulatory Requirements**
2. **Supervisory & Oversight Requirements**
3. **Control Framework Requirements** (e.g., NIST-inspired, ISO-style, SoGP-style)
4. **Sector-Specific Requirements**
5. **Customer / Client Assurance Requirements**
6. **Supply-Chain & Third-Party Requirements**
7. **Internal Governance Requirements**
8. **Data Protection & Privacy Requirements**
9. **Application Security & Engineering Requirements**

Requirements and obligations **never modify the CRT backbone**.  
They always **connect to it** via `mapped_control_ids` → CRT-C controls.

You may **append organisation-specific rows** to `CRT-REQ.csv` and `CRT-LR.csv`.  
You should **not modify or remove** CRT baseline rows; treat them as reference examples.

---

### 📋 CRT-REQ — Requirements Catalogue

Use `CRT-REQ.csv` to describe **statements of requirement** from frameworks, regulations, or internal programmes  
(e.g., NIST 800-53, ISO-style controls, sector guidance).

Key fields you control on new rows  
(matching the live `CRT-REQ.csv` headers):

- `requirement_set_id` → the family or source set  
  - e.g., `REQ-NIST-80053-R5`, `REQ-DORA`, `REQ-ISO27001`
- `requirement_id` → unique row ID within that set  
  - e.g., `REQ-NIST-001`, `REQ-DORA-010`
- `requirement_ref` → original source reference  
  - e.g., `AC-2`, `CP-2`, `SC-7`
- `requirement_name` → short label  
  - e.g., `Account Management`, `Contingency Plan`, `Boundary Protection`
- `requirement_text` → concise requirement statement in plain language  
  - e.g., “The organization manages information system accounts, including identification, authorization, and monitoring.”
- `requirement_category` → high-level grouping  
  - e.g., `Access Control`, `Audit & Monitoring`, `Contingency Planning`, `Risk Assessment`
- `requirement_subcategory` → more specific grouping  
  - e.g., `Account Management`, `Logging`, `Testing`, `Network Security`
- `source_ref` → full citation or shorthand  
  - e.g., `NIST SP 800-53 Rev5 AC-2`, `NIST SP 800-53 Rev5 CP-2`
- `mapped_control_ids` → **semicolon list of CRT-C IDs (required for structural use)**  
  - e.g., `CRT-C-0011;CRT-C-0010;CRT-C-0012`
- `rationale_summary` → short commentary on how the requirement relates to mapped controls  
  - e.g., “Maps to user/privileged access lifecycle controls.”
- `status` → simple lifecycle / applicability flag  
  - e.g., `Active`, `Deprecated`, `Draft`
- `notes` → optional free text  
  - e.g., “Public domain.” or internal scoping comments

> Requirements express *what is expected*.  
> CRT-C provides *how it is operationalised*.  
> `mapped_control_ids` binds those together.

---

### ⚖ CRT-LR — Legal & Regulatory Obligations Catalogue

Use **CRT-LR.csv** to register formal obligations with legal, regulatory, supervisory, or oversight weight.

These entries explain **why** certain controls exist and **what must be demonstrable** to regulators, auditors, or internal governance bodies.

#### Key fields you control on new rows
_(must match the live `CRT-LR.csv` headers)_

- `lr_id` → **Unique obligation identifier**  
  e.g. `LR-GOV-001`, `LR-DATA-002`, `LR-PRIV-008`.

- `obligation_name` → **Short label**  
  e.g. “Governance of Security & Resilience”, “Business Continuity Planning”.

- `obligation_description` → **Concise expectation**  
  e.g. “Maintain governance arrangements for oversight of cyber, technology, and operational resilience risks.”

- `mapped_control_ids` → **Semicolon-separated list of CRT-C IDs (required)**  
  e.g. `CRT-C-0037` or `CRT-C-0002;CRT-C-0003;CRT-C-0005`.  
  This shows **which CRT-C controls** underpin the obligation.

- `severity` → **Relative weight / impact**  
  e.g. `High`, `Medium`, `Low`.

- `evidence_required` → **Examples of evidence used to demonstrate compliance**  
  e.g. “Governance charters, board minutes”, “BCP plans”, “Retention logs”.

- `jurisdiction` → **Optional country / region tag for scoping**  
  Use this to indicate where the obligation primarily applies, for example:
  - `UK`, `EU`, `US`, `SG`, `CA`, `Global`, `Multi-Reg`, etc.  
  This enables organisation profiles and views to **filter or highlight obligations**
  for specific jurisdictions.  
  If left blank, the obligation is treated as **generic / global**.

- `source_reference_examples` → **Citations or anchors**  
  e.g. `DORA Art.17; MAS TRM Ch.3; PRA SS1/21`, `GDPR Art.32; ISO27001 A.10`.

- `notes` → **Optional free text**  
  Use for scoping, caveats, or internal commentary.

#### Good practice

- Start by **adding `jurisdiction` to your existing CRT-LR.csv** and tagging rows at a coarse level
  (e.g. `Global`, `EU`, `UK`, `SG`).
- When you introduce new regulatory regimes (e.g. Canada, Japan, Australia), **append new rows**
  with the appropriate `jurisdiction` tag and mapped controls.
- Avoid duplicating obligations unless you genuinely need separate tracking for different regimes.

---

### 🛡️ Safe Extension Model

- You may **append** rows to `CRT-REQ.csv` and `CRT-LR.csv`.
- Keep the **column structure identical** when adding new entries.
- If files become inconsistent, restore the defaults from `/defaults`.
- Requirements and obligations only **reference** CRT-C controls — they do **not** change them.
- Policies (CRT-POL) and Standards (CRT-STD) are created in the **Policy & Standard Orchestration** module, *not* edited here.

If a requirement or obligation cannot be clearly linked to CRT-C:

> It can sit outside the CRT mapping,  
> or be refined until a meaningful mapping exists.

---

### 🧠 AI-Assisted Mapping to CRT-C (Optional & Bounded)

You can map your requirements and obligations to CRT-C controls manually or with AI assistance.  
The goal is to keep mappings **deterministic**, **bounded**, and **drift-free**.

AI can help with **choosing CRT-C control IDs**.  
It must **not** invent new controls, IDs, or external frameworks.

#### 1️⃣ Provide a bounded CRT-C list

In your AI prompt, include a subset of CRT-C controls with:

- `control_id`
- `control_name`
- a short `description`

Example (extract):

- `CRT-C-0001` — Data Classification Framework  
- `CRT-C-0002` — Data Encryption (At Rest)  
- `CRT-C-0003` — Data Encryption (In Transit)  
- `CRT-C-0010` — Privileged Access Management (PAM)  
- `CRT-C-0049` — Security Monitoring and Anomaly Detection  

AI should only ever select from what you provide.

#### 2️⃣ Provide a small batch of requirements / obligations

Paste 3–10 items at a time from `CRT-REQ.csv` or `CRT-LR.csv`.

Example:

- `REQ-NIST-001` — Account Management  
  “The organization manages information system accounts, including identification, authorization, and monitoring.”

- `REQ-NIST-016` — Contingency Plan  
  “The organization develops a contingency plan for system recovery.”

- `LR-GOV-001` — Governance of Security & Resilience  
  “Maintain governance arrangements for oversight of cyber, technology, and operational resilience risks.”

Keep the text truthful and specific to your environment and selected sources.

#### 3️⃣ Apply strict mapping rules

In the same prompt, state clearly:

> Using **only** the CRT-C controls listed above:  
> – For each item, propose **0–3** candidate CRT-C IDs.  
> – If none fit, respond with **“NO GOOD MATCH”**.  
> – **Never** invent or guess new CRT-C IDs.  
> – **Never** assume controls not shown in the list.

Ask for an output format such as:

- `Item ID: <requirement_id or lr_id>`  
- `Candidate Controls: <CRT-C IDs or NO GOOD MATCH>`  
- `Reasoning: <one sentence>`

#### 4️⃣ Review as the decision-maker

For each mapping, consider:

- Does this control genuinely support the requirement or obligation?
- Is the selection too broad (mapped to everything)?
- Is something obvious missing?
- Would this mapping make sense to an auditor, regulator, or risk committee?

You remain the final authority.

#### 5️⃣ Update CRT-REQ / CRT-LR manually

Only copy CRT-C IDs you accept into `mapped_control_ids` in:

- `CRT-REQ.csv`
- `CRT-LR.csv`

Example:

- `CRT-REQ.csv` → `mapped_control_ids: CRT-C-0011;CRT-C-0010;CRT-C-0012`  
- `CRT-LR.csv` → `mapped_control_ids: CRT-C-0002;CRT-C-0003;CRT-C-0005`

Mappings can be revisited and refined over time without changing the CRT backbone.

---

### ⚠️ Drift Risk (Why These Rules Matter)

Without constraints, AI (or manual edits) can:

- invent control names or IDs  
- map to ISO / NIST / PCI identifiers instead of CRT  
- produce inconsistent mappings for the same requirement  
- break structural alignment between:
  - controls (CRT-C)
  - failures (CRT-F)
  - compensations (CRT-N)
  - requirements (CRT-REQ)
  - obligations (CRT-LR)
  - policies (CRT-POL) and standards (CRT-STD)

The pattern above keeps CRT-REQ and CRT-LR:

- **bounded by CRT-C**,  
- **consistent across runs**, and  
- **safe to use as inputs** into Policy & Standard Orchestration and other modules.
