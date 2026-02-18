# Lead Verification Gate

A self-contained Python Flask application that verifies email leads with OTPs and checks for disposable email addresses before saving them to Google Sheets.

## 📂 Project Structure

- `server.py`: The main Flask backend.
- `public/`: Frontend HTML/CSS/JS.
- `credentials.json`: Your Google Service Account key.
- `requirements.txt`: List of Python libraries needed.

## 🚀 How to Run

1.  **Open Terminal** in this folder.
2.  **Create Virtual Environment** (Only need to do this once):
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
3.  **Start Server**:
    ```bash
    # Ensure venv is active (type: source venv/bin/activate)
    python server.py
    ```
4.  **Open Browser**: [http://localhost:8080](http://localhost:8080)

## 📊 Google Sheets
Data is saved to Spreadsheet ID: `1SNxX0k2lO4gWmxJHokM5AT1edjr16SvaRzZpfI0mfCk`
Ensure `credentials.json` shares access with this sheet!
