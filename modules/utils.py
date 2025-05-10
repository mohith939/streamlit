"""
Utility functions for the documentation structure extractor.
"""
import re
import logging
from urllib.parse import urlparse, urljoin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def is_valid_url(url):
    """
    Check if the provided URL is valid.
    
    Args:
        url (str): URL to validate
        
    Returns:
        bool: True if URL is valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception as e:
        logger.error(f"Error validating URL: {e}")
        return False

def normalize_url(url):
    """
    Normalize a URL by removing fragments and ensuring proper format.
    
    Args:
        url (str): URL to normalize
        
    Returns:
        str: Normalized URL
    """
    try:
        parsed = urlparse(url)
        # Remove fragments
        normalized = parsed._replace(fragment='').geturl()
        return normalized
    except Exception as e:
        logger.error(f"Error normalizing URL: {e}")
        return url

def is_same_domain(url1, url2):
    """
    Check if two URLs belong to the same domain.
    
    Args:
        url1 (str): First URL
        url2 (str): Second URL
        
    Returns:
        bool: True if URLs belong to the same domain, False otherwise
    """
    try:
        domain1 = urlparse(url1).netloc
        domain2 = urlparse(url2).netloc
        return domain1 == domain2
    except Exception as e:
        logger.error(f"Error comparing domains: {e}")
        return False

def clean_text(text):
    """
    Clean text by removing extra whitespace and normalizing.
    
    Args:
        text (str): Text to clean
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    
    # Replace multiple whitespace with a single space
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text
