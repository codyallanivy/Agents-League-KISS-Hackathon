"""Work IQ — work-context layer.

Demo-grade implementation of the Work IQ pattern: synthetic work signals
(meeting load, focus hours, preferred learning slots) that personalise
scheduling and engagement. In production this layer is fed by Microsoft 365
tenant signals; here it reads data/work_signals.json (synthetic only).
"""

import json
from pathlib import Path


class WorkIQ:
    def __init__(self, signals_path):
        raw = json.loads(Path(signals_path).read_text(encoding="utf-8"))
        records = raw["signals"] if isinstance(raw, dict) else raw
        self.signals = {s["employee_id"]: s for s in records}

    def signal(self, employee_id):
        return self.signals.get(employee_id)

    def weekly_study_capacity(self, employee_id, fraction=0.4):
        """Hours/week available for study: a fraction of focus time (never meetings)."""
        s = self.signal(employee_id)
        return round(s["focus_hours_per_week"] * fraction, 1) if s else 2.0

    def reminder_window(self, employee_id):
        """When to nudge this learner, respecting their rhythm (rule R-5)."""
        s = self.signal(employee_id)
        if not s:
            return "Midday, low-meeting days"
        slot = s["preferred_learning_slot"]
        if s["meeting_hours_per_week"] > 20:
            return f"{slot}, only on days with < 3 meetings (heavy meeting load)"
        return f"{slot}, during focus blocks"
