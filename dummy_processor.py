# dummy_processor.py
import json
import random
import time
import uuid
from pathlib import Path
import tempfile

def run_pipeline(audio_path: Path, license_path: Path) -> Path:
    # Simulate some work
    time.sleep(1.5)

    # Create a random JSON payload
    payload = {
        "job_id": str(uuid.uuid4()),
        "status": "success",
        "summary": {
            "audio_file": audio_path.name,
            "license_file": license_path.name,
            "duration_sec_estimate": round(random.uniform(30, 7200), 2),
        },
        "insights": [
            {"topic": "greeting", "confidence": round(random.uniform(0.7, 0.99), 2)},
            {"topic": "pricing", "confidence": round(random.uniform(0.6, 0.95), 2)},
            {"topic": "next_steps", "confidence": round(random.uniform(0.65, 0.98), 2)},
        ],
        "metrics": {
            "turns": random.randint(8, 64),
            "silence_ratio": round(random.uniform(0.05, 0.45), 2),
        },
    }

    out_dir = Path(tempfile.mkdtemp(prefix="streamlit-demo-"))
    out_path = out_dir / f"result_{uuid.uuid4().hex}.json"
    out_path.write_text(json.dumps(payload, indent=2))
    return out_path
