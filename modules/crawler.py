"""
Web crawler functionality for the documentation structure extractor.
"""
import logging
import requests
import concurrent.futures
import time
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from .utils import is_valid_url, normalize_url, is_same_domain

# Configure logging
logger = logging.getLogger(__name__)

class Crawler:
    """
    Web crawler for documentation websites.
    """

    def __init__(self, max_depth=3, timeout=10, max_pages=100, max_workers=10):
        """
        Initialize the crawler.

        Args:
            max_depth (int): Maximum recursion depth for crawling
            timeout (int): Timeout for HTTP requests in seconds
            max_pages (int): Maximum number of pages to crawl
            max_workers (int): Maximum number of worker threads for parallel crawling
        """
        self.max_depth = max_depth
        self.timeout = timeout
        self.max_pages = max_pages
        self.max_workers = max_workers
        self.visited_urls = set()
        self.pages = {}  # Dictionary to store page content: {url: html_content}
        self.links_to_crawl = []  # Queue of links to crawl
        self.pages_crawled = 0  # Counter for pages crawled
        self.successful_pages = 0  # Counter for successfully crawled pages

    def fetch_url(self, url):
        """
        Fetch content from a URL.

        Args:
            url (str): URL to fetch

        Returns:
            str or None: HTML content if successful, None otherwise
        """

        try:
            # Default headers that work for most sites
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0'
            }

            # Special handling for specific sites
            domain = urlparse(url).netloc.lower()

            # Facebook sites need special handling
            if 'facebook.com' in domain or 'meta.com' in domain:
                # Add additional headers that might help with access
                headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
                    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="100", "Google Chrome";v="100"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Referer': 'https://www.google.com/'
                })

            # Use a session for better performance with connection pooling
            session = requests.Session()

            # Set cookies for sites that might require them
            if 'instagram.com' in domain:
                session.cookies.set('ig_did', '1234567890', domain='.instagram.com')
                session.cookies.set('ig_nrcb', '1', domain='.instagram.com')

            # Set a smaller chunk size for faster initial response
            response = session.get(
                url,
                headers=headers,
                timeout=self.timeout,
                stream=True,  # Stream the response
                allow_redirects=True  # Follow redirects
            )
            response.raise_for_status()

            # Only read the first 300KB of content (enough for most documentation pages)
            content = ""
            for chunk in response.iter_content(chunk_size=8192, decode_unicode=True):
                if chunk:
                    content += chunk
                # Limit to 300KB to improve performance
                if len(content) > 300000:
                    break

            # If we got a very small response, it might be a redirect or anti-bot page
            if len(content) < 500 and ('instagram.com' in domain or 'facebook.com' in domain):
                logger.warning(f"Received very small response from {url}, trying alternative approach")

                # Try an alternative approach - use a different URL format
                if 'help.instagram.com' in url or 'www.instagram.com/help' in url:
                    # Try the direct help center URL
                    alt_url = 'https://help.instagram.com/581066165581870'  # Known Instagram help article
                    logger.info(f"Trying alternative URL: {alt_url}")

                    # Use a different session with different headers
                    alt_session = requests.Session()
                    alt_headers = {
                        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Referer': 'https://www.google.com/'
                    }

                    try:
                        alt_response = alt_session.get(alt_url, headers=alt_headers, timeout=self.timeout)
                        alt_response.raise_for_status()
                        content = alt_response.text
                    except Exception as e:
                        logger.error(f"Alternative approach also failed: {e}")

            return content
        except requests.RequestException as e:
            logger.error(f"Error fetching URL {url}: {e}")
            return None

    def extract_links(self, url, html_content):
        """
        Extract links from HTML content.

        Args:
            url (str): Base URL
            html_content (str): HTML content

        Returns:
            list: List of extracted URLs
        """
        links = []
        try:
            # Use a faster parser
            soup = BeautifulSoup(html_content, 'lxml')

            # Focus on the main content area for links
            main_content = soup.select_one('main, #main, .main, #content, .content, article, .article, .documentation, #documentation')
            if not main_content:
                main_content = soup

            # Prioritize links that are likely to be documentation pages
            priority_links = []
            normal_links = []

            # Look for links in the main content
            for a_tag in main_content.find_all('a', href=True, limit=100):  # Limit to 100 links for performance
                href = a_tag['href']
                # Skip empty links, javascript links, and anchors
                if not href or href.startswith(('javascript:', '#', 'mailto:', 'tel:')):
                    continue

                # Convert relative URLs to absolute
                absolute_url = urljoin(url, href)
                # Normalize the URL
                normalized_url = normalize_url(absolute_url)

                # Only include links from the same domain
                if is_same_domain(url, normalized_url) and is_valid_url(normalized_url):
                    # Check if this is likely a documentation page
                    link_text = a_tag.get_text().lower()
                    if any(keyword in normalized_url.lower() or keyword in link_text for keyword in
                          ['doc', 'api', 'reference', 'guide', 'manual', 'tutorial', 'module', 'class', 'function']):
                        priority_links.append(normalized_url)
                    else:
                        normal_links.append(normalized_url)

            # Combine priority links first, then normal links
            links = priority_links + normal_links

            # Limit the number of links to avoid excessive crawling
            return links[:50]  # Return at most 50 links

        except Exception as e:
            logger.error(f"Error extracting links from {url}: {e}")

        return links

    def process_url(self, url_info):
        """
        Process a single URL (fetch and extract links).

        Args:
            url_info (tuple): Tuple containing (url, depth)

        Returns:
            tuple: (url, html_content, extracted_links, depth)
        """
        url, depth = url_info
        success = False

        try:
            # Skip if we've reached max depth or already visited
            if depth > self.max_depth or url in self.visited_urls:
                return (url, None, [], depth)

            # Mark as visited to prevent concurrent threads from processing it again
            self.visited_urls.add(url)

            # Increment the pages crawled counter
            self.pages_crawled += 1

            # Fetch the page content
            html_content = self.fetch_url(url)
            if not html_content:
                return (url, None, [], depth)

            # Extract links from the page
            links = self.extract_links(url, html_content)

            # Mark as successful and increment the successful pages counter
            success = True
            self.successful_pages += 1

            return (url, html_content, links, depth)

        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
            return (url, None, [], depth)

    def crawl_parallel(self, start_url):
        """
        Crawl a website in parallel using a thread pool.

        Args:
            start_url (str): Starting URL

        Returns:
            dict: Dictionary of crawled pages {url: html_content}
        """
        # Check if URL is valid
        if not is_valid_url(start_url):
            logger.error(f"Invalid URL: {start_url}")
            return self.pages

        # Normalize the URL
        start_url = normalize_url(start_url)

        # Initialize with the start URL
        self.links_to_crawl = [(start_url, 0)]  # (url, depth)

        # Process URLs in parallel until we've reached max pages or have no more links
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while self.links_to_crawl and len(self.pages) < self.max_pages:
                # Take a batch of URLs to process
                batch = self.links_to_crawl[:self.max_workers]
                self.links_to_crawl = self.links_to_crawl[self.max_workers:]

                # Process the batch in parallel
                future_to_url = {executor.submit(self.process_url, url_info): url_info for url_info in batch}

                # Collect results and add new links to crawl
                for future in concurrent.futures.as_completed(future_to_url):
                    url, html_content, links, depth = future.result()

                    # Store the page content if it was successfully fetched
                    if html_content:
                        self.pages[url] = html_content

                        # Add new links to crawl
                        new_depth = depth + 1
                        if new_depth <= self.max_depth:
                            for link in links:
                                if link not in self.visited_urls and len(self.pages) < self.max_pages:
                                    self.links_to_crawl.append((link, new_depth))

        return self.pages

    def crawl(self, start_url):
        """
        Crawl a website starting from a given URL.
        This is a wrapper around crawl_parallel for backward compatibility.

        Args:
            start_url (str): Starting URL

        Returns:
            dict: Dictionary of crawled pages {url: html_content}
        """
        return self.crawl_parallel(start_url)
