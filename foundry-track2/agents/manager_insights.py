"""Manager Insights Agent — team-level visibility into readiness and risk.
Grounding: Fabric IQ rules over synthetic learner metrics + Work IQ capacity
signals. Presents aggregates only — no sensitive personal detail.
"""

from agents.base_agent import BaseAgent


class ManagerInsightsAgent(BaseAgent):
    name = "ManagerInsightsAgent"
    instructions = (
        "You are the Manager Insights Agent. Summarise team certification "
        "readiness, capacity constraints, and risk patterns at aggregate level. "
        "Never expose sensitive personal data; learners are referenced by "
        "synthetic IDs only."
    )

    def run(self, learners):
        fabric, work = self.ctx.fabric_iq, self.ctx.work_iq
        rows, ready_n, risk_n = [], 0, 0
        for l in learners:
            cert = fabric.certification(l["certification"])
            ready, gap = fabric.exam_ready(l, cert)
            signal = work.signal(l["learner_id"]) or {}
            at_risk = fabric.at_risk(signal) if signal else False
            ready_n += ready
            risk_n += at_risk
            rows.append({
                "learner_id": l["learner_id"], "role": l["role"],
                "certification": l["certification"], "ready": ready,
                "at_risk": at_risk, "score_gap": gap["score_gap"],
                "hours_gap": gap["hours_gap"],
            })
        grounding = self.ctx.retrieve("manager readiness risk meeting hours pass rate",
                                      scope="shared")

        def offline():
            risky = [r["learner_id"] for r in rows if r["at_risk"]]
            return {
                "team_summary": {
                    "learners": len(rows), "exam_ready": ready_n,
                    "capacity_at_risk": risk_n, "rows": rows,
                },
                "answer": (
                    f"Team readiness: {ready_n}/{len(rows)} exam-ready. "
                    f"{risk_n} learner(s) capacity-constrained by >20h/week meetings "
                    f"(rule R-2): {', '.join(risky) or 'none'} — recommend protecting "
                    "focus blocks. Largest gaps are study-hours, not scores: schedule "
                    "study time before booking exams (rule R-1)."
                ),
            }

        return self.execute(
            task=f"Summarise certification readiness and risk for {len(rows)} learners "
                 "at aggregate level (synthetic IDs only).",
            grounding=grounding,
            offline_fn=offline,
            extra={"team_size": len(rows)},
        )
