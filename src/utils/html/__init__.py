import logging

try:
    from .formatter import format_confluence_page, create_issue_info_table, create_content_section, create_expandable_section, format_issue

    __all__ = [
        'format_confluence_page',
        'create_issue_info_table',
        'create_content_section',
        'create_expandable_section',
        'format_issue'
    ]
except ImportError as e:
    logging.error(f"Error importing HTML formatter: {str(e)}")
    
    # Provide fallback implementations
    def format_confluence_page(params):
        """Fallback implementation"""
        logging.warning("Using fallback format_confluence_page implementation")
        return f"<h1>{params.get('title', 'No Title')}</h1><p>Content unavailable</p>"
    
    def format_issue(issue_data, output_format='html'):
        """Fallback implementation"""
        logging.warning("Using fallback format_issue implementation")
        return format_confluence_page(issue_data)
    
    def create_issue_info_table(params):
        """Fallback implementation"""
        return ["<p>Issue information unavailable</p>"]
    
    def create_content_section(heading, content, macro_type):
        """Fallback implementation"""
        return [f"<h2>{heading}</h2><p>{content}</p>"]
    
    def create_expandable_section(heading, content):
        """Fallback implementation"""
        return [f"<h2>{heading}</h2><p>{content}</p>"]
        
    __all__ = [
        'format_confluence_page',
        'create_issue_info_table',
        'create_content_section',
        'create_expandable_section',
        'format_issue'
    ]
