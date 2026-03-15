import json
import os
import uuid


def _profile_path():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "data", "profile.json")


def load_profile():
    """Load the local user profile. Returns dict or None."""
    path = _profile_path()
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_profile(name):
    """Create or update the local user profile. Returns the profile dict."""
    path = _profile_path()
    profile = load_profile()
    if profile is None:
        profile = {"user_id": str(uuid.uuid4()), "name": name}
    else:
        profile["name"] = name
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)
    return profile


def get_user_id():
    """Return the current user's ID, or None if no profile."""
    profile = load_profile()
    return profile["user_id"] if profile else None


def get_user_name():
    """Return the current user's name, or empty string."""
    profile = load_profile()
    return profile.get("name", "") if profile else ""
