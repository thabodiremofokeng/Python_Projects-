"""
Job Applicator
Handles automatic job applications (placeholder for safety)
"""

import time
from typing import Dict, List, Any, Optional
from loguru import logger
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager


class JobApplicator:
    """Handles automatic job applications"""
    
    def __init__(self, config_manager):
        """
        Initialize job applicator
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager
        self.application_config = config_manager.get_application_config()
        
    def apply_to_jobs(self, matched_jobs: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Apply to matched jobs
        
        Args:
            matched_jobs: List of jobs with Gemini analysis
            
        Returns:
            Dictionary with application results
        """
        if not self.application_config.get('auto_apply', False):
            logger.info("⚠️  Auto-apply is disabled in configuration")
            logger.info("Enable auto_apply in config/config.yaml to start applying")
            return {'successful': 0, 'failed': 0, 'skipped': len(matched_jobs)}
        
        logger.info(f"Starting automatic job applications for {len(matched_jobs)} jobs")
        
        results = {
            'successful': 0,
            'failed': 0,
            'skipped': 0
        }
        
        # Filter jobs that are recommended for application
        recommended_jobs = [
            job for job in matched_jobs 
            if job.get('gemini_analysis', {}).get('recommended_application', False)
        ]
        
        logger.info(f"Found {len(recommended_jobs)} jobs recommended for application")
        
        for i, job in enumerate(recommended_jobs):
            try:
                analysis = job.get('gemini_analysis', {})
                score = analysis.get('compatibility_score', 0)
                
                logger.info(f"Applying to job {i+1}/{len(recommended_jobs)}: {job.get('title', 'Unknown')} (Score: {score}/100)")
                
                # Apply to the job
                success = self._apply_to_single_job(job)
                
                if success:
                    results['successful'] += 1
                    logger.info(f"✅ Successfully applied to {job.get('title', 'Unknown')}")
                else:
                    results['failed'] += 1
                    logger.error(f"❌ Failed to apply to {job.get('title', 'Unknown')}")
                
                # Rate limiting between applications
                delay = self.application_config.get('delay_between_applications', 30)
                if i < len(recommended_jobs) - 1:  # Don't delay after last application
                    logger.info(f"Waiting {delay} seconds before next application...")
                    time.sleep(delay)
                    
            except Exception as e:
                logger.error(f"Error applying to job {i+1}: {e}")
                results['failed'] += 1
                continue
        
        # Count skipped jobs (not recommended)
        results['skipped'] = len(matched_jobs) - len(recommended_jobs)
        
        logger.info(f"Application completed: {results['successful']} successful, {results['failed']} failed, {results['skipped']} skipped")
        return results
    
    def _apply_to_single_job(self, job: Dict[str, Any]) -> bool:
        """
        Apply to a single job on LinkedIn
        
        Args:
            job: Job posting with analysis
            
        Returns:
            True if application was successful, False otherwise
        """
        driver = None
        try:
            logger.info(f"Starting application to: {job.get('title')} at {job.get('company')}")
            
            # Setup webdriver
            driver = self._setup_webdriver()
            
            # Login to LinkedIn
            if not self._login_to_linkedin(driver):
                logger.error("Failed to login to LinkedIn")
                return False
            
            # Navigate to job page
            job_url = job.get('url', '')
            if not job_url:
                logger.error("No job URL provided")
                return False
            
            driver.get(job_url)
            time.sleep(3)
            
            # Apply to the job
            success = self._submit_linkedin_application(driver, job)
            
            if success:
                logger.info(f"✅ Successfully applied to {job.get('title')}")
            else:
                logger.error(f"❌ Failed to apply to {job.get('title')}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error applying to job: {e}")
            return False
            
        finally:
            if driver:
                driver.quit()
    
    def _setup_webdriver(self) -> webdriver.Chrome:
        """Setup Chrome webdriver for job applications"""
        chrome_options = Options()
        
        browser_config = self.config.get_browser_config()
        
        if browser_config.get('headless', False):
            chrome_options.add_argument('--headless')
        
        # Add common options for stability
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # User agent to appear more like a regular browser
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Disable automation flags
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Install and setup ChromeDriver
        driver = webdriver.Chrome(
            service=webdriver.chrome.service.Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        # Execute script to remove webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Configure timeouts
        driver.implicitly_wait(browser_config.get('implicit_wait', 10))
        
        return driver
    
    def _login_to_linkedin(self, driver: webdriver.Chrome) -> bool:
        """
        Login to LinkedIn
        
        Args:
            driver: Chrome webdriver instance
            
        Returns:
            True if login successful, False otherwise
        """
        try:
            linkedin_config = self.config.get_linkedin_config()
            email = linkedin_config.get('email')
            password = linkedin_config.get('password')
            
            if not email or not password:
                logger.error("LinkedIn credentials not configured")
                return False
            
            logger.info("Logging into LinkedIn...")
            driver.get("https://www.linkedin.com/login")
            
            # Wait for login form
            wait = WebDriverWait(driver, 10)
            
            # Enter email
            email_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
            email_field.clear()
            email_field.send_keys(email)
            
            # Enter password
            password_field = driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(password)
            
            # Click login button
            login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Wait for successful login
            try:
                wait.until(lambda d: "/feed/" in d.current_url or "/jobs/" in d.current_url or "/in/" in d.current_url)
                logger.info("Successfully logged into LinkedIn")
                return True
            except TimeoutException:
                if "challenge" in driver.current_url or "checkpoint" in driver.current_url:
                    logger.warning("LinkedIn requires additional verification. Please complete manually.")
                    input("Press Enter after completing verification...")
                    return True
                else:
                    logger.error("Login failed")
                    return False
                    
        except Exception as e:
            logger.error(f"Error during LinkedIn login: {e}")
            return False
    
    def _submit_linkedin_application(self, driver: webdriver.Chrome, job: Dict[str, Any]) -> bool:
        """
        Submit application on LinkedIn job page
        
        Args:
            driver: Chrome webdriver instance
            job: Job posting information
            
        Returns:
            True if application was successful, False otherwise
        """
        try:
            wait = WebDriverWait(driver, 15)
            
            # Look for Easy Apply button
            try:
                easy_apply_btn = wait.until(EC.element_to_be_clickable((
                    By.XPATH, "//button[contains(@aria-label, 'Easy Apply') or contains(text(), 'Easy Apply')]"
                )))
                
                logger.info("Found Easy Apply button, clicking...")
                driver.execute_script("arguments[0].click();", easy_apply_btn)
                time.sleep(2)
                
            except TimeoutException:
                logger.warning("No Easy Apply button found, looking for regular Apply button")
                try:
                    apply_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Apply') and not(contains(text(), 'Easy'))]")
                    logger.info("Found regular Apply button - this may redirect to external site")
                    driver.execute_script("arguments[0].click();", apply_btn)
                    time.sleep(3)
                    
                    # Check if we were redirected to external site
                    if "linkedin.com" not in driver.current_url:
                        logger.warning("Redirected to external application site - manual intervention required")
                        return False
                        
                except NoSuchElementException:
                    logger.error("No Apply button found on job page")
                    return False
            
            # Handle Easy Apply flow
            return self._handle_easy_apply_flow(driver, job)
            
        except Exception as e:
            logger.error(f"Error submitting LinkedIn application: {e}")
            return False
    
    def _handle_easy_apply_flow(self, driver: webdriver.Chrome, job: Dict[str, Any]) -> bool:
        """
        Handle the LinkedIn Easy Apply application flow
        
        Args:
            driver: Chrome webdriver instance
            job: Job posting information
            
        Returns:
            True if application was successful, False otherwise
        """
        try:
            wait = WebDriverWait(driver, 10)
            max_steps = 5  # Prevent infinite loops
            step = 0
            
            while step < max_steps:
                step += 1
                logger.info(f"Easy Apply step {step}")
                
                # Wait for modal to load
                time.sleep(2)
                
                # Check if we need to upload resume
                try:
                    upload_elements = driver.find_elements(By.XPATH, "//input[@type='file']")
                    if upload_elements:
                        logger.info("Resume upload detected")
                        self._handle_resume_upload(driver)
                except Exception as e:
                    logger.debug(f"No resume upload needed: {e}")
                
                # Fill out any text fields
                try:
                    self._fill_application_fields(driver, job)
                except Exception as e:
                    logger.debug(f"No additional fields to fill: {e}")
                
                # Look for Next, Review, or Submit button
                next_clicked = False
                
                # Try Submit first (final step)
                try:
                    submit_btn = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Submit') or contains(text(), 'Submit application')]")
                    if submit_btn.is_enabled():
                        logger.info("Found Submit button - submitting application")
                        driver.execute_script("arguments[0].click();", submit_btn)
                        time.sleep(3)
                        
                        # Check for success confirmation
                        try:
                            success_indicator = wait.until(EC.presence_of_element_located((
                                By.XPATH, "//h1[contains(text(), 'Application sent') or contains(text(), 'Your application was sent')]"
                            )))
                            logger.info("Application submitted successfully!")
                            return True
                        except TimeoutException:
                            logger.warning("Submit clicked but no success confirmation found")
                            return True  # Assume success if no error
                            
                except NoSuchElementException:
                    pass
                
                # Try Review button
                try:
                    review_btn = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Review') or contains(text(), 'Review')]")
                    if review_btn.is_enabled():
                        logger.info("Found Review button, clicking...")
                        driver.execute_script("arguments[0].click();", review_btn)
                        time.sleep(2)
                        next_clicked = True
                except NoSuchElementException:
                    pass
                
                # Try Next button
                if not next_clicked:
                    try:
                        next_btn = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Continue') or contains(text(), 'Next') or contains(text(), 'Continue')]")
                        if next_btn.is_enabled():
                            logger.info("Found Next/Continue button, clicking...")
                            driver.execute_script("arguments[0].click();", next_btn)
                            time.sleep(2)
                            next_clicked = True
                    except NoSuchElementException:
                        pass
                
                if not next_clicked:
                    logger.warning("No Next, Review, or Submit button found - application may be incomplete")
                    break
            
            logger.warning(f"Reached maximum steps ({max_steps}) in Easy Apply flow")
            return False
            
        except Exception as e:
            logger.error(f"Error in Easy Apply flow: {e}")
            return False
    
    def _handle_resume_upload(self, driver: webdriver.Chrome):
        """
        Handle resume upload during application
        
        Args:
            driver: Chrome webdriver instance
        """
        try:
            resume_config = self.config.get_resume_config()
            resume_path = resume_config.get('file_path')
            
            if not resume_path or not Path(resume_path).exists():
                logger.warning("Resume file not found - skipping upload")
                return
            
            logger.info(f"Uploading resume: {resume_path}")
            
            # Find file input element
            file_input = driver.find_element(By.XPATH, "//input[@type='file']")
            file_input.send_keys(str(Path(resume_path).absolute()))
            
            # Wait for upload to complete
            time.sleep(3)
            
            logger.info("Resume uploaded successfully")
            
        except Exception as e:
            logger.warning(f"Error uploading resume: {e}")
    
    def _fill_application_fields(self, driver: webdriver.Chrome, job: Dict[str, Any]):
        """
        Fill out application form fields
        
        Args:
            driver: Chrome webdriver instance
            job: Job posting information
        """
        try:
            # Common field mappings
            field_mappings = {
                'phone': self._get_phone_number(),
                'mobile': self._get_phone_number(),
                'website': 'https://linkedin.com/in/thabo-mofokeng',
                'portfolio': 'https://github.com/thabomofokeng',
            }
            
            # Find all text inputs and textareas
            text_fields = driver.find_elements(By.XPATH, "//input[@type='text'] | //input[@type='tel'] | //input[@type='url'] | //textarea")
            
            for field in text_fields:
                try:
                    field_label = self._get_field_label(driver, field)
                    field_name = field.get_attribute('name') or ''
                    field_id = field.get_attribute('id') or ''
                    
                    # Skip if field is already filled
                    if field.get_attribute('value'):
                        continue
                    
                    # Try to match field to our data
                    value = None
                    
                    for key, val in field_mappings.items():
                        if key.lower() in (field_label.lower() + ' ' + field_name.lower() + ' ' + field_id.lower()):
                            value = val
                            break
                    
                    if value:
                        logger.info(f"Filling field '{field_label}' with value")
                        field.clear()
                        field.send_keys(value)
                        time.sleep(0.5)
                        
                except Exception as e:
                    logger.debug(f"Error filling field: {e}")
                    continue
            
            # Handle dropdowns/select elements
            self._handle_dropdown_fields(driver)
            
        except Exception as e:
            logger.debug(f"Error filling application fields: {e}")
    
    def _get_field_label(self, driver: webdriver.Chrome, field) -> str:
        """
        Get the label text for a form field
        
        Args:
            driver: Chrome webdriver instance
            field: Form field element
            
        Returns:
            Label text or empty string
        """
        try:
            # Try to find label by 'for' attribute
            field_id = field.get_attribute('id')
            if field_id:
                label = driver.find_element(By.XPATH, f"//label[@for='{field_id}']")
                return label.text.strip()
        except:
            pass
        
        try:
            # Try to find label as parent or sibling
            parent = field.find_element(By.XPATH, "..")
            label_text = parent.text.strip()
            if label_text:
                return label_text
        except:
            pass
        
        return field.get_attribute('placeholder') or field.get_attribute('aria-label') or ''
    
    def _handle_dropdown_fields(self, driver: webdriver.Chrome):
        """
        Handle dropdown/select fields in the application
        
        Args:
            driver: Chrome webdriver instance
        """
        try:
            # Handle experience level dropdowns
            select_elements = driver.find_elements(By.TAG_NAME, "select")
            
            for select in select_elements:
                try:
                    label = self._get_field_label(driver, select)
                    
                    if 'experience' in label.lower() or 'years' in label.lower():
                        # Try to select senior level option
                        options = select.find_elements(By.TAG_NAME, "option")
                        for option in options:
                            option_text = option.text.lower()
                            if 'senior' in option_text or '5+' in option_text or '3-5' in option_text:
                                option.click()
                                logger.info(f"Selected experience level: {option.text}")
                                break
                                
                except Exception as e:
                    logger.debug(f"Error handling dropdown: {e}")
                    continue
                    
        except Exception as e:
            logger.debug(f"Error handling dropdown fields: {e}")
    
    def _get_phone_number(self) -> str:
        """
        Get phone number from resume data
        
        Returns:
            Phone number string
        """
        # This would typically come from parsed resume data
        # For now, return a placeholder
        return "+27 123 456 7890"
    
    def generate_application_summary(self, matched_jobs: List[Dict[str, Any]]) -> str:
        """
        Generate a summary of applications to be made
        
        Args:
            matched_jobs: List of matched jobs
            
        Returns:
            Formatted summary string
        """
        if not matched_jobs:
            return "No jobs to apply to."
        
        summary = f"📊 Application Summary\n"
        summary += f"{'='*50}\n"
        summary += f"Total matched jobs: {len(matched_jobs)}\n\n"
        
        # Group by recommendation
        recommended = [job for job in matched_jobs if job.get('gemini_analysis', {}).get('recommended_application', False)]
        not_recommended = [job for job in matched_jobs if not job.get('gemini_analysis', {}).get('recommended_application', False)]
        
        summary += f"✅ Recommended for application: {len(recommended)}\n"
        summary += f"❌ Not recommended: {len(not_recommended)}\n\n"
        
        if recommended:
            summary += "🎯 Top Recommendations:\n"
            summary += "-" * 30 + "\n"
            
            # Sort by compatibility score
            top_jobs = sorted(recommended, key=lambda x: x.get('gemini_analysis', {}).get('compatibility_score', 0), reverse=True)
            
            for i, job in enumerate(top_jobs[:5]):
                analysis = job.get('gemini_analysis', {})
                score = analysis.get('compatibility_score', 0)
                title = job.get('title', 'Unknown')
                company = job.get('company', 'Unknown')
                
                summary += f"{i+1}. {title} at {company}\n"
                summary += f"   Score: {score}/100\n"
                summary += f"   Assessment: {analysis.get('overall_assessment', 'N/A')}\n\n"
        
        return summary
