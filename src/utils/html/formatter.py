from typing import Dict, List, Optional
import os
from datetime import datetime

def format_confluence_page(params: Dict) -> str:
    """Format the content for a Confluence page with all available sections.
    
    Args:
        params: Dictionary containing page parameters and content sections
        
    Returns:
        Formatted HTML content as a string
    """
    import logging
    
    # Extract all possible fields from params
    title = params.get('title', '')
    executive_summary = params.get('executive_summary', '')
    technical_summary = params.get('technical_summary', '')
    cause = params.get('cause', '')
    fix = params.get('fix', '')
    impact = params.get('impact', '')
    reasoning = params.get('reasoning', '')
    categories = params.get('inferredCategories', [])
    confidence = params.get('confidence', '')
    
    # Log the content available for formatting
    content_fields = {
        "executive_summary": bool(executive_summary),
        "technical_summary": bool(technical_summary),
        "cause": bool(cause),
        "fix": bool(fix),
        "impact": bool(impact),
        "reasoning": bool(reasoning),
        "categories": bool(categories)
    }
    logging.debug(f"Formatting Confluence page for {title} with content fields: {content_fields}")
    
    # If body is explicitly provided and no other fields, use it as is
    if params.get('body') and not any([executive_summary, technical_summary, cause, fix, impact, reasoning]):
        logging.debug(f"Using explicit body content for {title}")
        return params.get('body', '')
        
    # If no substantial content is available, create minimal default content
    if not any([executive_summary, technical_summary, cause, fix, impact, reasoning]):
        logging.warning(f"No substantial content available for {title}, using default content")
        return f"""
        <h1>{title}</h1>
        <p>This is an automatically generated page for {params.get('key', 'this issue')}.</p>
        <p>No detailed content is available yet. Please check back later for updates.</p>
        """
        
    formatted_body = []
    
    # Add title with better styling
    formatted_body.append(f'<h1>{title}</h1>')
    
    # Add status and priority badges at the top
    formatted_body.extend(create_status_badges(params))
    
    # Add issue details prominently at the top (always visible)
    formatted_body.extend(create_issue_details_section(params))
    
    # Add a brief overview/summary panel
    if executive_summary:
        formatted_body.extend(create_overview_panel(executive_summary))
    
    # Add quick actions panel
    formatted_body.extend(create_quick_actions_panel(params))
    
    # Add tabbed content sections for better organization
    formatted_body.extend(create_tabbed_content(params))
    
    # Add categories and AI confidence in a sidebar-style layout
    if categories or confidence:
        formatted_body.extend(create_metadata_section(categories, confidence))
    
    # Add footer
    formatted_body.extend(create_footer())
    
    return '\n'.join(formatted_body)
    
def format_issue(issue_data: Dict, output_format: str = 'html') -> str:
    """
    Format issue data for various output formats.
    This function is a wrapper around format_confluence_page to maintain backwards compatibility.
    
    Args:
        issue_data: Raw issue data
        output_format: Output format ('html', 'confluence', etc.)
        
    Returns:
        Formatted content as a string
    """
    # Extract needed fields from issue data into params format expected by format_confluence_page
    params = {
        # Basic issue information
        'key': issue_data.get('key', ''),
        'title': f"{issue_data.get('key', '')} - {issue_data.get('summary', '')}",
        'summary': issue_data.get('summary', ''),
        'description': issue_data.get('description', ''),
        'issue_type': issue_data.get('issuetype', ''),
        'components': issue_data.get('components', []),
        'labels': issue_data.get('labels', []),
        'fix_version': issue_data.get('fix_version', []),
        'ticket_number': issue_data.get('ticket_number', ''),  # Add ticket number
        
        # Analysis fields
        'executive_summary': issue_data.get('executive_summary', ''),
        'technical_summary': issue_data.get('technical_summary', ''),
        'cause': issue_data.get('cause', ''),
        'fix': issue_data.get('fix', ''),
        'impact': issue_data.get('impact', ''),
        'reasoning': issue_data.get('reasoning', ''),
        'inferredCategories': issue_data.get('inferredCategories', []),
        'confidence': issue_data.get('confidence', '')
    }
    
    # Always use the Confluence formatter for now - can expand later for other formats
    return format_confluence_page(params)
    
