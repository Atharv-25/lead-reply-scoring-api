import urllib.request
import ssl
import json

print(f"Python SSL version: {ssl.OPENSSL_VERSION}")

url = "https://disposable.debounce.io/?email=test@temp-mail.org"
print(f"Testing URL: {url}")

try:
    with urllib.request.urlopen(url, timeout=5) as response:
        print(f"Status: {response.status}")
        content = response.read().decode()
        print(f"Response: {content}")
        data = json.loads(content)
        print(f"Is disposable? {data.get('disposable')}")
except Exception as e:
    print(f"ERROR: {e}")
    if "CERTIFICATE_VERIFY_FAILED" in str(e):
        print("\n>>> DETECTED SSL CERTIFICATE ISSUE <<<")
        print("This is common on macOS. Run '/Applications/Python 3.x/Install Certificates.command'")
