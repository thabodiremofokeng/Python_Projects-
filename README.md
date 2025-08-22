# Auto Job Application System 

An intelligent job search and application management system that combines web scraping, AI-powered job matching, and automated application tracking. The system parses your resume, finds relevant jobs, uses Google Gemini AI to analyze job compatibility, and provides a web interface to manage your job search process.

## ✨ Features
- Intelligent Job Discovery**: Scrapes jobs from multiple sources with fallback to sample data
- AI-Powered Job Matching**: Uses Google Gemini AI to analyze job-resume compatibility (0-100 score)
- Resume Intelligence**: Extracts skills, experience, and education from PDF/DOCX files
- Web Dashboard**: Modern Flask web interface for job browsing and application management
- Application Tracking**: SQLite database tracks jobs, analyses, and applications
- Security First**: Local-only operation with secure credential management
- Quick Launch**: One-command setup with background job scraping

## 🏗️ Architecture

The system consists of several integrated components:

### Core Components
- **Resume Parser** (`resume_parser.py`): Extracts structured data from PDF/DOCX resumes using NLTK
- **Job Scraper** (`job_scraper.py`): Multi-source job scraping with fallback mechanisms  
- **Gemini Matcher** (`gemini_matcher.py`): AI-powered job compatibility analysis
- **Database Manager** (`database_manager.py`): SQLite operations for jobs, analyses, and applications
- **Job Applicator** (`job_applicator.py`): Handles application workflow (disabled by default)

### Interfaces
- **Web Interface** (`web/app.py`): Flask dashboard with job browsing and management
- **CLI Interface** (`src/main.py`): Command-line job processing
- **Quick Launcher** (`quick_launch.py`): One-command setup and execution

### Data Flow
```
Resume (PDF/DOCX) → Parser → Structured Data
                                    ↓
Job Sources → Scraper → Raw Jobs → Gemini AI → Compatibility Analysis → Database
                                                        ↓
Web Dashboard ← Database ← Job Applications ← Manual Review
```

## ⚡ Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Create Configuration
```bash
# Copy configuration template
cp config/config.yaml.example config/config.yaml

# Create environment file
echo "GOOGLE_GEMINI_API_KEY=your_api_key_here" > .env
```

### 3. Add Your Resume
```bash
# Create a resume directory and add your file
mkdir -p data/resume
# Copy your resume.pdf or resume.docx to data/resume/
```

### 4. Configure Job Search
Edit `config/config.yaml`:
```yaml
job_search:
  keywords: ["data scientist", "python developer", "analyst"]
  locations: ["Remote", "Your City"]
  max_jobs_per_day: 5
google_gemini:
  api_key: YOUR_GOOGLE_GEMINI_API_KEY_HERE  # Will use .env if available
resume:
  file_path: data/resume/your_resume.pdf
```

## 🚀 Running the Application

### Option 1: Quick Launch (Recommended)
```bash
python quick_launch.py
```
This will:
- Parse your resume
- Scrape and analyze jobs
- Start the web interface
- Open your browser automatically

### Option 2: Secure Web Interface
```bash
python start_app.py
```
- Includes security checks
- Local-only operation (127.0.0.1)
- CSRF protection and secure headers

### Option 3: Background Processing
```bash
python launch_app.py
```
- Continuous background job scraping
- Web interface + automated updates
- Best for ongoing job search

### Option 4: CLI Only
```bash
python src/main.py
```
- Command-line interface only
- One-time job processing
- Saves results to JSON files

## 🎯 How It Works

### 1. Resume Analysis
- Parses PDF/DOCX resumes using PyPDF2, pdfplumber, and python-docx
- Extracts: personal info, skills, experience, education, certifications
- Uses NLTK for natural language processing
- Stores structured data in SQLite database

### 2. Job Discovery
- **Multi-source scraping**: Attempts various job sources
- **Fallback system**: Uses sample jobs if scraping fails
- **Deduplication**: Prevents duplicate job entries
- **Filtering**: Focuses on senior data roles based on keywords

