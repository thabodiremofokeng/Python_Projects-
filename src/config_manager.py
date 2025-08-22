"""
Configuration Manager
Handles loading and managing configuration from YAML files and environment variables
"""

import os
import yaml
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any


class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self, config_path: str = None):
        """
        Initialize configuration manager
        
        Args:
            config_path: Path to configuration file (default: config/config.yaml)
        """
        self.project_root = Path(__file__).parent.parent
        
        # Load environment variables
        env_path = self.project_root / '.env'
        if env_path.exists():
            load_dotenv(env_path)
        
        # Load configuration file
        if config_path is None:
            config_path = self.project_root / 'config' / 'config.yaml'
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # Override with environment variables
        self._override_with_env_vars()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in configuration file: {e}")
    
    def _override_with_env_vars(self):
        """Override configuration with environment variables"""
        # Google Gemini
        if os.getenv('GOOGLE_GEMINI_API_KEY'):
            self.config['google_gemini']['api_key'] = os.getenv('GOOGLE_GEMINI_API_KEY')
        
        # LinkedIn
        if os.getenv('LINKEDIN_EMAIL'):
            self.config['linkedin']['email'] = os.getenv('LINKEDIN_EMAIL')
        if os.getenv('LINKEDIN_PASSWORD'):
            self.config['linkedin']['password'] = os.getenv('LINKEDIN_PASSWORD')
    
    def get_gemini_config(self) -> Dict[str, str]:
        """Get Google Gemini configuration"""
        return self.config.get('google_gemini', {})
    
    def get_linkedin_config(self) -> Dict[str, str]:
        """Get LinkedIn configuration"""
        return self.config.get('linkedin', {})
    
    def get_job_search_config(self) -> Dict[str, Any]:
        """Get job search configuration"""
        return self.config.get('job_search', {})
    
    def get_resume_config(self) -> Dict[str, str]:
        """Get resume configuration"""
        resume_config = self.config.get('resume', {})
        
        # Convert relative paths to absolute paths
        if 'file_path' in resume_config:
            file_path = Path(resume_config['file_path'])
            if not file_path.is_absolute():
                resume_config['file_path'] = str(self.project_root / file_path)
        
        return resume_config
    
    def get_application_config(self) -> Dict[str, Any]:
        """Get application configuration"""
        app_config = self.config.get('application', {})
        
        # Convert relative paths to absolute paths
        if 'cover_letter_template' in app_config:
            template_path = Path(app_config['cover_letter_template'])
            if not template_path.is_absolute():
                app_config['cover_letter_template'] = str(self.project_root / template_path)
        
        return app_config
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        log_config = self.config.get('logging', {})
        
        # Convert relative paths to absolute paths
        if 'file' in log_config:
            log_path = Path(log_config['file'])
            if not log_path.is_absolute():
                log_config['file'] = str(self.project_root / log_path)
                
                # Create logs directory if it doesn't exist
                log_dir = Path(log_config['file']).parent
                log_dir.mkdir(parents=True, exist_ok=True)
        
        return log_config
    
    def get_browser_config(self) -> Dict[str, Any]:
        """Get browser configuration for Selenium"""
        return self.config.get('browser', {})
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def validate_config(self) -> bool:
        """Validate that required configuration is present"""
        required_keys = [
            'google_gemini.api_key',
            'linkedin.email',
            'linkedin.password'
        ]
        
        missing_keys = []
        for key in required_keys:
            if not self.get(key):
                missing_keys.append(key)
        
        if missing_keys:
            raise ValueError(f"Missing required configuration keys: {', '.join(missing_keys)}")
        
        return True
    
    def save_config(self, output_path: str = None):
        """Save current configuration to file"""
        if output_path is None:
            output_path = self.config_path
        
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, default_flow_style=False, indent=2)
