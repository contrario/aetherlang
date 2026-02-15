#!/usr/bin/env python3
"""
AetherLang Universal Report Generator
--------------------------------------
Generates premium PDF reports for ALL engines.
Does NOT modify any existing files.
Drop-in module: from universal_report import generate_engine_pdf
"""

import re
import html as html_mod
from datetime import datetime, timezone
from typing import Optional

import weasyprint

# ── Engine Themes ──
ENGINE_THEMES = {
    "apex": {
        "icon": "🏢", "name": "APEX Business Intelligence",
        "accent": "#4a9eff", "accent2": "#00e5a0", "bg": "#0a0e1a",
        "header_bg": "#0f1424", "border": "#1a2035",
    },
    "assembly": {
        "icon": "🏛️", "name": "Grand Assembly Council",
        "accent": "#ffd700", "accent2": "#ff8c00", "bg": "#0a0e1a",
        "header_bg": "#1a1400", "border": "#3d2e00",
    },
    "consulting": {
        "icon": "💼", "name": "McKinsey Strategic Consulting",
        "accent": "#00b4d8", "accent2": "#0077b6", "bg": "#0a0e1a",
        "header_bg": "#0a1520", "border": "#1a2535",
    },
    "lab": {
        "icon": "🔬", "name": "Deep Analysis Lab",
        "accent": "#7b2ff7", "accent2": "#a855f7", "bg": "#0a0e1a",
        "header_bg": "#140a24", "border": "#2a1a45",
    },
    "marketing": {
        "icon": "📣", "name": "Viral Marketing Engine",
        "accent": "#ff6b6b", "accent2": "#ee5a24", "bg": "#0a0e1a",
        "header_bg": "#1a0f0f", "border": "#352020",
    },
    "oracle": {
        "icon": "🎰", "name": "OPAP Oracle Intelligence",
        "accent": "#00e5a0", "accent2": "#00b894", "bg": "#0a0e1a",
        "header_bg": "#0a1a14", "border": "#1a3525",
    },
    "blueprint": {
        "icon": "📄", "name": "APEX Trading Blueprint",
        "accent": "#4a9eff", "accent2": "#00e5a0", "bg": "#0a0e1a",
        "header_bg": "#0f1424", "border": "#1a2035",
    },
    "crypto": {
        "icon": "📊", "name": "APEX Crypto Intelligence",
        "accent": "#f7931a", "accent2": "#627eea", "bg": "#0a0e1a",
        "header_bg": "#1a140a", "border": "#352a1a",
    },
    "molecular": {
        "icon": "⚗️", "name": "Molecular Gastronomy Lab",
        "accent": "#00cec9", "accent2": "#6c5ce7", "bg": "#0a0e1a",
        "header_bg": "#0a1a1a", "border": "#1a3535",
    },
    "omega": {
        "icon": "🔥", "name": "Chef Omega Neural Kitchen",
        "accent": "#ff6348", "accent2": "#ff9f43", "bg": "#0a0e1a",
        "header_bg": "#1a0f0a", "border": "#352015",
    },
    "chef": {
        "icon": "👨‍🍳", "name": "Chef Intelligence",
        "accent": "#ff6348", "accent2": "#ff9f43", "bg": "#0a0e1a",
        "header_bg": "#1a0f0a", "border": "#352015",
    },
    "brain": {
        "icon": "🧠", "name": "Super Brain Nobel Mode",
        "accent": "#e84393", "accent2": "#fd79a8", "bg": "#0a0e1a",
        "header_bg": "#1a0a14", "border": "#351a2a",
    },
    "cyber": {
        "icon": "🔒", "name": "Cyber Intelligence Unit",
        "accent": "#00ff88", "accent2": "#00cc6a", "bg": "#050a05",
        "header_bg": "#0a1a0f", "border": "#1a3520",
    },
    "academic": {
        "icon": "🎓", "name": "Academic Research Engine",
        "accent": "#dfe6e9", "accent2": "#b2bec3", "bg": "#0a0e1a",
        "header_bg": "#12141a", "border": "#2d3035",
    },
    "terra": {
        "icon": "🌿", "name": "Terra Alchemica Olympus",
        "accent": "#c49b63", "accent2": "#4a8c5c", "bg": "#0a0e0a",
        "header_bg": "#141a14", "border": "#2a352a",
    },
}