def create_issue_info_table(params: Dict) -> List[str]:
    """Create HTML table with issue information."""
    import logging
    table_html = []
    
    # Get values from params or use defaults
    issue_type = params.get('issue_type', '')
    fix_version = params.get('fix_version', '') or params.get('version', '')
    components = params.get('components', [])
    labels = params.get('labels', [])
    key = params.get('key', '')
    ticket_number = params.get('ticket_number', '')  # Add ticket number
    jira_url = params.get('jira_url', os.environ.get('ATLASSIAN_URL', ''))
    
    # Log ticket number for debugging
    if ticket_number:
        logging.info(f"Formatter: Including ticket number '{ticket_number}' in issue details table for {key}")
    else:
        logging.debug(f"Formatter: No ticket number found in params for {key}")
    
    # Format components and labels as comma-separated lists if they are arrays
    if isinstance(components, list):
        components = ", ".join(components)
    if isinstance(labels, list):
        labels = ", ".join(labels)
    
    # Create the table
    table_html.append('<table class="confluenceTable">')
    table_html.append('<tbody>')
    table_html.append('<tr>')
    table_html.append('<th class="confluenceTh">Field</th>')
    table_html.append('<th class="confluenceTh">Value</th>')
    table_html.append('</tr>')
    
    # Add Issue Type row
    table_html.append('<tr>')
    table_html.append('<td class="confluenceTd">Issue Type</td>')
    table_html.append(f'<td class="confluenceTd">{issue_type}</td>')
    table_html.append('</tr>')
    
    # Add Ticket Number row (only if present)
    if ticket_number:
        table_html.append('<tr>')
        table_html.append('<td class="confluenceTd">Ticket Number</td>')
        table_html.append(f'<td class="confluenceTd">{ticket_number}</td>')
        table_html.append('</tr>')
    
    # Add Fix Version row
    table_html.append('<tr>')
    table_html.append('<td class="confluenceTd">Fix Version</td>')
    table_html.append(f'<td class="confluenceTd">{fix_version}</td>')
    table_html.append('</tr>')
    
    # Add Components row
    table_html.append('<tr>')
    table_html.append('<td class="confluenceTd">Components</td>')
    table_html.append(f'<td class="confluenceTd">{components}</td>')
    table_html.append('</tr>')
    
    # Add Labels row
    table_html.append('<tr>')
    table_html.append('<td class="confluenceTd">Labels</td>')
    table_html.append(f'<td class="confluenceTd">{labels}</td>')
    table_html.append('</tr>')
    table_html.append('</tbody>')
    table_html.append('</table>')
    
    # Add Jira link if we have a key and URL
    if key and jira_url:
        jira_link = f"{jira_url.rstrip('/')}/browse/{key}"
        table_html.append(f'<p><a href="{jira_link}">View issue {key} in Jira</a></p>')
    
    table_html.append('<p><br /></p>')
    
    return table_html
    
def create_content_section(heading: str, content: str, macro_type: str) -> List[str]:
    """Create a formatted content section with specified macro type."""
    section_html = []
    
    section_html.append(f'<h2>{heading}</h2>')
    section_html.append(f'<ac:structured-macro ac:name="{macro_type}" ac:schema-version="1">')
    section_html.append('<ac:rich-text-body>')
    section_html.append(f'<p>{content}</p>')
    section_html.append('</ac:rich-text-body>')
    section_html.append('</ac:structured-macro>')
    
    return section_html
    
def create_expandable_section(heading: str, content: str) -> List[str]:
    """Create an expandable content section."""
    section_html = []
    
    section_html.append('<ac:structured-macro ac:name="expand" ac:schema-version="1">')
    section_html.append(f'<ac:parameter ac:name="title">{heading}</ac:parameter>')
    section_html.append('<ac:rich-text-body>')
    section_html.append('<ac:structured-macro ac:name="panel" ac:schema-version="1">')
    section_html.append('<ac:parameter ac:name="bgColor">#f9f9f9</ac:parameter>')
    section_html.append('<ac:parameter ac:name="borderColor">#cccccc</ac:parameter>')
    section_html.append('<ac:rich-text-body>')
    section_html.append(f'<p>{content}</p>')
    section_html.append('</ac:rich-text-body>')
    section_html.append('</ac:structured-macro>')
    section_html.append('</ac:rich-text-body>')
    section_html.append('</ac:structured-macro>')
    section_html.append('<p></p>')
    
    return section_html

