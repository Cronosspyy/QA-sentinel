# QA Rule Engine Logic (Pseudo-Code)

This document defines the automated scoring logic for the Quality Assurance system. It maps the criteria from the Scoring Framework to programmable rules.

## Global Variables

- `SCORE_TOTAL` = 0 (Max 100)
- `CRITICAL_FAIL` = False

---

## 1. Phase: Opening & Verification (10 Points)

### Rule 1.1: Professional Greeting

**Logic:** Check the first 30 seconds (or first 3 turns) for greeting keywords.

```pseudo
IF (Transcript.Segment[0:30s] CONTAINS ("Hello" AND "My name is" AND [CompanyName]))
THEN
    Score.Opening.Greeting = 5
ELSE
    Score.Opening.Greeting = 0
    Log("Missing proper greeting")
END IF
```

### Rule 1.2: Identity Verification

**Logic:** Ensure verification questions are asked before account data is provided.

```pseudo
// Define PII patterns (Account Number, DOB, Last 4 SSN)
IF (Agent.Ask("Can I have your name", "Verify your account", "Date of birth") BEFORE Agent.Mention([AccountDetails]))
THEN
    Score.Opening.Verification = 5
ELSE
    Score.Opening.Verification = 0
    Log("Verification failed or occurred too late")
END IF
```

---

## 2. Quality: Compliance & Security (15 Points - CRITICAL)

### Rule 2.1: Mandatory Scripts

**Logic:** Check for specific required legal phrases.

```pseudo
IF (Transcript CONTAINS ("This call is recorded for quality purposes"))
THEN
    Score.Compliance.Scripts = 5
ELSE
    Score.Compliance.Scripts = 0
    Log("Missing recording disclosure")
END IF
```

### Rule 2.2: Data Privacy (PCI-DSS)

**Logic:** Ensure sensitive data isn't exposed or mishandled.

```pseudo
IF (Customer.Says([CreditCardPattern]) AND Agent.Says("Read that back" OR "Repeat that"))
THEN
    CRITICAL_FAIL = True
    Score.Total = 0
    Log("CRITICAL: Agent asked to repeat clear text credit card info")
ELSE
    Score.Compliance.Security = 5
END IF
```

---

## 3. Quality: Communication & Soft Skills (20 Points)

### Rule 3.1: Tone & Sentiment Analysis

**Logic:** Analyze sentiment polarity (-1.0 to +1.0).

```pseudo
IF (Agent.AverageSentiment >= 0.2 AND Agent.MinSentiment > -0.1)
THEN
    Score.SoftSkills.Tone = 10
ELSE IF (Agent.AverageSentiment < 0)
THEN
    Score.SoftSkills.Tone = 0
    Log("Detected negative agent tone")
ELSE
    Score.SoftSkills.Tone = 5
END IF
```

### Rule 3.2: Active Listening (Interruptions)

**Logic:** count overlapping timestamps where both speak for > 1 second.

```pseudo
IF (Count(Interruptions) == 0)
THEN
    Score.SoftSkills.Listening = 5
ELSE IF (Count(Interruptions) > 3)
THEN
    Score.SoftSkills.Listening = 0
    Log(" excessive interruptions detected")
ELSE
    Score.SoftSkills.Listening = 2
END IF
```

---

## 4. Phase: Problem Solving (20 Points)

### Rule 4.1: Issue Understanding

**Logic:** Agent repeats/confirms the issue.

```pseudo
IF (Agent.Says("So just to confirm", "I understand that", "You are calling about"))
THEN
    Score.Resolution.Understanding = 5
ELSE
    Score.Resolution.Understanding = 0
END IF
```

### Rule 4.2: Accuracy & Resolution

**Logic:** Simple keyword match for success indicators near the end.

```pseudo
IF (Customer.Says("Thank you", "That works", "Fixed") IN Transcript.LastSegment)
THEN
    Score.Resolution.Accuracy = 5
    Score.Resolution.FCR = 5 // Assumed FCR based on positive close
ELSE
    Score.Resolution.Accuracy = 0
END IF
```

---

## 5. Phase: Call Management (15 Points)

### Rule 5.1: Hold Procedures

**Logic:** Detect specific "Hold" patterns.

```pseudo
IF (Agent.Says("mind if I place you on a brief hold") AND Silence > 10s)
THEN
   Score.Management.Hold = 5
ELSE IF (Silence > 30s AND NOT Agent.Says("Hold"))
THEN
   Score.Management.Hold = 0
   Log("Dead air detected without hold permission")
END IF
```

---

## 6. Phase: Closing (10 Points)

### Rule 6.1: Closing Offer

**Logic:** Check for the "help with anything else" pattern.

```pseudo
IF (Agent.Says("anything else", "further assistance") IN Transcript.LastSeconds[30])
THEN
    Score.Closing.Offer = 3
ELSE
    Score.Closing.Offer = 0
END IF
```
