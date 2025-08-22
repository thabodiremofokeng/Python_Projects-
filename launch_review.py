#!/usr/bin/env python3
"""
Quick Review Launcher
Starts the web app and opens directly to the review jobs page
"""

import sys
import threading
import time
import webbrowser
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))
sys.path.append(str(Path(__file__).parent / 'web'))

def start_web_app_for_review():
    """Start web app and open review page"""
    try:
        from app import app
        
        print("🚀 Starting Job Review System...")
        print("=" * 50)
        print("📋 Opening Job Review Page...")
        
        # Start browser in background to review page
        def open_review_page():
            time.sleep(3)  # Wait for app to start
            review_url = "http://127.0.0.1:5000/review"
            webbrowser.open(review_url)
            print(f"🌐 Browser opened to: {review_url}")
            print("\n💡 You can now review and categorize your scraped jobs!")
        
        browser_thread = threading.Thread(target=open_review_page, daemon=True)
        browser_thread.start()
        
        print("✅ Web interface starting...")
        print("\n" + "=" * 60)
        print("🎯 Job Review System Ready!")
        print("🌐 Review Page: http://127.0.0.1:5000/review")
        print("📊 Review and categorize your scraped jobs")
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
        print(f"❌ Error starting review system: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    start_web_app_for_review()