def create_status_badges(params: Dict) -> List[str]:
    """Create status badges for the issue."""
    badges = []
    
    issue_type = params.get('issue_type', '')
    fix_version = params.get('fix_version', '') or params.get('version', '')
    
    badges.append('<p>')
    
    # Issue type badge
    if issue_type:
        if issue_type.lower() == 'bug':
            badges.append('<ac:structured-macro ac:name="status" ac:schema-version="1">')
            badges.append('<ac:parameter ac:name="colour">Red</ac:parameter>')
            badges.append(f'<ac:parameter ac:name="title">{issue_type}</ac:parameter>')
            badges.append('</ac:structured-macro>')
        elif issue_type.lower() == 'story':
            badges.append('<ac:structured-macro ac:name="status" ac:schema-version="1">')
            badges.append('<ac:parameter ac:name="colour">Green</ac:parameter>')
            badges.append(f'<ac:parameter ac:name="title">{issue_type}</ac:parameter>')
            badges.append('</ac:structured-macro>')
        else:
            badges.append('<ac:structured-macro ac:name="status" ac:schema-version="1">')
            badges.append('<ac:parameter ac:name="colour">Blue</ac:parameter>')
            badges.append(f'<ac:parameter ac:name="title">{issue_type}</ac:parameter>')
            badges.append('</ac:structured-macro>')
    
    # Fix version badge
    if fix_version:
        badges.append(' ')
        badges.append('<ac:structured-macro ac:name="status" ac:schema-version="1">')
        badges.append('<ac:parameter ac:name="colour">Purple</ac:parameter>')
        badges.append(f'<ac:parameter ac:name="title">{fix_version}</ac:parameter>')
        badges.append('</ac:structured-macro>')
    
    badges.append('</p>')
    return badges

def create_overview_panel(executive_summary: str) -> List[str]:
    """Create an overview panel with the executive summary."""
    panel = []
    
    panel.append('<ac:structured-macro ac:name="panel" ac:schema-version="1">')
    panel.append('<ac:parameter ac:name="bgColor">#e6f3ff</ac:parameter>')
    panel.append('<ac:parameter ac:name="borderColor">#0066cc</ac:parameter>')
    panel.append('<ac:parameter ac:name="titleBGColor">#0066cc</ac:parameter>')
    panel.append('<ac:parameter ac:name="titleColor">#ffffff</ac:parameter>')
    panel.append('<ac:parameter ac:name="title">📋 Executive Summary</ac:parameter>')
    panel.append('<ac:rich-text-body>')
    panel.append(f'<p><strong>{executive_summary}</strong></p>')
    panel.append('</ac:rich-text-body>')
    panel.append('</ac:structured-macro>')
    panel.append('<p></p>')
    
    return panel

def create_quick_actions_panel(params: Dict) -> List[str]:
    """Create a quick actions panel with links."""
    actions = []
    
    key = params.get('key', '')
    jira_url = params.get('jira_url', os.environ.get('ATLASSIAN_URL', ''))
    
    if key and jira_url:
        jira_link = f"{jira_url.rstrip('/')}/browse/{key}"
        
        actions.append('<ac:structured-macro ac:name="panel" ac:schema-version="1">')
        actions.append('<ac:parameter ac:name="bgColor">#f0f0f0</ac:parameter>')
        actions.append('<ac:parameter ac:name="title">🔗 Quick Actions</ac:parameter>')
        actions.append('<ac:rich-text-body>')
        actions.append(f'<p><a href="{jira_link}"><strong>🎫 View in Jira: {key}</strong></a></p>')
        actions.append('</ac:rich-text-body>')
        actions.append('</ac:structured-macro>')
        actions.append('<p></p>')
    
    return actions

