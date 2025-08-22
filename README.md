# Auto Job Application System 🚀

An intelligent automated system that scrapes real LinkedIn jobs, uses Google Gemini AI to analyze compatibility with your resume, and can automatically apply to suitable positions.

## ✨ Features
- **Real LinkedIn Job Scraping**: Scrapes actual job postings from LinkedIn
- **AI-Powered Matching**: Uses Google Gemini to analyze job compatibility
- **Automated Applications**: Can automatically apply to jobs via LinkedIn Easy Apply
- **Web Dashboard**: Modern web interface to browse jobs and manage applications
- **Resume Analysis**: Intelligent parsing of PDF/DOCX resumes
- **Application Tracking**: Database-driven tracking of all applications

## 📁 Project Structure
```
├── src/                    # Core application code
│   ├── main.py            # Main CLI application
│   ├── job_scraper.py     # LinkedIn job scraping
│   ├── gemini_matcher.py  # AI job matching
│   ├── job_applicator.py  # Automated job applications
│   ├── resume_parser.py   # Resume parsing and analysis
│   └── database_manager.py # SQLite database operations
├── web/                   # Web interface
│   ├── app.py            # Flask web application
│   └── templates/        # HTML templates
├── config/               # Configuration files
├── data/                # Data storage
│   ├── resume/          # Your resume files
│   ├── jobs/            # Scraped job data
│   └── *.db            # SQLite database
└── logs/               # Application logs
```

## 🛠️ Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Keys
Edit `.env` file with your credentials:
```env
GOOGLE_GEMINI_API_KEY=your_gemini_api_key_here
LINKEDIN_EMAIL=your_linkedin_email
LINKEDIN_PASSWORD=your_linkedin_password
```

### 3. Configure Job Search
Edit `config/config.yaml` to customize your job search:
```yaml
job_search:
  keywords:
    - data analyst
    - business analyst
    - python developer
  locations:
    - Remote
    - South Africa
    - Cape Town
  max_jobs_per_day: 10
```

### 4. Add Your Resume
Place your resume (PDF or DOCX) in `data/resume/` directory.

## 🚀 Quick Start

### Option 1: Test the System
```bash
# Test that everything works
python test_real_scraping.py
```

### Option 2: Full Setup and Search
```bash
# Reset database and upload resume with job search
python reset_database.py
python upload_resume_and_search.py  # This will scrape real LinkedIn jobs!
```

### Option 3: Web Interface
```bash
# Start the web application
python start_app.py
# Open http://127.0.0.1:5000 in your browser
```

### Option 4: Command Line
```bash
# Run the main application
python src/main.py
```

## 🔧 Usage Modes

### 1. Job Discovery Mode (Safe)
- Scrapes real LinkedIn jobs
- Analyzes compatibility with AI
- Saves matches to database
- **Does NOT apply automatically**
- Review matches in web interface

### 2. Automatic Application Mode (Use with Caution!)
- Set `auto_apply: true` in `config/config.yaml`
- **Will automatically apply to recommended jobs**
- Uses LinkedIn Easy Apply when available
- Includes rate limiting and error handling

## 🛡️ Safety Features

- **Auto-apply disabled by default** - You control when to enable it
- **Rate limiting** - Respects LinkedIn's usage policies
- **Manual review** - Web interface to approve applications
- **Compatibility scoring** - Only applies to high-match jobs
- **Local data** - All data stored locally and securely
- **Detailed logging** - Track all activities

## 📊 Web Dashboard

Access the web interface at `http://127.0.0.1:5000` to:
- View all scraped jobs with compatibility scores
- Read detailed AI analysis for each job
- Manually approve applications
- Generate custom cover letters
- Track application status
- Manage your resume

## ⚠️ Important Notes

### LinkedIn Usage
- This tool automates LinkedIn interactions
- Use responsibly and respect LinkedIn's terms of service
- Consider using a dedicated LinkedIn account for automation
- Monitor for any account restrictions

### Data Privacy
- All data is stored locally on your machine
- Never share your `.env` file or API keys
- Resume and job data remain private

### Rate Limiting
- Built-in delays between requests
- Configurable application delays (default: 60 seconds)
- Respects LinkedIn's anti-bot measures

## 🔄 Workflow

1. **Setup**: Configure credentials and job search criteria
2. **Scrape**: System logs into LinkedIn and searches for jobs
3. **Analyze**: Google Gemini AI analyzes each job against your resume
4. **Score**: Jobs receive compatibility scores (0-100)
5. **Filter**: Only high-scoring jobs (50+) are recommended
6. **Review**: Use web interface to review matches
7. **Apply**: Manually approve or enable auto-apply for suitable jobs
8. **Track**: Monitor application status and responses

## 🚨 Troubleshooting

### LinkedIn Login Issues
- Verify credentials in `.env` file
- Handle 2FA manually when prompted
- Check for account restrictions

### No Jobs Found
- Verify job search keywords and locations
- Check LinkedIn search results manually
- Ensure network connectivity

### Gemini API Issues
- Verify API key in `.env` file
- Check API quotas and billing
- Review error logs in `logs/app.log`

## 🎯 Tips for Best Results

1. **Optimize Keywords**: Use job titles and skills from your resume
2. **Set Realistic Locations**: Include remote and local options
3. **Monitor Compatibility Scores**: Focus on jobs with 70+ scores
4. **Review AI Analysis**: Read match reasons and skill gaps
5. **Start with Manual Review**: Don't enable auto-apply immediately
6. **Track Applications**: Monitor response rates and adjust strategy

## 📈 Next Steps

After setup:
1. Run the system daily to find new jobs
2. Review and refine your job search criteria
3. Track which types of jobs get the best responses
4. Optimize your resume based on AI feedback
5. Consider enabling auto-apply for high-confidence matches

---

**Remember**: This is a powerful tool that interacts with real job platforms. Use it responsibly and always review applications before they are sent!
