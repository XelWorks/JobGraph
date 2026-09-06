"""
Account Creation Service for Company Career Pages

This module handles automatic account creation on company career pages
when a job application link redirects to a company's own ATS system.

Features:
- Detect career page redirects
- Generate secure credentials
- Create accounts with user profile data
- Store encrypted session cookies
- Handle common ATS platforms (Greenhouse, Lever, Workday, etc.)
"""
import asyncio
import logging
import secrets
import string
from typing import Any, Dict, Optional, Tuple

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from app.core.config import settings
from app.infrastructure.db.vault_repository import vault_repository
from app.infrastructure.db.session import SessionLocal
import uuid

logger = logging.getLogger("app.services.applications.account_creator")


class AccountCreationService:
    """
    Service for automatically creating accounts on company career pages.
    
    When a job application URL redirects to a company's own ATS system,
    this service can create an account using the candidate's profile data,
    allowing fully autonomous applications without manual intervention.
    """
    
    # Supported ATS platforms with their registration URLs and selectors
    ATS_PLATFORMS = {
        "greenhouse": {
            "signup_url": "https://boards.greenhouse.io/signup",
            "email_selector": "input[type='email'], input[name='email']",
            "password_selector": "input[type='password'][name='password']",
            "confirm_password_selector": "input[type='password'][name='password_confirmation']",
            "first_name_selector": "input[name='first_name']",
            "last_name_selector": "input[name='last_name']",
            "submit_selector": "button[type='submit'], input[type='submit']",
            "success_indicators": ["Welcome", "Account created", "Profile"],
        },
        "lever": {
            "signup_url": "https://www.lever.co/signup",
            "email_selector": "input[type='email']",
            "password_selector": "input[type='password']",
            "first_name_selector": "input[name='firstName']",
            "last_name_selector": "input[name='lastName']",
            "submit_selector": "button[type='submit']",
            "success_indicators": ["Welcome", "Account created"],
        },
        "workday": {
            "signup_url": "https://www.myworkday.com/registration",
            "email_selector": "input[type='email']",
            "password_selector": "input[type='password']",
            "submit_selector": "button[type='submit']",
            "success_indicators": ["Welcome", "Profile"],
        },
        "icims": {
            "signup_url": "",  # Dynamic per company
            "email_selector": "input[id*='email'], input[name*='email']",
            "password_selector": "input[id*='password'], input[name*='password']",
            "submit_selector": "button[type='submit'], input[type='submit']",
            "success_indicators": ["Welcome", "Profile created"],
        },
        "taleo": {
            "signup_url": "",  # Dynamic per company
            "email_selector": "input[type='email']",
            "password_selector": "input[type='password']",
            "submit_selector": "input[type='submit'], button[type='submit']",
            "success_indicators": ["Welcome", "Account"],
        },
    }
    
    def __init__(self) -> None:
        self._creation_attempts: Dict[str, int] = {}
    
    async def detect_and_create_account(
        self,
        page: Page,
        current_url: str,
        profile_data: Dict[str, Any],
        user_id: uuid.UUID,
    ) -> Tuple[bool, Optional[str]]:
        """
        Detect if we're on a career page requiring account creation and create one.
        
        Args:
            page: Playwright page object
            current_url: Current browser URL
            profile_data: User profile information
            user_id: User UUID for storing credentials
            
        Returns:
            Tuple of (success: bool, platform_name: Optional[str])
        """
        # Detect ATS platform from URL
        platform = self._detect_ats_platform(current_url)
        
        if not platform:
            logger.info("no_supported_ats_detected", extra={"url": current_url})
            return False, None
        
        logger.info(
            "ats_platform_detected",
            extra={"platform": platform, "url": current_url}
        )
        
        # Check if already logged in
        is_logged_in = await self._check_if_logged_in(page, platform)
        if is_logged_in:
            logger.info("already_logged_in", extra={"platform": platform})
            return True, platform
        
        # Check if we have stored credentials
        async with SessionLocal() as session:
            existing_creds = await vault_repository.get_portal_session(
                session, user_id, f"{platform}_credentials"
            )
            
            if existing_creds and existing_creds.encrypted_session_payload:
                # Try to use existing credentials
                from app.infrastructure.db.vault_repository import decrypt_payload
                creds = decrypt_payload(existing_creds.encrypted_session_payload)
                success = await self._login_with_credentials(page, platform, creds)
                if success:
                    return True, platform
        
        # Create new account if enabled
        if not settings.auto_create_accounts:
            logger.warning("auto_create_accounts_disabled")
            return False, platform
        
        # Attempt account creation
        try:
            success = await self._create_account_on_platform(
                page, platform, profile_data, user_id
            )
            return success, platform if success else None
        except Exception as e:
            logger.error(
                "account_creation_failed",
                extra={"platform": platform, "error": str(e)}
            )
            return False, None
    
    def _detect_ats_platform(self, url: str) -> Optional[str]:
        """Detect ATS platform from URL patterns."""
        url_lower = url.lower()
        
        if "greenhouse.io" in url_lower or "boards.greenhouse" in url_lower:
            return "greenhouse"
        if "lever.co" in url_lower or "jobs.lever" in url_lower:
            return "lever"
        if "myworkday.com" in url_lower or "wd5" in url_lower:
            return "workday"
        if "icims.com" in url_lower or "job icims" in url_lower:
            return "icims"
        if "taleo.net" in url_lower or "oraclecloud.com" in url_lower:
            return "taleo"
        
        # Try to detect from page content if URL doesn't reveal it
        return None
    
    async def _check_if_logged_in(self, page: Page, platform: str) -> bool:
        """Check if user is already logged in to the platform."""
        platform_config = self.ATS_PLATFORMS.get(platform, {})
        success_indicators = platform_config.get("success_indicators", [])
        
        # Look for logout button or profile indicators
        logout_selectors = [
            "a[href*='logout']",
            "a[href*='signout']",
            "button:has-text('Logout')",
            "button:has-text('Sign out')",
            "[data-testid='user-menu']",
            ".user-menu",
            "#user-profile",
        ]
        
        for selector in logout_selectors:
            try:
                count = await page.locator(selector).count()
                if count > 0:
                    return True
            except Exception:
                continue
        
        # Check for success indicators in page text
        try:
            body_text = await page.locator("body").inner_text()
            for indicator in success_indicators:
                if indicator.lower() in body_text.lower():
                    return True
        except Exception:
            pass
        
        return False
    
    async def _create_account_on_platform(
        self,
        page: Page,
        platform: str,
        profile_data: Dict[str, Any],
        user_id: uuid.UUID,
    ) -> bool:
        """Create an account on the specified ATS platform."""
        platform_config = self.ATS_PLATFORMS.get(platform)
        if not platform_config:
            logger.warning("unsupported_platform_for_signup", extra={"platform": platform})
            return False
        
        # Navigate to signup page
        signup_url = platform_config.get("signup_url")
        if signup_url:
            try:
                await page.goto(signup_url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(2000)  # Wait for page to stabilize
            except PlaywrightTimeoutError:
                logger.warning("signup_page_timeout", extra={"platform": platform})
                return False
        
        # Generate secure password
        password = self._generate_secure_password(settings.default_password_length)
        
        # Fill registration form
        try:
            # Email
            email_selector = platform_config.get("email_selector")
            if email_selector:
                email_field = page.locator(email_selector).first
                await email_field.wait_for(state="visible", timeout=10000)
                await email_field.fill(profile_data.get("email", ""))
            
            # Password
            password_selector = platform_config.get("password_selector")
            if password_selector:
                password_field = page.locator(password_selector).first
                await password_field.wait_for(state="visible", timeout=10000)
                await password_field.fill(password)
            
            # Confirm password (if required)
            confirm_selector = platform_config.get("confirm_password_selector")
            if confirm_selector:
                confirm_field = page.locator(confirm_selector).first
                try:
                    await confirm_field.wait_for(state="visible", timeout=5000)
                    await confirm_field.fill(password)
                except PlaywrightTimeoutError:
                    pass  # Some platforms don't require confirmation
            
            # First name
            first_name_selector = platform_config.get("first_name_selector")
            if first_name_selector:
                try:
                    first_name_field = page.locator(first_name_selector).first
                    await first_name_field.wait_for(state="visible", timeout=5000)
                    await first_name_field.fill(profile_data.get("first_name", ""))
                except PlaywrightTimeoutError:
                    pass
            
            # Last name
            last_name_selector = platform_config.get("last_name_selector")
            if last_name_selector:
                try:
                    last_name_field = page.locator(last_name_selector).first
                    await last_name_field.wait_for(state="visible", timeout=5000)
                    await last_name_field.fill(profile_data.get("last_name", ""))
                except PlaywrightTimeoutError:
                    pass
            
            # Submit form
            submit_selector = platform_config.get("submit_selector")
            if submit_selector:
                submit_button = page.locator(submit_selector).first
                try:
                    await submit_button.wait_for(state="clickable", timeout=10000)
                    await submit_button.click()
                    await page.wait_for_load_state("networkidle", timeout=30000)
                except PlaywrightTimeoutError:
                    logger.warning("form_submit_timeout", extra={"platform": platform})
                    return False
            
            # Wait for success indication
            await page.wait_for_timeout(3000)
            
            # Verify account creation
            success_indicators = platform_config.get("success_indicators", [])
            body_text = await page.locator("body").inner_text()
            
            account_created = any(
                indicator.lower() in body_text.lower() 
                for indicator in success_indicators
            )
            
            if account_created or await self._check_if_logged_in(page, platform):
                # Store credentials securely
                await self._store_credentials(
                    user_id, platform, profile_data.get("email", ""), password
                )
                
                # Capture session cookies
                cookies = await page.context.cookies()
                await self._store_session_cookies(user_id, platform, cookies)
                
                logger.info(
                    "account_created_successfully",
                    extra={"platform": platform, "email": profile_data.get("email")}
                )
                return True
            
            logger.warning(
                "account_creation_uncertain",
                extra={"platform": platform}
            )
            return False
            
        except PlaywrightTimeoutError as e:
            logger.error(
                "form_interaction_timeout",
                extra={"platform": platform, "error": str(e)}
            )
            return False
        except Exception as e:
            logger.error(
                "account_creation_error",
                extra={"platform": platform, "error": str(e)}
            )
            return False
    
    def _generate_secure_password(self, length: int = 16) -> str:
        """Generate a secure random password."""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        # Ensure at least one of each type
        password = [
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.digits),
            secrets.choice("!@#$%^&*"),
        ]
        # Fill remaining length
        password += [secrets.choice(alphabet) for _ in range(length - 4)]
        # Shuffle
        password_list = list(password)
        secrets.SystemRandom().shuffle(password_list)
        return "".join(password_list)
    
    async def _store_credentials(
        self, user_id: uuid.UUID, platform: str, email: str, password: str
    ) -> None:
        """Store account credentials securely in the vault."""
        import json
        from app.infrastructure.db.vault_repository import encrypt_payload
        
        credentials = {
            "platform": platform,
            "email": email,
            "password": password,
            "created_at": str(asyncio.get_event_loop().time()),
            "type": "account_credentials",
        }
        
        encrypted_payload = encrypt_payload(json.dumps(credentials))
        
        async with SessionLocal() as session:
            try:
                await vault_repository.upsert_session(
                    session,
                    user_id=user_id,
                    portal_name=f"{platform}_credentials",
                    encrypted_payload=encrypted_payload,
                    expires_at=None,  # Credentials don't expire
                )
                await session.commit()
                logger.info("credentials_stored", extra={"platform": platform})
            except Exception as e:
                logger.error(
                    "credentials_storage_failed",
                    extra={"platform": platform, "error": str(e)}
                )
    
    async def _store_session_cookies(
        self, user_id: uuid.UUID, platform: str, cookies: list
    ) -> None:
        """Store session cookies for future automated logins."""
        import json
        from app.infrastructure.db.vault_repository import encrypt_payload
        
        session_data = {
            "platform": platform,
            "cookies": cookies,
            "type": "session_cookies",
        }
        
        encrypted_payload = encrypt_payload(json.dumps(session_data))
        
        async with SessionLocal() as session:
            try:
                await vault_repository.upsert_session(
                    session,
                    user_id=user_id,
                    portal_name=platform,
                    encrypted_payload=encrypted_payload,
                    expires_at=None,
                )
                await session.commit()
                logger.info("session_cookies_stored", extra={"platform": platform})
            except Exception as e:
                logger.error(
                    "cookie_storage_failed",
                    extra={"platform": platform, "error": str(e)}
                )
    
    async def _login_with_credentials(
        self, page: Page, platform: str, credentials_json: str
    ) -> bool:
        """Attempt login using stored credentials."""
        import json
        
        try:
            creds = json.loads(credentials_json)
            email = creds.get("email", "")
            password = creds.get("password", "")
            
            if not email or not password:
                return False
            
            platform_config = self.ATS_PLATFORMS.get(platform, {})
            
            # Navigate to login page
            login_url = platform_config.get("signup_url", "").replace("signup", "signin").replace("signup", "login")
            if not login_url:
                # Try common login URL patterns
                base_urls = {
                    "greenhouse": "https://boards.greenhouse.io/signin",
                    "lever": "https://www.lever.co/login",
                    "workday": "https://www.myworkday.com/login",
                }
                login_url = base_urls.get(platform, "")
            
            if login_url:
                await page.goto(login_url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(2000)
            
            # Find and fill login form
            email_selector = platform_config.get("email_selector", "input[type='email']")
            password_selector = platform_config.get("password_selector", "input[type='password']")
            submit_selector = platform_config.get("submit_selector", "button[type='submit']")
            
            try:
                email_field = page.locator(email_selector).first
                await email_field.wait_for(state="visible", timeout=10000)
                await email_field.fill(email)
                
                password_field = page.locator(password_selector).first
                await password_field.wait_for(state="visible", timeout=10000)
                await password_field.fill(password)
                
                submit_button = page.locator(submit_selector).first
                await submit_button.wait_for(state="clickable", timeout=10000)
                await submit_button.click()
                
                await page.wait_for_load_state("networkidle", timeout=30000)
                await page.wait_for_timeout(3000)
                
                # Check if login succeeded
                if await self._check_if_logged_in(page, platform):
                    # Update session cookies
                    cookies = await page.context.cookies()
                    await self._store_session_cookies(uuid.UUID(creds.get("user_id", str(uuid.uuid4()))), platform, cookies)
                    return True
                    
            except PlaywrightTimeoutError:
                logger.warning("login_form_interaction_timeout", extra={"platform": platform})
            
            return False
            
        except Exception as e:
            logger.error(
                "login_with_credentials_failed",
                extra={"platform": platform, "error": str(e)}
            )
            return False


# Singleton instance
account_creation_service = AccountCreationService()
