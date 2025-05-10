#!/usr/bin/env python
"""
Module Extractor - Command line tool to extract structured module/submodule information from documentation websites.
"""
import argparse
import json
import sys
import time
from urllib.parse import urlparse
from modules.crawler import Crawler
from modules.parser import Parser
from modules.formatter import Formatter
from modules.utils import is_valid_url, normalize_url


def extract_modules(url, max_pages=20, timeout=5, aggressive=True):
    """
    Extract modules and submodules from a documentation website.

    Args:
        url (str): URL of the documentation website
        max_pages (int): Maximum number of pages to crawl
        timeout (int): Timeout for HTTP requests in seconds
        aggressive (bool): Whether to use aggressive submodule detection

    Returns:
        str: JSON string with extracted modules and submodules
    """
    # Normalize and validate URL
    url = normalize_url(url)
    if not is_valid_url(url):
        print(f"Error: Invalid URL: {url}")
        return "{}"

    # Extract domain for display
    domain = urlparse(url).netloc

    print(f"Extracting modules from {domain}...")

    try:
        # Step 1: Crawl the website
        print(f"Crawling {domain}...")
        crawler = Crawler(
            max_depth=1,  # Only crawl the main page and direct links
            timeout=timeout,
            max_pages=max_pages,
            max_workers=10
        )

        # Start crawling
        start_time = time.time()
        pages = crawler.crawl(url)
        crawl_time = time.time() - start_time

        if not pages:
            print(f"Error: Failed to crawl {domain}")
            return "{}"

        print(f"Crawled {len(pages)} pages in {crawl_time:.2f} seconds")

        # Step 2: Parse the HTML content
        print(f"Parsing content...")
        parse_start_time = time.time()

        # Initialize parser with aggressive settings for better submodule detection
        parser = Parser(
            max_workers=5,
            quick_mode=False,
            aggressive_submodule_detection=aggressive
        )

        # Parse the content
        all_modules = parser.parse_html_batch(pages)
        parse_time = time.time() - parse_start_time

        print(f"Parsed {parser.pages_processed} pages in {parse_time:.2f} seconds")

        # Step 3: Format the results
        formatter = Formatter()
        json_output = formatter.to_json(all_modules)

        # Calculate total time
        total_time = time.time() - start_time
        print(f"Total processing time: {total_time:.2f} seconds")

        # Print statistics
        total_modules = len(all_modules)
        total_submodules = sum(len(module.get('Submodules', {})) for module in all_modules)
        print(f"Found {total_modules} modules and {total_submodules} submodules")

        return json_output

    except Exception as e:
        print(f"Error: {str(e)}")
        return "{}"

def main():
    """
    Main function for the command line tool.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Extract structured module/submodule information from documentation websites.')
    parser.add_argument('--urls', type=str, required=True, help='URL of the documentation website')
    parser.add_argument('--max-pages', type=int, default=20, help='Maximum number of pages to crawl')
    parser.add_argument('--timeout', type=int, default=5, help='Timeout for HTTP requests in seconds')
    parser.add_argument('--output', type=str, help='Output file path (default: stdout)')
    parser.add_argument('--no-aggressive', action='store_true', help='Disable aggressive submodule detection')

    args = parser.parse_args()

    # Extract modules
    json_output = extract_modules(
        args.urls,
        max_pages=args.max_pages,
        timeout=args.timeout,
        aggressive=not args.no_aggressive
    )

    # Output the result
    if args.output:
        with open(args.output, 'w') as f:
            f.write(json_output)
        print(f"Output written to {args.output}")
    else:
        print(json_output)

if __name__ == "__main__":
    main()
