#!/usr/bin/env python3
"""
Auto Job Application System
Main entry point for the application
"""

import sys
import os
from pathlib import Path
from loguru import logger

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent))

from config_manager import ConfigManager
from resume_parser import ResumeParser
from job_scraper import JobScraper
from gemini_matcher import GeminiMatcher
from job_applicator import JobApplicator


class AutoJobApplication:
    """Main application class that orchestrates the job application process"""
    
    def __init__(self):
        self.config = ConfigManager()
        self.resume_parser = ResumeParser(self.config)
        self.job_scraper = JobScraper(self.config)
        self.gemini_matcher = GeminiMatcher(self.config)
        self.job_applicator = JobApplicator(self.config)
        
        # Setup logging
        self._setup_logging()
        
    def _setup_logging(self):
        """Configure logging based on config settings"""
        log_config = self.config.get_logging_config()
        
        # Remove default handler
        logger.remove()
        
        # Add file handler
        logger.add(
            log_config['file'],
            level=log_config['level'],
            rotation=log_config['max_file_size'],
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
        )
        
        # Add console handler
        logger.add(
            sys.stderr,
            level=log_config['level'],
            format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>"
        )
        
    def run(self):
        """Main application loop"""
        try:
            logger.info("Starting Auto Job Application System")
            
            # Step 1: Parse resume
            logger.info("Parsing resume...")
            resume_data = self.resume_parser.parse_resume()
            logger.info(f"Resume parsed successfully. Found {len(resume_data.get('skills', []))} skills")
            
            # Step 2: Scrape jobs from LinkedIn
            logger.info("Scraping real job listings from LinkedIn...")
            jobs = self.job_scraper.scrape_jobs()
            
            if not jobs:
                logger.warning("No jobs found - check your LinkedIn credentials and search configuration")
                return
                
            logger.info(f"Found {len(jobs)} real job listings from LinkedIn")
            
            # Step 3: Match jobs using Gemini
            logger.info("Matching jobs using Google Gemini...")
            matched_jobs = self.gemini_matcher.match_jobs(resume_data, jobs)
            logger.info(f"Found {len(matched_jobs)} matching jobs")
            
            # Step 4: Apply for jobs (if auto_apply is enabled)
            if self.config.get_application_config()['auto_apply']:
                logger.info("Starting automatic job applications...")
                results = self.job_applicator.apply_to_jobs(matched_jobs)
                logger.info(f"Applied to {results['successful']} jobs, {results['failed']} failed")
            else:
                logger.info("Auto-apply is disabled. Matched jobs saved for manual review.")
                self._save_matched_jobs(matched_jobs)
                
        except Exception as e:
            logger.error(f"Application failed with error: {str(e)}")
            raise
            
    def _save_matched_jobs(self, matched_jobs):
        """Save matched jobs to file for manual review"""
        import json
        from datetime import datetime
        
        output_file = f"data/jobs/matched_jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(matched_jobs, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Matched jobs saved to {output_file}")


def main():
    """Entry point"""
    try:
        app = AutoJobApplication()
        app.run()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
