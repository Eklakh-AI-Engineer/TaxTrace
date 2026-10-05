# UI Specification

**Version:** 1.0

---

# 1. UX Philosophy

The interface must help a CA answer:

> What needs my attention, why, and what evidence supports it?

Do not design the application as a generic chatbot.

---

# 2. Primary Navigation

```text
Dashboard
Clients
Reconciliation
Exceptions
Notices
Tasks
Knowledge
Audit
Settings
```

The first MVP can hide advanced sections until implemented.

---

# 3. Dashboard

Show:

- open exceptions;
- high-value exceptions;
- overdue tasks;
- notice deadlines;
- recent reconciliation runs;
- processing failures.

Example:

```text
Good morning

Open exceptions     78
High priority        9
Notice deadlines     3
Overdue tasks        7

Recent clients
ABC Traders
XYZ Enterprises
...
```

No alarming colors should be used merely for visual decoration. Severity should be explicit.

---

# 4. Reconciliation Page

Controls:

```text
Client
Period
Books file
GSTR-2B file
Rule version
[Run Reconciliation]
```

After processing:

```text
Matched           1,200
Partial              24
Missing in 2B        41
Missing in Books     13
Duplicates             3
```

Filters:

- exception type;
- severity;
- supplier;
- amount;
- status;
- assigned user.

---

# 5. Exception Detail

Recommended layout:

```text
-------------------------------------------------
Exception: VALUE_MISMATCH
Severity: HIGH
Status: IN REVIEW

BOOK RECORD                 GSTR-2B RECORD
Invoice: INV-1001           Invoice: INV-1001
GSTIN: ...                  GSTIN: ...
Taxable: ₹50,000            Taxable: ₹48,000
IGST: ₹9,000                IGST: ₹8,640

Why flagged?
[Deterministic rule explanation]

AI explanation
[Evidence-grounded explanation]

Evidence
[Book row] [GSTR-2B row] [Source document]

Actions
[Accept] [Reject] [Needs Info] [Create Task]
-------------------------------------------------
```

---

# 6. Notice Workspace

Sections:

1. Notice summary
2. Extracted facts
3. Issues
4. Retrieved authorities
5. Draft response
6. Citation verification
7. Evidence/attachments
8. Approval history

---

# 7. Draft Editor

The user must be able to:

- edit text;
- view citations;
- inspect source;
- see AI-generated sections;
- add comments;
- save versions;
- request regeneration of a selected section;
- approve/reject.

Never make "Send" the primary action for an AI-generated legal draft. "Review" and "Approve" should precede any external action.

---

# 8. Tasks

Columns:

```text
Open
In Progress
Blocked
Completed
```

Each task shows:
- client;
- source exception/notice;
- owner;
- due date;
- priority;
- last update.

---

# 9. WhatsApp UX

Commands should be short and natural.

Examples:

```text
show today's pending

show high-value mismatches for ABC

why is invoice 392 missing?

upload notice

what is pending for Sharma Traders?
```

The bot should confirm actions that create side effects.

Example:

```text
I prepared a supplier follow-up draft.

Send it?

[Review] [Send]
```

---

# 10. Accessibility

Minimum:
- keyboard navigation;
- readable contrast;
- visible focus states;
- descriptive labels;
- errors not conveyed by color alone;
- responsive layout.

---

# 11. UI States

Every async operation must show:

- queued;
- processing;
- completed;
- failed;
- retry available.

Never show an empty screen while a background job is running.

---

# 12. Error UX

Errors should say:

1. what happened;
2. what the user can do;
3. whether data was saved.

Example:

> We could not parse this XLSX file. No reconciliation was started. Please verify that the workbook contains the required columns and upload again.

---

# 13. Design Rule

The interface should optimize for **investigation and approval**, not for displaying AI-generated prose.
