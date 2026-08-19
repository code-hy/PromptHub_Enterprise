"""Five complete promptbooks / workflows (spec 25, 55, 56).

Workflows reference prompts by name; the seed resolves names to prompt rows.
"""

WORKFLOWS: list[dict] = [
    {
        "name": "Executive Project Review",
        "description": "Turn raw project inputs (emails, Teams, reports, risk register) into an executive summary and recommended actions — the flagship '45 minutes to 5 minutes' demo (spec 65).",
        "business_function": "PROJECT_MANAGEMENT",
        "tags": ["project", "executive", "demo"],
        "steps": [
            {
                "name": "Extract project information",
                "prompt_name": "Email Action Extractor",
                "mapping": {"emails": "input.project_emails"},
            },
            {
                "name": "Identify risks",
                "prompt_name": "Project Risk Assessment",
                "mapping": {"risk_register": "input.risk_register"},
            },
            {
                "name": "Identify issues",
                "prompt_name": "Issue Analysis",
                "mapping": {"issues": "input.project_issues"},
            },
            {
                "name": "Assess business impact",
                "prompt_name": "Project Health Assessment",
                "mapping": {"project_data": "input.project_data"},
            },
            {
                "name": "Generate executive summary",
                "prompt_name": "Executive Summary",
                "mapping": {"document": "step_4.output"},
            },
            {
                "name": "Generate recommended actions",
                "prompt_name": "Action Tracker",
                "mapping": {"sources": "step_5.output"},
            },
        ],
    },
    {
        "name": "Weekly Meeting Triage",
        "description": "Convert meeting transcripts into decisions, actions and risks in one pass.",
        "business_function": "PROJECT_MANAGEMENT",
        "tags": ["meeting", "actions"],
        "steps": [
            {
                "name": "Summarise meeting",
                "prompt_name": "Meeting Summary",
                "mapping": {"transcript": "input.transcript"},
            },
            {
                "name": "Extract actions",
                "prompt_name": "Meeting Actions",
                "mapping": {"transcript": "input.transcript"},
            },
            {
                "name": "Extract decisions",
                "prompt_name": "Meeting Decisions",
                "mapping": {"transcript": "input.transcript"},
            },
            {
                "name": "Extract risks",
                "prompt_name": "Meeting Risk Extractor",
                "mapping": {"transcript": "input.transcript"},
            },
            {
                "name": "Send follow-up email",
                "prompt_name": "Meeting Follow-up Email",
                "mapping": {"meeting_notes": "step_1.output"},
            },
        ],
    },
    {
        "name": "Inbox Zero",
        "description": "Process an email backlog into a priority inbox summary and follow-ups.",
        "business_function": "OPERATIONS",
        "tags": ["email", "productivity"],
        "steps": [
            {
                "name": "Classify email priorities",
                "prompt_name": "Email Priority Classifier",
                "mapping": {"emails": "input.emails"},
            },
            {
                "name": "Summarise thread",
                "prompt_name": "Email Summariser",
                "mapping": {"email_thread": "input.emails"},
            },
            {
                "name": "Extract actions",
                "prompt_name": "Email Action Extractor",
                "mapping": {"emails": "input.emails"},
            },
            {
                "name": "Draft follow-ups",
                "prompt_name": "Follow-up Email Generator",
                "mapping": {
                    "outstanding_item": "step_3.output",
                    "original_request": "input.emails",
                    "recipient": "input.recipient",
                },
            },
        ],
    },
    {
        "name": "Data Quality Review",
        "description": "Assess a dataset, explain findings and produce a remediation plan.",
        "business_function": "DATA_ANALYTICS",
        "tags": ["data", "quality"],
        "steps": [
            {
                "name": "Assess data quality",
                "prompt_name": "Data Quality Assessment",
                "mapping": {"dataset": "input.dataset"},
            },
            {
                "name": "Summarise dataset",
                "prompt_name": "Dataset Summary",
                "mapping": {"dataset": "input.dataset"},
            },
            {
                "name": "Detect outliers",
                "prompt_name": "Outlier Detection",
                "mapping": {"dataset": "input.dataset"},
            },
            {
                "name": "Generate dictionary",
                "prompt_name": "Data Dictionary Generator",
                "mapping": {"metadata": "input.metadata"},
            },
        ],
    },
    {
        "name": "Executive Deck Builder",
        "description": "Build an executive presentation from report and dataset inputs.",
        "business_function": "EXECUTIVE",
        "tags": ["presentation", "executive"],
        "steps": [
            {
                "name": "Summarise source report",
                "prompt_name": "Executive Summary",
                "mapping": {"document": "input.report"},
            },
            {
                "name": "Create deck outline",
                "prompt_name": "Executive Presentation",
                "mapping": {"source_material": "step_1.output"},
            },
            {
                "name": "Write speaker notes",
                "prompt_name": "Speaker Notes",
                "mapping": {"slides": "step_2.output"},
            },
        ],
    },
]
