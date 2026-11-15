# Proposed change management and operating model

This is a hypothetical adoption plan. No actual employees were trained or surveyed.

Start with shadow mode: preserve the current replenishment process, generate recommendations on the same frozen inputs, and ask an authorized inventory manager to record whether each proposal is accepted, modified or rejected and why. The demonstration's in-memory buttons illustrate this interaction; they are not a durable enterprise approval system.

Training should use real product examples: interpret WAPE/bias and forecast uncertainty, distinguish sales from unconstrained demand, inspect lead-time/safety assumptions, understand budget tradeoffs and avoid reading simulation costs as realized savings. Require a short competence check and access to a plain-language operating guide. Finance should teach the exact cost definitions and terminal inventory treatment.

Proposed operational ownership: Operations accountable for replenishment continuity; Inventory Manager owns order decisions; Analyst owns daily data-quality checks; ML Engineer owns model/fallback health and versioning; Finance owns assumptions and benefit measurement; QA owns release evidence. Assign named people and backup coverage before a pilot.

Adoption metrics: proportion of plans reviewed before cutoff, acceptance/modification/rejection rate, documented override reasons, time spent reviewing, completion of training, and unresolved exceptions. These should be measured alongside stock availability, fill rate, cash tied in stock and forecast error. Do not incentivize high acceptance regardless of outcome.

Monitoring proposal: daily schema/completeness/volume checks, lead-time and price freshness, order-budget/pack validation; weekly WAPE/bias by product, model fallback counts, availability-censoring indicators and override patterns; monthly Finance reconciliation and drift review. Pilot alert thresholds must be agreed on real data rather than invented from this short study.

Escalation: block recommendations on invalid inputs or constraint failures; send the issue to the operational owner; retain source/config/output versions and investigate. Cost assumption changes require Finance review; model changes require a new development comparison and a fresh future validation period. Never tune repeatedly on the preserved holdout.

Rollback: stop generating candidate recommendations, restore the last validated baseline policy and approved assumptions, leave actual procurement under the existing human process, reconcile outstanding orders, and communicate the incident. Re-enable only after QA verifies the fix and Operations approves the documented decision. There is no automatic execution path in this application to disable.
