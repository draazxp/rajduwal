#!/usr/bin/env python3
"""
Blog build script for rajduwal.com.np

Reads markdown posts from blog/posts/, converts them to HTML using the site
template, and generates the blog index page. No external dependencies required
(uses Python 3.x standard library only, except for markdown conversion which
uses a minimal bundled approach).

Post format:
  ---
  title: "My Post Title"
  date: 2025-01-15
  description: "Short description for the listing page."
  ---

  Markdown content here...
"""

import os
import re
import html
from pathlib import Path

# ---------------------------------------------------------------------------
# Minimal Markdown-to-HTML converter (no dependencies)
# Handles: headings, paragraphs, code blocks, inline code, bold, italic,
#           links, unordered/ordered lists, horizontal rules, blockquotes
# ---------------------------------------------------------------------------

def md_to_html(text):
    """Convert markdown text to HTML. Handles common patterns."""
    lines = text.split('\n')
    html_lines = []
    in_code_block = False
    code_lang = ''
    code_lines = []
    in_list = False
    list_type = None
    list_items = []

    def flush_list():
        nonlocal in_list, list_type, list_items
        if in_list:
            tag = 'ol' if list_type == 'ol' else 'ul'
            html_lines.append(f'<{tag}>')
            for item in list_items:
                html_lines.append(f'  <li>{inline_format(item)}</li>')
            html_lines.append(f'</{tag}>')
            in_list = False
            list_type = None
            list_items = []

    def inline_format(s):
        """Handle inline formatting: bold, italic, code, links."""
        # Inline code
        s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
        # Bold
        s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
        s = re.sub(r'__(.+?)__', r'<strong>\1</strong>', s)
        # Italic
        s = re.sub(r'\*(.+?)\*', r'<em>\1</em>', s)
        s = re.sub(r'_(.+?)_', r'<em>\1</em>', s)
        # Links
        s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank">\1</a>', s)
        return s

    i = 0
    while i < len(lines):
        line = lines[i]

        # Fenced code blocks
        if line.strip().startswith('```'):
            if not in_code_block:
                flush_list()
                in_code_block = True
                code_lang = line.strip()[3:].strip()
                code_lines = []
            else:
                lang_attr = f' class="language-{code_lang}"' if code_lang else ''
                code_content = html.escape('\n'.join(code_lines))
                html_lines.append(f'<pre><code{lang_attr}>{code_content}</code></pre>')
                in_code_block = False
                code_lang = ''
                code_lines = []
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # Blank line
        if line.strip() == '':
            flush_list()
            i += 1
            continue

        # Headings
        heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if heading_match:
            flush_list()
            level = len(heading_match.group(1))
            content = inline_format(heading_match.group(2))
            html_lines.append(f'<h{level}>{content}</h{level}>')
            i += 1
            continue

        # Horizontal rule
        if re.match(r'^(-{3,}|_{3,}|\*{3,})$', line.strip()):
            flush_list()
            html_lines.append('<hr>')
            i += 1
            continue

        # Blockquote
        if line.startswith('>'):
            flush_list()
            quote_content = inline_format(line[1:].strip())
            html_lines.append(f'<blockquote><p>{quote_content}</p></blockquote>')
            i += 1
            continue

        # Unordered list
        ul_match = re.match(r'^[\-\*]\s+(.+)$', line)
        if ul_match:
            if not in_list:
                in_list = True
                list_type = 'ul'
            list_items.append(ul_match.group(1))
            i += 1
            continue

        # Ordered list
        ol_match = re.match(r'^\d+\.\s+(.+)$', line)
        if ol_match:
            if not in_list:
                in_list = True
                list_type = 'ol'
            list_items.append(ol_match.group(1))
            i += 1
            continue

        # Paragraph
        flush_list()
        para_lines = [line]
        while i + 1 < len(lines) and lines[i + 1].strip() != '' and not lines[i + 1].startswith('#') and not lines[i + 1].startswith('```') and not re.match(r'^[\-\*]\s+', lines[i + 1]) and not re.match(r'^\d+\.\s+', lines[i + 1]):
            i += 1
            para_lines.append(lines[i])
        content = inline_format(' '.join(para_lines))
        html_lines.append(f'<p>{content}</p>')
        i += 1

    flush_list()
    return '\n'.join(html_lines)