DEFAULT_THEME = {
    "icon": "⚡", "name": "AetherLang Intelligence",
    "accent": "#4a9eff", "accent2": "#00e5a0", "bg": "#0a0e1a",
    "header_bg": "#0f1424", "border": "#1a2035",
}


def _esc(text: str) -> str:
    """HTML-escape text."""
    return html_mod.escape(str(text)) if text else ""


def _markdown_to_html(text: str) -> str:
    """Convert basic markdown in LLM response to HTML."""
    if not text:
        return ""

    lines = text.split("\n")
    html_lines = []
    in_list = False
    in_code = False
    code_block = []

    for line in lines:
        stripped = line.strip()

        # Code blocks
        if stripped.startswith("```"):
            if in_code:
                html_lines.append(
                    '<pre class="code-block">'
                    + _esc("\n".join(code_block))
                    + "</pre>"
                )
                code_block = []
                in_code = False
            else:
                in_code = True
            continue

        if in_code:
            code_block.append(line)
            continue

        # Close list if needed
        if in_list and not stripped.startswith(("- ", "* ", "• ")):
            if not re.match(r"^\d+[\.\)]\s", stripped):
                html_lines.append("</ul>")
                in_list = False

        # Empty line
        if not stripped:
            html_lines.append("<br>")
            continue

        # Headers
        if stripped.startswith("### "):
            html_lines.append(f'<h4 class="section-h4">{_esc(stripped[4:])}</h4>')
            continue
        if stripped.startswith("## "):
            html_lines.append(f'<h3 class="section-h3">{_esc(stripped[3:])}</h3>')
            continue
        if stripped.startswith("# "):
            html_lines.append(f'<h2 class="section-h2">{_esc(stripped[2:])}</h2>')
            continue

        # Horizontal rule
        if stripped in ("---", "***", "___"):
            html_lines.append('<hr class="divider">')
            continue

        # Bullet lists
        if stripped.startswith(("- ", "* ", "• ")):
            if not in_list:
                html_lines.append('<ul class="content-list">')
                in_list = True
            item = stripped.lstrip("-*• ").strip()
            html_lines.append(f"<li>{_esc(item)}</li>")
            continue

        # Numbered lists
        num_match = re.match(r"^(\d+)[\.\)]\s+(.*)", stripped)
        if num_match:
            if not in_list:
                html_lines.append('<ul class="content-list numbered">')
                in_list = True
            html_lines.append(f"<li>{_esc(num_match.group(2))}</li>")
            continue

        # Regular paragraph
        html_lines.append(f"<p>{_esc(stripped)}</p>")

    if in_list:
        html_lines.append("</ul>")
    if in_code:
        html_lines.append(
            '<pre class="code-block">'
            + _esc("\n".join(code_block))
            + "</pre>"
        )

    result = "\n".join(html_lines)

    # Inline formatting (after escaping)
    result = re.sub(
        r"\*\*(.+?)\*\*",
        r'<strong class="bold-accent">\1</strong>',
        result,
    )
    result = re.sub(r"\*(.+?)\*", r"<em>\1</em>", result)
    result = re.sub(r"`(.+?)`", r'<code class="inline-code">\1</code>', result)

    return result


