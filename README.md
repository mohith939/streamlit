# Documentation Structure Extractor

An AI-powered tool that extracts structured module/submodule information from documentation websites and returns a clean, structured JSON representation.

## Overview

This tool is designed to process documentation-based help websites and return a structured JSON of modules, submodules, and their respective descriptions. It uses a combination of web crawling, HTML parsing, and content analysis to identify the structure of documentation websites without using language models for inference.

## Features

- **URL Input Handling**: Accept and validate documentation website URLs
- **Recursive Crawling**: Crawl and follow internal links within the same domain
- **Content Extraction**: Parse HTML content and preserve content hierarchy
- **Module & Submodule Inference**: Identify modules and submodules based on HTML structure
- **JSON Output Format**: Generate structured JSON output with modules, descriptions, and submodules
- **Streamlit UI**: User-friendly interface for interacting with the tool
- **Command-line Interface**: Process URLs from the command line
- **Docker Support**: Easy deployment with Docker
- **Performance Statistics**: Tracks and displays processing times

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Local Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/documentation-structure-extractor.git
   cd documentation-structure-extractor
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

### Docker Installation

If you prefer using Docker:

1. Build and run with Docker Compose:
   ```bash
   docker-compose up -d
   ```

2. Access the application at http://localhost:8501

## Usage

### Streamlit Web Interface

1. Start the Streamlit app:
   ```bash
   streamlit run app.py
   ```

2. Open your browser and navigate to the URL shown in the terminal (typically http://localhost:8501)

3. Enter a documentation website URL in the input field

4. Adjust the options if needed:
   - Maximum pages to crawl
   - Request timeout in seconds

5. Click "Extract Structure" to process the website

6. View the JSON output and download it if desired

### Command-line Interface

Process a URL from the command line:

```bash
python module_extractor.py --urls https://docs.python.org/3/tutorial/
```

Options:
- `--urls`: URL of the documentation website (required)
- `--max-pages`: Maximum number of pages to crawl (default: 20)
- `--timeout`: Timeout for HTTP requests in seconds (default: 5)
- `--output`: Output file path (default: stdout)
- `--no-aggressive`: Disable aggressive submodule detection

Example with all options:
```bash
python module_extractor.py --urls https://docs.python.org/3/tutorial/ --max-pages 30 --timeout 10 --output python_modules.json --no-aggressive
```

## Output Format

The tool generates JSON output in the following format:

```json
[
  {
    "module": "Module Name",
    "Description": "Detailed description of the module",
    "Submodules": {
      "submodule_1": "Detailed description of submodule 1",
      "submodule_2": "Detailed description of submodule 2"
    }
  },
  {
    "module": "Another Module",
    "Description": "Another module description",
    "Submodules": {
      "another_submodule": "Description of another submodule"
    }
  }
]
```

## Design Rationale

The tool is designed with the following principles in mind:

1. **Modularity**: The codebase is organized into separate modules for crawling, parsing, and formatting to make it easier to maintain and extend.

2. **Flexibility**: The parser uses multiple techniques to identify modules and submodules, making it adaptable to different documentation structures.

3. **Performance**: The crawler uses connection pooling and content size limits to improve performance, and the parser uses multi-threading for faster processing.

4. **Robustness**: The tool includes comprehensive error handling and special case handling for sites that block automated access.

## Known Limitations

- **JavaScript-heavy sites**: The tool may not work well with sites that rely heavily on JavaScript to render content, as it only processes the initial HTML.

- **Complex layouts**: Some documentation sites with non-standard or highly complex layouts may not be parsed correctly.

- **Rate limiting**: Some websites may block or rate-limit automated access, which can affect the tool's ability to crawl the site.

- **Deep hierarchies**: The tool is designed to extract a two-level hierarchy (modules and submodules). More complex hierarchies may be flattened or simplified.

## Project Structure

```
Pulse/
├── modules/
│   ├── crawler.py      # Web crawler functionality
│   ├── formatter.py    # JSON formatting
│   ├── parser.py       # HTML parsing and module extraction
│   ├── utils.py        # Utility functions
│   └── __init__.py     # Package initialization
├── app.py              # Streamlit web interface (JSON-only version)
├── docker-compose.yml  # Docker Compose configuration
├── Dockerfile          # Docker container configuration
├── module_extractor.py # Command-line tool
├── README.md           # Project documentation
├── ARCHITECTURE.md     # Technical architecture document
├── APPROACH.md         # Approach and assumptions document
└── requirements.txt    # Python dependencies
```

## License

MIT
