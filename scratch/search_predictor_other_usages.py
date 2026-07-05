with open("backend/predictor.py", "r", encoding="utf-8") as f:
    text = f.read()

# Remove the model blocks to see if there are other references
# Lines 99 to 377 are the model flows
lines = text.splitlines()
other_lines = lines[:98] + lines[377:]
other_text = "\n".join(other_lines)

print("xgb occurrences outside model blocks:", other_text.count("xgb"))
print("tf occurrences outside model blocks:", other_text.count("tf"))
print("Ridge occurrences outside model blocks:", other_text.count("Ridge"))
print("StandardScaler occurrences outside model blocks:", other_text.count("StandardScaler"))
