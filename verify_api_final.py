from server import is_disposable

print("Testing Abstract API Integration (Post-Network Fix)...")

# Test Case 1: Valid Email
email_good = "atharvtotawar@gmail.com"
print(f"\nScanning Good Email: {email_good}")
is_bad = is_disposable(email_good)
print(f"Result: {'BLOCKED' if is_bad else 'ALLOWED'} (Expected: ALLOWED)")

# Test Case 2: Disposable Email
email_bad = "test@temp-mail.org"
print(f"\nScanning Bad Email: {email_bad}")
is_bad2 = is_disposable(email_bad)
print(f"Result: {'BLOCKED' if is_bad2 else 'ALLOWED'} (Expected: BLOCKED)")
