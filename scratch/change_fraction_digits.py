import re

path = "c:/Users/h1z1a/Desktop/Analyzeio/frontend/src/app/page.js"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace LocaleString formatting
new_content = content.replace("minimumFractionDigits: 2, maximumFractionDigits: 2", "minimumFractionDigits: 3, maximumFractionDigits: 3")
new_content = new_content.replace("minimumFractionDigits: 2", "minimumFractionDigits: 3")
new_content = new_content.replace("maximumFractionDigits: 2", "maximumFractionDigits: 3")

# Replace target price chart formatting for open, close, high, low, ema, bb
# activeHistory[activeHistory.length - 1]?.close?.toLocaleString("en-US", { minimumFractionDigits: 3, maximumFractionDigits: 3 })
# (This is already covered by the replacement above!)

# Replace toFixed(2) in specific price rendering sections:
# e.g., accuracy logs: predVal.toFixed(2) -> predVal.toFixed(3)
new_content = new_content.replace("predVal.toFixed(2)", "predVal.toFixed(3)")
new_content = new_content.replace("actualVal.toFixed(2)", "actualVal.toFixed(3)")

# Write back
with open(path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Updated price formatting in page.js to 3 decimal places.")
