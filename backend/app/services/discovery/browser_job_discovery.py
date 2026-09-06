"""Run portal job discovery in an isolated visible-browser subprocess."""

import json
import sys
from urllib.parse import quote_plus

from playwright.sync_api import sync_playwright


def search_url(portal: str, query: str, location: str) -> str:
    query_value = quote_plus(query)
    location_value = quote_plus(location)
    if portal == "linkedin":
        return f"https://www.linkedin.com/jobs/search/?keywords={query_value}&location={location_value}"
    if portal == "naukri":
        return f"https://www.naukri.com/{query.lower().replace(' ', '-')}-jobs-in-{location.lower().replace(' ', '-')}"
    return f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={query_value}&locKeyword={location_value}"


SELECTORS = {
    "linkedin": ["a.base-card__full-link", "a[href*='/jobs/view/']", "a[href*='/jobs/']"],
    "naukri": ["a.title", "a[href*='job-listings']", "a[href*='/job-listings-']"],
    "glassdoor": ["a[href*='/job-listing/']", "a.JobCard_jobTitle__"] ,
}


def main() -> None:
    portal = sys.argv[1].strip().lower()
    profile_dir = sys.argv[2]
    query = sys.argv[3] if len(sys.argv) > 3 else "software engineer"
    location = sys.argv[4] if len(sys.argv) > 4 else "remote"
    url = search_url(portal, query, location)

    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            profile_dir,
            headless=False,
            viewport={"width": 1440, "height": 900},
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2500)

        jobs = []
        seen = set()
        for selector in SELECTORS.get(portal, []):
            for link in page.locator(selector).all():
                href = link.get_attribute("href")
                title = link.inner_text().strip()
                if not href or not title or len(title) < 3:
                    continue
                absolute_url = page.url if href.startswith("#") else link.evaluate("el => el.href")
                if absolute_url in seen:
                    continue
                seen.add(absolute_url)
                jobs.append({
                    "title": title,
                    "company": portal.title(),
                    "location": location,
                    "url": absolute_url,
                    "description_text": "",
                    "external_job_id": f"{portal}-{abs(hash(absolute_url))}",
                })
                if len(jobs) >= 100:
                    break
            if len(jobs) >= 100:
                break

        body_text = page.locator("body").inner_text()[:500].lower()
        print(json.dumps({
            "search_url": url,
            "jobs": jobs,
            "final_url": page.url,
            "page_title": page.title(),
            "login_required": any(term in body_text for term in ("sign in", "join now", "log in")),
        }))
        context.close()


if __name__ == "__main__":
    main()