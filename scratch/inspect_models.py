with open("backend/models.py", "r", encoding="utf-8") as f:
    content = f.read()

import re
matches = re.findall(r"class\s+(\w+)", content)
print("Classes in backend/models.py:")
for m in matches:
    print(f"  {m}")
