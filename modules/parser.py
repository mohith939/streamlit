"""
HTML parsing and module extraction functionality.
"""
import logging
import concurrent.futures
import re
from bs4 import BeautifulSoup
from .utils import clean_text

# Configure logging
logger = logging.getLogger(__name__)

class Parser:
    """
    Parser for extracting modules and submodules from HTML content.
    """

    def __init__(self, max_workers=5, quick_mode=False, aggressive_submodule_detection=False):
        """
        Initialize the parser.

        Args:
            max_workers (int): Maximum number of worker threads for parallel parsing
            quick_mode (bool): If True, use faster but less detailed parsing
            aggressive_submodule_detection (bool): If True, use more aggressive techniques to find submodules
        """
        self.modules = []
        self.max_workers = max_workers
        self.quick_mode = quick_mode
        self.aggressive_submodule_detection = aggressive_submodule_detection
        self.pages_processed = 0
        self.modules_found = 0

        # Compile regular expressions for faster text processing
        self.whitespace_regex = re.compile(r'\s+')

        # Common non-content selectors - more aggressive in quick mode
        if quick_mode:
            self.non_content_selectors = 'nav, header, footer, .navigation, .sidebar, .menu, .ads, script, style, aside, .aside, .comments, .comment, .social, .share, .related, .recommendations'
        else:
            self.non_content_selectors = 'nav, header, footer, .navigation, .sidebar, .menu, .ads, script, style'

        # Main content selectors
        self.main_content_selectors = 'main, #main, .main, #content, .content, article, .article, .documentation, #documentation'

        # Submodule detection patterns
        self.submodule_patterns = [
            # Common patterns for submodule names
            r'(?:sub|child)[\s\-_]?modules?',
            r'components?',
            r'features?',
            r'functions?',
            r'methods?',
            r'properties?',
            r'attributes?',
            r'parameters?',
            r'options?',
            r'settings?',
            r'configurations?',
            r'apis?',
            r'endpoints?',
            r'services?',
            r'utilities?',
            r'helpers?',
            r'tools?',
            r'plugins?',
            r'extensions?',
            r'add-?ons?'
        ]

        # Compile the patterns
        self.submodule_regex = re.compile('|'.join(self.submodule_patterns), re.IGNORECASE)

    def extract_content(self, html):
        """
        Extract the main content from HTML, removing navigation, headers, footers, etc.

        Args:
            html (str): HTML content

        Returns:
            BeautifulSoup: BeautifulSoup object with main content
        """
        try:
            # Use lxml parser for faster parsing
            soup = BeautifulSoup(html, 'lxml')

            # Remove common non-content elements in one go
            for element in soup.select(self.non_content_selectors):
                element.decompose()

            # Try to find the main content using a single selector
            main_content = soup.select_one(self.main_content_selectors)

            # If main content is found, use it; otherwise, use the whole body
            if main_content:
                return main_content
            else:
                # If no body is found, return the whole soup
                return soup.body or soup
        except Exception as e:
            logger.error(f"Error extracting content: {e}")
            return BeautifulSoup(html, 'lxml')

    def extract_modules_from_headings(self, content):
        """
        Extract modules and submodules based on heading hierarchy.

        Args:
            content (BeautifulSoup): BeautifulSoup object with content

        Returns:
            list: List of module dictionaries
        """
        modules = []
        current_module = None
        current_level = 0
        heading_stack = []  # Stack to track heading hierarchy

        # Find all headings
        headings = content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])

        # If no headings found, try to find divs with class names that might indicate headings
        if not headings:
            potential_headings = content.find_all(['div', 'span'], class_=lambda c: c and any(x in str(c).lower() for x in ['title', 'heading', 'header', 'module', 'section']))
            if potential_headings:
                headings = potential_headings

        # Sort headings by their position in the document
        headings = sorted(headings, key=lambda x: x.sourceline or 0)

        for heading in headings:
            heading_text = clean_text(heading.get_text())
            if not heading_text or len(heading_text) > 100:  # Skip empty or very long headings
                continue

            # Get the heading level
            if heading.name.startswith('h') and heading.name[1:].isdigit():
                level = int(heading.name[1])
            else:
                # For non-standard headings, determine level by font size, class, or other attributes
                if heading.get('class') and any('title' in c.lower() for c in heading.get('class')):
                    level = 1
                elif heading.get('class') and any('subtitle' in c.lower() for c in heading.get('class')):
                    level = 2
                elif heading.get('class') and any('section' in c.lower() for c in heading.get('class')):
                    level = 3
                else:
                    level = 3  # Default level for non-standard headings

            # Extract description from the next sibling elements until the next heading
            description = ""
            next_element = heading.next_sibling

            # Look for paragraph elements that might contain descriptions
            while next_element:
                if hasattr(next_element, 'name'):
                    # Stop if we hit another heading
                    if next_element.name and next_element.name.startswith('h'):
                        break
                    # Collect text from paragraphs and other content elements
                    if next_element.name in ['p', 'div', 'span', 'section']:
                        description += next_element.get_text() + " "
                elif hasattr(next_element, 'string') and next_element.string:
                    description += next_element.string + " "

                next_element = next_element.next_sibling

                # Limit description length to avoid excessive text
                if len(description) > 500:
                    description = description[:500] + "..."
                    break

            description = clean_text(description)

            # If it's a top-level heading (h1 or h2), create a new module
            if level <= 2:
                current_module = {
                    "module": heading_text,
                    "Description": description,
                    "Submodules": {}
                }
                modules.append(current_module)
                current_level = level
                heading_stack = [(level, current_module)]
            # Otherwise, add it as a submodule to the appropriate parent
            elif current_module:
                # Find the appropriate parent module based on heading level
                while heading_stack and heading_stack[-1][0] >= level:
                    heading_stack.pop()

                if not heading_stack:
                    # If no appropriate parent, add to the current module
                    current_module["Submodules"][heading_text] = description
                else:
                    # Add to the appropriate parent module
                    parent_level, parent_module = heading_stack[-1]
                    parent_module["Submodules"][heading_text] = description

                # Add this heading to the stack
                heading_stack.append((level, {"module": heading_text, "Description": description, "Submodules": {}}))

        return modules

    def extract_modules_from_lists(self, content):
        """
        Extract modules and submodules from lists.

        Args:
            content (BeautifulSoup): BeautifulSoup object with content

        Returns:
            list: List of module dictionaries
        """
        modules = []

        # Find all lists and navigation menus
        lists = content.find_all(['ul', 'ol', 'nav', 'menu', 'div'], class_=lambda c: c and any(x in str(c).lower() for x in ['menu', 'nav', 'list', 'toc', 'index', 'modules']))

        # If no lists found with special classes, fall back to regular lists
        if not lists:
            lists = content.find_all(['ul', 'ol'])

        for list_element in lists:
            # Check if this list might be a module list
            list_items = list_element.find_all('li', recursive=False)

            # If no li elements found, try to find div or a elements that might be list items
            if not list_items:
                list_items = list_element.find_all(['div', 'a', 'span'], class_=lambda c: c and any(x in str(c).lower() for x in ['item', 'entry', 'module', 'link']))

            # Skip very small lists
            if len(list_items) < 2:
                continue

            # Skip very large lists (likely not module lists)
            if len(list_items) > 50:
                # Unless they have a class that suggests they're module lists
                if not (list_element.get('class') and any(x in str(c).lower() for c in list_element.get('class') for x in ['module', 'api', 'doc', 'toc'])):
                    continue

            # Check if the list has a heading that might indicate it's a module list
            list_heading = None
            prev_element = list_element.previous_sibling
            while prev_element and not list_heading:
                if hasattr(prev_element, 'name') and prev_element.name and prev_element.name.startswith('h'):
                    list_heading = clean_text(prev_element.get_text())
                prev_element = prev_element.previous_sibling

            # Process each list item as a potential module
            for item in list_items:
                item_text = clean_text(item.get_text())
                if not item_text or len(item_text) > 200:  # Skip empty or very long items
                    continue

                # Look for links or emphasized text as potential module names
                module_name = None
                module_link = item.find('a')
                module_emphasis = item.find(['strong', 'b', 'em', 'i', 'span'], class_=lambda c: c and any(x in str(c).lower() for x in ['title', 'name', 'module']))

                if module_link:
                    module_name = clean_text(module_link.get_text())
                    # Check if the link has a title attribute
                    if module_link.get('title'):
                        module_title = clean_text(module_link['title'])
                        if module_title and module_title != module_name:
                            module_name = module_title
                elif module_emphasis:
                    module_name = clean_text(module_emphasis.get_text())
                else:
                    # Try to extract the first sentence or phrase as the module name
                    parts = item_text.split(':', 1)
                    if len(parts) > 1 and len(parts[0]) < 50:
                        module_name = clean_text(parts[0])
                    else:
                        module_name = item_text

                # Extract description
                description = ""
                # Try to find a description in a paragraph or div following the link
                desc_element = item.find(['p', 'div', 'span'], class_=lambda c: c and any(x in str(c).lower() for x in ['desc', 'summary', 'info']))
                if desc_element:
                    description = clean_text(desc_element.get_text())
                # If no dedicated description element, use the item text minus the module name
                elif module_name and module_name != item_text:
                    # Try to extract description after a colon or dash
                    if ':' in item_text:
                        description = clean_text(item_text.split(':', 1)[1])
                    elif ' - ' in item_text:
                        description = clean_text(item_text.split(' - ', 1)[1])
                    else:
                        description = clean_text(item_text.replace(module_name, '', 1))

                # Check for nested lists as potential submodules
                submodules = {}

                # First, look for nested lists
                nested_lists = item.find_all(['ul', 'ol', 'div'], class_=lambda c: c and any(x in str(c).lower() for x in ['submenu', 'children', 'nested', 'sub']))

                for nested_list in nested_lists:
                    nested_items = nested_list.find_all(['li', 'a', 'div', 'span'])
                    for nested_item in nested_items:
                        submodule_text = clean_text(nested_item.get_text())
                        if not submodule_text or len(submodule_text) > 100:  # Skip empty or very long items
                            continue

                        # Look for links or emphasized text as potential submodule names
                        submodule_name = None
                        submodule_link = nested_item.find('a')
                        submodule_emphasis = nested_item.find(['strong', 'b', 'em', 'i'])

                        if submodule_link:
                            submodule_name = clean_text(submodule_link.get_text())
                            # Check if the link has a title attribute
                            if submodule_link.get('title'):
                                submodule_title = clean_text(submodule_link['title'])
                                if submodule_title and submodule_title != submodule_name:
                                    submodule_name = submodule_title
                        elif submodule_emphasis:
                            submodule_name = clean_text(submodule_emphasis.get_text())
                        else:
                            # Try to extract the first sentence or phrase as the submodule name
                            parts = submodule_text.split(':', 1)
                            if len(parts) > 1 and len(parts[0]) < 50:
                                submodule_name = clean_text(parts[0])
                            else:
                                submodule_name = submodule_text

                        # Extract description
                        submodule_description = ""
                        # Try to find a description in a paragraph or div
                        subdesc_element = nested_item.find(['p', 'div', 'span'], class_=lambda c: c and any(x in str(c).lower() for x in ['desc', 'summary', 'info']))
                        if subdesc_element:
                            submodule_description = clean_text(subdesc_element.get_text())
                        # If no dedicated description element, use the item text minus the submodule name
                        elif submodule_name and submodule_name != submodule_text:
                            # Try to extract description after a colon or dash
                            if ':' in submodule_text:
                                submodule_description = clean_text(submodule_text.split(':', 1)[1])
                            elif ' - ' in submodule_text:
                                submodule_description = clean_text(submodule_text.split(' - ', 1)[1])
                            else:
                                submodule_description = clean_text(submodule_text.replace(submodule_name, '', 1))

                        # Add to submodules if not already present
                        if submodule_name and submodule_name not in submodules:
                            submodules[submodule_name] = submodule_description

                # Add the module if it has a name and either a description or submodules
                if module_name and (description or submodules):
                    module = {
                        "module": module_name,
                        "Description": description,
                        "Submodules": submodules
                    }
                    modules.append(module)

        return modules

    def parse_html_batch(self, pages):
        """
        Parse multiple HTML pages in parallel.

        Args:
            pages (dict): Dictionary of {url: html_content}

        Returns:
            list: List of module dictionaries from all pages
        """
        all_modules = []
        total_pages = len(pages)

        # Reset counters
        self.pages_processed = 0
        self.modules_found = 0

        # In quick mode, limit the number of pages to process
        if self.quick_mode and total_pages > 20:
            # Select a subset of pages to process
            logger.info(f"Quick mode: Processing only 20 pages out of {total_pages}")
            # Prioritize pages with 'api', 'doc', 'reference' in the URL
            priority_pages = {url: html for url, html in pages.items()
                             if any(keyword in url.lower() for keyword in ['api', 'doc', 'reference', 'module', 'class'])}

            # If we have enough priority pages, use those; otherwise, add random pages
            if len(priority_pages) >= 20:
                pages_subset = dict(list(priority_pages.items())[:20])
            else:
                # Add random pages to reach 20
                remaining_pages = {url: html for url, html in pages.items() if url not in priority_pages}
                remaining_needed = 20 - len(priority_pages)
                if remaining_needed > 0 and remaining_pages:
                    random_subset = dict(list(remaining_pages.items())[:remaining_needed])
                    pages_subset = {**priority_pages, **random_subset}
                else:
                    pages_subset = priority_pages

            # Replace the original pages with the subset
            pages = pages_subset
            total_pages = len(pages)

        # Use ThreadPoolExecutor for parallel processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit parsing tasks for each page
            future_to_url = {executor.submit(self.parse_single_html, html): url
                            for url, html in pages.items()}

            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    modules = future.result()
                    all_modules.extend(modules)
                    self.modules_found += len(modules)
                    self.pages_processed += 1

                    logger.info(f"Successfully parsed {url}, found {len(modules)} modules")
                except Exception as e:
                    logger.error(f"Error parsing {url}: {e}")
                    self.pages_processed += 1

        # Remove duplicates based on module name
        unique_modules = []
        module_names = set()

        for module in all_modules:
            if module["module"] not in module_names:
                unique_modules.append(module)
                module_names.add(module["module"])

        return unique_modules

    def find_submodules_aggressively(self, content, modules):
        """
        Aggressively find submodules for existing modules.

        Args:
            content (BeautifulSoup): BeautifulSoup object with content
            modules (list): List of module dictionaries

        Returns:
            list: Updated list of module dictionaries with more submodules
        """
        if not modules or not self.aggressive_submodule_detection:
            return modules

        # For each module, try to find more submodules
        for module in modules:
            module_name = module["module"]

            # Ensure Submodules exists
            if "Submodules" not in module:
                module["Submodules"] = {}

            # Skip if already has many submodules
            if len(module.get("Submodules", {})) > 15:
                continue

            # Common submodule keywords for documentation sites
            submodule_keywords = [
                'feature', 'tool', 'setting', 'option', 'preference', 'configuration',
                'function', 'method', 'property', 'attribute', 'parameter',
                'api', 'endpoint', 'service', 'utility', 'helper',
                'component', 'element', 'widget', 'control',
                'page', 'screen', 'view', 'section', 'panel',
                'create', 'edit', 'delete', 'manage', 'configure',
                'upload', 'download', 'share', 'publish', 'post',
                'privacy', 'security', 'permission', 'access', 'role',
                'notification', 'alert', 'message', 'comment', 'feedback',
                'profile', 'account', 'user', 'group', 'team',
                'search', 'filter', 'sort', 'browse', 'navigate',
                'import', 'export', 'backup', 'restore', 'sync',
                'report', 'analytics', 'statistics', 'metric', 'dashboard',
                'schedule', 'calendar', 'event', 'reminder', 'notification',
                'payment', 'subscription', 'billing', 'invoice', 'transaction',
                'integration', 'connection', 'plugin', 'extension', 'add-on'
            ]

            # 1. Look for tables that might contain submodules
            tables = content.find_all('table')
            for table in tables:
                # Check if the table is related to this module
                table_text = table.get_text().lower()
                if module_name.lower() in table_text or any(keyword in table_text for keyword in submodule_keywords):
                    # Extract rows as potential submodules
                    rows = table.find_all('tr')
                    for row in rows[1:]:  # Skip header row
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            submodule_name = clean_text(cells[0].get_text())
                            submodule_desc = clean_text(cells[1].get_text())
                            if submodule_name and len(submodule_name) < 100 and submodule_name != module_name:
                                module["Submodules"][submodule_name] = submodule_desc

            # 2. Look for definition lists
            dl_lists = content.find_all('dl')
            for dl in dl_lists:
                # Check if the list is related to this module
                dl_text = dl.get_text().lower()
                if module_name.lower() in dl_text or any(keyword in dl_text for keyword in submodule_keywords):
                    # Extract dt/dd pairs as potential submodules
                    dts = dl.find_all('dt')
                    for dt in dts:
                        submodule_name = clean_text(dt.get_text())
                        dd = dt.find_next('dd')
                        submodule_desc = clean_text(dd.get_text()) if dd else ""
                        if submodule_name and len(submodule_name) < 100 and submodule_name != module_name:
                            module["Submodules"][submodule_name] = submodule_desc

            # 3. Look for sections with submodule-like names
            sections = content.find_all(['div', 'section'], class_=lambda c: c and any(x in str(c).lower() for x in ['api', 'method', 'function', 'property', 'feature', 'tool', 'setting']))
            for section in sections:
                # Check if the section is related to this module
                section_text = section.get_text().lower()
                if module_name.lower() in section_text or self.submodule_regex.search(section_text) or any(keyword in section_text for keyword in submodule_keywords):
                    # Find headings within the section
                    headings = section.find_all(['h3', 'h4', 'h5', 'h6'])
                    for heading in headings:
                        submodule_name = clean_text(heading.get_text())
                        # Get description from next sibling paragraph
                        next_p = heading.find_next('p')
                        submodule_desc = clean_text(next_p.get_text()) if next_p else ""
                        if submodule_name and len(submodule_name) < 100 and submodule_name != module_name:
                            module["Submodules"][submodule_name] = submodule_desc

            # 4. Look for lists that might contain submodules
            lists = content.find_all(['ul', 'ol'])
            for list_element in lists:
                list_text = list_element.get_text().lower()
                if module_name.lower() in list_text or any(keyword in list_text for keyword in submodule_keywords):
                    list_items = list_element.find_all('li')
                    for item in list_items:
                        item_text = clean_text(item.get_text())

                        # Try to extract submodule name and description
                        if ':' in item_text:
                            parts = item_text.split(':', 1)
                            submodule_name = clean_text(parts[0])
                            submodule_desc = clean_text(parts[1])
                        elif ' - ' in item_text:
                            parts = item_text.split(' - ', 1)
                            submodule_name = clean_text(parts[0])
                            submodule_desc = clean_text(parts[1])
                        elif item.find('strong') or item.find('b'):
                            strong = item.find('strong') or item.find('b')
                            submodule_name = clean_text(strong.get_text())
                            submodule_desc = clean_text(item_text.replace(submodule_name, ''))
                        elif item.find('a'):
                            link = item.find('a')
                            submodule_name = clean_text(link.get_text())
                            submodule_desc = clean_text(item_text.replace(submodule_name, ''))
                        else:
                            # If no clear structure, use the whole text as name
                            submodule_name = item_text
                            submodule_desc = "Feature or setting in " + module_name

                        if submodule_name and len(submodule_name) < 100 and submodule_name != module_name:
                            module["Submodules"][submodule_name] = submodule_desc

            # 5. Look for code blocks that might contain submodules
            code_blocks = content.find_all(['pre', 'code'])
            for code_block in code_blocks:
                code_text = code_block.get_text()
                # Look for patterns like "function X", "method Y", "property Z"
                for pattern in ['function', 'method', 'class', 'property', 'attribute', 'parameter', 'option', 'setting', 'feature']:
                    matches = re.finditer(rf'{pattern}\s+([a-zA-Z0-9_]+)', code_text, re.IGNORECASE)
                    for match in matches:
                        submodule_name = match.group(1)
                        if submodule_name and submodule_name != module_name:
                            module["Submodules"][submodule_name] = f"{pattern.capitalize()} in {module_name}"

            # 6. Look for specific documentation patterns (like Instagram help)
            help_sections = content.find_all(['div', 'section'], class_=lambda c: c and any(x in str(c).lower() for x in ['help', 'faq', 'guide', 'tutorial', 'howto', 'how-to']))
            for section in help_sections:
                # Find all links in the help section
                links = section.find_all('a')
                for link in links:
                    link_text = clean_text(link.get_text())
                    if link_text and len(link_text) < 100 and link_text != module_name:
                        # Try to get description from title attribute or parent paragraph
                        if link.get('title'):
                            submodule_desc = clean_text(link['title'])
                        elif link.parent and link.parent.name == 'p':
                            submodule_desc = clean_text(link.parent.get_text().replace(link_text, ''))
                        else:
                            submodule_desc = f"Help topic in {module_name}"

                        module["Submodules"][link_text] = submodule_desc

            # 7. If still no submodules, try to extract from paragraphs
            if not module["Submodules"]:
                paragraphs = content.find_all('p')
                for p in paragraphs:
                    p_text = p.get_text().lower()
                    if module_name.lower() in p_text:
                        # Look for strong/bold text or links as potential submodules
                        for element in p.find_all(['strong', 'b', 'a', 'em']):
                            submodule_name = clean_text(element.get_text())
                            if submodule_name and len(submodule_name) < 100 and submodule_name != module_name:
                                module["Submodules"][submodule_name] = f"Feature mentioned in {module_name} documentation"

        return modules

    def parse_single_html(self, html):
        """
        Parse a single HTML content to extract modules and submodules.

        Args:
            html (str): HTML content

        Returns:
            list: List of module dictionaries
        """
        try:
            # Limit the HTML content size to improve performance
            if len(html) > 300000:  # 300KB
                logger.info(f"Truncating large HTML content from {len(html)} bytes")
                # Keep the first part of the HTML which usually contains the most important content
                html = html[:300000]

            # Extract the main content
            content = self.extract_content(html)

            # Extract modules from headings
            modules_from_headings = self.extract_modules_from_headings(content)

            # Extract modules from lists
            modules_from_lists = self.extract_modules_from_lists(content)

            # Combine the results
            all_modules = modules_from_headings + modules_from_lists

            # If aggressive submodule detection is enabled, try to find more submodules
            if self.aggressive_submodule_detection:
                all_modules = self.find_submodules_aggressively(content, all_modules)

            return all_modules

        except Exception as e:
            logger.error(f"Error parsing HTML: {e}")
            return []

    def parse_html(self, html):
        """
        Parse HTML content to extract modules and submodules.
        Backward compatibility method.

        Args:
            html (str): HTML content

        Returns:
            list: List of module dictionaries
        """
        return self.parse_single_html(html)
