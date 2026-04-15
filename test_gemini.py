import os
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    tomllib = None


def _load_api_key() -> str | None:
    """Load GEMINI_API_KEY from env first, then .streamlit/secrets.toml."""
    env_key = os.getenv("GEMINI_API_KEY")
    if env_key:
        return env_key.strip()

    # Look in common locations so this works regardless of current working directory.
    candidate_paths = [
        Path(__file__).resolve().parent / ".streamlit" / "secrets.toml",
        Path.cwd() / ".streamlit" / "secrets.toml",
    ]

    secrets_path = next((p for p in candidate_paths if p.exists()), None)
    if secrets_path is None:
        return None

    raw_text = secrets_path.read_text(encoding="utf-8")
    if tomllib is not None:
        try:
            data = tomllib.loads(raw_text)
            key = data.get("GEMINI_API_KEY")
            if isinstance(key, str) and key.strip():
                return key.strip()
        except Exception:
            # Fallback for non-TOML lines like: GEMINI_API_KEY = abc123
            pass

    for line in raw_text.splitlines():
        if "=" not in line:
            continue
        left, right = line.split("=", 1)
        if left.strip() != "GEMINI_API_KEY":
            continue
        key = right.strip().strip("\"' ")
        if key:
            return key
    return None


def main() -> None:
    print("starting script...", flush=True)

    try:
        from google import genai
    except Exception as exc:
        print("ERROR: google-genai is not installed in this Python environment.", flush=True)
        print("Install with: pip install google-genai", flush=True)
        print(f"Import details: {exc}", flush=True)
        return

    api_key = _load_api_key()
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found.", flush=True)
        print("Set it in environment or .streamlit/secrets.toml", flush=True)
        return

    print("client creating...", flush=True)
    client = genai.Client(api_key=api_key)
    print("client created", flush=True)

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Respond with only the word WORKING",
        )
        print("API call finished", flush=True)
        print("Gemini response:", flush=True)
        print(repr(response.text), flush=True)
    except Exception as exc:
        print(f"ERROR: API call failed: {exc}", flush=True)


if __name__ == "__main__":
    main()