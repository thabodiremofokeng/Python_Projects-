#!/usr/bin/env python3
"""
Unified Auto Job Application Launcher
Combines job scraping, AI analysis, and web interface in one application
"""

import sys
import os
import threading
import time
import webbrowser
from pathlib import Path
import signal
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))
sys.path.append(str(Path(__file__).parent / 'web'))

from loguru import logger

class UnifiedJobApp:
    """Unified application that combines scraping and web interface"""
    
    def __init__(self):
        self.web_app = None
        self.scraping_thread = None
        self.running = True
        self.setup_signal_handlers()
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info("Shutdown signal received")
            self.shutdown()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def initialize_system(self):
        """Initialize the system components"""
        try:
            from config_manager import ConfigManager
            from database_manager import DatabaseManager
            
            logger.info("🚀 Initializing Auto Job Application System")
            
            # Initialize configuration
            self.config = ConfigManager()
            
            # Validate configuration
            try:
                self.config.validate_config()
                logger.info("✅ Configuration validated")
            except Exception as e:
                logger.error(f"❌ Configuration error: {e}")
                return False
            
            # Initialize database
            self.db = DatabaseManager()
            logger.info("✅ Database initialized")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ System initialization failed: {e}")
            return False
    
    def start_background_scraping(self):
        """Start background job scraping in a separate thread"""
        def scraping_worker():
            try:
                from resume_parser import ResumeParser
                from job_scraper import JobScraper
                from gemini_matcher import GeminiMatcher
                
                logger.info("🕷️ Starting background job scraping...")
                
                # Initialize components
                resume_parser = ResumeParser(self.config)
                job_scraper = JobScraper(self.config)
                gemini_matcher = GeminiMatcher(self.config)
                
                # Parse resume once
                logger.info("📄 Parsing resume...")
                resume_data = resume_parser.parse_resume()
                
                # Save resume to database
                resume_config = self.config.get_resume_config()
                resume_path = Path(resume_config['file_path'])
                
                if resume_path.exists():
                    file_size = resume_path.stat().st_size
                    self.db.save_resume(
                        filename=resume_path.name,
                        file_path=str(resume_path.absolute()),
                        file_size=file_size,
                        parsed_data=resume_data
                    )
                    logger.info("✅ Resume saved to database")
                
                # Continuous scraping loop
                scrape_interval = 3600  # 1 hour between scrapes
                last_scrape = datetime.min
                
                while self.running:
                    try:
                        current_time = datetime.now()
                        time_since_scrape = (current_time - last_scrape).total_seconds()
                        
                        if time_since_scrape >= scrape_interval:
                            logger.info("🔍 Starting job scraping cycle...")
                            
                            # Scrape jobs
                            jobs = job_scraper.scrape_jobs()
                            
                            if jobs:
                                logger.info(f"📊 Found {len(jobs)} new jobs")
                                
                                # Analyze each job
                                matched_count = 0
                                for job in jobs:
                                    # Save job to database
                                    job_id = self.db.save_job_posting(job)
                                    
                                    if job_id:
                                        # Analyze with Gemini
                                        analysis = gemini_matcher._analyze_job_compatibility(resume_data, job)
                                        
                                        if analysis and analysis.get('compatibility_score', 0) > 0:
                                            self.db.save_job_analysis(job_id, analysis)
                                            matched_count += 1
                                
                                logger.info(f"🎯 {matched_count} jobs matched and analyzed")
                                last_scrape = current_time
                            else:
                                logger.warning("⚠️ No jobs found in this scraping cycle")
                        
                        # Sleep for a shorter interval to check for shutdown
                        time.sleep(60)  # Check every minute
                        
                    except Exception as e:
                        logger.error(f"❌ Error in scraping cycle: {e}")
                        time.sleep(300)  # Wait 5 minutes before retrying
                        
            except Exception as e:
                logger.error(f"❌ Background scraping failed: {e}")
        
        self.scraping_thread = threading.Thread(target=scraping_worker, daemon=True)
        self.scraping_thread.start()
        logger.info("✅ Background scraping started")
    
    def start_web_interface(self):
        """Start the web interface"""
        try:
            from app import app, config_manager
            
            logger.info("🌐 Starting web interface...")
            
            # Start browser in background
            def open_browser():
                time.sleep(2)  # Wait for Flask to start
                webbrowser.open("http://127.0.0.1:5000")
                logger.info("🌐 Browser opened to http://127.0.0.1:5000")
            
            browser_thread = threading.Thread(target=open_browser, daemon=True)
            browser_thread.start()
            
            # Start Flask app
            app.run(
                debug=False,
                host='127.0.0.1',
                port=5000,
                threaded=True,
                use_reloader=False  # Disable reloader to avoid issues with threads
            )
            
        except Exception as e:
            logger.error(f"❌ Web interface failed: {e}")
    
    def initial_setup(self):
        """Perform initial setup if needed"""
        try:
            # Check if resume exists
            resume_config = self.config.get_resume_config()
            resume_path = Path(resume_config.get('file_path', ''))
            
            if not resume_path.exists():
                logger.warning("⚠️ Resume file not found. Please add your resume to data/resume/")
                return False
            
            # Check if we have any jobs in database
            stats = self.db.get_dashboard_stats()
            
            if stats['total_matched_jobs'] == 0:
                logger.info("📊 No jobs in database - will start scraping immediately")
                return True
            else:
                logger.info(f"📊 Found {stats['total_matched_jobs']} existing jobs in database")
                return True
                
        except Exception as e:
            logger.error(f"❌ Initial setup failed: {e}")
            return False
    
    def run(self):
        """Main application entry point"""
        print("🚀 Auto Job Application System - Unified Launcher")
        print("=" * 60)
        
        # Initialize system
        if not self.initialize_system():
            print("❌ System initialization failed")
            return 1
        
        # Perform initial setup
        if not self.initial_setup():
            print("❌ Initial setup failed")
            return 1
        
        print("\n🎯 System Status:")
        print("✅ Configuration loaded")
        print("✅ Database ready")
        print("✅ Resume found")
        
        # Start background scraping
        self.start_background_scraping()
        
        print("\n🌐 Starting services...")
        print("✅ Background job scraping started")
        print("✅ Web interface starting...")
        print("\n" + "=" * 60)
        print("🎉 System is running!")
        print("🌐 Web interface: http://127.0.0.1:5000")
        print("🕷️ Background scraping: Active")
        print("🛑 Press Ctrl+C to stop")
        print("=" * 60)
        
        # Start web interface (this blocks)
        self.start_web_interface()
        
        return 0
    
    def shutdown(self):
        """Gracefully shutdown the application"""
        logger.info("🛑 Shutting down application...")
        self.running = False
        
        if self.scraping_thread and self.scraping_thread.is_alive():
            logger.info("⏳ Waiting for scraping thread to finish...")
            self.scraping_thread.join(timeout=5)
        
        logger.info("👋 Application shutdown complete")

def main():
    """Main entry point"""
    try:
        app = UnifiedJobApp()
        return app.run()
    except KeyboardInterrupt:
        logger.info("\n👋 Application interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
