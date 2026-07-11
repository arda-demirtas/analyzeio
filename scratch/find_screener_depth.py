with open('frontend/src/app/page.js', 'r', encoding='utf-8') as f:
    content = f.read()

start_idx = content.find('{showScreener ? (')
if start_idx == -1:
    print("Not found")
    exit()

print(f"Start index: {start_idx}, Line: {content[:start_idx].count('\n') + 1}")

# We will trace brace depth
depth = 0
for i in range(start_idx, len(content)):
    char = content[i]
    if char == '{':
        depth += 1
    elif char == '}':
        depth -= 1
        if depth == 1:
            line_num = content[:i].count('\n') + 1
            print(f"Depth 1 brace at char {i}, line {line_num}:")
            print(content[i-50:i+50])
            print("-" * 40)
        elif depth == 0:
            line_num = content[:i].count('\n') + 1
            print(f"Depth 0 brace at char {i}, line {line_num}:")
            print(content[i-100:i+100])
            print("=" * 40)
            break