def create_tabbed_content(params: Dict) -> List[str]:
    """Create tabbed content sections for better organization."""
    tabs = []
    
    technical_summary = params.get('technical_summary', '')
    cause = params.get('cause', '')
    fix = params.get('fix', '')
    impact = params.get('impact', '')
    reasoning = params.get('reasoning', '')
    
    # Only create tabs if we have content
    if not any([technical_summary, cause, fix, impact]):
        return tabs
    
    # Remove the invalid panel-group macro and create individual panels
    
    # Technical Details Panel
    if technical_summary:
        tabs.append('<ac:structured-macro ac:name="panel" ac:schema-version="1">')
        tabs.append('<ac:parameter ac:name="bgColor">#fff9e6</ac:parameter>')
        tabs.append('<ac:parameter ac:name="borderColor">#ffcc00</ac:parameter>')
        tabs.append('<ac:parameter ac:name="title">🔧 Technical Details</ac:parameter>')
        tabs.append('<ac:rich-text-body>')
        tabs.append(f'<p>{technical_summary}</p>')
        tabs.append('</ac:rich-text-body>')
        tabs.append('</ac:structured-macro>')
        tabs.append('<p></p>')
    
    # Root Cause Panel
    if cause:
        tabs.append('<ac:structured-macro ac:name="panel" ac:schema-version="1">')
        tabs.append('<ac:parameter ac:name="bgColor">#ffe6e6</ac:parameter>')
        tabs.append('<ac:parameter ac:name="borderColor">#ff6666</ac:parameter>')
        tabs.append('<ac:parameter ac:name="title">⚠️ Root Cause</ac:parameter>')
        tabs.append('<ac:rich-text-body>')
        tabs.append(f'<p>{cause}</p>')
        tabs.append('</ac:rich-text-body>')
        tabs.append('</ac:structured-macro>')
        tabs.append('<p></p>')
    
    # Solution Panel
    if fix:
        tabs.append('<ac:structured-macro ac:name="panel" ac:schema-version="1">')
        tabs.append('<ac:parameter ac:name="bgColor">#e6ffe6</ac:parameter>')
        tabs.append('<ac:parameter ac:name="borderColor">#66cc66</ac:parameter>')
        tabs.append('<ac:parameter ac:name="title">✅ Solution</ac:parameter>')
        tabs.append('<ac:rich-text-body>')
        tabs.append(f'<p>{fix}</p>')
        tabs.append('</ac:rich-text-body>')
        tabs.append('</ac:structured-macro>')
        tabs.append('<p></p>')
    
    # Impact Panel
    if impact:
        tabs.append('<ac:structured-macro ac:name="panel" ac:schema-version="1">')
        tabs.append('<ac:parameter ac:name="bgColor">#fff0e6</ac:parameter>')
        tabs.append('<ac:parameter ac:name="borderColor">#ff9933</ac:parameter>')
        tabs.append('<ac:parameter ac:name="title">📊 Impact</ac:parameter>')
        tabs.append('<ac:rich-text-body>')
        tabs.append(f'<p>{impact}</p>')
        tabs.append('</ac:rich-text-body>')
        tabs.append('</ac:structured-macro>')
        tabs.append('<p></p>')
    
    # Add AI Reasoning as expandable section if available
    if reasoning:
        tabs.extend(create_expandable_section('🤖 AI Analysis Reasoning', reasoning))
    
    return tabs

def create_issue_details_section(params: Dict) -> List[str]:
    """Create a prominent section with detailed issue information."""
    details = []
    
    # Add section heading
    details.append('<h2>📋 Issue Details</h2>')
    
    # Add the issue information table directly (always visible)
    details.extend(create_issue_info_table(params))
    
    return details

def create_metadata_section(categories: List, confidence: str) -> List[str]:
    """Create a metadata section with categories and AI confidence."""
    metadata = []
    
    if categories or confidence:
        metadata.append('<ac:structured-macro ac:name="panel" ac:schema-version="1">')
        metadata.append('<ac:parameter ac:name="bgColor">#f5f5f5</ac:parameter>')
        metadata.append('<ac:parameter ac:name="title">📊 Analysis Metadata</ac:parameter>')
        metadata.append('<ac:rich-text-body>')
        
        # Add categories
        if categories:
            if isinstance(categories, str):
                categories = [cat.strip() for cat in categories.split(',')]
            
            metadata.append('<p><strong>Categories:</strong></p>')
            metadata.append('<ul>')
            for category in categories:
                metadata.append(f'<li><ac:structured-macro ac:name="status" ac:schema-version="1">')
                metadata.append('<ac:parameter ac:name="colour">Grey</ac:parameter>')
                metadata.append(f'<ac:parameter ac:name="title">{category}</ac:parameter>')
                metadata.append('</ac:structured-macro></li>')
            metadata.append('</ul>')
        
        # Add confidence score
        if confidence:
            metadata.append(f'<p><strong>AI Confidence Score:</strong> {confidence}</p>')
        
        metadata.append('</ac:rich-text-body>')
        metadata.append('</ac:structured-macro>')
        metadata.append('<p></p>')
    
    return metadata

def create_footer() -> List[str]:
    """Create a footer with generation information."""
    footer = []
    
    footer.append('<hr />')
    footer.append('<ac:structured-macro ac:name="info" ac:schema-version="1">')
    footer.append('<ac:rich-text-body>')
    footer.append(f'<p><em>🤖 Generated by AI4ReleaseNotes on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</em></p>')
    footer.append('<p><em>This page was automatically created using AI analysis of the Jira issue.</em></p>')
    footer.append('</ac:rich-text-body>')
    footer.append('</ac:structured-macro>')
    
    return footer
