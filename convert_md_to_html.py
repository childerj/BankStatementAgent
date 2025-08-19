#!/usr/bin/env python3
"""Convert BankStatementAgent_Documentation.md to HTML"""

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
    
    # Add section classes
    html_content = re.sub(r'(<h1[^>]*>)', r'</div><div class="section">\1', html_content)
    html_content = '<div class="section">' + html_content + '</div>'
    
    # Enhance blockquotes as alerts
    html_content = re.sub(r'<blockquote>(.*?)</blockquote>', r'<div class="alert">\1</div>', html_content, flags=re.DOTALL)
    
    # Add badges for key terms
    key_terms = {
        'Azure': '<span class="badge">Azure</span>',
        'Python': '<span class="badge" style="background-color: #306998;">Python</span>',
        'AI': '<span class="badge" style="background-color: #ff6b6b;">AI</span>',
        'BAI2': '<span class="badge" style="background-color: #4ecdc4;">BAI2</span>',
        'PDF': '<span class="badge" style="background-color: #ff9f43;">PDF</span>'
    }
    
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
    print(f"📊 HTML is {size_ratio:.1f}x larger (includes styling)")
    print(f"🎉 HTML documentation ready: {html_file}")
    print(f"📖 Open in browser to view formatted documentation")

if __name__ == "__main__":
    convert_md_to_html()
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bank Statement Processing Agent - Documentation</title>
    
    <!-- Mermaid.js for diagram rendering -->
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
    <script>
        // Initialize Mermaid with custom configuration
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'default',
            themeVariables: {{
                primaryColor: '#0066cc',
                primaryTextColor: '#333',
                primaryBorderColor: '#004d99',
                lineColor: '#666',
                secondaryColor: '#f8f9fa',
                tertiaryColor: '#e9ecef'
            }},
            flowchart: {{
                htmlLabels: true,
                curve: 'basis'
            }},
            sequence: {{
                diagramMarginX: 50,
                diagramMarginY: 10,
                actorMargin: 50,
                width: 150,
                height: 65,
                boxMargin: 10,
                boxTextMargin: 5,
                noteMargin: 10,
                messageMargin: 35
            }},
            gantt: {{
                titleTopMargin: 25,
                barHeight: 20,
                fontFamily: '"Segoe UI", sans-serif'
            }}
        }});
        
        // Custom styling for Mermaid diagrams
        document.addEventListener('DOMContentLoaded', function() {{
            // Add custom CSS for Mermaid diagrams
            const mermaidStyle = document.createElement('style');
            mermaidStyle.textContent = `
                .mermaid {{
                    display: flex;
                    justify-content: center;
                    margin: 20px 0;
                    padding: 20px;
                    background-color: #f8f9fa;
                    border: 1px solid #e9ecef;
                    border-radius: 8px;
                }}
                
                .mermaid svg {{
                    max-width: 100%;
                    height: auto;
                }}
                
                /* Custom node styling */
                .mermaid .node rect,
                .mermaid .node circle,
                .mermaid .node ellipse,
                .mermaid .node polygon {{
                    stroke: #0066cc;
                    stroke-width: 2px;
                }}
                
                .mermaid .node .label {{
                    color: #333;
                    font-family: "Segoe UI", sans-serif;
                    font-size: 12px;
                }}
                
                /* Edge styling */
                .mermaid .edgePath .path {{
                    stroke: #666;
                    stroke-width: 1.5px;
                }}
                
                .mermaid .edgeLabel {{
                    background-color: white;
                    border-radius: 3px;
                    padding: 2px 4px;
                    font-size: 11px;
                }}
                
                /* Sequence diagram styling */
                .mermaid .actor {{
                    fill: #0066cc;
                    stroke: #004d99;
                }}
                
                .mermaid .actor-line {{
                    stroke: #ccc;
                }}
                
                .mermaid .messageLine0,
                .mermaid .messageLine1 {{
                    stroke: #333;
                    stroke-width: 1.5px;
                }}
                
                .mermaid .messageText {{
                    fill: #333;
                    font-family: "Segoe UI", sans-serif;
                    font-size: 11px;
                }}
                
                /* Responsive diagram scaling */
                @media (max-width: 768px) {{
                    .mermaid {{
                        padding: 10px;
                        overflow-x: auto;
                    }}
                    
                    .mermaid svg {{
                        min-width: 600px;
                    }}
                }}
            `;
            document.head.appendChild(mermaidStyle);
        }});
    </script>
    
    <style>
        /* Modern documentation styling */
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        
        .container {{
            background-color: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        h1 {{
            color: #0066cc;
            border-bottom: 3px solid #0066cc;
            padding-bottom: 10px;
        }}
        
        h2 {{
            color: #004d99;
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 8px;
            margin-top: 30px;
        }}
        
        h3 {{
            color: #0066cc;
            margin-top: 25px;
        }}
        
        h4 {{
            color: #495057;
            margin-top: 20px;
        }}
        
        /* Code styling */
        code {{
            background-color: #f8f9fa;
            color: #e83e8c;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
        }}
        
        pre {{
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            padding: 16px;
            overflow-x: auto;
            margin: 16px 0;
        }}
        
        pre code {{
            background-color: transparent;
            color: #333;
            padding: 0;
        }}
        
        /* Tables */
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 16px 0;
        }}
        
        th, td {{
            border: 1px solid #dee2e6;
            padding: 12px;
            text-align: left;
        }}
        
        th {{
            background-color: #e9ecef;
            font-weight: 600;
        }}
        
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        
        /* Lists */
        ul, ol {{
            margin: 16px 0;
            padding-left: 24px;
        }}
        
        li {{
            margin: 4px 0;
        }}
        
        /* Blockquotes */
        blockquote {{
            border-left: 4px solid #0066cc;
            margin: 16px 0;
            padding: 8px 16px;
            background-color: #f8f9fa;
            font-style: italic;
        }}
        
        /* Links */
        a {{
            color: #0066cc;
            text-decoration: none;
        }}
        
        a:hover {{
            text-decoration: underline;
        }}
        
        /* Badges/Labels */
        .badge {{
            display: inline-block;
            padding: 2px 8px;
            font-size: 12px;
            border-radius: 12px;
            font-weight: 600;
        }}
        
        .badge-success {{
            background-color: #28a745;
            color: white;
        }}
        
        .badge-warning {{
            background-color: #ffc107;
            color: #212529;
        }}
        
        .badge-info {{
            background-color: #17a2b8;
            color: white;
        }}
        
        /* Alerts */
        .alert {{
            padding: 12px 16px;
            margin: 16px 0;
            border-radius: 6px;
            border: 1px solid transparent;
        }}
        
        .alert-info {{
            color: #0c5460;
            background-color: #d1ecf1;
            border-color: #bee5eb;
        }}
        
        .alert-success {{
            color: #155724;
            background-color: #d4edda;
            border-color: #c3e6cb;
        }}
        
        .alert-warning {{
            color: #856404;
            background-color: #fff3cd;
            border-color: #ffeaa7;
        }}
        
        /* Table of Contents */
        .toc {{
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            padding: 20px;
            margin: 20px 0;
        }}
        
        .toc ul {{
            list-style-type: none;
            padding-left: 0;
        }}
        
        .toc > ul > li {{
            margin: 8px 0;
        }}
        
        .toc ul ul {{
            padding-left: 20px;
            margin-top: 4px;
        }}
        
        /* Mermaid diagram containers */
        .mermaid {{
            text-align: center;
            margin: 24px 0;
            padding: 20px;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 8px;
            border: 1px solid #dee2e6;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        /* Diagram titles */
        .diagram-title {{
            text-align: center;
            font-weight: 600;
            color: #495057;
            margin-bottom: 16px;
            font-size: 16px;
        }}
        
        /* Code blocks containing mermaid */
        pre:has(code.language-mermaid) {{
            display: none; /* Hide the raw mermaid code */
        }}
        
        /* Architecture diagrams styling */
        .architecture-section {{
            background-color: #f8f9fa;
            padding: 24px;
            border-radius: 8px;
            margin: 24px 0;
            border-left: 4px solid #0066cc;
        }}
        
        .architecture-section h3 {{
            color: #0066cc;
            margin-top: 0;
        }}
        
        /* Responsive design */
        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}
            
            .container {{
                padding: 20px;
            }}
            
            pre {{
                overflow-x: scroll;
            }}
            
            .mermaid {{
                padding: 10px;
                overflow-x: auto;
            }}
        }}
        
        /* Print styles */
        @media print {{
            body {{
                background-color: white;
            }}
            
            .container {{
                box-shadow: none;
                padding: 0;
            }}
            
            a {{
                color: #333;
                text-decoration: none;
            }}
        }}
        
        /* Header with metadata */
        .doc-header {{
            text-align: center;
            margin-bottom: 40px;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
        }}
        
        .doc-header h1 {{
            color: white;
            border: none;
            margin: 0;
        }}
        
        .doc-meta {{
            margin-top: 10px;
            font-size: 14px;
            opacity: 0.9;
        }}
        
        /* Footer */
        .doc-footer {{
            margin-top: 60px;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 6px;
            text-align: center;
            font-size: 14px;
            color: #6c757d;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="doc-header">
            <h1>🏦 Bank Statement Processing Agent</h1>
            <div class="doc-meta">
                Complete Technical Documentation<br>
                Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br>
                Version: 4.0 | Azure Functions | Python 3.12
            </div>
        </div>
        
        {html_body}
        
        <div class="doc-footer">
            <p><strong>BankStatementAgent Documentation</strong></p>
            <p>Generated from Markdown on {datetime.now().strftime('%B %d, %Y')}</p>
            <p>Azure Function App: BankStatementAgent (azure_ai_rg, East US)</p>
        </div>
    </div>
</body>
</html>"""
    
    # Write the HTML file
    print(f"✍️ Writing {html_file}...")
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Get file sizes
    md_size = os.path.getsize(md_file)
    html_size = os.path.getsize(html_file)
    
    print(f"✅ Conversion complete!")
    print(f"📄 Input:  {md_file} ({md_size:,} bytes)")
    print(f"🌐 Output: {html_file} ({html_size:,} bytes)")
    print(f"📊 HTML is {html_size/md_size:.1f}x larger (includes styling)")
    
    return html_file

if __name__ == "__main__":
    try:
        html_file = convert_md_to_html()
        print(f"🎉 HTML documentation ready: {html_file}")
        print("📖 Open in browser to view formatted documentation")
    except Exception as e:
        print(f"❌ Error: {e}")
