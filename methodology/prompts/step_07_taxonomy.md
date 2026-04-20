# Step 7 — Innovation Taxonomy: AI Prompts

**Methodology step**: Step 7 — Develop the innovation taxonomy
**Purpose**: Generate tagging keywords for each of the four innovation categories, and propose initial taxonomy assignments for projects in the innovative subset.
**Human review**: [hr_07_taxonomy.md](../human_review/hr_07_taxonomy.md)

### Output handling
Keywords were reviewed by authors (HR-07) and incorporated into the taxonomy tagging lexicon (`data/reference/keywords/taxonomy_keywords.json`). Python then applied these keywords to generate provisional category assignments (four binary flags: operational, technological, collaborative, financial), defaulting to operational/institutional where no category matched. A sample of assignments was passed to author review (HR-07) for validation and revision.

### Models
**Model A**: ChatGPT (GPT-4o) — approx. June–August 2025
**Model B**: DeepSeek (V3) — approx. June–August 2025

---

## Session 7.1 — Generate taxonomy keywords

### User prompt
> Based on the provided innovation taxonomy (Operational / Institutional, Technological, Collaborative, Financial), generate 15 concise tagging keywords for each innovation type. Aim for single-word (or tight compound-word) tags, not descriptive phrases or examples. Think lexical scanning. 

| Innovation Type | Examples and Features | Contexts Where Successful |
| --- | --- | --- |
| Operational/Institutional | New delivery systems, transparency and accountability mechanisms (e.g., e-governance and e-procurement) | All sectors, especially complex or fragile environments |
| Technological | Digital services (e.g., telemedicine) | Middle-income geographies; urban, governance, and health sectors |
| Collaborative | Multi-stakeholder coalitions, CDD, self-help groups | Fragile, rural, and natural resource projects |
| Financial | Fintech, psychometric testing, output-based financing, community funds | Infrastructure, financial inclusion, service delivery, urban or rural |


### ChatGPT output

Operational / Institutional

1.	E-governance
2.	E-procurement
3.	Digital-ID
4.	Grievance-redress
5.	Audit-trail
6.	Decentralization
7.	MIS
8.	Workflow-automation
9.	One-stop-shop
10.	Public-registry
11.	Interoperability
12.	Permitting-systems
13.	Beneficiary-tracking
14.	Service-charter
15.	Process-reengineering

Technological

1.	Telemedicine
2.	IoT
3.	GIS
4.	Remote-sensing
5.	Chatbots
6.	Blockchain
7.	AI
8.	Machine-learning
9.	Digital-platform
10.	E-learning
11.	Biometric
12.	Digital-payments
13.	Mobile-app
14.	Cloud-services
15.	Data-visualization

Collaborative

1.	CDD
2.	Co-creation
3.	Self-help
4.	User-committee
5.	Peer-learning
6.	Platform-coalition
7.	Public-private
8.	Stakeholder-engagement
9.	Inter-agency
10.	Community-forum
11.	Farmer-group
12.	Youth-network
13.	Participatory-planning
14.	Women’s-group
15.	Civil-society

Financial

1.	Fintech
2.	Microfinance
3.	Blended-finance
4.	Output-based
5.	Conditional-transfer
6.	Cash-transfer
7.	Community-fund
8.	Mobile-money
9.	Crowdfunding
10.	Pay-for-results
11.	Revolving-fund
12.	Subsidy-reform
13.	Risk-sharing
14.	Psychometrics
15.	Savings-group

### DeepSeek output

Here are 15 concise tagging keywords for each innovation type in the taxonomy:

Operational/Institutional

- Streamlined
- Accountable
- Transparent
- Governance
- Systematic
- Procedural
- Delivery
- Bureaucratic
- Compliance
- Oversight
- Mechanistic
- Regulatory
- Framework
- Standardized
- Adaptive

Technological

- Digital
- Automated
- Platform
- Connected
- Smart
- Tech-enabled
- Robotic
- Data-driven
- App-based
- Online
- Integrated
- Hardware
- Software
- AI
- IoT

Collaborative

- Cooperative
- Participatory
- Networked
- Coalition
- Alliance
- Partnership
- Collective
- Community-led
- Joint
- Shared
- Multi-actor
- Co-created
- Grassroots
- Federated
- Communal

Financial

- Fintech
- Funding
- Investment
- Incentivized
- Risk-sharing
- Capital
- Output-based
- Pay-for-results
- Scoring
- Microlending
- Blended-finance
- Impact-investing
- Crowdfunded
- Insured
- Bond
