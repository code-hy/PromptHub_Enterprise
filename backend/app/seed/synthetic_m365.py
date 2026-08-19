"""Synthetic Contoso M365 dataset for the RAG/knowledge demo (spec 42, 57).

Documents are written so the LocalRetriever's lexical scorer finds them for
demo queries such as "Project Atlas risk register", "quarterly sales", or
"cyber incident" — everything is deterministic.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Emails
# ---------------------------------------------------------------------------

EMAILS: list[dict] = [
    {
        "name": "Contoso - Executive Project Review - kickoff email thread",
        "app": "OUTLOOK",
        "department": "PROJECT_MANAGEMENT",
        "author": "Sarah Chen",
        "summary": "Kickoff correspondence for Project Atlas defining budget, timeline and steering committee.",
        "content": (
            "Subject: Project Atlas kickoff — budget and timeline.\n\n"
            "All, the Project Atlas steering committee has approved a budget of $4.2M with a target "
            "go-live of 30 November. Key milestones: requirements freeze 15 September, UAT complete 31 "
            "October, training the first two weeks of November. The risk register shows the migration "
            "dependency on legacy systems as our highest-rated risk with a score of 20 (likelihood high, "
            "impact high). Sarah Chen will chair the weekly escalation call on Mondays 09:00. Please email "
            "any risks or issues to the programme mailbox by close of business each Friday. From 45 minutes "
            "to 5 minutes for the review cycle is the team goal."
        ),
    },
    {
        "name": "Project Atlas - milestone delay notification",
        "app": "OUTLOOK",
        "department": "PROJECT_MANAGEMENT",
        "author": "David Okafor",
        "summary": "IT flags a two-week slip on the integration milestone.",
        "content": (
            "Subject: URGENT — integration milestone delay.\n\n"
            "Hi all, I need to flag an issue: the API integration with the legacy general ledger system is "
            "blocked pending vendor credentials, which will delay the requirements freeze milestone. The "
            "issue is rated medium severity. We have raised a procurement ticket to expedite the contract. "
            "Mitigation being evaluated is an interim data extract that avoids the blocked dependency. "
            "Impact to go-live is currently assessed as two weeks unless the interim approach is accepted."
        ),
    },
    {
        "name": "Customer escalation - onboarding delay complaint",
        "app": "OUTLOOK",
        "department": "CUSTOMER_SERVICE",
        "author": "James Taylor",
        "summary": "Customer complaint about onboarding timeline and suggested remedies.",
        "content": (
            "Subject: Escalation — customer onboarding delay.\n\n"
            "A key customer has escalated concerns about the onboarding timeline. The complaint references "
            "missed milestones and asks for a remediation plan. Suggested remedy: assign a dedicated "
            "onboarding manager, publish a revised plan within five business days, and provide a monthly "
            "status letter. The account team recommends prioritising the technical configuration workstream "
            "to recover two weeks of slippage."
        ),
    },
    {
        "name": "Quarterly sales performance - finance and sales email",
        "app": "OUTLOOK",
        "department": "SALES",
        "author": "Emily Wilson",
        "summary": "Quarterly sales figures showing variance to budget and pipeline movements.",
        "content": (
            "Subject: Q3 sales performance vs budget.\n\n"
            "Quarter three recognised revenue is $18.4M versus a budget of $19.8M, a shortfall of 7%. "
            "Pipeline conversion improved to 34%, driven by the enterprise segment. Average deal size is "
            "$86k, up 12% year on year. Cost of sales came in 4% under budget due to lower partner "
            "commissions. Two large deals slipped into Q4 and account for most of the variance. The "
            "forecast for Q4 is $21.5M with management attention on the two slipped deals."
        ),
    },
]

# ---------------------------------------------------------------------------
# Teams channels
# ---------------------------------------------------------------------------

TEAMS_CHANNELS: list[dict] = [
    {
        "name": "Project Atlas - general channel - weekly threads",
        "app": "TEAMS",
        "department": "PROJECT_MANAGEMENT",
        "author": "Sarah Chen",
        "summary": "Weekly channel threads capturing decisions, actions and risks.",
        "content": (
            "Decision 14: UAT will run in parallel with data migration. Action: David to circulate draft "
            "test plan by Friday. Risk: vendor credentials not yet received - owner Priya, due Friday. "
            "Priya noted the cyber incident review recommendation to patch the finance workstations cluster "
            "by end of month. Emily confirmed the budget contingency of $250k remains unallocated and "
            "available for the integration workaround."
        ),
    },
    {
        "name": "Executive briefing - data quality initiative - Teams discussion",
        "app": "TEAMS",
        "department": "DATA_ANALYTICS",
        "author": "Henry",
        "summary": "Discussion on data quality scoring and the data dictionary rollout.",
        "content": (
            "The data quality assessment shows the customer master is the weakest domain with a score of "
            "62/100, driven by duplicate records and missing address fields. The data dictionary generator "
            "will standardise column metadata across the warehouse. Outlier detection flagged the "
            "Q2 revenue adjustment as the largest anomaly. Recommendation: run the dataset summary weekly "
            "and publish the dictionary to the data catalogue."
        ),
    },
    {
        "name": "IT service desk - incident thread",
        "app": "TEAMS",
        "department": "IT",
        "author": "David Okafor",
        "summary": "Triage of open incidents including a phishing campaign and workstation patching.",
        "content": (
            "Tickets: INC-2201 phishing campaign detected in marketing inbox - closed, users re-trained. "
            "INC-2205 legacy VPN certificate expiring - assigned to network team. INC-2210 finance "
            "workstations missing critical patches - scheduled for weekend maintenance. The incident "
            "report writer will summarise the phishing incident for the board briefing."
        ),
    },
]

# ---------------------------------------------------------------------------
# Word documents
# ---------------------------------------------------------------------------

WORD_DOCS: list[dict] = [
    {
        "name": "Project Atlas - consolidated status report",
        "app": "WORD",
        "department": "PROJECT_MANAGEMENT",
        "author": "Sarah Chen",
        "summary": "Monthly status report covering scope, schedule, budget and risks.",
        "content": (
            "PROJECT ATLAS STATUS REPORT\n\n"
            "Overall health: AMBER. Scope is baseline-approved; schedule is at risk due to the integration "
            "delay. Budget spend to date is $1.85M of $4.2M (44%). Milestones: requirements freeze slipped "
            "from 15 September to 30 September; UAT target 31 October; go-live 30 November at risk. Top "
            "risks: (1) legacy general ledger integration - score 20, HIGH; (2) key vendor availability - "
            "score 12; (3) data migration completeness - score 10. Issues: vendor credentials outstanding. "
            "The steering committee meets Mondays 09:00; the executive summary goal is to cut the review "
            "cycle from 45 minutes to 5 minutes."
        ),
    },
    {
        "name": "Contoso - cyber incident review report",
        "app": "WORD",
        "department": "IT",
        "author": "Priya Sharma",
        "summary": "Post-incident review of a phishing campaign including recommendations.",
        "content": (
            "INCIDENT REVIEW INC-2201\n\n"
            "A phishing campaign targeted the marketing department on 12 July. Five users clicked and three "
            "credentials were exposed; the account was locked within 40 minutes. Root cause: missing "
            "multi-factor enrolment on legacy accounts and delayed patch of the finance workstations "
            "cluster. Recommendations: enforce MFA for all accounts, complete the workstation patching "
            "schedule, and run simulated phishing monthly. The incident report writer summarises this "
            "document for the board briefing."
        ),
    },
    {
        "name": "Contoso - digital transformation strategy 2026",
        "app": "WORD",
        "department": "EXECUTIVE",
        "author": "Olivia Brown",
        "summary": "Strategy paper describing the AI-enabled operating model.",
        "content": (
            "CONTOSO DIGITAL TRANSFORMATION STRATEGY\n\n"
            "Goal: embed an AI-enabled operating model across finance, HR, marketing and operations. "
            "Context: legacy processes cost approximately 40 minutes per knowledge task. Source: internal "
            "benchmarks and competitor analysis. Expectations: a phased roadmap, a governance framework "
            "for AI use cases, and key performance indicators including time saved per employee. The "
            "executive presentation will condense this paper into a board deck with speaker notes."
        ),
    },
    {
        "name": "Contoso - procurement vendor assessment memo",
        "app": "WORD",
        "department": "FINANCE",
        "author": "Emily Wilson",
        "summary": "Vendor comparison for the integration supplier extension.",
        "content": (
            "VENDOR ASSESSMENT MEMO\n\n"
            "Three vendors were evaluated for the Project Atlas integration extension: NorthBridge (best "
            "capability, highest cost), Keystone Partners (mid capability, best value), and AtlasOps "
            "(lowest score on security review). Recommendation: award to Keystone Partners for the interim "
            "data extract workstream. The vendor assessment uses a weighted scoring model of 40% "
            "capability, 30% cost, 20% security, 10% delivery track record."
        ),
    },
]

# ---------------------------------------------------------------------------
# Excel workbooks
# ---------------------------------------------------------------------------

EXCEL_WORKBOOKS: list[dict] = [
    {
        "name": "Project Atlas - risk register workbook",
        "app": "EXCEL",
        "department": "PROJECT_MANAGEMENT",
        "author": "Priya Sharma",
        "summary": "Risk register with likelihood, impact and mitigation ratings.",
        "content": (
            "RISK REGISTER\n"
            "ID, Risk, Likelihood, Impact, Score, Owner, Mitigation\n"
            "R01, Legacy GL integration blocked, High, High, 20, David, Interim extract workaround\n"
            "R02, Vendor resource availability, Medium, High, 12, Priya, Contract expedite\n"
            "R03, Data migration completeness, Medium, Medium, 9, Sarah, Reconciliation plan\n"
            "R04, Regulatory change scope, Low, High, 6, Olivia, Early legal review\n"
            "R05, Budget overrun on training, Low, Medium, 4, Emily, Cap contingency\n"
            "R06, Key stakeholder turnover, Low, Medium, 4, Sarah, Succession alignment"
        ),
    },
    {
        "name": "Contoso - quarterly KPI workbook",
        "app": "EXCEL",
        "department": "FINANCE",
        "author": "Emily Wilson",
        "summary": "Quarterly KPIs: revenue, margin, attrition, NPS with targets and actuals.",
        "content": (
            "QUARTERLY KPIS\n"
            "Metric, Q1, Q2, Q3, Target, Variance\n"
            "Revenue ($M), 15.2, 16.8, 18.4, 19.0, -3%\n"
            "Gross margin (%), 61, 60, 58, 60, -2pts\n"
            "Customer attrition (%), 3.1, 2.9, 2.6, 3.0, +0.4pts\n"
            "NPS, 41, 44, 47, 45, +2\n"
            "Pipeline conversion (%), 28, 31, 34, 33, +1pt"
        ),
    },
    {
        "name": "Contoso - budget vs actual workbook",
        "app": "EXCEL",
        "department": "FINANCE",
        "author": "Emily Wilson",
        "summary": "Full-year budget, actual and variance by cost centre.",
        "content": (
            "BUDGET VS ACTUAL\n"
            "Cost centre, Budget ($k), Actual ($k), Variance (%)\n"
            "IT Operations, 1,240, 1,312, +6%\n"
            "Sales Enablement, 610, 574, -6%\n"
            "Data Platform, 830, 902, +9%\n"
            "Marketing, 720, 701, -3%\n"
            "Project Atlas, 4,200, 1,850, 44% YTD"
        ),
    },
]

# ---------------------------------------------------------------------------
# PowerPoint
# ---------------------------------------------------------------------------

POWERPOINT_DECKS: list[dict] = [
    {
        "name": "Project Atlas - steering committee deck",
        "app": "POWERPOINT",
        "department": "PROJECT_MANAGEMENT",
        "author": "Sarah Chen",
        "summary": "Steering deck with health, timeline and the '45 to 5' productivity story.",
        "content": (
            "STEERING COMMITTEE DECK\n"
            "Slide 1: Project Atlas - status AMBER.\n"
            "Slide 2: Schedule - integration delay, UAT target 31 October.\n"
            "Slide 3: Budget - $1.85M of $4.2M spent (44%).\n"
            "Slide 4: Top risk - legacy GL integration (score 20).\n"
            "Slide 5: Productivity - AI review cycle cut from 45 minutes to 5 minutes per iteration."
        ),
    },
    {
        "name": "Contoso - Q3 board deck",
        "app": "POWERPOINT",
        "department": "EXECUTIVE",
        "author": "Olivia Brown",
        "summary": "Board deck covering quarterly results, risks and strategy.",
        "content": (
            "Q3 BOARD DECK\n"
            "Slide 1: Revenue $18.4M, shortfall 7% vs budget.\n"
            "Slide 2: Margin pressure from cost of sales.\n"
            "Slide 3: Digital transformation - AI operating model approved.\n"
            "Slide 4: Cyber risk - remediation plan in progress.\n"
            "Slide 5: Outlook - Q4 forecast $21.5M."
        ),
    },
]

DOCUMENT_SETS = {
    "emails": EMAILS,
    "teams": TEAMS_CHANNELS,
    "word": WORD_DOCS,
    "excel": EXCEL_WORKBOOKS,
    "powerpoint": POWERPOINT_DECKS,
}


def build_all() -> list[dict]:
    """Return a flat list of document dicts with a stable doc_id per set."""
    docs: list[dict] = []
    seen: dict[str, int] = {}
    for kind, items in DOCUMENT_SETS.items():
        for item in items:
            doc_type = {
                "emails": "EMAIL",
                "teams": "TEAMS",
                "word": "DOCUMENT",
                "excel": "SPREADSHEET",
                "powerpoint": "PRESENTATION",
            }[kind]
            seen[kind] = seen.get(kind, 0) + 1
            docs.append(
                {
                    "doc_id": f"DOC-{kind.upper()}-{seen[kind]:02d}",
                    "name": item["name"],
                    "doc_type": doc_type,
                    "source_app": item["app"],
                    "department": item["department"],
                    "author": item["author"],
                    "summary": item["summary"],
                    "content": item["content"],
                    "metadata_": {"synthetic": True, "set": kind, "source": "Contoso M365"},
                }
            )
    return docs
