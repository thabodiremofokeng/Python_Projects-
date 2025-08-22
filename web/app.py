"""
Flask Web Application
Main web interface for the Auto Job Application System
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from werkzeug.utils import secure_filename

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length

from config_manager import ConfigManager
from database_manager import DatabaseManager
from resume_parser import ResumeParser
from job_scraper import JobScraper
from gemini_matcher import GeminiMatcher
from job_applicator import JobApplicator

# Initialize Flask app
app = Flask(__name__)

# Security Configuration
import secrets
app.config['SECRET_KEY'] = secrets.token_hex(32)  # Generate secure random key
app.config['UPLOAD_FOLDER'] = Path(__file__).parent.parent / 'data' / 'resume'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Security headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; img-src 'self' data:; font-src 'self' https://cdn.jsdelivr.net;"
    return response

# Initialize components
config_manager = ConfigManager()
db_manager = DatabaseManager()

# Make CSRF token available in templates
from flask_wtf.csrf import generate_csrf

@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf)


# Forms
class ResumeUploadForm(FlaskForm):
    """Form for uploading resume files"""
    resume_file = FileField('Resume File', validators=[
        FileRequired(),
        FileAllowed(['pdf', 'docx'], 'Only PDF and DOCX files are allowed!')
    ])
    submit = SubmitField('Upload Resume')


class JobSearchForm(FlaskForm):
    """Form for configuring job search criteria"""
    keywords = StringField('Keywords (comma-separated)', validators=[DataRequired()])
    locations = StringField('Locations (comma-separated)', validators=[DataRequired()])
    experience_level = SelectField('Experience Level', choices=[
        ('entry', 'Entry Level'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior Level')
    ])
    job_types = SelectField('Job Type', choices=[
        ('full-time', 'Full Time'),
        ('part-time', 'Part Time'),
        ('contract', 'Contract'),
        ('internship', 'Internship')
    ])
    max_jobs_per_day = SelectField('Max Jobs Per Day', choices=[
        ('5', '5'),
        ('10', '10'),
        ('20', '20'),
        ('50', '50')
    ])
    submit = SubmitField('Update Search Criteria')


class ApplicationApprovalForm(FlaskForm):
    """Form for approving job applications"""
    notes = TextAreaField('Application Notes', validators=[Length(max=500)])
    generate_cover_letter = BooleanField('Generate Custom Cover Letter', default=True)
    submit = SubmitField('Approve Application')


# Routes
@app.route('/')
def dashboard():
    """Main dashboard"""
    stats = db_manager.get_dashboard_stats()
    recent_matches = db_manager.get_matched_jobs(limit=5)
    recent_applications = db_manager.get_applications()[:5]
    
    return render_template('dashboard.html', 
                         stats=stats, 
                         recent_matches=recent_matches,
                         recent_applications=recent_applications)


@app.route('/jobs')
def jobs():
    """View all matched jobs"""
    page = request.args.get('page', 1, type=int)
    limit = 20
    
    matched_jobs = db_manager.get_matched_jobs(limit=limit * page)
    
    return render_template('jobs.html', jobs=matched_jobs)


@app.route('/job/<int:job_id>')
def job_detail(job_id):
    """View detailed job information"""
    # Get job from database
    jobs = db_manager.get_matched_jobs(limit=1000)  # Get all for now
    job = next((j for j in jobs if j['id'] == job_id), None)
    
    if not job:
        flash('Job not found', 'error')
        return redirect(url_for('jobs'))
    
    form = ApplicationApprovalForm()
    
    return render_template('job_detail.html', job=job, form=form)


@app.route('/apply/<int:job_id>', methods=['POST'])
def apply_job(job_id):
    """Approve and create job application"""
    form = ApplicationApprovalForm()
    
    # Check if it's a form submission or direct form data
    valid_submission = False
    notes = None
    generate_cover_letter = False
    
    if form.validate_on_submit():
        # From job detail page with form validation
        valid_submission = True
        notes = form.notes.data
        generate_cover_letter = form.generate_cover_letter.data
    elif request.method == 'POST':
        # From quick apply button - validate CSRF manually
        from flask_wtf.csrf import validate_csrf
        try:
            validate_csrf(request.form.get('csrf_token'))
            valid_submission = True
            notes = request.form.get('notes', '')
            generate_cover_letter = request.form.get('generate_cover_letter') == 'y'
        except Exception as e:
            flash('Security validation failed', 'error')
            return redirect(url_for('jobs'))
    
    if valid_submission:
        # Generate cover letter if requested
        cover_letter = None
        if generate_cover_letter:
            try:
                # Get job details
                jobs = db_manager.get_matched_jobs(limit=1000)
                job = next((j for j in jobs if j['id'] == job_id), None)
                
                if job:
                    # Get active resume
                    resume = db_manager.get_active_resume()
                    if resume and resume['parsed_data']:
                        # Generate cover letter using Gemini
                        gemini_matcher = GeminiMatcher(config_manager)
                        
                        job_dict = {
                            'title': job['title'],
                            'company': job['company'],
                            'description': job['description'],
                            'requirements': job['requirements']
                        }
                        
                        analysis = {
                            'cover_letter_suggestions': job.get('cover_letter_suggestions', [])
                        }
                        
                        cover_letter = gemini_matcher.generate_cover_letter(
                            resume['parsed_data'], job_dict, analysis
                        )
                        
            except Exception as e:
                flash(f'Error generating cover letter: {str(e)}', 'warning')
        
        # Create application
        application_id = db_manager.create_application(
            job_id=job_id,
            cover_letter=cover_letter,
            notes=notes
        )
        
        if application_id:
            flash('Application approved successfully!', 'success')
        else:
            flash('Error creating application', 'error')
    else:
        flash('Invalid form submission', 'error')
    
    # Redirect based on where the request came from
    if request.referrer and 'jobs' in request.referrer:
        return redirect(url_for('jobs'))
    else:
        return redirect(url_for('job_detail', job_id=job_id))


@app.route('/applications')
def applications():
    """View all applications"""
    status_filter = request.args.get('status')
    applications_list = db_manager.get_applications(status=status_filter)
    
    return render_template('applications.html', applications=applications_list)


@app.route('/application/<int:app_id>/update', methods=['POST'])
def update_application(app_id):
    """Update application status"""
    status = request.form.get('status')
    response_type = request.form.get('response_type')
    notes = request.form.get('notes')
    
    success = db_manager.update_application_status(
        application_id=app_id,
        status=status,
        response_type=response_type,
        notes=notes
    )
    
    if success:
        flash('Application updated successfully!', 'success')
    else:
        flash('Error updating application', 'error')
    
    return redirect(url_for('applications'))


@app.route('/resume')
def resume_management():
    """Resume management page"""
    form = ResumeUploadForm()
    active_resume = db_manager.get_active_resume()
    
    return render_template('resume.html', form=form, active_resume=active_resume)


@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    """Handle resume upload"""
    form = ResumeUploadForm()
    
    if form.validate_on_submit():
        file = form.resume_file.data
        filename = secure_filename(file.filename)
        
        # Save file
        upload_folder = Path(app.config['UPLOAD_FOLDER'])
        upload_folder.mkdir(parents=True, exist_ok=True)
        file_path = upload_folder / filename
        file.save(file_path)
        
        # Parse resume
        try:
            resume_parser = ResumeParser(config_manager)
            # Update config to use the new file
            config_manager.config['resume']['file_path'] = str(file_path)
            parsed_data = resume_parser.parse_resume()
            
            # Save to database
            file_size = file_path.stat().st_size
            resume_id = db_manager.save_resume(
                filename=filename,
                file_path=str(file_path),
                file_size=file_size,
                parsed_data=parsed_data
            )
            
            if resume_id:
                flash('Resume uploaded and parsed successfully!', 'success')
            else:
                flash('Error saving resume to database', 'error')
                
        except Exception as e:
            flash(f'Error parsing resume: {str(e)}', 'error')
    
    return redirect(url_for('resume_management'))


@app.route('/settings')
def settings():
    """Settings page"""
    form = JobSearchForm()
    
    # Pre-populate form with current settings
    job_search_config = config_manager.get_job_search_config()
    form.keywords.data = ', '.join(job_search_config.get('keywords', []))
    form.locations.data = ', '.join(job_search_config.get('locations', []))
    
    return render_template('settings.html', form=form)


@app.route('/update_settings', methods=['POST'])
def update_settings():
    """Update job search settings"""
    form = JobSearchForm()
    
    if form.validate_on_submit():
        # Update configuration
        config_manager.config['job_search']['keywords'] = [k.strip() for k in form.keywords.data.split(',')]
        config_manager.config['job_search']['locations'] = [l.strip() for l in form.locations.data.split(',')]
        config_manager.config['job_search']['experience_level'] = [form.experience_level.data]
        config_manager.config['job_search']['job_types'] = [form.job_types.data]
        config_manager.config['job_search']['max_jobs_per_day'] = int(form.max_jobs_per_day.data)
        
        # Save configuration
        try:
            config_manager.save_config()
            flash('Settings updated successfully!', 'success')
        except Exception as e:
            flash(f'Error saving settings: {str(e)}', 'error')
    
    return redirect(url_for('settings'))


@app.route('/run_job_search')
def run_job_search():
    """Trigger a new job search"""
    try:
        # Get active resume
        active_resume = db_manager.get_active_resume()
        if not active_resume or not active_resume['parsed_data']:
            flash('Please upload a resume first', 'error')
            return redirect(url_for('resume_management'))
        
        # Initialize components
        job_scraper = JobScraper(config_manager)
        gemini_matcher = GeminiMatcher(config_manager)
        
        # Scrape jobs
        jobs = job_scraper.scrape_jobs()
        
        if not jobs:
            flash('No jobs found from scraping. Please try again later.', 'warning')
            return redirect(url_for('dashboard'))
        
        # Save jobs and analyze with Gemini
        new_matches = 0
        saved_jobs = 0
        gemini_quota_exceeded = False
        gemini_error_count = 0
        
        for job in jobs:
            # Save job posting first (this always works)
            job_id = db_manager.save_job_posting(job)
            
            if job_id:
                saved_jobs += 1
                
                # Only try Gemini analysis if we haven't exceeded quota
                if not gemini_quota_exceeded:
                    try:
                        # Analyze with Gemini
                        analysis = gemini_matcher._analyze_job_compatibility(
                            active_resume['parsed_data'], job
                        )
                        
                        if analysis and analysis.get('compatibility_score', 0) > 0:
                            db_manager.save_job_analysis(job_id, analysis)
                            new_matches += 1
                            
                    except Exception as gemini_error:
                        gemini_error_count += 1
                        error_msg = str(gemini_error).lower()
                        
                        # Check for quota-related errors
                        if any(quota_keyword in error_msg for quota_keyword in 
                               ['quota', 'rate limit', 'exceeded', 'too many requests', '429']):
                            gemini_quota_exceeded = True
                            flash(
                                f'⚠️ Gemini AI quota exceeded after analyzing {new_matches} jobs. '
                                f'Jobs are still being saved without AI analysis. '
                                f'Please try again later for AI matching.', 
                                'warning'
                            )
                        elif gemini_error_count <= 3:  # Only show first few errors
                            print(f"Gemini analysis error for job {job_id}: {gemini_error}")

                # Continue processing other jobs even if Gemini fails. The job is already saved
                continue
        
        # Provide comprehensive feedback
        if saved_jobs > 0:
            if new_matches > 0:
                flash(
                    f'✅ Job search completed! Found {saved_jobs} jobs and analyzed {new_matches} matches with AI.', 
                    'success'
                )
            elif gemini_quota_exceeded:
                flash(
                    f'✅ Job search completed! Found and saved {saved_jobs} jobs. '
                    f'AI analysis unavailable due to quota limits. Check jobs manually.', 
                    'info'
                )
            else:
                flash(
                    f'✅ Job search completed! Found {saved_jobs} jobs. '
                    f'AI analysis encountered issues - check jobs manually.', 
                    'info'
                )
        else:
            flash('No new jobs were saved. They may already exist in the database.', 'info')
        
    except Exception as e:
        error_msg = str(e).lower()
        if any(quota_keyword in error_msg for quota_keyword in 
               ['quota', 'rate limit', 'exceeded', 'too many requests']):
            flash(
                '⚠️ Gemini AI quota exceeded. Jobs will be scraped without AI analysis. '
                'Please check the jobs manually or try again later.', 
                'warning'
            )
        else:
            flash(f'Error running job search: {str(e)}', 'error')
    
    return redirect(url_for('jobs'))  # Redirect to jobs page to see results


@app.route('/api/stats')
def api_stats():
    """API endpoint for dashboard stats"""
    stats = db_manager.get_dashboard_stats()
    return jsonify(stats)


@app.route('/review')
def review_jobs():
    """Review all scraped jobs manually"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    source_filter = request.args.get('source', 'all')
    limit = 100  # Show 100 most recent jobs as requested
    offset = (page - 1) * limit
    
    try:
        jobs = db_manager.get_all_jobs(limit=limit, offset=offset, status_filter=status_filter, source_filter=source_filter)
        total_jobs = db_manager.get_jobs_count(status_filter=status_filter, source_filter=source_filter)
        total_pages = max(1, (total_jobs + limit - 1) // limit)
        
        # Get unique sources for filter dropdown
        sources = db_manager.get_job_sources()
        
        # Ensure we have valid data
        if not jobs:
            jobs = []
        if not sources:
            sources = []
            
        return render_template('review.html', 
                             jobs=jobs, 
                             current_page=page,
                             total_pages=total_pages,
                             total_jobs=total_jobs,
                             status_filter=status_filter,
                             source_filter=source_filter,
                             sources=sources)
    except Exception as e:
        flash(f'Error loading jobs for review: {str(e)}', 'error')
        return render_template('review.html', 
                             jobs=[], 
                             current_page=1,
                             total_pages=1,
                             total_jobs=0,
                             status_filter='all',
                             source_filter='all',
                             sources=[])


@app.route('/job/<int:job_id>/update_review', methods=['POST'])
def update_job_review(job_id):
    """Update job review status"""
    # Handle both JSON and form data
    if request.is_json:
        data = request.get_json()
        action = data.get('action')
        notes = data.get('notes', '')
    else:
        action = request.form.get('action')
        notes = request.form.get('notes', '')
    
    if action == 'interested':
        success = db_manager.mark_job_interested(job_id, notes)
        if success:
            flash('Job marked as interested', 'success')
        else:
            flash('Error updating job', 'error')
    elif action == 'not_interested':
        success = db_manager.mark_job_not_interested(job_id, notes)
        if success:
            flash('Job marked as not interested', 'info')
        else:
            flash('Error updating job', 'error')
    elif action == 'mark_reviewed':
        success = db_manager.mark_job_reviewed(job_id, notes)
        if success:
            flash('Job marked as reviewed', 'success')
        else:
            flash('Error updating job', 'error')
    
    if request.is_json:
        return jsonify({'success': True})
    else:
        return redirect(url_for('review_jobs'))


@app.route('/jobs/bulk_action', methods=['POST'])
def bulk_job_action():
    """Handle bulk actions on jobs"""
    job_ids = request.form.getlist('job_ids')
    action = request.form.get('bulk_action')
    
    if not job_ids:
        flash('No jobs selected', 'warning')
        return redirect(url_for('review_jobs'))
    
    success_count = 0
    
    for job_id in job_ids:
        if action == 'mark_reviewed':
            if db_manager.mark_job_reviewed(int(job_id)):
                success_count += 1
        elif action == 'mark_interested':
            if db_manager.mark_job_interested(int(job_id)):
                success_count += 1
        elif action == 'mark_not_interested':
            if db_manager.mark_job_not_interested(int(job_id)):
                success_count += 1
        elif action == 'delete':
            if db_manager.delete_job(int(job_id)):
                success_count += 1
    
    if success_count > 0:
        flash(f'Successfully processed {success_count} jobs', 'success')
    else:
        flash('No jobs were processed', 'warning')
    
    return redirect(url_for('review_jobs'))


if __name__ == '__main__':
    import sys
    # Run locally only for security
    print("🚀 Starting Auto Job Application System")
    print("🔒 Running on localhost only for security")
    print("🌐 Access the application at: http://127.0.0.1:5000")
    print("⚠️  This application contains sensitive data - keep it local!")
    print("-" * 60)
    
    # Check if config is valid
    try:
        config_manager.validate_config()
        print("✅ Configuration validated successfully")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        print("Please check your .env file and config/config.yaml")
        sys.exit(1)
    
    app.run(debug=False, host='127.0.0.1', port=5000, threaded=True)