# ---------------------------------------------------------------------------
# Frontmatter parser
# ---------------------------------------------------------------------------

def parse_frontmatter(content):
    """Parse YAML-like frontmatter from markdown content."""
    if not content.startswith('---'):
        return {}, content

    end = content.find('---', 3)
    if end == -1:
        return {}, content

    frontmatter_str = content[3:end].strip()
    body = content[end + 3:].strip()

    metadata = {}
    for line in frontmatter_str.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            metadata[key] = value

    return metadata, body


# ---------------------------------------------------------------------------
# HTML templates
# ---------------------------------------------------------------------------

def post_template(title, date, content_html, number=None):
    """Generate full HTML page for a blog post."""
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} - RajD</title>
  <link href="https://fonts.googleapis.com/css2?family=Roboto+Mono&display=swap" rel="stylesheet">
  <style>
    body {{
      font-family: 'Roboto Mono', monospace;
      background: #ffffff;
      color: #000;
      margin: 0;
      padding: 40px 0 0;
      box-sizing: border-box;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }}
    .container {{
      margin: 0 20%;
      padding: 0 0 40px;
      max-width: 960px;
      box-sizing: border-box;
      flex: 1 1 auto;
      display: flex;
      flex-direction: column;
    }}
    nav {{
      display: flex;
      justify-content: flex-end;
      gap: 2em;
      margin-bottom: 1em;
      align-items: center;
      min-height: 44px;
    }}
    nav a {{
      color: #000;
      text-decoration: none;
      font-weight: 500;
      display: inline-flex;
      align-items: center;
      padding: 6px 6px 8px;
      box-sizing: border-box;
      position: relative;
      transition: font-size 200ms ease, opacity 150ms ease;
    }}
    nav a::after {{
      content: "";
      position: absolute;
      left: 0;
      right: 0;
      bottom: 4px;
      height: 2px;
      background: #000;
      transform: scaleX(0);
      transform-origin: left;
      transition: transform 220ms ease;
    }}
    nav a:not(.active):hover::after {{ transform: scaleX(1); }}
    nav a:not(.active):hover {{ opacity: 0.8; }}
    nav a.active {{ font-weight: 700; font-size: 1.15em; opacity: 1; }}

    .post-header {{
      margin: 2em 0 1em;
    }}
    .post-number {{
      display: block;
      color: rgba(0,0,0,0.35);
      font-size: 0.85em;
      margin-bottom: 0.3em;
    }}
    .post-header h1 {{
      font-size: 1.6em;
      margin: 0 0 0.3em;
      line-height: 1.3;
    }}
    .post-date {{
      color: rgba(0,0,0,0.5);
      font-size: 0.9em;
    }}
    .post-content {{
      line-height: 1.7;
    }}
    .post-content h2 {{
      margin: 1.8em 0 0.6em;
      font-size: 1.3em;
    }}
    .post-content h3 {{
      margin: 1.5em 0 0.5em;
      font-size: 1.1em;
    }}
    .post-content p {{
      margin: 0 0 1.2em;
    }}
    .post-content a {{
      color: #000;
      border-bottom: 2px solid rgba(0,0,0,0.18);
      text-decoration: none;
      padding-bottom: 1px;
      transition: border-color 180ms ease;
    }}
    .post-content a:hover {{
      border-bottom-color: rgba(0,0,0,0.6);
    }}
    .post-content pre {{
      background: #f5f5f5;
      border: 1px solid rgba(0,0,0,0.08);
      border-radius: 6px;
      padding: 16px;
      overflow-x: auto;
      font-size: 0.9em;
      line-height: 1.5;
    }}
    .post-content code {{
      background: #f5f5f5;
      padding: 2px 6px;
      border-radius: 3px;
      font-size: 0.9em;
    }}
    .post-content pre code {{
      background: none;
      padding: 0;
      border-radius: 0;
    }}
    .post-content ul, .post-content ol {{
      padding-left: 1.5em;
      margin: 0 0 1.2em;
    }}
    .post-content li {{
      margin-bottom: 0.4em;
    }}
    .post-content blockquote {{
      border-left: 3px solid rgba(0,0,0,0.2);
      margin: 0 0 1.2em;
      padding: 0.5em 1em;
      color: rgba(0,0,0,0.7);
    }}

    .back-link {{
      display: inline-block;
      margin-top: 2em;
      color: #000;
      text-decoration: none;
      border-bottom: 2px solid rgba(0,0,0,0.18);
      padding-bottom: 1px;
      transition: border-color 180ms ease;
    }}
    .back-link:hover {{
      border-bottom-color: rgba(0,0,0,0.6);
    }}

    .footer {{
      margin-top: auto;
      text-align: center;
      font-size: 0.9rem;
      color: rgba(0,0,0,0.6);
      padding: 12px 0 6px;
    }}
    .social {{
      text-align: center;
      margin-top: 8px;
    }}
    .social a {{ margin: 0 8px; color: inherit; display: inline-block; opacity: 0.95 }}
    .social svg {{ width:20px; height:20px; vertical-align:middle; fill:currentColor }}

    @media screen and (max-width: 1024px) {{ .container {{ margin: 0 12%; padding: 20px 0; }} }}
    @media screen and (max-width: 768px) {{
      .container {{ margin: 0 8%; padding: 16px 0; }}
      .post-header h1 {{ font-size: 1.4em; }}
    }}
    @media screen and (max-width: 480px) {{
      .container {{ margin: 0 5%; padding: 12px 0; }}
      .post-header h1 {{ font-size: 1.2em; }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <nav>
      <a href="/">home</a>
      <a href="/blog">blog</a>
      <a href="/whoami">whoami</a>
    </nav>

    <article>
      <div class="post-header">
        {'<span class="post-number">#' + number + '</span>' if number else ''}
        <h1>{title}</h1>
        <span class="post-date">{date}</span>
      </div>
      <div class="post-content">
        {content_html}
      </div>
    </article>

    <a href="/blog" class="back-link">&larr; back to blog</a>

    <script>
      (function () {{
        const links = document.querySelectorAll('nav a');
        let current = location.pathname;
        if (current.length > 1 && current.endsWith('/')) current = current.slice(0, -1);
        links.forEach(a => {{
          let href = a.getAttribute('href');
          if (!href || href.startsWith('#')) return;
          if (href.length > 1 && href.endsWith('/')) href = href.slice(0, -1);
          if (href === '/' && current === '/') a.classList.add('active');
          else if (href !== '/' && current.startsWith(href)) a.classList.add('active');
        }});
      }})();
    </script>

    <footer class="footer">&copy; 2026 Raj Duwal. All rights reserved.</footer>
    <div class="social">
      <a href="https://linkedin.com/in/draazxp" target="_blank" rel="noopener" aria-label="LinkedIn">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4.98 3.5C4.98 4.88 3.88 6 2.5 6S0 4.88 0 3.5 1.12 1 2.5 1 4.98 2.12 4.98 3.5zM.2 8h4.6V24H.2zM8.6 8h4.4v2.2h.1c.6-1.1 2.2-2.2 4.6-2.2 4.9 0 5.8 3.2 5.8 7.3V24h-4.6v-6.7c0-1.6 0-3.7-2.3-3.7-2.3 0-2.6 1.8-2.6 3.6V24H8.6z"/></svg>
      </a>
      <a href="https://github.com/draazxp" target="_blank" rel="noopener" aria-label="GitHub">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 .5C5.65.5.5 5.65.5 12c0 5.08 3.29 9.38 7.86 10.9.58.11.79-.25.79-.56 0-.28-.01-1.02-.02-2-3.2.7-3.88-1.54-3.88-1.54-.53-1.36-1.3-1.72-1.3-1.72-1.06-.72.08-.71.08-.71 1.17.08 1.78 1.2 1.78 1.2 1.04 1.78 2.73 1.27 3.4.97.11-.76.41-1.27.75-1.56-2.55-.29-5.24-1.28-5.24-5.68 0-1.25.45-2.27 1.19-3.07-.12-.29-.52-1.46.11-3.04 0 0 .97-.31 3.18 1.17a11 11 0 0 1 5.79 0c2.21-1.48 3.18-1.17 3.18-1.17.63 1.58.23 2.75.12 3.04.74.8 1.19 1.82 1.19 3.07 0 4.41-2.7 5.38-5.27 5.66.42.36.8 1.08.8 2.18 0 1.58-.02 2.85-.02 3.24 0 .31.21.68.8.56C20.71 21.38 24 17.08 24 12 24 5.65 18.35.5 12 .5z"/></svg>
      </a>
    </div>
  </div>
</body>
</html>'''


def blog_index_template(posts_html):
    """Generate the blog index page with list of posts."""
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Blog - RajD</title>
  <link href="https://fonts.googleapis.com/css2?family=Roboto+Mono&display=swap" rel="stylesheet">
  <style>
    body {{ font-family: 'Roboto Mono', monospace; margin:0; padding:40px 0 0; box-sizing:border-box; background:#fff; color:#000; min-height:100vh; display:flex; flex-direction:column }}
    .container {{ margin:0 20%; padding:0 0 40px; max-width:960px; box-sizing:border-box; flex:1 1 auto; display:flex; flex-direction:column }}
    nav {{ display:flex; justify-content:flex-end; gap:2em; margin-bottom:1em; align-items:center; min-height:44px }}
    nav a {{ color:#000; text-decoration:none; font-weight:500; display:inline-flex; align-items:center; padding:6px 6px 8px; box-sizing:border-box; position:relative; transition: font-size 200ms ease, opacity 150ms ease; }}
    nav a::after {{ content:""; position:absolute; left:0; right:0; bottom:4px; height:2px; background:#000; transform:scaleX(0); transform-origin:left; transition:transform 220ms ease; }}
    nav a:not(.active):hover::after {{ transform:scaleX(1); }}
    nav a:not(.active):hover {{ opacity: 0.8; }}
    nav a.active {{ font-weight:700; font-size:1.15em; opacity:1; }}
    h1 {{ margin: 2em 0 1em; font-size: 1.6em; }}
    .post-list {{ list-style: none; padding: 0; margin: 0; }}
    .post-item {{ margin-bottom: 1em; }}
    .post-item a {{
      display: block;
      color: #000;
      text-decoration: none;
      padding: 20px 24px;
      border: 1px solid rgba(0,0,0,0.12);
      border-radius: 6px;
      transition: border-color 180ms ease, background 180ms ease;
    }}
    .post-item a:hover {{
      border-color: rgba(0,0,0,0.4);
      background: rgba(0,0,0,0.02);
    }}
    .post-number {{ display: block; color: rgba(0,0,0,0.35); font-size: 0.8em; margin-bottom: 0.3em; }}
    .post-title {{ font-weight: 700; font-size: 1.05em; line-height: 1.4; }}
    .post-date {{ display: block; color: rgba(0,0,0,0.45); font-size: 0.82em; margin-top: 0.4em; }}
    .post-desc {{ display: block; margin-top: 0.5em; color: rgba(0,0,0,0.65); font-size: 0.9em; line-height: 1.5; }}
    .footer {{
      margin-top: auto;
      text-align: center;
      font-size: 0.9rem;
      color: rgba(0,0,0,0.6);
      padding: 12px 0 6px;
    }}
    .social {{
      text-align: center;
      margin-top: 8px;
    }}
    .social a {{ margin: 0 8px; color: inherit; display: inline-block; opacity: 0.95 }}
    .social svg {{ width:20px; height:20px; vertical-align:middle; fill:currentColor }}
    @media (max-width:1024px) {{ .container{{margin:0 12%}} }}
    @media (max-width:768px) {{ .container{{margin:0 8%}} }}
    @media (max-width:480px) {{ .container{{margin:0 5%}} }}
  </style>
</head>
<body>
  <div class="container">
    <nav>
      <a href="/">home</a>
      <a href="/blog">blog</a>
      <a href="/whoami">whoami</a>
    </nav>

    <h1>Blog</h1>
    <ul class="post-list">
      {posts_html}
    </ul>

    <script>
      (function () {{
        const links = document.querySelectorAll('nav a');
        let current = location.pathname;
        if (current.length > 1 && current.endsWith('/')) current = current.slice(0, -1);
        links.forEach(a => {{
          let href = a.getAttribute('href');
          if (!href || href.startsWith('#')) return;
          if (href.length > 1 && href.endsWith('/')) href = href.slice(0, -1);
          if (href === '/' && current === '/') a.classList.add('active');
          else if (href !== '/' && current === href) a.classList.add('active');
        }});
      }})();
    </script>

    <footer class="footer">&copy; 2026 Raj Duwal. All rights reserved.</footer>
    <div class="social">
      <a href="https://linkedin.com/in/draazxp" target="_blank" rel="noopener" aria-label="LinkedIn">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4.98 3.5C4.98 4.88 3.88 6 2.5 6S0 4.88 0 3.5 1.12 1 2.5 1 4.98 2.12 4.98 3.5zM.2 8h4.6V24H.2zM8.6 8h4.4v2.2h.1c.6-1.1 2.2-2.2 4.6-2.2 4.9 0 5.8 3.2 5.8 7.3V24h-4.6v-6.7c0-1.6 0-3.7-2.3-3.7-2.3 0-2.6 1.8-2.6 3.6V24H8.6z"/></svg>
      </a>
      <a href="https://github.com/draazxp" target="_blank" rel="noopener" aria-label="GitHub">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 .5C5.65.5.5 5.65.5 12c0 5.08 3.29 9.38 7.86 10.9.58.11.79-.25.79-.56 0-.28-.01-1.02-.02-2-3.2.7-3.88-1.54-3.88-1.54-.53-1.36-1.3-1.72-1.3-1.72-1.06-.72.08-.71.08-.71 1.17.08 1.78 1.2 1.78 1.2 1.04 1.78 2.73 1.27 3.4.97.11-.76.41-1.27.75-1.56-2.55-.29-5.24-1.28-5.24-5.68 0-1.25.45-2.27 1.19-3.07-.12-.29-.52-1.46.11-3.04 0 0 .97-.31 3.18 1.17a11 11 0 0 1 5.79 0c2.21-1.48 3.18-1.17 3.18-1.17.63 1.58.23 2.75.12 3.04.74.8 1.19 1.82 1.19 3.07 0 4.41-2.7 5.38-5.27 5.66.42.36.8 1.08.8 2.18 0 1.58-.02 2.85-.02 3.24 0 .31.21.68.8.56C20.71 21.38 24 17.08 24 12 24 5.65 18.35.5 12 .5z"/></svg>
      </a>
    </div>
  </div>
</body>
</html>'''


# ---------------------------------------------------------------------------
# Build logic
# ---------------------------------------------------------------------------

def build():
    """Main build function."""
    root = Path(__file__).parent
    posts_dir = root / 'blog' / 'posts'
    output_dir = root / 'blog'

    if not posts_dir.exists():
        print("No blog/posts/ directory found. Nothing to build.")
        return

    # Collect all markdown posts
    posts = []
    for md_file in sorted(posts_dir.glob('*.md')):
        content = md_file.read_text(encoding='utf-8')
        metadata, body = parse_frontmatter(content)

        if not metadata.get('title') or not metadata.get('date'):
            print(f"Skipping {md_file.name}: missing title or date in frontmatter")
            continue

        slug = md_file.stem
        html_content = md_to_html(body)

        posts.append({
            'title': metadata['title'],
            'date': metadata['date'],
            'description': metadata.get('description', ''),
            'number': metadata.get('number', ''),
            'slug': slug,
            'html': html_content,
        })

    # Sort by date descending (newest first)
    posts.sort(key=lambda p: p['date'], reverse=True)

    # Generate individual post pages
    for post in posts:
        post_dir = output_dir / post['slug']
        post_dir.mkdir(parents=True, exist_ok=True)

        post_html = post_template(post['title'], post['date'], post['html'], post.get('number'))
        (post_dir / 'index.html').write_text(post_html, encoding='utf-8')
        print(f"Built: blog/{post['slug']}/index.html")

    # Generate blog index
    posts_list_html = ''
    for post in posts:
        number_html = f'<span class="post-number">#{post["number"]}</span>' if post.get('number') else ''
        desc_html = f'<span class="post-desc">{html.escape(post["description"])}</span>' if post['description'] else ''
        posts_list_html += f'''      <li class="post-item">
        <a href="/blog/{post['slug']}">
          {number_html}
          <span class="post-title">{html.escape(post['title'])}</span>
          <span class="post-date">{post['date']}</span>
          {desc_html}
        </a>
      </li>\n'''

    index_html = blog_index_template(posts_list_html)
    (output_dir / 'index.html').write_text(index_html, encoding='utf-8')
    print(f"Built: blog/index.html ({len(posts)} posts)")


if __name__ == '__main__':
    build()
