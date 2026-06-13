"""Learning Path Curator — suggests certification content for a learner's role.
Grounding: Foundry IQ knowledge base (cited), Fabric IQ role→certification map.
"""

from agents.base_agent import BaseAgent


class LearningPathCurator(BaseAgent):
    name = "LearningPathCurator"
    instructions = (
        "You are the Learning Path Curator for the KISS AI-Collaboration "
        "Certification programme. Map a learner's role and goal to the right "
        "certification and return cited content from the approved knowledge "
        "base only — never unsupported free-text recommendations."
    )

    def run(self, learner):
        fabric = self.ctx.fabric_iq
        passed = set(learner.get("passed", []))
        # Derive implicit prerequisites already passed (current cert implies its prereqs)
        cur = fabric.certification(learner["certification"])
        if cur:
            passed.update(cur.get("prerequisites", []))
        target = fabric.next_certification(learner["role"], passed) or cur
        grounding = self.ctx.foundry_iq.retrieve(
            f"{target['name']} skills {' '.join(target['skills'])}")

        def offline():
            return {
                "target_certification": target["id"],
                "answer": (
                    f"Recommended path for {learner['role']} {learner['learner_id']}: "
                    f"{target['id']} — {target['name']}. Focus skills: "
                    f"{', '.join(target['skills'])}. "
                    f"Study the cited sections of the certification guide; "
                    f"prerequisites satisfied: {sorted(passed) or 'none required'}."
                ),
            }

        result = self.execute(
            task=f"Curate a learning path toward {target['id']} for a {learner['role']} "
                 f"(passed: {sorted(passed)}). Return focus skills and cited content.",
            grounding=grounding,
            offline_fn=offline,
            extra={"learner_id": learner["learner_id"]},
        )
        result["target_certification"] = result.get("target_certification", target["id"])
        return result
