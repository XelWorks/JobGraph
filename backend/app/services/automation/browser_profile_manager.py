import os
import subprocess
import sys
from pathlib import Path
from typing import Any


class PersistentBrowserProfileManager:
    """Manages a local Playwright browser profile that can be reused across runs."""

    _processes: dict[str, subprocess.Popen] = {}

    @staticmethod
    def profile_dir_for(portal_name: str, base_dir: str | None = None) -> str:
        normalized = (portal_name or "default").strip().lower().replace(" ", "_")
        root = Path(base_dir or os.path.join(os.getcwd(), "browser_profiles"))
        return str(root / normalized)

    @classmethod
    async def launch_profile(cls, portal_name: str, base_dir: str | None = None) -> dict[str, Any]:
        """Open a visible profile in a separate process outside Uvicorn's event loop."""
        import asyncio

        return await asyncio.to_thread(cls._launch_profile_process, portal_name, base_dir)

    @classmethod
    def _launch_profile_process(cls, portal_name: str, base_dir: str | None = None) -> dict[str, Any]:
        normalized = (portal_name or "default").strip().lower()
        profile_dir = cls.profile_dir_for(normalized, base_dir)
        profile_path = Path(profile_dir)
        profile_path.mkdir(parents=True, exist_ok=True)

        class_name = normalized.replace(" ", "_")
        existing = cls._processes.get(class_name)
        if existing and existing.poll() is None:
            return {
                "portal_name": portal_name,
                "profile_dir": profile_dir,
                "status": "browser_profile_ready",
                "login_url": cls._portal_url(normalized),
                "reuse_hint": "Sign in normally in this browser window. The local profile will be reused for future runs.",
            }

        launcher = Path(__file__).with_name("browser_profile_launcher.py")
        creation_flags = 0
        if sys.platform == "win32":
            creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        process = subprocess.Popen(
            [sys.executable, str(launcher), normalized, profile_dir],
            cwd=str(launcher.parent.parent.parent.parent),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creation_flags,
        )
        cls._processes[class_name] = process

        return {
            "portal_name": portal_name,
            "profile_dir": profile_dir,
            "status": "browser_profile_ready",
            "login_url": cls._portal_url(normalized),
            "reuse_hint": "Sign in normally in this browser window. The local profile will be reused for future runs.",
        }

    @staticmethod
    def _portal_url(portal_name: str) -> str:
        mapping = {
            "linkedin": "https://www.linkedin.com/login",
            "naukri": "https://www.naukri.com/",
            "glassdoor": "https://www.glassdoor.com/profile/login_input.htm",
            "greenhouse": "https://boards.greenhouse.io/signin",
            "lever": "https://www.lever.co/",
            "workday": "https://www.myworkday.com/",
            "indeed": "https://secure.indeed.com/account/login",
        }
        return mapping.get(portal_name, "https://www.google.com")

    @classmethod
    def has_profile(cls, portal_name: str) -> bool:
        normalized = (portal_name or "default").strip().lower().replace(" ", "_")
        process = cls._processes.get(normalized)
        return bool(process and process.poll() is None)


persistent_browser_profile_manager = PersistentBrowserProfileManager()
