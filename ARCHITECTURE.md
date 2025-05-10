# Technical Architecture

This document describes the technical architecture of the Documentation Structure Extractor, including the approach, assumptions, and edge case handling.

## System Overview

The Documentation Structure Extractor is designed to process documentation websites and extract their structure in a standardized JSON format. The system consists of four main components:

1. **Crawler**: Responsible for fetching web pages and following links
2. **Parser**: Extracts modules and submodules from HTML content
3. **Formatter**: Converts the extracted data into the required JSON format
4. **User Interface**: Provides a web interface (Streamlit) and command-line interface

## Component Architecture

### Crawler (modules/crawler.py)

The crawler is responsible for fetching web pages and following links within the same domain. It uses a breadth-first search algorithm to crawl the website up to a specified depth.

#### Key Features:

- **Domain Filtering**: Only follows links within the same domain
- **Depth Control**: Limits the crawl depth to avoid infinite loops
- **Connection Pooling**: Uses connection pooling for better performance
- **Content Size Limiting**: Limits the size of downloaded content to improve performance
- **Special Case Handling**: Includes special handling for sites that block automated access

#### Assumptions:

- The documentation website is accessible via HTTP/HTTPS
- The website structure can be determined from the HTML content
- Internal links are relative or absolute URLs within the same domain

#### Edge Case Handling:

- **Rate Limiting**: Implements connection pooling and request delays to avoid rate limiting
- **Blocked Access**: Includes special case handling for sites that block automated access
- **Redirects**: Follows redirects to handle URL canonicalization
- **Malformed URLs**: Normalizes and validates URLs before processing

### Parser (modules/parser.py)

The parser extracts modules and submodules from HTML content using a combination of techniques based on HTML structure.

#### Key Features:

- **HTML Parsing**: Uses BeautifulSoup to parse HTML content
- **Module Detection**: Identifies modules based on headings and content structure
- **Submodule Detection**: Uses multiple techniques to identify submodules
- **Content Cleaning**: Removes non-content elements and normalizes text
- **Multi-threading**: Uses multi-threading for faster processing

#### Techniques for Module Detection:

1. **Heading-based**: Identifies modules based on heading tags (h1, h2, h3)
2. **Section-based**: Identifies modules based on section tags with class attributes
3. **List-based**: Identifies modules based on list items with strong emphasis
4. **Table-based**: Identifies modules based on table rows with header cells

#### Techniques for Submodule Detection:

1. **Table-based**: Extracts submodules from tables related to a module
2. **Definition List-based**: Extracts submodules from definition lists
3. **Section-based**: Extracts submodules from sections with submodule-like names
4. **List-based**: Extracts submodules from lists within module sections
5. **Code Block-based**: Extracts submodules from code blocks with function/method declarations

#### Assumptions:

- Modules are typically represented by headings or distinct sections
- Submodules are typically represented by sub-headings, lists, or tables
- Module descriptions are typically found near the module heading
- Submodule descriptions are typically found near the submodule name

#### Edge Case Handling:

- **Complex Layouts**: Uses multiple detection techniques to handle different layouts
- **Missing Descriptions**: Provides default descriptions when none are found
- **Duplicate Modules**: Merges duplicate modules based on name similarity
- **JavaScript Content**: Only processes the initial HTML, not JavaScript-rendered content

### Formatter (modules/formatter.py)

The formatter converts the extracted data into the required JSON format.

#### Key Features:

- **Data Cleaning**: Cleans and normalizes the extracted data
- **JSON Formatting**: Formats the data as JSON with proper indentation
- **Custom Format Support**: Supports both standard JSON and custom format

#### Assumptions:

- The output format is a list of module objects
- Each module has a name, description, and list of submodules
- Submodules are represented as key-value pairs (name: description)

#### Edge Case Handling:

- **Empty Data**: Handles empty data gracefully
- **Special Characters**: Properly escapes special characters in JSON
- **Large Output**: Handles large output efficiently

### User Interface

#### Streamlit App (app_simple.py)

The Streamlit app provides a web interface for the tool.

#### Key Features:

- **URL Input**: Accepts a documentation website URL
- **Options**: Allows configuration of crawl depth and timeout
- **Progress Tracking**: Shows progress during processing
- **Results Display**: Displays the extracted modules and submodules
- **Download**: Allows downloading the JSON output

#### Command-line Interface (module_extractor.py)

The command-line interface allows processing URLs from the command line.

#### Key Features:

- **URL Input**: Accepts a documentation website URL
- **Options**: Allows configuration of crawl depth, timeout, and output file
- **Output**: Prints the JSON output or saves it to a file

## Data Flow

1. **URL Input**: The user provides a documentation website URL
2. **Crawling**: The crawler fetches the web pages and follows links
3. **Parsing**: The parser extracts modules and submodules from the HTML content
4. **Formatting**: The formatter converts the extracted data into JSON
5. **Output**: The JSON is displayed to the user or saved to a file

## Performance Considerations

- **Connection Pooling**: Uses connection pooling to reduce connection overhead
- **Content Size Limiting**: Limits the size of downloaded content to improve performance
- **Multi-threading**: Uses multi-threading for faster processing
- **Caching**: Avoids reprocessing the same URLs

## Security Considerations

- **URL Validation**: Validates URLs before processing
- **Content Size Limiting**: Limits the size of downloaded content to prevent memory issues
- **Error Handling**: Includes comprehensive error handling to prevent crashes

## Future Improvements

- **JavaScript Support**: Add support for JavaScript-rendered content
- **More Detection Techniques**: Implement additional techniques for module and submodule detection
- **Caching**: Implement caching to avoid reprocessing the same URLs
- **API Endpoint**: Add an API endpoint for programmatic access
- **User Authentication**: Add user authentication for the web interface
- **Custom Parsers**: Add support for custom parsers for specific websites
