import os
import json
from abogen.utils import get_user_config_path


def _get_profiles_path():
    config_path = get_user_config_path()
    config_dir = os.path.dirname(config_path)
    return os.path.join(config_dir, "voice_profiles.json")


def load_profiles():
    """Load all voice profiles from JSON file."""
    path = _get_profiles_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # always expect abogen_voice_profiles wrapper
                if isinstance(data, dict) and "abogen_voice_profiles" in data:
                    return data["abogen_voice_profiles"]
                # fallback: treat as profiles dict
                if isinstance(data, dict):
                    return data
        except Exception:
            return {}
    return {}


def save_profiles(profiles):
    """Save all voice profiles to JSON file."""
    path = _get_profiles_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        # always save with abogen_voice_profiles wrapper
        json.dump({"abogen_voice_profiles": profiles}, f, indent=2)


def delete_profile(name):
    """Remove a profile by name."""
    profiles = load_profiles()
    if name in profiles:
        del profiles[name]
        save_profiles(profiles)


def duplicate_profile(src, dest):
    """Duplicate an existing profile."""
    profiles = load_profiles()
    if src in profiles and dest:
        profiles[dest] = profiles[src]
        save_profiles(profiles)


def export_profiles(export_path):
    """Export all profiles to specified JSON file."""
    profiles = load_profiles()
    with open(export_path, "w", encoding="utf-8") as f:
        json.dump({"abogen_voice_profiles": profiles}, f, indent=2)