### 3. AI-Powered Matching
- **Google Gemini Analysis**: Sends job description + resume to Gemini AI
- **Compatibility Scoring**: 0-100 score based on skills, experience match
- **Detailed Analysis**: Match reasons, skill gaps, cover letter suggestions
- **Application Recommendations**: AI decides if job is worth applying to

### 4. Application Management
- **Web Dashboard**: Browse jobs by compatibility score
- **Manual Review**: Approve applications before sending
- **Cover Letter Generation**: AI-generated personalized cover letters
- **Status Tracking**: Track application progress and responses

## 🔒 Security & Privacy

### Data Security
- **Local-only operation**: All data stored on your machine
- **No cloud dependencies**: Resume and job data never leaves your computer
- **Secure credential management**: API keys stored in `.env` (gitignored)
- **Config templates**: Real config files excluded from version control

### Web Interface Security
- **Localhost binding**: Only accessible from 127.0.0.1
- **CSRF protection**: Prevents cross-site request forgery
- **Security headers**: XSS protection, content security policy
- **File upload validation**: Only allows PDF/DOCX resume files

### Application Safety
- **Manual approval required**: Auto-apply disabled by default
- **Review before applying**: Web interface for application approval
- **Rate limiting**: Respects platform usage policies
- **Detailed logging**: Full audit trail of all activities

## 📊 Web Dashboard Features

### Dashboard Overview (`/`)
- **Statistics**: Total jobs, matches, applications
- **Recent Activity**: Latest matched jobs and applications
- **Quick Actions**: Run job search, upload resume

### Job Browser (`/jobs`)
- **Compatibility scores**: AI-generated 0-100 ratings
- **Detailed analysis**: Match reasons, skill gaps, recommendations
- **Company information**: Job title, company, location, salary
- **Filtering**: Sort by score, company, date

### Job Details (`/job/<id>`)
- **Full job description**: Complete posting content
- **AI analysis breakdown**: Detailed compatibility report
- **Application approval**: Review and approve applications
- **Cover letter generation**: AI-generated personalized letters

### Settings & Management
- **Resume upload**: Replace resume and reprocess matches
- **Search configuration**: Update keywords, locations, limits
- **Application history**: Track sent applications and responses

## 🛠️ Technical Details

### Database Schema
- **job_postings**: Scraped job information
- **job_analysis**: Gemini AI analysis results
- **applications**: Application tracking and status
- **resumes**: Uploaded resume files and parsed data
- **search_sessions**: Job search session tracking

### AI Analysis Process
1. **Prompt Engineering**: Creates detailed prompts combining resume + job description
2. **Gemini API Call**: Sends structured request to Google Gemini
3. **Response Parsing**: Extracts JSON analysis or creates fallback analysis
4. **Score Calculation**: 0-100 compatibility score with detailed reasoning
5. **Database Storage**: Saves analysis for web interface display

### Job Sources & Fallbacks
- **Primary**: Web scraping from job boards
- **Fallback**: Sample job generation for demo/testing
- **Filtering**: Senior data role focus based on keywords
- **Deduplication**: Hash-based duplicate prevention

## 🔄 Complete Workflow

### Initial Setup
1. **Configuration**: API keys, job search criteria, resume path
2. **Resume Upload**: Parse and extract structured data
3. **Database Initialization**: Create tables and schemas

### Job Processing Cycle
1. **Job Discovery**: Multi-source scraping with fallbacks
2. **Deduplication**: Remove duplicate postings
3. **AI Analysis**: Gemini analyzes each job vs. resume
4. **Database Storage**: Save jobs and analysis results
5. **Web Interface Update**: Real-time dashboard updates

