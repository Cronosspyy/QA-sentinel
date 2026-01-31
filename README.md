## PHASE 1: DEFINE (No code, most important)

### 1️⃣ Start with “Good Call” Definition (FIRST thing)

Before any system, answer this on paper:

- What MUST happen in every call?
- What SHOULD happen?
- What is unacceptable?

Example (raw, not final):

- Must: greeting, verification, issue identification
- Should: empathy, clear explanation
- Unacceptable: rude tone, wrong SOP

📌 Output:
**“Call Quality Rubric – v1” (1–2 pages)**

If this is weak, whole system fails.

---

### 2️⃣ Break Call into Fixed Phases

Define phases once, use everywhere.

Example:

1. Opening
2. Problem Understanding
3. Resolution
4. Closure

📌 Output:
**Call Phase Definition Doc**

This makes scoring consistent.

---

### 3️⃣ Design Scoring Framework (still no code)

Define:

- Dimensions (process, resolution, communication, risk)
- Weight per dimension
- Pass / fail thresholds

📌 Output:
**Scoring Table + Examples**

This is what interviewers care about most.

---

## PHASE 2: PROTOTYPE LOGIC (Low code, high clarity)

Now we _simulate_ the system.

### 4️⃣ Manually Evaluate 10 Sample Calls

Even if fake transcripts.

For each call:

- Mark phases
- Tick rules
- Assign scores manually

📌 Output:

- 10 evaluated calls
- Shows feasibility
- Reveals missing rules

This step sharpens design more than coding ever will.

---

### 5️⃣ Define Rule Engine (Pseudo-code level)

Write rules in plain English or pseudo-code:

- IF greeting missing in first 30 sec → -5
- IF sentiment worsens AND unresolved → high risk

📌 Output:
**Rule Specification Document**

This is literally your future code.

---

## PHASE 3: AUTOMATE CORE (Only now code starts)

### 6️⃣ Start with Speech-to-Text (Commodity)

Do NOT build this.
Use existing service.

Goal:

- Get transcript + timestamps
- Don’t care about perfection yet

📌 Output:

- Audio → transcript pipeline working

---

### 7️⃣ Build Conversation Structuring (Key differentiator)

This is where you add value.

Implement:

- Speaker separation
- Phase detection (simple heuristics)
- Silence gaps

📌 Output:
Structured conversation JSON

---

### 8️⃣ Implement Rule-Based QA Engine

Convert your rules into code.

Start with:

- Script adherence
- SOP steps
- Order checks

No sentiment yet.

📌 Output:

- Deterministic scores
- Explainable outputs

---

## PHASE 4: ADD INTELLIGENCE (Optional, controlled)

### 9️⃣ Add Sentiment Trajectory (Assistive AI)

Use prebuilt model.
Do NOT train.

- Slice call into time windows
- Track sentiment change

📌 Output:
Sentiment trend graph per call

---

### 🔟 Risk Flagging Logic

Combine:

- Rule violations
- Sentiment worsening
- Long silences

📌 Output:
Supervisor alert queue

---

## PHASE 5: INSIGHTS & UX (Last)

### 1️⃣1️⃣ Build Aggregations

- Agent patterns
- City patterns

This is mostly SQL / grouping logic.

---

### 1️⃣2️⃣ Dashboards (Read-only first)

- QA scorecard
- Risk list
- Trends
