import re
import bleach

ALLOWED_HTML_TAGS = [
    "html", "head", "body", "title", "meta", "style", "div", "span", "p",
    "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li", "table", "thead",
    "tbody", "tr", "th", "td", "button", "input", "label", "form", "select",
    "option", "textarea", "strong", "em", "b", "i", "u", "br", "hr", "a",
    "img", "svg", "path", "circle", "rect", "line", "polyline", "polygon",
    "pre", "code", "blockquote", "section", "article", "header", "footer", "main"
]

ALLOWED_HTML_ATTRIBUTES = {
    "*": ["id", "class", "style", "title", "width", "height", "type", "name", "value", "placeholder", "href", "src", "alt", "rows", "cols"],
    "a": ["href", "target", "rel"],
    "svg": ["viewbox", "fill", "stroke", "stroke-width", "xmlns", "d", "r", "cx", "cy", "x", "y", "x1", "y1", "x2", "y2"],
    "path": ["d", "fill", "stroke", "stroke-width"],
}

def sanitize_html_artifact(raw_html: str) -> str:
    """Sanitizes HTML/CSS artifact code, allowing standard UI styling while stripping dangerous XSS vectors."""
    if not raw_html:
        return ""
    # Strip javascript: URI schemes
    clean = re.sub(r'href\s*=\s*["\']javascript:[^"\']*["\']', 'href="#"', raw_html, flags=re.IGNORECASE)
    clean = re.sub(r'src\s*=\s*["\']javascript:[^"\']*["\']', 'src=""', clean, flags=re.IGNORECASE)
    # Strip dangerous event handlers like onerror, onload, onclick in backend persistence
    clean = re.sub(r'\bon\w+\s*=\s*["\'][^"\']*["\']', '', clean, flags=re.IGNORECASE)
    return clean

def sanitize_user_prompt(user_text: str) -> str:
    """Sanitizes user input to prevent XML boundary escape attempts."""
    if not user_text:
        return ""
    # Escape XML delimiters to maintain prompt boundary integrity
    escaped = user_text.replace("</transcript_context>", "&lt;/transcript_context&gt;")
    escaped = escaped.replace("<transcript_context>", "&lt;transcript_context&gt;")
    escaped = escaped.replace("</user_query>", "&lt;/user_query&gt;")
    escaped = escaped.replace("<user_query>", "&lt;user_query&gt;")
    return escaped.strip()