### Application Management
1. **Job Review**: Browse compatible jobs in web interface
2. **Detailed Analysis**: Read AI compatibility reports
3. **Application Approval**: Manually review and approve
4. **Cover Letter**: Generate personalized cover letters
5. **Status Tracking**: Monitor application progress

### Continuous Operation
- **Background Scraping**: Automatic job discovery (launch_app.py)
- **Real-time Updates**: New jobs appear in dashboard
- **Progressive Analysis**: AI processes new jobs automatically

## 🚨 Troubleshooting

### Configuration Issues
```bash
# Check if config files exist
ls config/config.yaml .env

# Validate Gemini API key
python -c "import google.generativeai as genai; genai.configure(api_key='your_key'); print('✅ API key valid')"
```

### Resume Parsing Problems
```bash
# Test resume parsing directly
python -c "from src.resume_parser import ResumeParser; from src.config_manager import ConfigManager; rp = ResumeParser(ConfigManager()); print(rp.parse_resume())"
```

### Database Issues
```bash
# Reset database
rm -f data/job_applications.db
python -c "from src.database_manager import DatabaseManager; DatabaseManager().init_database()"
```

### Web Interface Not Starting
```bash
# Check if port 5000 is in use
netstat -an | grep :5000

# Start with different port
FLASK_PORT=5001 python start_app.py
```

### Common Error Messages
- **"Resume file not found"**: Check file path in `config/config.yaml`
- **"API key not configured"**: Add `GOOGLE_GEMINI_API_KEY` to `.env`
- **"No jobs found"**: Normal if sources are down, will use sample data
- **"JSON parsing failed"**: Gemini response format issue, fallback analysis used

## 💡 Tips for Best Results

### Resume Optimization
- **Use clear formatting**: Simple layouts parse better than complex designs
- **Include relevant keywords**: Match job posting terminology
- **List specific technologies**: "Python, pandas, scikit-learn" vs. "programming"
- **Quantify achievements**: "Increased efficiency by 25%" vs. "improved processes"

### Job Search Configuration
- **Specific keywords**: "data scientist" vs. "data professional"
- **Multiple locations**: Include "Remote" + specific cities
- **Realistic limits**: Start with 5-10 jobs per day
- **Regular updates**: Refresh keywords based on market trends

### Using AI Analysis
- **Focus on 70+ scores**: Higher compatibility = better match
- **Read skill gaps**: Identify areas for improvement
- **Use cover letter suggestions**: AI provides personalized tips
- **Review match reasons**: Understand why jobs are recommended

### Application Strategy
- **Start manual**: Review applications before enabling auto-apply
- **Customize cover letters**: Use AI suggestions as starting point
- **Track responses**: Monitor which job types get replies
- **Iterate and improve**: Adjust keywords based on results

## 📈 Advanced Usage

### Custom Job Sources
Extend `job_scraper.py` to add new job boards:
```python
def _scrape_custom_source(self):
    # Add your custom scraping logic
    return jobs_list
```

### AI Prompt Customization
Modify `gemini_matcher.py` to customize analysis:
```python
def _create_analysis_prompt(self, resume_data, job):
    # Customize the AI analysis prompt
    return custom_prompt
```

### Database Extensions
Add custom fields to `database_manager.py`:
```sql
ALTER TABLE job_postings ADD COLUMN custom_field TEXT;
```

### API Integration
Connect to external systems via Flask routes in `web/app.py`:
```python
@app.route('/api/jobs')
def api_jobs():
    return jsonify(db_manager.get_matched_jobs())
```

## 📋 Requirements

- **Python**: 3.8+ (tested on 3.9, 3.10, 3.11)
- **Google Gemini API**: Requires active API key with billing
- **Chrome Browser**: For web scraping (ChromeDriver auto-installed)
- **Disk Space**: ~50MB for dependencies, ~10MB for data
- **RAM**: ~512MB during scraping, ~256MB for web interface

---

**⚠️ Important**: This system is designed for personal job search assistance. Always review applications before submission and comply with platform terms of service.
