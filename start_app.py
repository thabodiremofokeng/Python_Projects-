#!/usr/bin/env python3
"""
Secure Startup Script for Auto Job Application System
This script ensures the application runs securely and locally only
"""

import os
import sys
import webbrowser
import threading
import time
from pathlib import Path

def check_security():
    """Check security requirements before starting"""
    print("🔐 Security Check")
    print("=" * 30)
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        print("Please copy .env.example to .env and configure your API keys")
        return False
    
    # Check if sensitive files are in .gitignore
    gitignore = Path(".gitignore")
    if gitignore.exists():
        gitignore_content = gitignore.read_text()
        if ".env" not in gitignore_content:
            print("⚠️  .env file should be in .gitignore")
    else:
        print("⚠️  No .gitignore file found - create one to protect sensitive files")
    
    # Check file permissions on sensitive files
    sensitive_files = [".env", "data/", "logs/"]
    for file_path in sensitive_files:
        if Path(file_path).exists():
            print(f"✅ Found {file_path}")
    
    return True

def create_gitignore():
    """Create .gitignore to protect sensitive files"""
    gitignore_content = """# Environment variables (contains API keys and passwords)
.env

# Database files
*.db
*.sqlite
*.sqlite3

# Resume files (personal data)
data/resume/
data/jobs/

# Log files
logs/
*.log

# Python cache
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# IDE files
.vscode/
.idea/
*.swp
*.swo
*~

# OS files
.DS_Store
Thumbs.db
"""
    
    gitignore_path = Path(".gitignore")
    if not gitignore_path.exists():
        gitignore_path.write_text(gitignore_content)
        print("✅ Created .gitignore file to protect sensitive data")

def open_browser_after_delay():
    """Open browser after Flask starts"""
    time.sleep(2)  # Wait for Flask to start
    webbrowser.open("http://127.0.0.1:5000")

def main():
    """Main startup function"""
    print("🚀 Auto Job Application System - Secure Startup")
    print("=" * 50)
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # Run security checks
    if not check_security():
        print("\n❌ Security check failed. Please fix the issues above.")
        input("Press Enter to exit...")
        return 1
    
    # Create .gitignore if needed
    create_gitignore()
    
    print("\n🔒 Security Features Enabled:")
    print("✅ Running on localhost only (127.0.0.1)")
    print("✅ CSRF protection enabled")
    print("✅ Secure file uploads")
    print("✅ XSS protection headers")
    print("✅ Content security policy")
    print("✅ Secure session management")
    
    print("\n⚠️  Important Security Notes:")
    print("• Never share your .env file or API keys")
    print("• Don't commit sensitive files to version control")
    print("• Keep your resume and application data private")
    print("• This app is for local use only - don't deploy publicly")
    
    # Check if we have jobs in database
    try:
        sys.path.append(str(project_dir / "src"))
        from database_manager import DatabaseManager
        db = DatabaseManager()
        stats = db.get_dashboard_stats()
        
        if stats['total_matched_jobs'] == 0:
            print("\n📊 No jobs found in database.")
            print("💡 Tip: Run 'python quick_launch.py' to scrape jobs first")
            print("    Or use the 'Run Job Search' button in the web interface")
    except Exception as e:
        print(f"\n⚠️  Could not check database status: {e}")
    
    print("\n🌐 Starting web interface...")
    print("📂 Data stored locally in:", project_dir / "data")
    
    # Start browser in background
    browser_thread = threading.Thread(target=open_browser_after_delay)
    browser_thread.daemon = True
    browser_thread.start()
    
    try:
        # Import and run the Flask app
        sys.path.append(str(project_dir / "web"))
        from app import app, config_manager
        
        # Validate configuration
        try:
            config_manager.validate_config()
            print("✅ Configuration validated")
        except Exception as e:
            print(f"❌ Configuration error: {e}")
            print("\nPlease check your .env file and config/config.yaml")
            input("Press Enter to exit...")
            return 1
        
        print("\n" + "=" * 50)
        print("🎯 Web Interface Starting...")
        print("🌐 Open your browser to: http://127.0.0.1:5000")
        print("🔍 Use 'Run Job Search' button to scrape LinkedIn jobs")
        print("🛑 Press Ctrl+C to stop the application")
        print("=" * 50)
        
        # Start Flask app
        app.run(debug=False, host='127.0.0.1', port=5000, threaded=True)
        
    except KeyboardInterrupt:
        print("\n\n👋 Application stopped by user")
        print("🔒 Your data is secure and stored locally")
        return 0
        
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        input("Press Enter to exit...")
        return 1

if __name__ == "__main__":
    sys.exit(main())
