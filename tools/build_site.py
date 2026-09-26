"""Build the site's HTML pages from the Markdown sources.

Usage (from the repository root):  python tools/build_site.py
Needs Python-Markdown:              pip install markdown

README.md becomes index.html; every other page in PAGES becomes the same path
with .html. All pages share one shell: the styles, header and navigation.
Links between rendered pages stay on the site, so they work locally and on
GitHub Pages; links to other Markdown files go to the file on GitHub.
Edit the Markdown, then rerun this. Do not edit the generated HTML by hand.
(.nojekyll keeps GitHub Pages from converting the Markdown a second time.)
"""
import html
import posixpath
import re
from pathlib import Path

try:
    import markdown
except ImportError:
    raise SystemExit('Python-Markdown is needed: pip install markdown')

ROOT = Path(__file__).resolve().parent.parent
BLOB = 'https://github.com/Nate-BadScienceFiction/logic-engine-experiment/blob/main/'
PAGES = ['README.md', 'docs/HISTORY.md', 'docs/ENGINE.md', 'docs/MIGRATION.md', 'docs/AI-DEVELOPMENT.md', 'docs/GLOSSARY.md',
         'docs/prompts/README.md', 'docs/prompts/1-design-brief-2026-09-13.md',
         'docs/prompts/2-test-migration-audit-2026-09-14.md', 'docs/prompts/3-two-way-audit-2026-09-15.md',
         'evidence/README.md', 'evidence/benchmarks-2026-09-25.md',
         'evidence/benchmarks-revised-2026-09-25.md', 'evidence/comparison-revised-2026-09-25.md', 'archive/README.md']
NAV = [('History', 'docs/HISTORY.md'), ('How it works', 'docs/ENGINE.md'), ('Building it with AI', 'docs/AI-DEVELOPMENT.md'),
       ('Migration', 'docs/MIGRATION.md'), ('Evidence', 'evidence/README.md'), ('Glossary', 'docs/GLOSSARY.md')]
HISTORY_PAGE = ('# Earlier notes\n\nThe notes from the first year of this project, including the old front page and its charts, '
                'are in the [archive](archive/README.md). The short version of the story is in [History](docs/HISTORY.md).\n')
CSS = """
    :root { color-scheme:light; --ink:#283238; --muted:#586269; --paper:#faf9f6; --line:#d6d9d8; --link:#215e73; }
    * { box-sizing:border-box; }
    body { margin:0; background:var(--paper); color:var(--ink); font:16px/1.65 system-ui,-apple-system,"Segoe UI",sans-serif; }
    .wrap { width:min(1000px,calc(100% - 2.5rem)); margin-inline:auto; }
    a { color:var(--link); text-underline-offset:.18em; }
    a:hover { color:#163f4d; }
    a:focus-visible,summary:focus-visible,.table-scroll:focus-visible { outline:3px solid #9a5b1a; outline-offset:4px; }
    .skip { position:absolute; left:-1000px; top:0; padding:.6rem 1rem; background:#fff; }
    .skip:focus { left:1rem; }
    .site-head { border-bottom:1px solid var(--line); }
    .site-head .wrap { display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:.5rem 2rem; padding-block:1rem; }
    .site-head a { color:var(--ink); }
    .site-name { font-weight:650; text-decoration:none; }
    nav { display:flex; flex-wrap:wrap; gap:.4rem 1.2rem; font-size:.9rem; }
    nav a[aria-current="page"] { color:var(--link); font-weight:650; }
    main { padding-block:2.5rem 3rem; }
    h1,h2,h3 { line-height:1.3; font-weight:650; }
    h1 { margin:.35rem 0 1rem; font-size:clamp(1.8rem,4vw,2.4rem); }
    h2 { margin:0 0 1rem; font-size:1.4rem; }
    h3 { margin:1.5rem 0 .6rem; font-size:1.08rem; }
    p { max-width:82ch; margin:0 0 1rem; }
    .intro { margin-bottom:2rem; }
    section { border-top:1px solid var(--line); padding-top:1.8rem; margin-top:2rem; }
    .table-scroll { overflow-x:auto; margin:1rem 0; }
    table { width:100%; border-collapse:collapse; font-size:.94rem; }
    th,td { text-align:left; vertical-align:top; padding:.65rem .7rem; border-bottom:1px solid var(--line); }
    thead { background:#eef0ed; }
    th { font-weight:600; }
    li { margin-bottom:.6rem; }
    ul,ol { max-width:82ch; padding-left:1.4rem; }
    code { font-family:ui-monospace,SFMono-Regular,Consolas,monospace; font-size:.88em; overflow-wrap:anywhere; }
    pre { background:#f1f2ee; border:1px solid var(--line); border-radius:4px; padding:.9rem 1rem; overflow-x:auto; font-size:.86rem; line-height:1.5; max-width:100%; }
    pre code { font-size:inherit; overflow-wrap:normal; }
    blockquote { margin:1rem 0; padding:.2rem 0 .2rem 1rem; border-left:3px solid var(--line); color:var(--muted); }
    hr { border:0; border-top:1px solid var(--line); margin:2rem 0; }
    details { margin:1.2rem 0; }
    summary { cursor:pointer; color:var(--link); }
    img { display:block; max-width:100%; height:auto; border:1px solid var(--line); }
    figcaption { margin-top:.5rem; color:var(--muted); font-size:.9rem; }
    .page-contents { display:block; margin:1rem 0 2rem; padding:1rem 1.2rem; background:#eef0ed; border:1px solid var(--line); }
    .page-contents ul { columns:2 18rem; margin:.5rem 0 0; }
    .page-contents li { break-inside:avoid; margin-bottom:.25rem; }
    footer { border-top:1px solid var(--line); padding-block:1.4rem; color:var(--muted); font-size:.88rem; }
    footer p { margin:0; }
    @media (max-width:480px) { .wrap { width:calc(100% - 2rem); } main { padding-top:1.5rem; } th,td { padding:.6rem .4rem; } }"""


