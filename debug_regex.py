import re

text = "We're evaluating two platforms this week."

patterns = [
    r"evaluat(?:ing|e|ion)\s+(?:.{0,20}\s+)?(?:vendors?|platforms?|solutions?|options?)",
    r"looking\s+at\s+(?:.{0,20}\s+)?(?:vendors?|platforms?|solutions?|options?)",
    r"compar(?:e|ing)\s+(?:.{0,20}\s+)?(?:vendors?|platforms?|solutions?|options?)"
]

print(f"Text: '{text}'")
for i, p in enumerate(patterns):
    match = re.search(p, text)
    print(f"Pattern {i}: {p}")
    print(f"Match: {bool(match)}")
    if match:
        print(f"  -> '{match.group(0)}'")
