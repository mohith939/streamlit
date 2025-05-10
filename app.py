"""
Streamlit application that focuses solely on JSON output.
This version is stripped down to the essentials to ensure reliable JSON output.
"""
import streamlit as st
import json
import time
from urllib.parse import urlparse
from modules.crawler import Crawler
from modules.parser import Parser
from modules.utils import is_valid_url, normalize_url

# Set page configuration
st.set_page_config(
    page_title="Documentation Structure Extractor",
    page_icon="📚",
    layout="wide"
)

# Simple header
st.markdown("## Documentation Structure Extractor")

# URL input
url = st.text_input("Enter a documentation website URL:", "")

# Sidebar options
st.sidebar.title("Options")
max_pages = st.sidebar.slider("Maximum pages to crawl:", 5, 100, 20)
timeout = st.sidebar.slider("Request timeout (seconds):", 1, 10, 3)

# Process button
if st.button("Extract Structure"):
    if not url:
        st.error("Please enter a URL.")
    else:
        # Normalize and validate URL
        url = normalize_url(url)
        if not is_valid_url(url):
            st.error("Please enter a valid URL.")
        else:
            # Extract domain for display
            domain = urlparse(url).netloc

            # Main progress bar
            progress_bar = st.progress(0)
            status = st.empty()

            # Step 1: Crawl the website
            status.text(f"Crawling {domain}...")
            progress_bar.progress(10)

            # Initialize crawler
            crawler = Crawler(
                max_depth=1,
                timeout=timeout,
                max_pages=max_pages,
                max_workers=10
            )

            # Start crawling
            start_time = time.time()
            pages = crawler.crawl(url)
            crawl_time = time.time() - start_time

            if not pages:
                st.error(f"Failed to crawl {domain}. Please check the URL and try again.")
            else:
                # Update progress
                progress_bar.progress(40)
                status.text(f"Parsing content from {len(pages)} pages...")

                # Step 2: Parse the HTML content
                parse_start_time = time.time()
                parser = Parser(
                    max_workers=5,
                    quick_mode=False,
                    aggressive_submodule_detection=True
                )

                # Parse the content
                all_modules = parser.parse_html_batch(pages)
                parse_time = time.time() - parse_start_time

                # Update progress
                progress_bar.progress(70)
                status.text("Formatting results...")

                # Step 3: Format the results directly to JSON
                formatted_modules = []
                for module in all_modules:
                    if not module.get("module"):
                        continue

                    # Get description from either field name
                    description = module.get("Description", "")
                    if not description:
                        description = module.get("description", "")
                    if not description:
                        description = "No description available"

                    # Get submodules from either field name
                    submodules = module.get("Submodules", {})
                    if not submodules:
                        submodules = module.get("submodules", {})
                    if not isinstance(submodules, dict):
                        submodules = {}

                    # Clean submodules
                    cleaned_submodules = {}
                    for name, desc in submodules.items():
                        if not name:
                            continue
                        cleaned_submodules[str(name)] = str(desc) if desc else "No description available"

                    # Create formatted module
                    formatted_module = {
                        "module": str(module.get("module", "")),
                        "Description": str(description),
                        "Submodules": cleaned_submodules
                    }

                    formatted_modules.append(formatted_module)

                # Create JSON directly
                json_output = json.dumps(formatted_modules, indent=2)

                # Calculate total time
                total_time = time.time() - start_time

                # Complete progress
                progress_bar.progress(100)
                status.text("Done!")

                # Display the JSON output
                st.markdown(f"### JSON Output")

                # Download button for JSON
                st.download_button(
                    label="Download JSON",
                    data=json_output,
                    file_name=f"{domain}_modules.json",
                    mime="application/json"
                )

                # Display the JSON
                st.code(json_output, language="json")
