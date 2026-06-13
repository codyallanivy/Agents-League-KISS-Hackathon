"""Assessment Agent — evaluates readiness with grounded, cited questions, and
runs the *applied* exam: live scope reasoning on a real project's files.

Decision semantics: ACCEPT (in scope / ready), WARN (borderline — human call),
BLOCK (out of scope / not ready). Tier 2/3 requests are parked per rule R-4.
"""

import re

from agents.base_agent import BaseAgent


class AssessmentAgent(BaseAgent):
    name = "AssessmentAgent"
    instructions = (
        "You are the Assessment Agent for the KISS certification programme. "
        "Generate credible practice questions cited from approved content, and "
        "grade applied scope-reasoning exercises against the project's "
        "PRODUCT_VISION.md. Use ACCEPT/WARN/BLOCK semantics; Tier 2/3 requests "
        "are parked in DECISIONS.md, never built mid-sprint (rule R-4)."
    )

    # --- Part 1: readiness check + grounded practice questions ---------------
    def readiness(self, learner, cert_id):
        cert = self.ctx.fabric_iq.certification(cert_id)
        ready, gap = self.ctx.fabric_iq.exam_ready(learner, cert)
        grounding = self.ctx.retrieve(
            f"{cert['name']} pass threshold practice exam format", scope="shared")

        def offline():
            questions = [
                f"Q{i + 1}. According to [{g['citation']}]: {self._question_from(g['snippet'])}"
                for i, g in enumerate(grounding[:3])
            ]
            verdict = "ACCEPT" if ready else ("WARN" if gap["score_gap"] <= 8 else "BLOCK")
            return {
                "verdict": verdict,
                "ready": ready,
                "gaps": gap,
                "practice_questions": questions,
                "answer": (
                    f"{learner['learner_id']} readiness for {cert_id}: {verdict}. "
                    + ("Meets rule R-1 — schedule the exam." if ready else
                       f"Gaps — practice score short by {gap['score_gap']} pts, "
                       f"study hours short by {gap['hours_gap']}h (rule R-1).")
                ),
            }

        return self.execute(
            task=f"Assess exam readiness of {learner['learner_id']} for {cert_id} "
                 f"(practice {learner['practice_score_avg']}%, threshold {cert['pass_threshold']}%, "
                 f"{learner['hours_studied']}h of {cert['recommended_hours']}h) and generate "
                 "3 cited practice questions.",
            grounding=grounding,
            offline_fn=offline,
            extra={"learner_id": learner["learner_id"], "certification": cert_id},
        )

    # --- Part 2: applied exam — live scope reasoning -------------------------
    def applied_scope_exam(self, feature_request, project_vision_text):
        tier = self._classify_tier(feature_request, project_vision_text)
        action = self.ctx.fabric_iq.tier_action(tier)
        grounding = self.ctx.retrieve("tier classification scope creep park decisions revisit",
                                      scope="shared")

        def offline():
            verdict = {1: "ACCEPT", 2: "WARN", 3: "BLOCK"}[tier]
            decision_entry = (
                f"D-NEW | Feature: {feature_request} | Tier: {tier} | "
                f"Action: {action} | Revisit: after v1 launch"
            ) if tier > 1 else None
            return {
                "verdict": verdict,
                "tier": tier,
                "action": action,
                "decision_entry": decision_entry,
                "answer": (
                    f"'{feature_request}' → Tier {tier} → {verdict}. "
                    + ("In current sprint scope: proceed." if tier == 1 else
                       f"Rule R-4: capture it, don't build it. Park in DECISIONS.md: {decision_entry}")
                ),
            }

        baseline = offline()
        result = self.execute(
            task=f"Applied exam: classify '{feature_request}' against the project vision "
                 f"and choose ACCEPT/WARN/BLOCK with the correct KISS action.\n\n"
                 f"Deterministic KISS classifier result: Tier {tier}, "
                 f"verdict {baseline['verdict']}, action {action}. Use this "
                 "classification unless the cited project vision clearly proves it wrong.\n\n"
                 f"PRODUCT_VISION excerpt:\n{project_vision_text[:600]}",
            grounding=grounding,
            offline_fn=offline,
            extra={"feature_request": feature_request, "tier": tier},
        )
        for key in ("verdict", "tier", "action", "decision_entry"):
            result.setdefault(key, baseline.get(key))
        return result

    # --- helpers --------------------------------------------------------------
    def _classify_tier(self, request, vision_text):
        """Parse tier sections from PRODUCT_VISION.md and score the request
        against each tier's listed items by term coverage. Conservative by
        design: weak/unknown matches are parked, never built (rule R-4)."""
        req_terms = set(re.findall(r"[a-z]+", request.lower())) - {
            "the", "a", "an", "add", "can", "we", "for", "with", "and", "our",
            "show", "to", "of", "in", "it"}
        patterns = {1: r"Tier 1", 2: r"Tier 2", 3: r"(?:Tier 3|Out of Scope)"}
        coverage = {}
        for tier, pat in patterns.items():
            m = re.search(r"###? .*" + pat + r".*?\n(.*?)(?=\n###? |\Z)",
                          vision_text, re.S)
            if not m:
                continue
            items = " ".join(re.findall(r"- .{0,3}? ?(.+)", m.group(1))).lower()
            matched = sum(1 for t in req_terms if t in items)
            coverage[tier] = matched / max(1, len(req_terms))
        if not coverage or max(coverage.values()) == 0:
            return 2  # unknown request: park it, human decides
        # ties resolve to the HIGHER tier (more cautious)
        best_tier = max(coverage, key=lambda t: (coverage[t], t))
        if best_tier == 1 and coverage[1] < 0.6:
            return 2  # partial Tier-1 overlap is not licence to build
        return best_tier

    @staticmethod
    def _question_from(snippet):
        first = snippet.split(".")[0][:140]
        return f"Complete the rule — \"{first}...\"?"
