"""Study Plan Generator — converts curated content into a capacity-aware schedule.
Grounding: Fabric IQ (recommended hours, thresholds), Work IQ (focus capacity).
"""

import math

from agents.base_agent import BaseAgent


class StudyPlanGenerator(BaseAgent):
    name = "StudyPlanGenerator"
    instructions = (
        "You are the Study Plan Generator. Build a practical, capacity-aware "
        "study schedule. Allocate hours only inside the learner's focus time "
        "(rule R-5); never schedule over meeting-heavy periods."
    )

    def run(self, learner, cert_id):
        fabric, work = self.ctx.fabric_iq, self.ctx.work_iq
        cert = fabric.certification(cert_id)
        capacity = work.weekly_study_capacity(learner["learner_id"])
        remaining = max(0, cert["recommended_hours"] - learner["hours_studied"])
        weeks = max(1, math.ceil(remaining / capacity)) if remaining else 0
        signal = work.signal(learner["learner_id"]) or {}
        grounding = self.ctx.retrieve("recommended study pattern focus hours weekly checkpoints",
                                      scope="shared")

        def offline():
            return {
                "plan": {
                    "certification": cert_id,
                    "remaining_hours": remaining,
                    "weekly_capacity_hours": capacity,
                    "estimated_weeks": weeks,
                    "slot": signal.get("preferred_learning_slot", "Morning"),
                    "milestones": [
                        f"Week {w}: {min(capacity, remaining - capacity * (w - 1)):.1f}h focused study + practice checkpoint"
                        for w in range(1, weeks + 1)
                    ] or ["Hours requirement already met — proceed to readiness assessment"],
                },
                "answer": (
                    f"{learner['learner_id']} needs {remaining}h more for {cert_id} "
                    f"(rule R-1 requires >= {0.75 * cert['recommended_hours']:.0f}h). "
                    f"Capacity is {capacity}h/week inside focus time, so plan "
                    f"{weeks} week(s) of {signal.get('preferred_learning_slot', 'Morning').lower()} "
                    f"study blocks with weekly practice checkpoints."
                ),
            }

        return self.execute(
            task=f"Generate a study schedule for {learner['learner_id']} toward {cert_id}: "
                 f"{remaining}h remaining, {capacity}h/week focus capacity, "
                 f"meeting load {signal.get('meeting_hours_per_week', '?')}h/week.",
            grounding=grounding,
            offline_fn=offline,
            extra={"learner_id": learner["learner_id"], "certification": cert_id},
        )
