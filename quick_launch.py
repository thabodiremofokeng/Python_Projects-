#!/usr/bin/env python3
"""
Quick Launch Auto Job Application System
Simple launcher with immediate scraping and web interface
"""

import sys
import os
import threading
import time
import webbrowser
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))
sys.path.append(str(Path(__file__).parent / 'web'))

def run_initial_scraping():
    """Run initial job scraping and analysis"""
    try:
        from config_manager import ConfigManager
        from database_manager import DatabaseManager
        from resume_parser import ResumeParser
        from job_scraper import JobScraper
        from gemini_matcher import GeminiMatcher
        
        print("🔍 Running initial job search and analysis...")
        print("=" * 50)
        
        # Initialize components
        config_manager = ConfigManager()
        db_manager = DatabaseManager()
        
        # Parse resume
        print("📄 Parsing resume...")
        resume_parser = ResumeParser(config_manager)
        resume_data = resume_parser.parse_resume()
        
        # Save resume to database
        resume_config = config_manager.get_resume_config()
        resume_path = Path(resume_config['file_path'])
        
        if resume_path.exists():
            file_size = resume_path.stat().st_size
            resume_id = db_manager.save_resume(
                filename=resume_path.name,
                file_path=str(resume_path.absolute()),
                file_size=file_size,
                parsed_data=resume_data
            )
            print("✅ Resume parsed and saved")
        
        # Scrape jobs
        print("\n🕷️ Scraping LinkedIn jobs...")
        job_scraper = JobScraper(config_manager)
        jobs = job_scraper.scrape_jobs()
        
        if not jobs:
            print("⚠️ No jobs found - check your credentials and configuration")
            return False
        
        print(f"📊 Found {len(jobs)} jobs from LinkedIn")
        
        # Analyze jobs with AI
        print("\n🤖 Analyzing jobs with Gemini AI...")
        gemini_matcher = GeminiMatcher(config_manager)
        
        matched_count = 0
        for i, job in enumerate(jobs, 1):
            print(f"Analyzing job {i}/{len(jobs)}: {job['title']} at {job['company']}")
            
            # Save job to database
            job_id = db_manager.save_job_posting(job)
            
            if job_id:
                # Analyze with Gemini
                analysis = gemini_matcher._analyze_job_compatibility(resume_data, job)
                
                if analysis and analysis.get('compatibility_score', 0) > 0:
                    db_manager.save_job_analysis(job_id, analysis)
                    matched_count += 1
        
        print(f"\n🎯 Analysis complete! {matched_count} jobs matched and ready for review")
        return True
        
    except Exception as e:
        print(f"❌ Error during initial scraping: {e}")
        import traceback
        traceback.print_exc()
        return False

def start_web_interface():
    """Start the web interface"""
    try:
        from app import app
        
        print("\n🌐 Starting web interface...")
        
        # Start browser in background
        def open_browser():
            time.sleep(2)
            webbrowser.open("http://127.0.0.1:5000")
            print("🌐 Browser opened to http://127.0.0.1:5000")
        
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        print("✅ Web interface starting...")
        print("\n" + "=" * 60)
        print("🎉 System is ready!")
        print("🌐 Web interface: http://127.0.0.1:5000")
        print("📊 Browse and apply to your matched jobs")
        print("🛑 Press Ctrl+C to stop")
        print("=" * 60)
        
        # Start Flask app
        app.run(
            debug=False,
            host='127.0.0.1',
            port=5000,
            threaded=True
        )
        
    except Exception as e:
        print(f"❌ Web interface error: {e}")

def main():
    """Main entry point"""
    print("⚡ Quick Launch - Auto Job Application System")
    print("=" * 60)
    
    # Ask user what they want to do
    print("\nChoose an option:")
    print("1. Run job search + start web interface (recommended)")
    print("2. Just start web interface (use existing data)")
    print("3. Just run job search (no web interface)")
    
    try:
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            print("\n🚀 Running full setup...")
            success = run_initial_scraping()
            if success:
                start_web_interface()
            else:
                print("❌ Job search failed. Please check your configuration.")
                return 1
                
        elif choice == "2":
            print("\n🌐 Starting web interface with existing data...")
            start_web_interface()
            
        elif choice == "3":
            print("\n🔍 Running job search only...")
            success = run_initial_scraping()
            if success:
                print("\n✅ Job search completed!")
                print("💡 Run 'python start_app.py' to access the web interface")
            else:
                print("❌ Job search failed.")
                return 1
        else:
            print("❌ Invalid choice. Please run the script again.")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n👋 Cancelled by user")
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
