import json
import re


def should_exclude_chunk(chunk: str) -> bool:
    """(references, acknowledgements, etc.)"""
    ref_patterns = [
        r'References\s', r'Bibliography\s', r'Acknowledgements\s',
        r'et al\.\s+\(\d{4}\)', r'\[\d+\]\s+[A-Z][a-z]+,',
        r'^\s*\d+\.\s+[A-Z][a-z]+\s+[A-Z][a-z]+\s+et\s+al\.',
    ]
    for pattern in ref_patterns:
        if re.search(pattern, chunk):
            return True
    citation_count = len(re.findall(r'\[\d+\]|\(\w+ et al\.,? \d{4}\)|\([A-Za-z]+, \d{4}\)', chunk))
    text_length = len(chunk)
    if citation_count > 3 and (citation_count * 10 / text_length) > 0.2:
        return True
    return False

def clean_json_response(content: str) -> str:
    """Clean and parse JSON from API response"""
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.replace(",]", "]").replace(",}", "}")
    if not (content.startswith("[") and content.endswith("]")):
        if content.startswith("{") and content.endswith("}"):
            content = f"[{content}]"
        elif "{" in content and "}" in content:
            parts = []
            depth = 0
            start = -1
            for i, char in enumerate(content):
                if char == '{':
                    if depth == 0:
                        start = i
                    depth += 1
                elif char == '}':
                    depth -= 1
                    if depth == 0 and start != -1:
                        parts.append(content[start:i+1])
                        start = -1
            if parts:
                content = f"[{','.join(parts)}]"
    return content

def save_to_json(items: list, output_file: str):
    """Save items in JSON format"""
    if not items:
        print("❌ No items to save")
        return
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=4)
    print(f"✅ {len(items)} items saved to {output_file}")