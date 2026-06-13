"""Engagement Agent — keeps learners on track without disrupting peak work.
Grounding: Work IQ signals (meeting load, focus windows, preferred slots).
"""

from agents.base_agent import BaseAgent


class EngagementAgent(BaseAgent):
    name = "EngagementAgent"
    instructions = (
        "You are the Engagement Agent. Suggest reminder timing adapted to each "
        "learner's work rhythm. Never propose one-size-fits-all reminders; "
        "respect focus time and avoid meeting-heavy periods. Be supportive and "
        "privacy-conscious."
    )

    def run(self, learner):
        work = self.ctx.work_iq
        signal = work.signal(learner["learner_id"]) or {}
        window = work.reminder_window(learner["learner_id"])
        at_risk = self.ctx.fabric_iq.at_risk(signal) if signal else False
        grounding = self.ctx.retrieve("meeting hours study completion focus time managers",
                                      scope="shared")

        def offline():
            nudge = (
                f"Schedule {signal.get('preferred_learning_slot', 'morning').lower()} reminders: {window}. "
                + ("Meeting load exceeds 20h/week (rule R-2) — flag to manager to protect focus time; "
                   "reduce reminder frequency to avoid pile-on." if at_risk
                   else "Healthy focus capacity — weekly cadence with a practice-checkpoint nudge.")
            )
            return {"reminder_window": window, "at_risk": at_risk, "answer": nudge}

        return self.execute(
            task=f"Plan engagement for {learner['learner_id']}: "
                 f"meetings {signal.get('meeting_hours_per_week', '?')}h/wk, "
                 f"focus {signal.get('focus_hours_per_week', '?')}h/wk, "
                 f"prefers {signal.get('preferred_learning_slot', '?')}.",
            grounding=grounding,
            offline_fn=offline,
            extra={"learner_id": learner["learner_id"], "at_risk": at_risk},
        )