def _build_html(
    engine_key: str,
    title: str,
    content_html: str,
    subtitle: Optional[str] = None,
    user_query: Optional[str] = None,
    extra_sections: Optional[list[dict]] = None,
) -> str:
    """Build complete HTML document for PDF rendering."""

    theme = ENGINE_THEMES.get(engine_key, DEFAULT_THEME)
    accent = theme["accent"]
    accent2 = theme["accent2"]
    bg = theme["bg"]
    header_bg = theme["header_bg"]
    border = theme["border"]
    icon = theme["icon"]
    engine_name = theme["name"]

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    sub = subtitle or engine_name

    # Extra sections HTML
    extra_html = ""
    if extra_sections:
        for sec in extra_sections:
            sec_title = _esc(sec.get("title", ""))
            sec_body = _markdown_to_html(sec.get("content", ""))
            extra_html += f"""
            <div class="extra-section">
                <h2 class="section-h2">{sec_title}</h2>
                {sec_body}
            </div>"""

    # User query block
    query_html = ""
    if user_query:
        query_html = f"""
        <div class="query-box">
            <span class="query-label">QUERY</span>
            <span class="query-text">{_esc(user_query)}</span>
        </div>"""

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
@page {{
    size: A4;
    margin: 15mm 18mm;
    @bottom-center {{
        content: "Page " counter(page) " of " counter(pages);
        font-size: 7pt;
        color: #555;
    }}
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    font-family: 'Helvetica Neue', Arial, sans-serif;
    background: {bg};
    color: #c0c8d4;
    font-size: 10pt;
    line-height: 1.6;
}}

/* ── Header ── */
.header {{
    text-align: center;
    padding: 25px 0 20px;
    border-bottom: 2px solid {accent};
    margin-bottom: 20px;
}}
.header .icon {{
    font-size: 28pt;
    display: block;
    margin-bottom: 8px;
}}
.header h1 {{
    font-size: 20pt;
    color: #ffffff;
    letter-spacing: 2px;
    margin-bottom: 4px;
}}
.header .subtitle {{
    font-size: 10pt;
    color: {accent};
    letter-spacing: 1px;
}}
.header .timestamp {{
    font-size: 7pt;
    color: #555;
    margin-top: 6px;
}}

/* ── Query Box ── */
.query-box {{
    background: {header_bg};
    border: 1px solid {border};
    border-left: 3px solid {accent2};
    border-radius: 4px;
    padding: 10px 16px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 12px;
}}
.query-label {{
    font-size: 7pt;
    color: {accent2};
    text-transform: uppercase;
    letter-spacing: 2px;
    font-weight: bold;
    white-space: nowrap;
}}
.query-text {{
    color: #e0e0e0;
    font-size: 9.5pt;
}}

/* ── Main Content ── */
.content {{
    background: {header_bg};
    border: 1px solid {border};
    border-radius: 6px;
    padding: 20px 24px;
    margin-bottom: 20px;
}}
.content p {{
    margin-bottom: 8px;
    color: #c0c8d4;
    font-size: 9.5pt;
}}
.content h2, .section-h2 {{
    color: {accent};
    font-size: 14pt;
    border-bottom: 1px solid {border};
    padding-bottom: 5px;
    margin: 20px 0 12px 0;
}}
.content h3, .section-h3 {{
    color: {accent2};
    font-size: 12pt;
    margin: 16px 0 8px 0;
}}
.content h4, .section-h4 {{
    color: #e0e0e0;
    font-size: 10.5pt;
    margin: 12px 0 6px 0;
}}

/* ── Lists ── */
.content-list {{
    margin: 8px 0 8px 20px;
    color: #c0c8d4;
    font-size: 9.5pt;
}}
.content-list li {{
    margin-bottom: 4px;
    padding-left: 4px;
}}

/* ── Code ── */
.code-block {{
    background: #050810;
    border: 1px solid {border};
    border-radius: 4px;
    padding: 12px 16px;
    font-family: 'Courier New', monospace;
    font-size: 8.5pt;
    color: #00e5a0;
    overflow-wrap: break-word;
    white-space: pre-wrap;
    margin: 10px 0;
}}
.inline-code {{
    background: #1a1e30;
    padding: 1px 5px;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
    font-size: 8.5pt;
    color: {accent};
}}
.bold-accent {{
    color: #ffffff;
    font-weight: bold;
}}

