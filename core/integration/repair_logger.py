# # core/integration/repair_logger.py

import json
import os
from datetime import datetime
from multiprocessing.util import LOGGER_NAME


class RepairLogger:

    def __init__(self, log_dir="logs/repair_plans"):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)

    def save(self, plan, iteration):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_name = f"plan_{iteration}_{timestamp}.json"
        path = os.path.join(self.log_dir, f"{log_name}")

        data = {
            "actions": [
                {
                    "action": a.action,
                    "target": a.target,
                    "details": a.details
                }
                for a in plan.actions
            ]
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        print(f"[REPAIR LOG] Saved → {path}")