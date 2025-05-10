"""
Streamlit application for extracting structured module/submodule information from documentation websites.
Simplified version for better performance and reliability.
"""
import streamlit as st
import json
import time
import pandas as pd
from urllib.parse import urlparse
from modules.crawler import Crawler
from modules.parser import Parser
from modules.formatter import Formatter
from modules.utils import is_valid_url, normalize_url

# Set page configuration
st.set_page_config(
    page_title="Documentation Structure Extractor",
    page_icon="📚",
    layout="wide"
)

# App title and description
st.title("Documentation Structure Extractor")
st.markdown("""
This application extracts structured module/submodule information from documentation websites.
Enter a URL below to get started.
""")

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

            # Initialize crawler with aggressive settings for speed
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
                st.error(f"Failed to crawl {domain}. Please check the URL and try again.")
            else:
                # Update progress
                progress_bar.progress(40)
                status.text(f"Parsing content from {len(pages)} pages...")

                # Step 2: Parse the HTML content
                parse_start_time = time.time()

                # Initialize parser with aggressive settings for speed and better submodule detection
                parser = Parser(
                    max_workers=5,
                    quick_mode=False,  # We want to find submodules
                    aggressive_submodule_detection=True  # New option for better submodule detection
                )

                # Parse the content
                all_modules = parser.parse_html_batch(pages)
                parse_time = time.time() - parse_start_time

                # Update progress
                progress_bar.progress(70)
                status.text("Formatting results...")

                # Step 3: Format the results
                formatter = Formatter()
                formatted_modules = formatter.to_dict(all_modules)
                json_output = formatter.to_json(all_modules)

                # Calculate total time
                total_time = time.time() - start_time

                # Complete progress
                progress_bar.progress(100)
                status.text("Done!")

                # Display results
                st.subheader(f"Results for {domain}")

                # Display statistics
                total_submodules = sum(len(module.get('Submodules', {})) for module in formatted_modules)

                st.markdown(f"""
                **Statistics:**
                - Pages crawled: {len(pages)}
                - Modules found: {len(formatted_modules)}
                - Submodules found: {total_submodules}
                - Total time: {total_time:.2f} seconds
                """)

                # Display modules and submodules
                if formatted_modules:
                    # Create tabs for different views
                    tab1, tab2, tab3 = st.tabs(["Modules & Submodules", "JSON Output", "Custom Format"])

                    with tab1:
                        for module in formatted_modules:
                            with st.expander(f"{module['module']}"):
                                st.markdown(f"**Description:** {module['Description']}")

                                if module['Submodules']:
                                    st.markdown("**Submodules:**")

                                    # Create a simple table for submodules
                                    for submodule_name, submodule_desc in module['Submodules'].items():
                                        st.markdown(f"- **{submodule_name}**: {submodule_desc}")
                                else:
                                    st.markdown("*No submodules found*")

                    with tab2:
                        # Download button for standard JSON
                        st.download_button(
                            label="Download JSON",
                            data=json_output,
                            file_name=f"{domain}_modules.json",
                            mime="application/json"
                        )

                        # Display the JSON
                        try:
                            # Parse the JSON
                            parsed_json = json.loads(json_output)

                            # Display the JSON using st.write instead of st.json
                            st.write("### JSON Output")
                            for i, module in enumerate(parsed_json):
                                st.write(f"**Module {i+1}:** {module['module']}")
                                st.write(f"**Description:** {module['Description']}")

                                if module['Submodules']:
                                    st.write("**Submodules:**")
                                    for submodule_name, submodule_desc in module['Submodules'].items():
                                        st.write(f"- **{submodule_name}:** {submodule_desc}")

                                st.write("---")

                        except Exception as e:
                            st.error(f"Error parsing JSON: {str(e)}")
                            st.code(json_output)

                    with tab3:
                        # Generate custom format
                        custom_format = formatter.to_custom_format(all_modules)

                        # Download button for custom format
                        st.download_button(
                            label="Download Custom Format",
                            data=custom_format,
                            file_name=f"{domain}_modules_custom.json",
                            mime="text/plain"
                        )

                        # Display the custom format
                        st.code(custom_format, language="json")
                else:
                    st.warning("No modules found. Try a different URL.")