def output_for(source):
    return 'index.html' if source == 'README.md' else source[:-3] + '.html'


RENDERED = {source: output_for(source) for source in PAGES}


def github_slug(value, separator='-'):
    """GitHub's heading anchors: lower case, punctuation dropped, spaces to hyphens."""
    value = re.sub(r'<[^>]+>', '', value).strip().lower()
    value = re.sub(r'[^\w\- ]', '', value)
    return value.replace(' ', separator)


def site_link(href, source_dir, output_dir):
    """Rendered pages link to each other; other Markdown goes to GitHub; files stay relative."""
    if re.match(r'^(?:[a-z]+:|#|//)', href):
        return href
    path, hash_mark, fragment = href.partition('#')
    target = posixpath.normpath(posixpath.join(source_dir, path))
    if target in RENDERED:
        return posixpath.relpath(RENDERED[target], output_dir or '.') + hash_mark + fragment
    if target.endswith('.md'):
        return f'{BLOB}{target}{hash_mark}{fragment}'
    return posixpath.relpath(target, output_dir or '.') + hash_mark + fragment


def render(source, text, output):
    source_dir, output_dir = posixpath.dirname(source), posixpath.dirname(output)
    converter = markdown.Markdown(extensions=['tables', 'fenced_code', 'md_in_html', 'toc', 'sane_lists'],
                                  extension_configs={'toc': {'slugify': github_slug}})
    body = converter.convert(text.replace('<details>', '<details markdown="1">'))
    body = re.sub(r'(href|src)="([^"]+)"',
                  lambda m: f'{m.group(1)}="{html.escape(site_link(html.unescape(m.group(2)), source_dir, output_dir), quote=True)}"', body)
    title_match = re.search(r'<h1[^>]*>(.*?)</h1>', body, re.S)
    title = html.unescape(re.sub(r'<[^>]+>', '', title_match.group(1)).strip()) if title_match else 'Cyclops Storm'
    first = re.search(r'<p>(.*?)</p>', body, re.S)
    description = html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', first.group(1))).strip()) if first else title
    if len(description) > 160:
        description = description[:157].rsplit(' ', 1)[0] + '…'

    # Tables scroll on their own on narrow screens and stay keyboard reachable.
    label, parts, last = title, [], 0
    for match in re.finditer(r'<h[23][^>]*>(.*?)</h[23]>|<table>.*?</table>', body, re.S):
        parts.append(body[last:match.start()])
        if match.group(0).startswith('<table'):
            parts.append(f'<div class="table-scroll" tabindex="0" role="region" aria-label="{html.escape(label, quote=True)} table">{match.group(0)}</div>')
        else:
            label = html.unescape(re.sub(r'<[^>]+>', '', match.group(1)).strip()); parts.append(match.group(0))
        last = match.end()
    parts.append(body[last:])
    chunks = re.split(r'(?=<h2[ >])', ''.join(parts))
    sections = '\n'.join(f'<section aria-labelledby="{re.search(r'id="([^"]+)"', chunk).group(1)}">{chunk}</section>' for chunk in chunks[1:])

    contents = ''
    if source in {'docs/HISTORY.md', 'docs/ENGINE.md', 'docs/MIGRATION.md',
                  'docs/AI-DEVELOPMENT.md', 'evidence/README.md',
                  'evidence/comparison-revised-2026-09-25.md',
                  'evidence/benchmarks-revised-2026-09-25.md'}:
        headings = re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', body, re.S)
        links = ''.join(f'<li><a href="#{anchor}">{label}</a></li>' for anchor, label in headings)
        contents = f'<nav class="page-contents" aria-label="On this page"><strong>On this page</strong><ul>{links}</ul></nav>'

    up = posixpath.relpath('.', output_dir or '.')
    home = 'index.html' if up == '.' else f'{up}/index.html'
    nav = ''.join(
        f'<a href="{posixpath.relpath(RENDERED[target], output_dir or ".")}"'
        f'{" aria-current=\"page\"" if RENDERED[target] == output else ""}>{name}</a>' for name, target in NAV)
    page_title = 'Cyclops Storm — lab notes' if output == 'index.html' else f'{title} · Cyclops Storm'
    footer = (f'Generated from <code>{source}</code> by <code>tools/build_site.py</code>.'
              if source in RENDERED else f'<a href="{home}">Cyclops Storm lab notes</a>')
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{html.escape(description, quote=True)}">
  <title>{html.escape(page_title)}</title>
  <style>{CSS}
  </style>
</head>
<body id="top">
  <a class="skip" href="#main">Skip to main content</a>
  <header class="site-head">
    <div class="wrap">
      <a class="site-name" href="{home}">Cyclops Storm / Lab notes</a>
      <nav aria-label="Main navigation">{nav}</nav>
    </div>
  </header>
  <main id="main" class="wrap">
<div class="intro">{chunks[0]}</div>
{contents}
{sections}
  </main>
  <footer><div class="wrap"><p>{footer}</p></div></footer>
</body>
</html>
"""


def build():
    written = []
    for source in PAGES:
        output = RENDERED[source]
        (ROOT / output).write_text(render(source, (ROOT / source).read_text(encoding='utf-8'), output), encoding='utf-8', newline='\n')
        written.append(output)
    (ROOT / 'history.html').write_text(render('history.md', HISTORY_PAGE, 'history.html'), encoding='utf-8', newline='\n')
    written.append('history.html')
    return written


if __name__ == '__main__':
    print('built', ', '.join(build()))
