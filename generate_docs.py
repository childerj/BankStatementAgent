import markdown
import os
from datetime import datetime

# Read the markdown file
with open('BankStatementAgent_Documentation.md', 'r', encoding='utf-8') as f:
    md_content = f.read()

# HTML template with proper escaping
html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bank Statement Agent - Complete Documentation</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({{ 
            startOnLoad: true,
            theme: 'default',
            themeVariables: {{
                primaryColor: '#0066cc',
                primaryTextColor: '#ffffff',
                primaryBorderColor: '#004080',
                lineColor: '#333333',
                sectionBkgColor: '#f8f9fa',
                altSectionBkgColor: '#ffffff',
                gridColor: '#e9ecef',
                tertiaryColor: '#e3f2fd'
            }}
        }});
    </script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        h1 {{
            color: #0066cc;
            border-bottom: 3px solid #0066cc;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }}
        h2 {{
            color: #0052a3;
            margin-top: 40px;
            margin-bottom: 20px;
            border-left: 4px solid #0066cc;
            padding-left: 15px;
        }}
        h3 {{
            color: #004080;
            margin-top: 30px;
            margin-bottom: 15px;
        }}
        h4 {{
            color: #006600;
            margin-top: 25px;
            margin-bottom: 10px;
        }}
        pre {{
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 5px;
            padding: 15px;
            overflow-x: auto;
            font-size: 14px;
        }}
        code {{
            background: #f1f3f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
        }}
        .production-ready {{
            background: linear-gradient(45deg, #4caf50, #8bc34a);
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            text-align: center;
            font-weight: bold;
            font-size: 18px;
        }}
        .enhancement-section {{
            background: #e8f5e8;
            border: 2px solid #4caf50;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }}
        blockquote {{
            border-left: 4px solid #ffc107;
            background: #fff8e1;
            margin: 20px 0;
            padding: 15px 20px;
            border-radius: 0 5px 5px 0;
        }}
        .mermaid {{
            text-align: center;
            margin: 20px 0;
            background: #fafafa;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
        }}
        .toc {{
            background: #e3f2fd;
            border: 1px solid #2196f3;
            border-radius: 8px;
            padding: 20px;
            margin: 30px 0;
        }}
        .toc h2 {{
            margin-top: 0;
            color: #1976d2;
            border: none;
            padding: 0;
        }}
        .toc ul {{
            list-style-type: none;
            padding-left: 0;
        }}
        .toc li {{
            margin: 8px 0;
            padding: 5px 0;
        }}
        .toc a {{
            color: #1976d2;
            text-decoration: none;
            font-weight: 500;
            transition: color 0.3s ease;
        }}
        .toc a:hover {{
            color: #0d47a1;
            text-decoration: underline;
        }}
        .toc a.active {{
            background: #1976d2;
            color: white;
            padding: 5px 10px;
            border-radius: 4px;
            text-decoration: none;
        }}
        .anchor {{
            position: relative;
            top: -80px;
            visibility: hidden;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="production-ready">
            🚀 PRODUCTION READY - Multi-Bank Scalable Architecture
        </div>
        {content}
        <hr style="margin: 40px 0; border: 2px solid #0066cc;">
        <p style="text-align: center; color: #666; font-style: italic;">
            Generated on {date} | Bank Statement Agent v2.0 - Production Ready
        </p>
    </div>
    <script>
        // Enhance table of contents functionality
        document.addEventListener('DOMContentLoaded', function() {{
            // Smooth scrolling for anchor links
            const links = document.querySelectorAll('a[href^="#"]');
            links.forEach(link => {{
                link.addEventListener('click', function(e) {{
                    e.preventDefault();
                    const target = document.querySelector(this.getAttribute('href'));
                    if (target) {{
                        target.scrollIntoView({{
                            behavior: 'smooth',
                            block: 'start'
                        }});
                    }}
                }});
            }});
            
            // Highlight current section in TOC
            const sections = document.querySelectorAll('h1, h2, h3, h4');
            const tocLinks = document.querySelectorAll('.toc a');
            
            window.addEventListener('scroll', function() {{
                let current = '';
                sections.forEach(section => {{
                    const sectionTop = section.offsetTop;
                    const sectionHeight = section.clientHeight;
                    if (pageYOffset >= sectionTop - 100) {{
                        current = section.getAttribute('id');
                    }}
                }});
                
                tocLinks.forEach(link => {{
                    link.classList.remove('active');
                    if (link.getAttribute('href') === '#' + current) {{
                        link.classList.add('active');
                    }}
                }});
            }});
        }});
    </script>
</body>
</html>"""

# Convert markdown to HTML
html_content = markdown.markdown(
    md_content, 
    extensions=[
        'markdown.extensions.codehilite',
        'markdown.extensions.toc',
        'markdown.extensions.tables',
        'markdown.extensions.fenced_code'
    ],
    extension_configs={
        'markdown.extensions.toc': {
            'anchorlink': True,
            'permalink': True,
            'permalink_class': 'anchor-link',
            'toc_depth': 4
        },
        'markdown.extensions.codehilite': {
            'css_class': 'highlight'
        }
    }
)

# Process Mermaid diagrams - convert fenced code blocks with mermaid to div elements
import re
mermaid_pattern = r'<pre><code class="language-mermaid">(.*?)</code></pre>'
html_content = re.sub(
    mermaid_pattern,
    r'<div class="mermaid">\1</div>',
    html_content,
    flags=re.DOTALL
)

# Also handle standard mermaid code blocks
mermaid_pattern2 = r'```mermaid\n(.*?)\n```'
md_content_processed = re.sub(
    mermaid_pattern2,
    r'<div class="mermaid">\1</div>',
    md_content,
    flags=re.DOTALL
)

# Re-process if we found mermaid diagrams in original markdown
if md_content_processed != md_content:
    html_content = markdown.markdown(
        md_content_processed, 
        extensions=[
            'markdown.extensions.codehilite',
            'markdown.extensions.toc',
            'markdown.extensions.tables',
            'markdown.extensions.fenced_code'
        ],
        extension_configs={
            'markdown.extensions.toc': {
                'anchorlink': True,
                'permalink': True,
                'permalink_class': 'anchor-link',
                'toc_depth': 4
            }
        }
    )

# Get current date
current_date = datetime.now().strftime('%B %d, %Y')

# Create final HTML
final_html = html_template.format(content=html_content, date=current_date)

# Write to file
with open('BankStatementAgent_Documentation.html', 'w', encoding='utf-8') as f:
    f.write(final_html)

print('✅ Documentation HTML generated successfully!')
print('📄 File: BankStatementAgent_Documentation.html')
print('🎯 Features: Enhanced styling, production-ready badges, responsive design')