/* ── Divider ── */
.divider {{
    border: none;
    border-top: 1px solid {border};
    margin: 16px 0;
}}

/* ── Extra Sections ── */
.extra-section {{
    background: {header_bg};
    border: 1px solid {border};
    border-radius: 6px;
    padding: 20px 24px;
    margin-bottom: 20px;
    page-break-inside: avoid;
}}

/* ── Footer ── */
.footer {{
    text-align: center;
    padding-top: 15px;
    border-top: 1px solid {border};
    margin-top: 20px;
}}
.footer .brand {{
    font-size: 9pt;
    color: {accent};
    letter-spacing: 1px;
}}
.footer .disclaimer {{
    font-size: 7pt;
    color: #555;
    margin-top: 4px;
}}
</style>
</head>
<body>

<div class="header">
    <span class="icon">{icon}</span>
    <h1>{_esc(title)}</h1>
    <div class="subtitle">{_esc(sub)}</div>
    <div class="timestamp">{timestamp}</div>
</div>

{query_html}

<div class="content">
{content_html}
</div>

{extra_html}

<div class="footer">
    <div class="brand">⚡ AetherLang Intelligence Platform — {_esc(engine_name)}</div>
    <div class="disclaimer">Generated by NeuroAether APEX • For informational purposes only</div>
</div>

</body>
</html>"""


def generate_engine_pdf(
    engine_key: str,
    title: str,
    content: str,
    output_path: str,
    subtitle: Optional[str] = None,
    user_query: Optional[str] = None,
    extra_sections: Optional[list[dict]] = None,
) -> str:
    """
    Generate a PDF report for any engine.

    Args:
        engine_key: Engine identifier (apex, crypto, chef, etc.)
        title: Report title
        content: LLM response text (markdown supported)
        output_path: Where to save the PDF
        subtitle: Optional subtitle (defaults to engine name)
        user_query: Optional user query to display
        extra_sections: Optional list of {"title": "...", "content": "..."} dicts

    Returns:
        output_path on success
    """
    content_html = _markdown_to_html(content)
    full_html = _build_html(
        engine_key=engine_key,
        title=title,
        content_html=content_html,
        subtitle=subtitle,
        user_query=user_query,
        extra_sections=extra_sections,
    )
    pdf_bytes = weasyprint.HTML(string=full_html).write_pdf()
    with open(output_path, "wb") as f:
        f.write(pdf_bytes)
    return output_path


# ── Quick test ──
if __name__ == "__main__":
    test_content = """# Executive Summary

This is a **comprehensive analysis** of the current market conditions.

## Key Findings

- Finding 1: Market is showing *bullish* signals
- Finding 2: Volume has increased by 45%
- Finding 3: Support levels are holding strong

### Technical Indicators

1. RSI is at 65 — approaching overbought
2. MACD crossover confirmed
3. Bollinger Bands expanding

---

## Risk Assessment

The primary risks include:

- Regulatory uncertainty in EU markets
- Potential interest rate changes
- Geopolitical tensions

```python
# Example code block
def calculate_risk(portfolio):
    return sum(asset.risk for asset in portfolio)
```

## Recommendation

Based on our analysis, we recommend a **cautious long** position with strict stop-losses.
"""

    for eng in ["apex", "crypto", "chef", "cyber", "assembly", "oracle"]:
        path = f"/tmp/test_report_{eng}.pdf"
        generate_engine_pdf(
            engine_key=eng,
            title=f"Test Report — {eng.upper()}",
            content=test_content,
            output_path=path,
            user_query="Analyze current BTC market conditions",
        )
        print(f"✅ {eng}: {path}")
