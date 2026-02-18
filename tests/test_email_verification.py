from server import is_disposable

test_emails = [
    "test@yopmail.com",       # In local blocklist
    "test@temp-mail.org",     # In local blocklist
    "test@gmail.com",         # Valid
    "test@mailinator.com",    # In local blocklist
    "something@0-mail.com",   # In file blocklist
    "randomuser@sharklasers.com", # In hardcoded blocklist
    "test@guerrillamail.com" # In hardcoded blocklist
]

print("Testing email verification...")
for email in test_emails:
    result = is_disposable(email)
    status = "BLOCKED" if result else "ALLOWED"
    print(f"{email}: {status}")
