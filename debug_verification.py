import server
import sys

print(f"Loaded {len(server.LOCAL_BLOCKLIST)} domains in blocklist.")

test_emails = [
    "test@temp-mail.org",       # Explicitly in list
    "test@10minutemail.com",    # Explicitly in list
    "test@gmail.com",           # Should be allowed
    "test@sub.temp-mail.org",   # Subdomain check - might fail if exact match only
    "test@0-mail.com",          # From file (line 1)
    "test@TEMP-MAIL.ORG",       # Case check
]

print("\n--- Testing Emails ---")
for email in test_emails:
    try:
        # We need to simulate the environment or mock attributes if needed, 
        # but is_disposable seems substantial enough to run.
        result = server.is_disposable(email)
        print(f"Email: {email:30} | Blocked: {result}")
    except Exception as e:
        print(f"Error testing {email}: {e}")
