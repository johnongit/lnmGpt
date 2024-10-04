import json
import os
from datetime import datetime

class StructuredLogger:
    def __init__(self, base_dir='logs'):
        self.base_dir = base_dir
        self.current_execution_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.ensure_log_directory()

    def ensure_log_directory(self):
        os.makedirs(os.path.join(self.base_dir, self.current_execution_id), exist_ok=True)

    def log(self, log_type, data, metadata=None):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": log_type,
            "data": data
        }
        if metadata:
            log_entry["metadata"] = metadata

        file_path = os.path.join(self.base_dir, self.current_execution_id, f"{log_type}.json")
        
        with open(file_path, 'a') as f:
            json.dump(log_entry, f)
            f.write('\n')

    def log_prompt(self, prompt, metadata=None):
        self.log("prompt", prompt, metadata)

    def log_response(self, response, metadata=None):
        self.log("response", response, metadata)

    def log_decision(self, decision, metadata=None):
        self.log("decision", decision, metadata)

    def log_error(self, error, metadata=None):
        self.log("error", str(error), metadata)