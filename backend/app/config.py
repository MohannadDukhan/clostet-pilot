# backend/app/config.py
import os, pathlib

def _load_env_file():
    # read backend/.env manually (no extra deps)
    env_path = pathlib.Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip()
        # don't overwrite if already set in real environment
        os.environ.setdefault(k, v)

_load_env_file()

class Settings:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.auto_classify_on_upload = os.getenv("AUTO_CLASSIFY_ON_UPLOAD", "false").lower() == "true"

settings = Settings()
