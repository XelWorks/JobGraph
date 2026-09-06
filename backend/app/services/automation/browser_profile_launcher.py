"""Standalone visible browser-profile launcher for Windows and FastAPI hosts."""

import sys
import time

from playwright.sync_api import sync_playwright


LOGIN_URLS = {
    "linkedin": "https://www.linkedin.com/login",
    "naukri": "https://www.naukri.com/",
    "glassdoor": "https://www.glassdoor.com/profile/login_input.htm",
    "greenhouse": "https://boards.greenhouse.io/signin",
    "lever": "https://www.lever.co/",
    "workday": "https://www.myworkday.com/",
    "indeed": "https://secure.indeed.com/account/login",
}


def main() -> None:
    portal_name = (sys.argv[1] if len(sys.argv) > 1 else "default").strip().lower()
    profile_dir = sys.argv[2]

    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            profile_dir,
            headless=False,
            viewport={"width": 1280, "height": 900},
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(LOGIN_URLS.get(portal_name, "https://www.google.com"), wait_until="domcontentloaded")
        while True:
            time.sleep(1)


if __name__ == "__main__":
    main()