import re

def search_in_file(filepath, pattern_str):
    pattern = re.compile(pattern_str, re.IGNORECASE)
    matches = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f):
            if pattern.search(line):
                matches.append((idx + 1, line.strip()))
    return matches

files = {
    "translations.js": r"c:\Users\h1z1a\Desktop\Analyzeio\frontend\src\app\translations.js",
    "page.js": r"c:\Users\h1z1a\Desktop\Analyzeio\frontend\src\app\page.js"
}

keywords = ["consensus", "konsens", "tavsiye", "mock", "disclaimer", "yasal uyarı"]

for name, path in files.items():
    print(f"\n================= SEARCHING IN {name} =================")
    for kw in keywords:
        matches = search_in_file(path, kw)
        if matches:
            print(f"Keyword: '{kw}' -> Found {len(matches)} occurrences. Showing up to 5:")
            for line_no, content in matches[:5]:
                print(f"  L{line_no}: {content[:120]}")
