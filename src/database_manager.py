"""
Database Manager
Handles SQLite database operations for job tracking and application management
"""

import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from loguru import logger


class DatabaseManager:
    """Manages SQLite database for job application tracking"""
    
    def __init__(self, db_path: str = None):
        """
        Initialize database manager
        
        Args:
            db_path: Path to SQLite database file
        """
        if db_path is None:
            db_path = Path(__file__).parent.parent / 'data' / 'job_applications.db'
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self.init_database()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures cleanup"""
        pass
        
    def init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Job postings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS job_postings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    location TEXT,
                    description TEXT,
                    requirements TEXT,
                    url TEXT,
                    salary TEXT,
                    posted_date TEXT,
                    source TEXT DEFAULT 'Unknown',
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    job_hash TEXT UNIQUE,
                    review_status TEXT DEFAULT 'new',
                    review_notes TEXT,
                    reviewed_at TIMESTAMP
                )
            ''')
            
            # Job analysis table (Gemini results)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS job_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER,
                    compatibility_score INTEGER,
                    match_reasons TEXT,
                    skill_gaps TEXT,
                    recommended_application BOOLEAN,
                    cover_letter_suggestions TEXT,
                    interview_preparation TEXT,
                    overall_assessment TEXT,
                    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (job_id) REFERENCES job_postings (id)
                )
            ''')
            
            # Applications table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER,
                    status TEXT DEFAULT 'pending',
                    applied_at TIMESTAMP,
                    cover_letter TEXT,
                    notes TEXT,
                    response_received BOOLEAN DEFAULT FALSE,
                    response_date TIMESTAMP,
                    response_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (job_id) REFERENCES job_postings (id)
                )
            ''')
            
            # Resume uploads table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS resumes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    parsed_data TEXT
                )
            ''')
            
            # Search sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS search_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_name TEXT,
                    keywords TEXT,
                    locations TEXT,
                    total_jobs_found INTEGER,
                    matched_jobs INTEGER,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            ''')
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    def save_job_posting(self, job: Dict[str, Any]) -> int:
        """
        Save a job posting to database
        
        Args:
            job: Job posting dictionary
            
        Returns:
            Job ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create job hash for deduplication
            job_hash = f"{job.get('title', '').lower()}_{job.get('company', '').lower()}"
            
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO job_postings 
                    (title, company, location, description, requirements, url, salary, posted_date, source, job_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    job.get('title'),
                    job.get('company'),
                    job.get('location'),
                    job.get('description'),
                    job.get('requirements'),
                    job.get('url'),
                    job.get('salary'),
                    job.get('posted_date'),
                    job.get('source', 'Unknown'),
                    job_hash
                ))
                
                # Get the job ID
                if cursor.rowcount > 0:
                    job_id = cursor.lastrowid
                else:
                    # Job already exists, get its ID
                    cursor.execute('SELECT id FROM job_postings WHERE job_hash = ?', (job_hash,))
                    result = cursor.fetchone()
                    job_id = result[0] if result else None
                
                conn.commit()
                return job_id
                
            except sqlite3.Error as e:
                logger.error(f"Error saving job posting: {e}")
                return None
    
    def save_job_analysis(self, job_id: int, analysis: Dict[str, Any]) -> bool:
        """
        Save Gemini analysis results
        
        Args:
            job_id: Job posting ID
            analysis: Analysis results from Gemini
            
        Returns:
            Success status
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO job_analysis 
                    (job_id, compatibility_score, match_reasons, skill_gaps, 
                     recommended_application, cover_letter_suggestions, 
                     interview_preparation, overall_assessment)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    job_id,
                    analysis.get('compatibility_score'),
                    json.dumps(analysis.get('match_reasons', [])),
                    json.dumps(analysis.get('skill_gaps', [])),
                    analysis.get('recommended_application'),
                    json.dumps(analysis.get('cover_letter_suggestions', [])),
                    json.dumps(analysis.get('interview_preparation', [])),
                    analysis.get('overall_assessment')
                ))
                
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Error saving job analysis: {e}")
            return False
    
    def get_matched_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get matched jobs with analysis (only jobs from last 2 months)
        
        Args:
            limit: Maximum number of jobs to return
            
        Returns:
            List of matched jobs with analysis
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Only show jobs from the last 2 months (60 days)
            cursor.execute('''
                SELECT 
                    jp.*,
                    ja.compatibility_score,
                    ja.match_reasons,
                    ja.skill_gaps,
                    ja.recommended_application,
                    ja.cover_letter_suggestions,
                    ja.interview_preparation,
                    ja.overall_assessment,
                    ja.analyzed_at,
                    a.status as application_status,
                    a.applied_at
                FROM job_postings jp
                LEFT JOIN job_analysis ja ON jp.id = ja.job_id
                LEFT JOIN applications a ON jp.id = a.job_id
                WHERE ja.compatibility_score IS NOT NULL
                  AND jp.scraped_at >= datetime('now', '-60 days')
                  AND (jp.posted_date IS NULL OR jp.posted_date >= datetime('now', '-60 days'))
                ORDER BY ja.compatibility_score DESC, jp.scraped_at DESC
                LIMIT ?
            ''', (limit,))
            
            jobs = []
            for row in cursor.fetchall():
                job = dict(row)
                
                # Parse JSON fields
                if job['match_reasons']:
                    job['match_reasons'] = json.loads(job['match_reasons'])
                if job['skill_gaps']:
                    job['skill_gaps'] = json.loads(job['skill_gaps'])
                if job['cover_letter_suggestions']:
                    job['cover_letter_suggestions'] = json.loads(job['cover_letter_suggestions'])
                if job['interview_preparation']:
                    job['interview_preparation'] = json.loads(job['interview_preparation'])
                
                jobs.append(job)
            
            return jobs
    
    def create_application(self, job_id: int, cover_letter: str = None, notes: str = None) -> int:
        """
        Create a new job application
        
        Args:
            job_id: Job posting ID
            cover_letter: Generated cover letter
            notes: Application notes
            
        Returns:
            Application ID
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO applications 
                    (job_id, status, cover_letter, notes)
                    VALUES (?, ?, ?, ?)
                ''', (job_id, 'approved', cover_letter, notes))
                
                application_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Created application {application_id} for job {job_id}")
                return application_id
                
        except sqlite3.Error as e:
            logger.error(f"Error creating application: {e}")
            return None
    
    def update_application_status(self, application_id: int, status: str, 
                                response_type: str = None, notes: str = None) -> bool:
        """
        Update application status
        
        Args:
            application_id: Application ID
            status: New status (pending, applied, rejected, interview, hired)
            response_type: Type of response received
            notes: Additional notes
            
        Returns:
            Success status
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                update_fields = ['status = ?', 'updated_at = CURRENT_TIMESTAMP']
                values = [status]
                
                if status == 'applied':
                    update_fields.append('applied_at = CURRENT_TIMESTAMP')
                
                if response_type:
                    update_fields.extend(['response_received = TRUE', 'response_type = ?', 'response_date = CURRENT_TIMESTAMP'])
                    values.append(response_type)
                
                if notes:
                    update_fields.append('notes = ?')
                    values.append(notes)
                
                values.append(application_id)
                
                cursor.execute(f'''
                    UPDATE applications 
                    SET {', '.join(update_fields)}
                    WHERE id = ?
                ''', values)
                
                conn.commit()
                return cursor.rowcount > 0
                
        except sqlite3.Error as e:
            logger.error(f"Error updating application status: {e}")
            return False
    
    def get_applications(self, status: str = None) -> List[Dict[str, Any]]:
        """
        Get applications with job details
        
        Args:
            status: Filter by application status
            
        Returns:
            List of applications
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = '''
                SELECT 
                    a.*,
                    jp.title,
                    jp.company,
                    jp.location,
                    jp.url,
                    ja.compatibility_score
                FROM applications a
                JOIN job_postings jp ON a.job_id = jp.id
                LEFT JOIN job_analysis ja ON jp.id = ja.job_id
            '''
            
            params = []
            if status:
                query += ' WHERE a.status = ?'
                params.append(status)
            
            query += ' ORDER BY a.created_at DESC'
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def save_resume(self, filename: str, file_path: str, file_size: int, parsed_data: Dict[str, Any] = None) -> int:
        """
        Save resume information
        
        Args:
            filename: Original filename
            file_path: Path to saved file
            file_size: File size in bytes
            parsed_data: Parsed resume data
            
        Returns:
            Resume ID
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Deactivate previous resumes
                cursor.execute('UPDATE resumes SET is_active = FALSE')
                
                # Insert new resume
                cursor.execute('''
                    INSERT INTO resumes 
                    (filename, file_path, file_size, parsed_data, is_active)
                    VALUES (?, ?, ?, ?, TRUE)
                ''', (filename, file_path, file_size, json.dumps(parsed_data) if parsed_data else None))
                
                resume_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Saved resume {filename} with ID {resume_id}")
                return resume_id
                
        except sqlite3.Error as e:
            logger.error(f"Error saving resume: {e}")
            return None
    
    def get_active_resume(self) -> Optional[Dict[str, Any]]:
        """Get the currently active resume"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM resumes 
                WHERE is_active = TRUE 
                ORDER BY uploaded_at DESC 
                LIMIT 1
            ''')
            
            result = cursor.fetchone()
            if result:
                resume = dict(result)
                if resume['parsed_data']:
                    resume['parsed_data'] = json.loads(resume['parsed_data'])
                return resume
            
            return None
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Total matched jobs
            cursor.execute('SELECT COUNT(*) FROM job_analysis WHERE compatibility_score > 0')
            stats['total_matched_jobs'] = cursor.fetchone()[0]
            
            # High-score matches (80+)
            cursor.execute('SELECT COUNT(*) FROM job_analysis WHERE compatibility_score >= 80')
            stats['high_score_matches'] = cursor.fetchone()[0]
            
            # Total applications
            cursor.execute('SELECT COUNT(*) FROM applications')
            stats['total_applications'] = cursor.fetchone()[0]
            
            # Applied applications
            cursor.execute('SELECT COUNT(*) FROM applications WHERE status = "applied"')
            stats['applied_count'] = cursor.fetchone()[0]
            
            # Pending applications
            cursor.execute('SELECT COUNT(*) FROM applications WHERE status = "approved"')
            stats['pending_count'] = cursor.fetchone()[0]
            
            # Recent activity (last 7 days)
            cursor.execute('''
                SELECT COUNT(*) FROM job_postings 
                WHERE scraped_at > datetime('now', '-7 days')
            ''')
            stats['recent_jobs'] = cursor.fetchone()[0]
            
            return stats
    
    def get_all_jobs(self, limit: int = 25, offset: int = 0, status_filter: str = 'all', source_filter: str = 'all') -> List[Dict[str, Any]]:
        """
        Get all jobs for review with filters and pagination
        
        Args:
            limit: Number of jobs per page
            offset: Number of jobs to skip (for pagination)
            status_filter: Filter by review status
            source_filter: Filter by job source
            
        Returns:
            List of jobs
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = '''
                SELECT 
                    jp.*,
                    jp.review_status as status,
                    ja.compatibility_score
                FROM job_postings jp
                LEFT JOIN job_analysis ja ON jp.id = ja.job_id
                WHERE 1=1
            '''
            
            params = []
            
            if status_filter != 'all':
                query += ' AND jp.review_status = ?'
                params.append(status_filter)
            
            if source_filter != 'all':
                query += ' AND jp.source = ?'
                params.append(source_filter)
            
            query += ' ORDER BY jp.scraped_at DESC LIMIT ? OFFSET ?'
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_jobs_count(self, status_filter: str = 'all', source_filter: str = 'all') -> int:
        """
        Get total count of jobs for pagination
        
        Args:
            status_filter: Filter by review status
            source_filter: Filter by job source
            
        Returns:
            Total count of jobs
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = 'SELECT COUNT(*) FROM job_postings WHERE 1=1'
            params = []
            
            if status_filter != 'all':
                query += ' AND review_status = ?'
                params.append(status_filter)
            
            if source_filter != 'all':
                query += ' AND source = ?'
                params.append(source_filter)
            
            cursor.execute(query, params)
            return cursor.fetchone()[0]
    
    def get_job_sources(self) -> List[str]:
        """
        Get unique job sources for filter dropdown
        
        Returns:
            List of unique sources
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT DISTINCT source FROM job_postings WHERE source IS NOT NULL ORDER BY source')
            return [row[0] for row in cursor.fetchall()]
    
    def mark_job_reviewed(self, job_id: int, notes: str = None) -> bool:
        """
        Mark a job as reviewed
        
        Args:
            job_id: Job ID
            notes: Optional review notes
            
        Returns:
            Success status
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE job_postings 
                    SET review_status = 'reviewed', review_notes = ?, reviewed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (notes, job_id))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except sqlite3.Error as e:
            logger.error(f"Error marking job as reviewed: {e}")
            return False
    
    def mark_job_interested(self, job_id: int, notes: str = None) -> bool:
        """
        Mark a job as interested
        
        Args:
            job_id: Job ID
            notes: Optional review notes
            
        Returns:
            Success status
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE job_postings 
                    SET review_status = 'interested', review_notes = ?, reviewed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (notes, job_id))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except sqlite3.Error as e:
            logger.error(f"Error marking job as interested: {e}")
            return False
    
    def mark_job_not_interested(self, job_id: int, notes: str = None) -> bool:
        """
        Mark a job as not interested
        
        Args:
            job_id: Job ID
            notes: Optional review notes
            
        Returns:
            Success status
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE job_postings 
                    SET review_status = 'not_interested', review_notes = ?, reviewed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (notes, job_id))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except sqlite3.Error as e:
            logger.error(f"Error marking job as not interested: {e}")
            return False
    
    def delete_job(self, job_id: int) -> bool:
        """
        Delete a job and related records
        
        Args:
            job_id: Job ID
            
        Returns:
            Success status
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete related records first
                cursor.execute('DELETE FROM job_analysis WHERE job_id = ?', (job_id,))
                cursor.execute('DELETE FROM applications WHERE job_id = ?', (job_id,))
                cursor.execute('DELETE FROM job_postings WHERE id = ?', (job_id,))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except sqlite3.Error as e:
            logger.error(f"Error deleting job: {e}")
            return False
