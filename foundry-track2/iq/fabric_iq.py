"""Fabric IQ — semantic business layer.

Demo-grade implementation of the Fabric IQ pattern: an ontology (data/ontology.json)
that unifies certifications, roles, skills, scope tiers, and business rules so
agents reason over shared business meaning instead of raw strings. In the hosted
version this maps to a Fabric IQ ontology in Microsoft Fabric (see README).
"""

import json
from pathlib import Path


class FabricIQ:
    def __init__(self, ontology_path):
        self.ontology = json.loads(Path(ontology_path).read_text(encoding="utf-8"))
        ents = self.ontology["entities"]
        self.certs = {c["id"]: c for c in ents["certifications"]}
        self.roles = {r["name"]: r for r in ents["roles"]}
        self.tiers = {t["tier"]: t for t in ents["scope_tiers"]}
        self.rules = self.ontology["rules"]

    def certification(self, cert_id):
        return self.certs.get(cert_id)

    def required_certs_for_role(self, role_name):
        role = self.roles.get(role_name)
        return [self.certs[c] for c in role["required_certifications"]] if role else []

    def next_certification(self, role_name, passed):
        """First required cert (in order) not yet passed and with prerequisites met (rule R-3)."""
        for cert in self.required_certs_for_role(role_name):
            if cert["id"] in passed:
                continue
            if all(p in passed for p in cert.get("prerequisites", [])):
                return cert
            return None  # blocked on prerequisite
        return None  # fully certified

    def exam_ready(self, learner, cert):
        """Rule R-1: ready when practice >= threshold and hours >= 75% of recommended."""
        ready = (learner["practice_score_avg"] >= cert["pass_threshold"]
                 and learner["hours_studied"] >= 0.75 * cert["recommended_hours"])
        gap = {
            "score_gap": max(0, cert["pass_threshold"] - learner["practice_score_avg"]),
            "hours_gap": max(0, round(0.75 * cert["recommended_hours"] - learner["hours_studied"], 1)),
        }
        return ready, gap

    def at_risk(self, work_signal):
        """Rule R-2: >20 meeting hours/week correlates with low study completion."""
        return work_signal["meeting_hours_per_week"] > 20

    def tier_action(self, tier):
        """Rule R-4: tier 2/3 requests are parked, never built mid-sprint."""
        return self.tiers[tier]["action"]

    def rule(self, rule_id):
        return next((r["rule"] for r in self.rules if r["id"] == rule_id), None)
