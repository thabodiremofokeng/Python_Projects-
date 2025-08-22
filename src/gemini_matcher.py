"""
Google Gemini Matcher
Uses Google Gemini AI to match job descriptions with resume content
"""

import json
from typing import Dict, List, Any, Optional
from loguru import logger

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold


class GeminiMatcher:
    """Uses Google Gemini to analyze job compatibility with resume"""
    
    def __init__(self, config_manager):
        """
        Initialize Gemini matcher
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager
        self.gemini_config = config_manager.get_gemini_config()
        
        # Configure Gemini
        self._setup_gemini()
        
        # Initialize the model
        self.model = genai.GenerativeModel(
            model_name=self.gemini_config.get('model', 'gemini-pro'),
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
        )
        
    def _setup_gemini(self):
        """Configure Google Gemini API"""
        api_key = self.gemini_config.get('api_key')
        if not api_key or api_key == "YOUR_GOOGLE_GEMINI_API_KEY_HERE":
            raise ValueError("Google Gemini API key not configured. Please set GOOGLE_GEMINI_API_KEY in .env file")
        
        genai.configure(api_key=api_key)
        logger.info("Google Gemini API configured successfully")
    
    def match_jobs(self, resume_data: Dict[str, Any], jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Match jobs against resume using Gemini AI
        
        Args:
            resume_data: Parsed resume information
            jobs: List of job postings
            
        Returns:
            List of matched jobs with compatibility scores and analysis
        """
        if not jobs:
            logger.warning("No jobs provided for matching")
            return []
        
        logger.info(f"Matching {len(jobs)} jobs against resume using Gemini AI")
        
        matched_jobs = []
        
        for i, job in enumerate(jobs):
            try:
                logger.info(f"Analyzing job {i+1}/{len(jobs)}: {job.get('title', 'Unknown Title')}")
                
                # Analyze job compatibility
                analysis = self._analyze_job_compatibility(resume_data, job)
                
                if analysis and analysis.get('compatibility_score', 0) > 0:
                    job_with_analysis = job.copy()
                    job_with_analysis['gemini_analysis'] = analysis
                    matched_jobs.append(job_with_analysis)
                    
                    logger.info(f"Match found! Score: {analysis.get('compatibility_score', 0)}/100")
                else:
                    logger.debug(f"Job {i+1} did not meet compatibility threshold")
                    
            except Exception as e:
                logger.error(f"Error analyzing job {i+1}: {e}")
                continue
        
        # Sort by compatibility score (highest first)
        matched_jobs.sort(key=lambda x: x['gemini_analysis'].get('compatibility_score', 0), reverse=True)
        
        logger.info(f"Found {len(matched_jobs)} compatible jobs out of {len(jobs)} analyzed")
        return matched_jobs
    
    def _create_fallback_analysis(self, response_text: str, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a basic analysis when JSON parsing fails
        
        Args:
            response_text: Raw response from Gemini
            job: Job posting information
            
        Returns:
            Basic analysis dictionary
        """
        logger.info("Creating fallback analysis from text response")
        
        # Basic scoring based on keywords in response
        response_lower = response_text.lower()
        
        # Look for positive indicators
        positive_keywords = ['good match', 'excellent', 'qualified', 'suitable', 'recommend']
        negative_keywords = ['poor match', 'not suitable', 'lacks', 'missing', 'not qualified']
        
        positive_score = sum(1 for keyword in positive_keywords if keyword in response_lower)
        negative_score = sum(1 for keyword in negative_keywords if keyword in response_lower)
        
        # Calculate basic compatibility score
        base_score = 60  # Default moderate score
        score_adjustment = (positive_score * 10) - (negative_score * 15)
        compatibility_score = max(0, min(100, base_score + score_adjustment))
        
        return {
            'compatibility_score': compatibility_score,
            'match_reasons': ["Analysis based on text response (JSON parsing failed)"],
            'skill_gaps': ["Full analysis unavailable due to parsing error"],
            'recommended_application': compatibility_score >= 50,
            'cover_letter_suggestions': ["Highlight relevant experience and skills"],
            'interview_preparation': ["Prepare to discuss your background"],
            'overall_assessment': f"Fallback analysis suggests a {compatibility_score}/100 compatibility score. Full analysis unavailable due to parsing error."
        }
    
    def _analyze_job_compatibility(self, resume_data: Dict[str, Any], job: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyze a single job's compatibility with the resume
        
        Args:
            resume_data: Parsed resume information
            job: Job posting information
            
        Returns:
            Analysis results with compatibility score and details
        """
        try:
            # Create the analysis prompt
            prompt = self._create_analysis_prompt(resume_data, job)
            
            # Generate response from Gemini
            response = self.model.generate_content(prompt)
            
            if not response.text:
                logger.warning("Empty response from Gemini")
                return None
            
            # Parse the JSON response
            try:
                # Clean the response text
                response_text = response.text.strip()
                
                # Try to extract JSON from the response if it's wrapped in markdown
                if response_text.startswith('```json'):
                    response_text = response_text.replace('```json', '').replace('```', '').strip()
                elif response_text.startswith('```'):
                    response_text = response_text.replace('```', '').strip()
                
                analysis = json.loads(response_text)
                return analysis
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini response as JSON: {e}")
                logger.debug(f"Raw response: {response.text}")
                
                # Try to create a basic analysis from the text response
                return self._create_fallback_analysis(response.text, job)
                
        except Exception as e:
            logger.error(f"Error generating Gemini analysis: {e}")
            return None
    
    def _create_analysis_prompt(self, resume_data: Dict[str, Any], job: Dict[str, Any]) -> str:
        """
        Create a prompt for Gemini to analyze job compatibility
        
        Args:
            resume_data: Parsed resume information
            job: Job posting information
            
        Returns:
            Formatted prompt string
        """
        # Extract key resume information
        skills = ', '.join(resume_data.get('skills', []))
        experience_titles = [exp.get('title', '') for exp in resume_data.get('experience', [])]
        experience_summary = '; '.join(experience_titles)
        
        personal_info = resume_data.get('personal_info', {})
        candidate_name = personal_info.get('name', 'Candidate')
        
        # Extract job information
        job_title = job.get('title', 'Unknown Title')
        job_description = job.get('description', '')
        job_requirements = job.get('requirements', '')
        company = job.get('company', 'Unknown Company')
        location = job.get('location', 'Unknown Location')
        
        prompt = f'''
You are an expert career advisor and recruiter. Analyze the compatibility between this candidate's resume and job posting.

**CANDIDATE PROFILE:**
Name: {candidate_name}
Skills: {skills}
Experience: {experience_summary}

**JOB POSTING:**
Title: {job_title}
Company: {company}
Location: {location}
Description: {job_description}
Requirements: {job_requirements}

**ANALYSIS INSTRUCTIONS:**
Provide a detailed analysis in JSON format with the following structure:

{{
    "compatibility_score": <integer 0-100>,
    "match_reasons": [
        "<reason why this job matches the candidate>",
        "<another matching reason>"
    ],
    "skill_gaps": [
        "<skills the candidate might be missing>",
        "<areas for improvement>"
    ],
    "recommended_application": <boolean true/false>,
    "cover_letter_suggestions": [
        "<key point to highlight in cover letter>",
        "<another important point>"
    ],
    "interview_preparation": [
        "<topic to prepare for interview>",
        "<another topic>"
    ],
    "overall_assessment": "<2-3 sentence summary of the match quality>"
}}

**SCORING CRITERIA:**
- 90-100: Excellent match, highly qualified
- 70-89: Good match, well qualified
- 50-69: Moderate match, some qualifications
- 30-49: Weak match, few qualifications
- 0-29: Poor match, not recommended

Focus on:
1. Technical skill alignment
2. Experience level match
3. Industry relevance
4. Career progression fit
5. Location compatibility

Be honest but constructive in your assessment. Only recommend application if score is 50 or above.
'''
        
        return prompt.strip()
    
    def generate_cover_letter(self, resume_data: Dict[str, Any], job: Dict[str, Any], analysis: Dict[str, Any] = None) -> str:
        """
        Generate a customized cover letter for a specific job
        
        Args:
            resume_data: Parsed resume information
            job: Job posting information
            analysis: Optional previous Gemini analysis
            
        Returns:
            Generated cover letter text
        """
        try:
            # Create cover letter prompt
            prompt = self._create_cover_letter_prompt(resume_data, job, analysis)
            
            # Generate response from Gemini
            response = self.model.generate_content(prompt)
            
            if response.text:
                logger.info("Cover letter generated successfully")
                return response.text.strip()
            else:
                logger.warning("Empty cover letter response from Gemini")
                return ""
                
        except Exception as e:
            logger.error(f"Error generating cover letter: {e}")
            return ""
    
    def _create_cover_letter_prompt(self, resume_data: Dict[str, Any], job: Dict[str, Any], analysis: Dict[str, Any] = None) -> str:
        """Create a prompt for generating a cover letter"""
        
        personal_info = resume_data.get('personal_info', {})
        candidate_name = personal_info.get('name', 'Candidate')
        
        job_title = job.get('title', 'Unknown Title')
        company = job.get('company', 'Unknown Company')
        
        # Use analysis suggestions if available
        cover_letter_suggestions = []
        if analysis and 'cover_letter_suggestions' in analysis:
            cover_letter_suggestions = analysis['cover_letter_suggestions']
        
        suggestions_text = ""
        if cover_letter_suggestions:
            suggestions_text = f"Key points to highlight: {'; '.join(cover_letter_suggestions)}"
        
        prompt = f'''
Write a professional cover letter for this job application:

**CANDIDATE:** {candidate_name}
**POSITION:** {job_title}
**COMPANY:** {company}

**CANDIDATE BACKGROUND:**
Skills: {', '.join(resume_data.get('skills', []))}
Experience: {'; '.join([exp.get('title', '') for exp in resume_data.get('experience', [])])}

**JOB DETAILS:**
{job.get('description', '')[:500]}...

{suggestions_text}

**REQUIREMENTS:**
1. Professional tone, enthusiastic but not overly casual
2. 3-4 paragraphs maximum
3. Highlight relevant experience and skills
4. Show genuine interest in the company/role
5. Include a strong closing with call to action
6. Make it personal and specific to this role
7. Keep it concise and impactful

Format as a complete cover letter with proper greeting and closing.
'''
        
        return prompt.strip()
    
    def batch_analyze_jobs(self, resume_data: Dict[str, Any], jobs: List[Dict[str, Any]], 
                          batch_size: int = 5) -> List[Dict[str, Any]]:
        """
        Analyze jobs in batches to handle rate limits
        
        Args:
            resume_data: Parsed resume information
            jobs: List of job postings
            batch_size: Number of jobs to process at once
            
        Returns:
            List of matched jobs with analysis
        """
        if not jobs:
            return []
        
        logger.info(f"Processing {len(jobs)} jobs in batches of {batch_size}")
        
        matched_jobs = []
        
        for i in range(0, len(jobs), batch_size):
            batch = jobs[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(jobs) + batch_size - 1)//batch_size}")
            
            batch_results = self.match_jobs(resume_data, batch)
            matched_jobs.extend(batch_results)
            
            # Add a small delay between batches to respect rate limits
            import time
            time.sleep(1)
        
        return matched_jobs
