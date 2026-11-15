# Stakeholder and communication plan

All roles below are fictional planning roles. Dmitry Petrushin implemented this portfolio independently. No interviews, meetings, approvals or team feedback are represented as actual events.

| Role | Interest / influence | Proposed communication | Cadence | Decision or evidence |
|---|---|---|---|---|
| Project Sponsor | Value and risk / high | One-page decision brief | Weekly and gates | Scope, investment, pilot approval |
| Operations Manager | Service and continuity / high | Process and exception review | Weekly | Operating owner, escalation, rollback |
| Inventory Manager | Usable replenishment / high | Hands-on plan review | Each replenishment cycle | Accept/reject recommendations |
| Data Analyst | Data interpretation / medium | Data-quality exceptions | Daily in pilot | Sales/availability definitions |
| ML Engineer | Model reliability / medium | Error/drift dashboard | Weekly and incidents | Model/fallback revisions |
| Finance Representative | Working capital and modeled cost / high | Cost reconciliation and scenario review | Fortnightly and gates | Validated cost assumptions |
| QA Engineer | Acceptance evidence / medium | Test and defect report | Each release | Verified gates, defect severity |

R = responsible; A = accountable; C = consulted; I = informed. One accountable role per activity.

| Activity | Sponsor | Operations | Inventory | Analyst | ML | Finance | QA |
|---|---|---|---|---|---|---|---|
| Approve charter and scope | A | R | C | C | C | C | I |
| Define data contract and quality | I | A | C | R | C | I | C |
| Freeze model evaluation | I | C | C | C | A/R | I | C |
| Validate cost assumptions | I | C | C | R | C | A | C |
| Build and test decision support | I | A | C | C | R | C | R |
| Review proposed orders | I | C | A/R | I | C | C | I |
| Release acceptance evidence | I | A | C | C | R | C | R |
| Authorize analytical pilot | A | R | C | C | C | C | C |
| Respond to operational incident | I | A | R | R | R | C | C |

Escalation proposal: data corruption or budget breaches stop recommendations immediately and notify Operations; Finance reviews cost assumption changes; Sponsor resolves unresolved scope/risk tradeoffs. Real approvals would be recorded in an organization's durable decision log, which this local demonstration does not implement.
