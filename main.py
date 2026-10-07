from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS: lets the grader's web page call your API from the browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- The four layers, hardcoded (so the server's own env vars can't interfere) ----
DEFAULTS = {"port": 8000, "workers": 1, "debug": "false",
            "log_level": "info", "api_key": "default-secret-000"}

YAML_LAYER = {"port": 8247, "workers": 9, "debug": "false",
              "api_key": "key-ybgtskegel"}

DOTENV_LAYER = {"APP_PORT": "8918", "APP_DEBUG": "false",
                "APP_API_KEY": "key-1wwfho25og"}

OS_ENV_LAYER = {"APP_WORKERS": "1", "APP_DEBUG": "true",
                "APP_LOG_LEVEL": "info"}

ALIASES = {"num_workers": "workers"}   # NUM_WORKERS -> workers


def clean_key(key: str) -> str:
    """APP_PORT -> port, NUM_WORKERS -> workers"""
    key = key.strip()
    if key.upper().startswith("APP_"):
        key = key[4:]
    key = key.lower()
    return ALIASES.get(key, key)


def clean_layer(layer: dict) -> dict:
    return {clean_key(k): v for k, v in layer.items()}


def to_bool(value) -> bool:
    return str(value).strip().lower() in ("true", "1", "yes", "on")


def coerce(key: str, value):
    if key in ("port", "workers"):
        return int(value)
    if key == "debug":
        return to_bool(value)
    return str(value)


@app.get("/effective-config")
def effective_config(overrides: list[str] = Query(default=[], alias="set")):
    merged = {}

    # low -> high precedence: later layers overwrite earlier ones
    for layer in (DEFAULTS, YAML_LAYER, DOTENV_LAYER, OS_ENV_LAYER):
        merged.update(clean_layer(layer))

    # CLI overrides (highest): "port=9000" -> split at the FIRST "="
    for item in overrides:
        if "=" in item:
            k, v = item.split("=", 1)
            merged[clean_key(k)] = v

    # convert types
    result = {k: coerce(k, v) for k, v in merged.items()}

    # hide the secret
    result["api_key"] = "****"
    return result