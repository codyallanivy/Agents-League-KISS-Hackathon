"""Orchestrator — planner-executor pattern with a critic/verifier pass.

Coordinates the five scenario agents end-to-end:
  plan → execute (curator → study plan → engagement → assessment) → critic
The critic verifies every agent answer carries citations before the final
synthesis is returned (Critic/Verifier reasoning pattern).
"""

from agents.base_agent import AgentContext
from agents.learning_path_curator import LearningPathCurator
from agents.study_plan_generator import StudyPlanGenerator
from agents.engagement_agent import EngagementAgent
from agents.assessment_agent import AssessmentAgent
from agents.manager_insights import ManagerInsightsAgent


class KISSOrchestrator:
    def __init__(self, ctx: AgentContext):
        self.ctx = ctx
        self.curator = LearningPathCurator(ctx)
        self.planner = StudyPlanGenerator(ctx)
        self.engagement = EngagementAgent(ctx)
        self.assessment = AssessmentAgent(ctx)
        self.insights = ManagerInsightsAgent(ctx)

    # ---- learner journey (baseline flow from the challenge scenario) --------
    def learner_journey(self, learner):
        plan_steps = ["curate_path", "generate_study_plan", "plan_engagement",
                      "assess_readiness", "critic_verify"]
        self.ctx.tracer.log(agent="Orchestrator", phase="plan",
                            output={"steps": plan_steps},
                            extra={"learner_id": learner["learner_id"]})

        curated = self.curator.run(learner)
        cert_id = curated.get("target_certification", learner["certification"])
        study = self.planner.run(learner, cert_id)
        engage = self.engagement.run(learner)
        assess = self.assessment.readiness(learner, cert_id)

        steps = {"curator": curated, "study_plan": study,
                 "engagement": engage, "assessment": assess}
        critic = self._critic(steps)
        synthesis = {
            "learner_id": learner["learner_id"],
            "target_certification": cert_id,
            "verdict": assess.get("verdict", "WARN"),
            "steps": steps,
            "critic": critic,
        }
        self.ctx.tracer.log(agent="Orchestrator", phase="synthesis",
                            output={"verdict": synthesis["verdict"],
                                    "critic": critic},
                            extra={"learner_id": learner["learner_id"]})
        return synthesis

    # ---- applied governance flow (scope exam on a live project) -------------
    def scope_request(self, feature_request, vision_text):
        result = self.assessment.applied_scope_exam(feature_request, vision_text)
        critic = self._critic({"assessment": result})
        result["critic"] = critic
        return result

    # ---- manager view --------------------------------------------------------
    def team_insights(self, learners):
        result = self.insights.run(learners)
        result["critic"] = self._critic({"insights": result})
        return result

    # ---- critic/verifier ------------------------------------------------------
    def _critic(self, steps):
        """Verify grounding hygiene: every step must carry citations."""
        issues = [f"{name}: missing citations"
                  for name, r in steps.items() if not r.get("citations")]
        verdict = "PASS" if not issues else "FAIL"
        self.ctx.tracer.log(agent="Critic", phase="verify",
                            output={"verdict": verdict, "issues": issues})
        return {"verdict": verdict, "issues": issues}
