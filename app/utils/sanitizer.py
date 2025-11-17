"""
HTML Sanitizer per contenuto rich text.

Usa bleach per sanitizzare HTML proveniente da editor rich text (TipTap)
e prevenire attacchi XSS attraverso contenuto utente.
"""
import bleach
from bleach.css_sanitizer import CSSSanitizer


# Tag HTML permessi nel contenuto rich text
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 's', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'blockquote', 'code', 'pre', 'a', 'img'
]

# Attributi permessi per i tag
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target', 'rel'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
    '*': ['class', 'id']  # Attributi globali
}

# Protocolli permessi per href e src
ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']

# CSS permessi (per style inline se necessario)
css_sanitizer = CSSSanitizer(allowed_css_properties=['color', 'background-color', 'text-align'])


def sanitize_html(html_content: str) -> str:
    """
    Sanitizza contenuto HTML per prevenire XSS.
    
    Rimuove script, event handlers e altri contenuti pericolosi,
    mantenendo solo tag e attributi sicuri per rich text.
    
    Args:
        html_content: Contenuto HTML da sanitizzare (può essere None o vuoto)
    
    Returns:
        str: HTML sanitizzato e sicuro
    
    Example:
        >>> sanitize_html('<p>Safe content</p><script>alert("XSS")</script>')
        '<p>Safe content</p>'
        
        >>> sanitize_html('<a href="javascript:alert(1)">Link</a>')
        '<a>Link</a>'  # href pericoloso rimosso
    """
    if not html_content:
        return ""
    
    # Sanitizza HTML usando bleach
    sanitized = bleach.clean(
        html_content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        css_sanitizer=css_sanitizer,
        strip=True  # Rimuove tag non permessi invece di escape
    )
    
    return sanitized


def sanitize_text(text_content: str) -> str:
    """
    Sanitizza testo semplice rimuovendo caratteri pericolosi.
    
    Utile per campi testo che non dovrebbero contenere HTML.
    
    Args:
        text_content: Testo da sanitizzare
    
    Returns:
        str: Testo sanitizzato
    """
    if not text_content:
        return ""
    
    # Rimuove HTML completamente e escape caratteri speciali
    return bleach.clean(text_content, tags=[], strip=True)

