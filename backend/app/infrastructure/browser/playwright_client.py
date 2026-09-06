# ruff: noqa: C901
import logging
import os
from typing import Any, Dict

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

logger = logging.getLogger("app.infrastructure.browser.playwright_client")


class PlaywrightBrowserCore:
    """Headless browser handler using Playwright to automate job application form filling and document uploads."""

    def __init__(self, headless: bool = True, default_timeout_ms: int = 15000) -> None:
        self.headless = headless
        self.default_timeout_ms = default_timeout_ms
        self.manual_review_timeout_ms = 30 * 60 * 1000

    async def _keep_review_page_open(self, page: Any) -> None:
        """Keep a visible review page alive while the user handles interactive prompts."""
        if self.headless:
            return
        logger.info(
            "manual_review_browser_open",
            extra={"timeout_minutes": self.manual_review_timeout_ms // 60000},
        )
        await page.wait_for_timeout(self.manual_review_timeout_ms)

    async def fill_application_form(
        self,
        url: str,
        profile_data: Dict[str, Any],
        resume_path: str,
        screenshot_path: str | None = None,
        mode: str = "Autonomous",  # "Manual", "Assisted", "Autonomous"
        browser_context: Dict[str, Any] | None = None,
        user_data_dir: str | None = None,
    ) -> Dict[str, Any]:
        """
        Navigates to the job application form at the specified URL, detects the ATS type
        (Greenhouse, Lever, or Generic), autofills the standard profile fields, uploads the
        tailored resume, answers custom/dynamic recruiter questions, and completes the action
        according to the selected mode (Manual, Assisted, Autonomous).
        Ensures the browser instance is always closed gracefully under all conditions.
        """
        if not os.path.exists(resume_path):
            raise FileNotFoundError(f"Tailored resume file not found at path: {resume_path}")

        result: Dict[str, Any] = {
            "status": "failed",
            "ats_type": "unknown",
            "filled_fields": [],
            "uploaded_resume": False,
            "custom_questions_answered": 0,
            "submitted": False,
            "error": None,
            "portal_name": None,
            "requires_manual_review": False,
        }
        keep_browser_open = False

        # If Manual mode, compiling files is done, skip loading the browser
        if mode == "Manual":
            logger.info("Manual execution mode specified. Skipping headless browser form filling.")
            result["status"] = "success"
            result["mode_handled"] = "Manual"
            return result

        logger.info(
            "Launching %s browser to navigate to application URL: %s in %s mode",
            "headless" if self.headless else "visible",
            url,
            mode,
        )

        async with async_playwright() as p:
            browser = None
            context = None
            use_persistent_profile = bool(user_data_dir)

            try:
                if use_persistent_profile:
                    logger.info("Launching persistent Chromium profile for portal session: %s", user_data_dir)
                    browser = await p.chromium.launch_persistent_context(
                        user_data_dir,
                        viewport={"width": 1280, "height": 800},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                        headless=self.headless,
                        args=[
                            "--no-sandbox",
                            "--disable-setuid-sandbox",
                            "--disable-dev-shm-usage",
                        ],
                    )
                    context = browser
                else:
                    browser = await p.chromium.launch(
                        headless=self.headless,
                        args=[
                            "--no-sandbox",
                            "--disable-setuid-sandbox",
                            "--disable-dev-shm-usage",
                        ],
                    )
                    context = await browser.new_context(
                        viewport={"width": 1280, "height": 800},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    )

                page = await context.new_page()
                page.set_default_timeout(self.default_timeout_ms)

                logger.info(f"Navigating to {url}")
                await page.goto(url, wait_until="domcontentloaded")

                portal_name = self._detect_portal_name(url, browser_context)
                result["portal_name"] = portal_name
                if portal_name in {"linkedin", "naukri", "glassdoor"}:
                    result["requires_manual_review"] = True

                manual_review = await self._preflight_portal_gate(page, portal_name, browser_context)
                if manual_review:
                    result["requires_manual_review"] = True
                    result["status"] = "review_required"
                    keep_browser_open = True
                    logger.warning("portal_review_gate_triggered", extra={"portal": portal_name, "url": url})
                    await self._keep_review_page_open(page)
                    return result

                # Execute portal-specific pre-actions before standard ATS fill
                portal_action_handled = await self._handle_portal_specific_actions(
                    page=page,
                    portal_name=portal_name,
                    profile_data=profile_data,
                    resume_path=resume_path,
                    result=result,
                )
                if portal_action_handled:
                    result["status"] = "success"
                    keep_browser_open = True
                    logger.info("Portal-specific browser flow completed for %s", portal_name)
                    await self._keep_review_page_open(page)
                    return result

                # Detect the ATS platform
                ats_type = await self._detect_ats_platform(page, url)
                result["ats_type"] = ats_type
                logger.info(f"Detected ATS Platform: {ats_type}")

                # Retrieve candidate details
                first_name = profile_data.get("first_name", "")
                last_name = profile_data.get("last_name", "")
                full_name = f"{first_name} {last_name}".strip()
                email = profile_data.get("email", "")
                phone = profile_data.get("phone", "")

                # Autofill fields depending on detected ATS structure
                if ats_type == "greenhouse":
                    await self._fill_greenhouse_form(
                        page=page,
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        phone=phone,
                        resume_path=resume_path,
                        result=result
                    )
                elif ats_type == "lever":
                    await self._fill_lever_form(
                        page=page,
                        full_name=full_name,
                        email=email,
                        phone=phone,
                        resume_path=resume_path,
                        result=result
                    )
                else:
                    # Fallback generic form filler
                    await self._fill_generic_form(
                        page=page,
                        first_name=first_name,
                        last_name=last_name,
                        full_name=full_name,
                        email=email,
                        phone=phone,
                        resume_path=resume_path,
                        result=result
                    )

                # Process custom/dynamic recruiter questions via QAAgentService
                await self._answer_dynamic_questions(page, profile_data, result)

                # Trigger submit depending on execution mode
                if mode == "Autonomous":
                    logger.info("Executing Autonomous form submission click trigger.")
                    submit_clicked = await self._trigger_form_submission(page, ats_type)
                    result["submitted"] = submit_clicked
                elif mode == "Assisted":
                    logger.info("Executing Assisted form fill mode. Pausing page to allow candidate manual review.")
                    # Sleep for a short, controllable timeframe representing pause-and-review step
                    import asyncio
                    await asyncio.sleep(2.0)
                    result["submitted"] = False
                    result["paused_for_review"] = True

                # Capture optional verification screenshot
                if screenshot_path:
                    # Create parent directories if they do not exist
                    parent_dir = os.path.dirname(screenshot_path)
                    if parent_dir:
                        os.makedirs(parent_dir, exist_ok=True)
                    await page.screenshot(path=screenshot_path)
                    logger.info(f"Saved autofill verification screenshot to: {screenshot_path}")

                result["status"] = "success"
                keep_browser_open = not result["submitted"]
                if keep_browser_open:
                    await self._keep_review_page_open(page)
                logger.info("Successfully completed application form filling automation core.")

            except PlaywrightTimeoutError as e:
                err_msg = f"Timeout elapsed during Playwright page interaction: {e}"
                logger.error(err_msg)
                result["error"] = err_msg
            except Exception as e:
                err_msg = f"Unexpected error occurred during form filling: {e}"
                logger.error(err_msg)
                result["error"] = err_msg
            finally:
                # Keep visible sessions open when the user still needs to complete
                # a login, OTP, verification, or any other manual step.
                if keep_browser_open and not self.headless:
                    logger.info("Keeping visible browser open for user review.")
                else:
                    logger.info("Closing browser context and instances gracefully.")
                    if context is not None:
                        await context.close()
                    if browser is not None and not use_persistent_profile:
                        await browser.close()

        return result

    def _detect_portal_name(self, url: str, browser_context: Dict[str, Any] | None = None) -> str | None:
        """Detect the portal by URL, then fall back to runtime browser context."""
        url_lower = url.lower()
        if "linkedin.com" in url_lower:
            return "linkedin"
        if "naukri.com" in url_lower:
            return "naukri"
        if "glassdoor.com" in url_lower:
            return "glassdoor"
        if browser_context and isinstance(browser_context, dict):
            portal = browser_context.get("portal")
            if isinstance(portal, str) and portal:
                return portal.lower()
        return None

    async def _portal_requires_manual_review(
        self,
        page: Any,
        portal_name: str | None,
        browser_context: Dict[str, Any] | None = None,
    ) -> bool:
        """Return True when the current portal page requires a human review gate or re-authentication."""
        if portal_name is None:
            return False

        gate_selectors = [
            "text=Sign in",
            "text=Log in",
            "text=Join now",
            "text=Verify your identity",
            "text=Security check",
            "button:has-text(\"Continue\")",
            "button:has-text(\"Verify\")",
        ]

        if portal_name in {"linkedin", "naukri", "glassdoor"}:
            for selector in gate_selectors:
                if await page.locator(selector).count() > 0:
                    return True

            if browser_context and browser_context.get("manual_review_required"):
                return True

            if portal_name == "linkedin" and await page.locator("input[autocomplete='username']").count() > 0:
                return True

            if portal_name == "naukri" and await page.locator("input[placeholder*='Email']").count() > 0:
                return True

            if portal_name == "glassdoor" and await page.locator("input[name='email']").count() > 0:
                return True

        return False

    async def _evaluate_page_state(
        self,
        page: Any,
        portal_name: str | None,
        browser_context: Dict[str, Any] | None = None,
    ) -> Dict[str, bool]:
        """Classify the portal page before starting form automation."""
        state = {
            "login_required": False,
            "verification_required": False,
            "requires_manual_review": False,
        }

        if portal_name is None:
            return state

        if portal_name in {"linkedin", "naukri", "glassdoor"}:
            login_selectors = [
                "text=Sign in",
                "text=Log in",
                "text=Join now",
                "input[autocomplete='username']",
                "input[placeholder*='Email']",
                "input[name='email']",
            ]
            verification_selectors = [
                "text=Verify your identity",
                "text=Security check",
                "button:has-text(\"Continue\")",
                "button:has-text(\"Verify\")",
            ]

            for selector in login_selectors:
                if await page.locator(selector).count() > 0:
                    state["login_required"] = True
                    break

            for selector in verification_selectors:
                if await page.locator(selector).count() > 0:
                    state["verification_required"] = True
                    break

            if browser_context and browser_context.get("manual_review_required"):
                state["requires_manual_review"] = True

            if state["login_required"] or state["verification_required"]:
                state["requires_manual_review"] = True

        return state

    async def _preflight_portal_gate(
        self,
        page: Any,
        portal_name: str | None,
        browser_context: Dict[str, Any] | None = None,
    ) -> bool:
        """Pause browser automation when a portal is not session-ready or triggers human verification."""
        state = await self._evaluate_page_state(page, portal_name, browser_context)
        return state["requires_manual_review"]

    async def _handle_portal_specific_actions(
        self,
        page: Any,
        portal_name: str | None,
        profile_data: Dict[str, Any],
        resume_path: str,
        result: Dict[str, Any],
    ) -> bool:
        """Handle portal-specific browser actions for human-like Chrome automation."""
        if portal_name is None:
            return False

        if await self._portal_requires_manual_review(page, portal_name):
            result["portal_flow"] = portal_name
            result["status"] = "review_required"
            result["requires_manual_review"] = True
            return True

        if portal_name == "linkedin":
            apply_button = page.locator("button:has-text('Apply')")
            if await apply_button.count() == 0:
                result["portal_flow"] = "linkedin"
                result["status"] = "review_required"
                result["requires_manual_review"] = True
                return True
            await apply_button.click()
            result["portal_flow"] = "linkedin"
            result["status"] = "review_required"
            result["requires_manual_review"] = True
            return True

        if portal_name == "naukri":
            apply_button = page.locator("button:has-text('Apply')")
            if await apply_button.count() == 0:
                result["portal_flow"] = "naukri"
                result["status"] = "review_required"
                result["requires_manual_review"] = True
                return True
            await apply_button.click()
            result["portal_flow"] = "naukri"
            result["status"] = "review_required"
            result["requires_manual_review"] = True
            return True

        if portal_name == "glassdoor":
            apply_button = page.locator("button:has-text('Apply Now')")
            if await apply_button.count() == 0:
                result["portal_flow"] = "glassdoor"
                result["status"] = "review_required"
                result["requires_manual_review"] = True
                return True
            await apply_button.click()
            result["portal_flow"] = "glassdoor"
            result["status"] = "review_required"
            result["requires_manual_review"] = True
            return True
        
        # Handle company career pages that redirect from job boards
        # Try to detect and create account on ATS platforms
        current_url = page.url
        ats_detected = self._detect_ats_from_url(current_url)
        
        if ats_detected and ats_detected not in {"linkedin", "naukri", "glassdoor"}:
            # This is a company career page - try account creation
            from app.services.applications.account_creator import account_creation_service
            
            # Get user_id from profile_data or context
            user_id_str = profile_data.get("user_id")
            if user_id_str:
                import uuid
                try:
                    user_id = uuid.UUID(user_id_str)
                    account_created, platform = await account_creation_service.detect_and_create_account(
                        page=page,
                        current_url=current_url,
                        profile_data=profile_data,
                        user_id=user_id,
                    )
                    
                    if account_created:
                        logger.info(
                            "account_created_on_career_page",
                            extra={"platform": platform, "url": current_url}
                        )
                        result["account_created"] = True
                        result["ats_platform"] = platform
                        # Continue with standard form filling after account creation
                        return False  # Don't skip standard ATS handling
                
                except (ValueError, TypeError) as e:
                    logger.warning(f"invalid_user_id_for_account_creation: {e}")

        return False
    
    def _detect_ats_from_url(self, url: str) -> str | None:
        """Detect ATS platform from URL."""
        url_lower = url.lower()
        if "greenhouse.io" in url_lower:
            return "greenhouse"
        if "lever.co" in url_lower:
            return "lever"
        if "myworkday.com" in url_lower or "wd5.myworkday.com" in url_lower:
            return "workday"
        if "icims.com" in url_lower:
            return "icims"
        if "taleo.net" in url_lower or "oraclecloud.com" in url_lower:
            return "taleo"
        if "linkedin.com" in url_lower:
            return "linkedin"
        if "naukri.com" in url_lower:
            return "naukri"
        if "glassdoor.com" in url_lower:
            return "glassdoor"
        return None

    async def _detect_ats_platform(self, page: Any, url: str) -> str:
        """Heuristic check to determine if the page is Greenhouse or Lever."""
        url_lower = url.lower()
        if "greenhouse.io" in url_lower:
            return "greenhouse"
        if "lever.co" in url_lower:
            return "lever"

        # Content/Selector checks
        if await page.locator("form#application_form").count() > 0:
            return "greenhouse"
        if await page.locator("form#application-form").count() > 0:
            return "lever"

        # Fallback to checking for specific classes/IDs
        if await page.locator("#resume_file").count() > 0 or await page.locator("[name*='job_application[']").count() > 0:
            return "greenhouse"
        if await page.locator("[id='resume-upload-input']").count() > 0:
            return "lever"

        return "generic"

    async def _fill_greenhouse_form(
        self,
        page: Any,
        first_name: str,
        last_name: str,
        email: str,
        phone: str,
        resume_path: str,
        result: Dict[str, Any]
    ) -> None:
        """Greenhouse specific element filling and resume upload logic."""
        logger.info("Executing Greenhouse form filling rules.")

        # 1. Fill First Name
        first_name_selectors = ["input#first_name", "input[name='job_application[first_name]']"]
        for selector in first_name_selectors:
            if await page.locator(selector).count() > 0:
                await page.fill(selector, first_name)
                result["filled_fields"].append("first_name")
                break

        # 2. Fill Last Name
        last_name_selectors = ["input#last_name", "input[name='job_application[last_name]']"]
        for selector in last_name_selectors:
            if await page.locator(selector).count() > 0:
                await page.fill(selector, last_name)
                result["filled_fields"].append("last_name")
                break

        # 3. Fill Email
        email_selectors = ["input#email", "input[name='job_application[email]']"]
        for selector in email_selectors:
            if await page.locator(selector).count() > 0:
                await page.fill(selector, email)
                result["filled_fields"].append("email")
                break

        # 4. Fill Phone
        phone_selectors = ["input#phone", "input[name='job_application[phone]']"]
        for selector in phone_selectors:
            if await page.locator(selector).count() > 0:
                await page.fill(selector, phone)
                result["filled_fields"].append("phone")
                break

        # 5. Upload Resume
        # Greenhouse often supports direct file input
        resume_selectors = [
            "input[type='file'][id='resume_file']",
            "input[type='file'][name='job_application[resume]']",
            "input[type='file'][id*='resume']"
        ]
        for selector in resume_selectors:
            if await page.locator(selector).count() > 0:
                await page.set_input_files(selector, resume_path)
                result["uploaded_resume"] = True
                break

    async def _fill_lever_form(
        self,
        page: Any,
        full_name: str,
        email: str,
        phone: str,
        resume_path: str,
        result: Dict[str, Any]
    ) -> None:
        """Lever specific element filling and resume upload logic."""
        logger.info("Executing Lever form filling rules.")

        # 1. Fill Combined Name
        name_selectors = ["input[name='name']", "input[id='name']"]
        for selector in name_selectors:
            if await page.locator(selector).count() > 0:
                await page.fill(selector, full_name)
                result["filled_fields"].append("full_name")
                break

        # 2. Fill Email
        email_selectors = ["input[name='email']", "input[id='email']"]
        for selector in email_selectors:
            if await page.locator(selector).count() > 0:
                await page.fill(selector, email)
                result["filled_fields"].append("email")
                break

        # 3. Fill Phone
        phone_selectors = ["input[name='phone']", "input[id='phone']"]
        for selector in phone_selectors:
            if await page.locator(selector).count() > 0:
                await page.fill(selector, phone)
                result["filled_fields"].append("phone")
                break

        # 4. Upload Resume
        # Lever uses input#resume-upload-input
        resume_selectors = [
            "input[type='file'][id='resume-upload-input']",
            "input[type='file'][name='resume']",
            "input[type='file'][id*='resume']"
        ]
        for selector in resume_selectors:
            if await page.locator(selector).count() > 0:
                await page.set_input_files(selector, resume_path)
                result["uploaded_resume"] = True
                break

    async def _fill_generic_form(
        self,
        page: Any,
        first_name: str,
        last_name: str,
        full_name: str,
        email: str,
        phone: str,
        resume_path: str,
        result: Dict[str, Any]
    ) -> None:
        """Fuzzy fallback search for standard fields on other ATS platforms."""
        logger.info("ATS type generic/unknown. Running fuzzy fallback selectors.")

        # Search patterns
        first_name_regex = r"(first.*name|forename|given.*name)"
        last_name_regex = r"(last.*name|surname|family.*name)"
        full_name_regex = r"(^name|full.*name|candidate.*name)"
        email_regex = r"(email|e-mail)"
        phone_regex = r"(phone|telephone|mobile|tel\b)"

        inputs = await page.locator("input").all()
        for input_el in inputs:
            name_attr = (await input_el.get_attribute("name") or "").lower()
            id_attr = (await input_el.get_attribute("id") or "").lower()
            placeholder = (await input_el.get_attribute("placeholder") or "").lower()
            aria_label = (await input_el.get_attribute("aria-label") or "").lower()
            type_attr = (await input_el.get_attribute("type") or "").lower()

            target_val = f"{name_attr} {id_attr} {placeholder} {aria_label}"

            if type_attr == "file":
                # Handle resume upload element
                import re
                if re.search(r"(resume|cv\b|curriculum|upload)", target_val):
                    await input_el.set_input_files(resume_path)
                    result["uploaded_resume"] = True
                continue

            if type_attr in ["text", "email", "tel", ""]:
                import re
                # Check split first name
                if "first_name" not in result["filled_fields"] and re.search(first_name_regex, target_val):
                    await input_el.fill(first_name)
                    result["filled_fields"].append("first_name")
                # Check split last name
                elif "last_name" not in result["filled_fields"] and re.search(last_name_regex, target_val):
                    await input_el.fill(last_name)
                    result["filled_fields"].append("last_name")
                # Check combined full name (only if split names aren't both filled)
                elif "full_name" not in result["filled_fields"] and re.search(full_name_regex, target_val):
                    if "first_name" not in result["filled_fields"]:
                        await input_el.fill(full_name)
                        result["filled_fields"].append("full_name")
                # Check email
                elif "email" not in result["filled_fields"] and re.search(email_regex, target_val):
                    await input_el.fill(email)
                    result["filled_fields"].append("email")
                # Check phone
                elif "phone" not in result["filled_fields"] and re.search(phone_regex, target_val):
                    await input_el.fill(phone)
                    result["filled_fields"].append("phone")

        # Second-chance file element check if resume is not uploaded
        if not result["uploaded_resume"]:
            file_inputs = await page.locator("input[type='file']").all()
            if len(file_inputs) == 1:
                # If there's exactly one file upload on the application form, it's highly likely the resume input
                logger.info("Exactly one file input found. Attempting resume upload fallback.")
                await file_inputs[0].set_input_files(resume_path)
                result["uploaded_resume"] = True

    async def _answer_dynamic_questions(
        self,
        page: Any,
        profile_data: Dict[str, Any],
        result: Dict[str, Any]
    ) -> None:
        """
        Locates non-standard form controls (custom text inputs, dropdown selects, checkboxes,
        radios) and answers them using QAAgentService.
        """
        from app.services.applications.qa_agent import qa_agent_service

        logger.info("Locating non-standard custom recruiter fields on page.")

        # Standard system fields already processed (should be skipped)
        standard_ids = ["first_name", "last_name", "email", "phone", "name", "resume", "cv", "resume_file", "resume-upload-input"]

        # 1. Custom text fields & textareas
        text_fields = await page.locator("input[type='text'], textarea").all()
        for field in text_fields:
            name_attr = await field.get_attribute("name") or ""
            id_attr = await field.get_attribute("id") or ""

            # Skip standard fields
            if any(std in name_attr.lower() or std in id_attr.lower() for std in standard_ids):
                continue

            # Skip hidden elements or empty names
            if not name_attr and not id_attr:
                continue

            # Fetch question text label associated with field
            label_text = await self._get_label_for_field(page, id_attr, name_attr)
            if not label_text:
                label_text = name_attr  # fallback to name attribute as prompt question

            logger.info(f"Answering custom text question: {label_text}")
            qa_res = await qa_agent_service.answer_custom_question(
                question_text=label_text,
                field_type="text",
                options=[],
                candidate_profile=profile_data
            )
            await field.fill(qa_res["answer_text"])
            result["custom_questions_answered"] += 1

        # 2. Custom Select dropdowns
        selects = await page.locator("select").all()
        for sel in selects:
            name_attr = await sel.get_attribute("name") or ""
            id_attr = await sel.get_attribute("id") or ""

            if not name_attr and not id_attr:
                continue

            label_text = await self._get_label_for_field(page, id_attr, name_attr)
            if not label_text:
                label_text = name_attr

            # Extract options available on select element
            option_elements = await sel.locator("option").all()
            options_list = []
            for opt in option_elements:
                text_content = await opt.text_content()
                if text_content and text_content.strip():
                    options_list.append(text_content.strip())

            # Skip select lists with zero valid choices
            if not options_list:
                continue

            logger.info(f"Answering custom dropdown select question: {label_text} with options: {options_list}")
            qa_res = await qa_agent_service.answer_custom_question(
                question_text=label_text,
                field_type="select",
                options=options_list,
                candidate_profile=profile_data
            )

            idx = qa_res.get("matched_option_index", 0)
            if 0 <= idx < len(option_elements):
                val_attr = await option_elements[idx].get_attribute("value")
                if val_attr is not None:
                    await sel.select_option(value=val_attr)
                else:
                    await sel.select_option(label=options_list[idx])
                result["custom_questions_answered"] += 1

    async def _get_label_for_field(self, page: Any, element_id: str, element_name: str) -> str | None:
        """Finds label text associated with the element ID or name."""
        if element_id:
            label_loc = page.locator(f"label[for='{element_id}']")
            if await label_loc.count() > 0:
                text = await label_loc.first.text_content()
                return text.strip() if text else None

        # Check wrapping labels
        id_query = f"#{element_id}" if element_id else f"input[name='{element_name}']"
        wrap_label = page.locator(f"label:has({id_query})")
        if await wrap_label.count() > 0:
            text = await wrap_label.first.text_content()
            return text.strip() if text else None

        return None

    async def _trigger_form_submission(self, page: Any, ats_type: str) -> bool:
        """Locates and clicks the primary submit button on the application page."""
        submit_selectors = [
            "button[type='submit']",
            "input[type='submit']",
            "button#submit_app",
            "input#submit_app",
            "#submit-button"
        ]

        for selector in submit_selectors:
            loc = page.locator(selector)
            if await loc.count() > 0:
                logger.info(f"Clicking submit button matching selector: {selector}")
                await loc.first.click()
                return True

        return False


playwright_browser_core = PlaywrightBrowserCore()
