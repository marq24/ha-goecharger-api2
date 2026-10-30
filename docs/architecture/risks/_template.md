---
id: RNNN
date: YYYY-MM-DD
category: ARCH
probability: 3
impact: 3
residual_probability: 2
residual_impact: 2
strategy: mitigate
status: open
owner:
review: release
---
# RNNN: Title of the risk

<!--
Template for a new risk. Copy this file to `RNNN-short-title.md` in this folder
(NNN = the number after the highest in the register, always three digits).
Replace every placeholder, delete these comments, then run
`python tests/tools/build_risk_register.py`. Do not edit the blocks between the
`risk:` markers; the script fills them from the front matter. Run it with
`--check` to see whether anything is out of date.

Front matter
- id            The same number as in the file name, three digits.
- date          The day the risk entered this documentation (YYYY-MM-DD).
- category      ARCH architecture / technology, SEC security, INT interface or integration,
                QA quality or testing, DOC documentation, MAINT maintainability.
- probability   W, 1 (very unlikely) to 5 (very likely). An assessment, not a measurement.
- impact        A, 1 (low) to 5 (severe).
- residual_*    W and A that remain after the countermeasure (equal to the first values if there is none).
- strategy      mitigate, accept, avoid or transfer.
- status        open, fixed (name the change), settled (not a defect, say who decided), superseded, or note.
- owner         Leave empty unless someone has taken the risk on.
- review        When the assessment is looked at again (for example `release`).

Rules
- Write the title as the risk, not as the cure.
- A closed risk is not deleted and its first assessment is never changed. Write what was done and which
  residual risk remains (accepted or not) under "Countermeasure" and "Status and history".
- An open risk may be reassessed when new facts justify it. Add a "Reassessment" entry under
  "Status and history" with the date, the old and the new values and the reason.
- Do not inflate a risk: close it and record what remains as a new risk.
- Tag every claim in the evidence: [Code] read in the code (file and line, and the commit), [Docs] taken from
  documentation (name the file), [Inference] concluded by you and not checked. Say what you did not try on a real charger.
- Do not put secrets, tokens or passwords into a risk file. Report security findings to the maintainer privately first.
-->

## Risk description

If [cause], then [event], which leads to [impact].

## Finding in detail

**Finding.** What was found, with file and line.

**Effect.** What happens to the user or the charger. Mark what you concluded without checking as [Inference].

## Assessment

<!-- risk:assessment -->
(generated)
<!-- /risk:assessment -->

## Countermeasure

What reduces the risk, or what was done. Say plainly if it is only a proposal and not implemented. Describe the residual risk and whether it is accepted.

## Status and history

<!-- risk:status -->
(generated)
<!-- /risk:status -->

Change that closed the risk (commit or pull request), or "Reassessment YYYY-MM-DD: W x → y, A x → y. Reason: ... Original assessment: ...".

## Evidence

*Evidence at the time of the finding (not today's state)*

[Code] File, line and commit (or `main` at a commit). [Docs] Name of the document. [Inference] What was concluded. What was not tried on a real device.

## Note on the assessment

W, A, strategy and residual risk are **assessments** by the author of this documentation (with AI assistance) [Inference]. They are not measured and not agreed with the maintainer. The risk owner should confirm or change them.

Architecture: [arc42](../arc42-ha-goecharger-api2.md) | [Back to the register](README.md)
