#!/usr/bin/env python3
"""Convert BankStatementAgent_Documentation.md to HTML based on the provided template"""

import markdown
import os
import re
from datetime import datetime

def create_styled_html_template():
    """Create the HTML template with styling based on the provided design"""
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bank Statement Processing Agent - Documentation</title>
    <script src="https://unpkg.com/mermaid@9.4.3/dist/mermaid.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            margin: -30px -30px 40px -30px;
            border-radius: 10px 10px 0 0;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5rem;
            font-weight: 300;
            border: none !important;
            padding: 0 !important;
        }}
        .header p {{
            margin: 10px 0;
            opacity: 0.9;
        }}
        h1, h2, h3 {{ 
            color: #2c3e50; 
        }}
        h1 {{ 
            border-bottom: 3px solid #3498db; 
            padding-bottom: 10px; 
            margin-top: 40px;
        }}
        h2 {{ 
            border-bottom: 2px solid #ecf0f1; 
            padding-bottom: 5px; 
            margin-top: 30px;
        }}
        h3 {{
            margin-top: 25px;
            color: #34495e;
        }}
        .mermaid {{
            background-color: #fff;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            margin: 20px 0;
            padding: 20px;
            text-align: center;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background-color: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #e9ecef;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: 600;
            color: #495057;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        .code-block, pre {{
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            padding: 16px;
            margin: 16px 0;
            overflow-x: auto;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        }}
        code {{
            background-color: #f1f3f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 0.9em;
        }}
        .alert {{
            padding: 12px 16px;
            margin: 16px 0;
            border-radius: 6px;
            border-left: 4px solid #007bff;
            background-color: #e7f3ff;
        }}
        .alert-info {{
            border-left-color: #17a2b8;
            background-color: #d1ecf1;
        }}
        .alert-warning {{
            border-left-color: #ffc107;
            background-color: #fff3cd;
        }}
        .alert-success {{
            border-left-color: #28a745;
            background-color: #d4edda;
        }}
        blockquote {{
            border-left: 4px solid #007bff;
            background-color: #e7f3ff;
            margin: 16px 0;
            padding: 12px 16px;
            font-style: italic;
        }}
        ul, ol {{
            padding-left: 20px;
        }}
        li {{
            margin: 8px 0;
        }}
        .footer {{
            margin-top: 40px;
            padding: 20px;
            text-align: center;
            background-color: #f8f9fa;
            border-radius: 8px;
            color: #6c757d;
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            font-size: 0.8em;
            font-weight: bold;
            border-radius: 12px;
            background-color: #007bff;
            color: white;
            margin: 2px;
        }}
        .emoji {{
            font-size: 1.2em;
            margin-right: 8px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Bank Statement Processing Agent</h1>
            <p>Complete Technical Documentation</p>
            <p><span class="emoji">🤖</span>Autonomous • <span class="emoji">🧠</span>AI-Powered • <span class="emoji">🔒</span>Secure • <span class="emoji">📊</span>Monitored</p>
        </div>
        
        <div class="content">
{content}
        </div>

        <div class="footer">
            <p><strong>Bank Statement Processing Agent Documentation</strong></p>
            <p>Version 1.0 | {date} | BankStatementAgent Development Team</p>
        </div>
    </div>

    <script>
        mermaid.initialize({{startOnLoad:true, theme: 'default'}});
    </script>
</body>
</html>'''

def process_mermaid_diagrams(content):
    """Convert Mermaid code blocks to proper Mermaid div elements"""
    
    # Pattern to match ```mermaid ... ``` blocks
    mermaid_pattern = r'```mermaid\n(.*?)\n```'
    
    def replace_mermaid(match):
        # Extract the mermaid code
        mermaid_code = match.group(1).strip()
        
        # Create a proper Mermaid div
        return f'<div class="mermaid">\n{mermaid_code}\n</div>'
    
    # Replace all mermaid code blocks
    return re.sub(mermaid_pattern, replace_mermaid, content, flags=re.DOTALL)

def enhance_html_content(html_content):
    """Enhance the HTML content with better styling and structure"""
    
    # Add section classes to h1 elements
    html_content = re.sub(r'(<h1[^>]*>)', r'</div><div class="section">\1', html_content)
    html_content = '<div class="section">' + html_content + '</div>'
    
    # Enhance blockquotes as alerts
    html_content = re.sub(r'<blockquote>(.*?)</blockquote>', r'<div class="alert">\1</div>', html_content, flags=re.DOTALL)
    
    # Add badges for key terms (only in text content, not in code blocks)
    def add_badges(match):
        text = match.group(0)
        # Skip if we're inside code tags
        if '<code>' in text or '</code>' in text:
            return text
        
        # Apply badge replacements
        text = re.sub(r'\bAzure\b', '<span class="badge">Azure</span>', text)
        text = re.sub(r'\bPython\b', '<span class="badge" style="background-color: #306998;">Python</span>', text)
        text = re.sub(r'\bAI\b', '<span class="badge" style="background-color: #ff6b6b;">AI</span>', text)
        text = re.sub(r'\bBAI2\b', '<span class="badge" style="background-color: #4ecdc4;">BAI2</span>', text)
        text = re.sub(r'\bPDF\b', '<span class="badge" style="background-color: #ff9f43;">PDF</span>', text)
        
        return text
    
    # Apply badge enhancement to paragraphs and list items
    html_content = re.sub(r'<p>(.*?)</p>', add_badges, html_content, flags=re.DOTALL)
    html_content = re.sub(r'<li>(.*?)</li>', add_badges, html_content, flags=re.DOTALL)
    
    return html_content

def convert_md_to_html():
    """Convert the Markdown documentation to HTML with styling and Mermaid support"""
    
    # Input and output file paths
    md_file = "BankStatementAgent_Documentation.md"
    html_file = "BankStatementAgent_Documentation.html"
    
    # Check if markdown file exists
    if not os.path.exists(md_file):
        print(f"❌ Error: {md_file} not found")
        return
    
    # Read the markdown content
    print(f"📖 Reading {md_file}...")
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Process Mermaid diagrams before markdown conversion
    print(f"🔄 Processing Mermaid diagrams...")
    md_content = process_mermaid_diagrams(md_content)
    
    # Configure markdown with extensions for better HTML
    md = markdown.Markdown(extensions=[
        'markdown.extensions.toc',          # Table of contents
        'markdown.extensions.tables',       # Table support
        'markdown.extensions.fenced_code',  # Code blocks
        'markdown.extensions.codehilite',   # Code highlighting
        'markdown.extensions.attr_list',    # Attribute lists
        'markdown.extensions.def_list',     # Definition lists
    ])
    
    # Convert markdown to HTML body
    html_body = md.convert(md_content)
    
    # Enhance the HTML content
    print(f"🎨 Enhancing HTML styling...")
    html_body = enhance_html_content(html_body)
    
    # Get the styled HTML template
    html_template = create_styled_html_template()
    
    # Fill in the template with content and current date
    current_date = datetime.now().strftime("%B %d, %Y")
    complete_html = html_template.format(
        content=html_body,
        date=current_date
    )
    
    # Write the HTML file
    print(f"✍️ Writing {html_file}...")
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(complete_html)
    
    # Get file sizes for reporting
    md_size = os.path.getsize(md_file)
    html_size = os.path.getsize(html_file)
    size_ratio = html_size / md_size
    
    print(f"✅ Conversion complete!")
    print(f"📄 Input:  {md_file} ({md_size:,} bytes)")
    print(f"🌐 Output: {html_file} ({html_size:,} bytes)")
    print(f"📊 HTML is {size_ratio:.1f}x larger (includes professional styling)")
    print(f"🎉 Professional HTML documentation ready: {html_file}")
    print(f"📖 Open in browser to view beautifully formatted documentation")

if __name__ == "__main__":
    convert_md_to_html()
