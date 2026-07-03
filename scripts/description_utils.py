"""
Post-processing for AI-generated descriptions.
Removes * and empty lines, adds retry for empty responses.
"""

def clean_description(content: str) -> str:
    """Clean AI-generated description: remove *, remove empty lines."""
    if not content:
        return content
    content = content.replace('*', '')
    lines = [line for line in content.split('\n') if line.strip()]
    return '\n'.join(lines)


def is_description_valid(content: str, min_length: int = 50) -> bool:
    """Check if description is valid (non-empty, minimum length)."""
    if not content:
        return False
    cleaned = clean_description(content)
    return len(cleaned) >= min_length
