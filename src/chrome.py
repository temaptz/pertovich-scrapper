from pathlib import Path
import subprocess

def chrome_profile_path(profile: str = "Default") -> Path:
    app_support = subprocess.check_output(
        ["osascript", "-e", 'POSIX path of (path to application support folder from user domain)'],
        text=True,
    ).strip()
    return Path(app_support) / "Google" / "Chrome" / profile