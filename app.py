import os
from datetime import datetime
from flask import Flask, render_template_string

app = Flask(__name__)

# Record start time for uptime calculation
START_TIME = datetime.now()
REQUEST_COUNT = 0

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hello! | {{ app_name }}</title>
    <style>
        body {
            margin: 0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: "Trebuchet MS", "Segoe UI", sans-serif;
            background: #e3f1e0;
            color: #2f5233;
            text-align: center;
        }
        .card {
            background: #f6fbf4;
            padding: 2.5rem 3rem;
            border: 2px solid #a8d5a2;
            border-radius: 1.5rem;
        }
        h1 { margin: 0 0 0.5rem; }
        p { margin: 0.25rem 0; }
    </style>
</head>
<body>
    <div class="card">
        <h1>Hello, World! 🌱</h1>
    </div>
</body>
</html>
"""

@app.route("/")
def home():
    global REQUEST_COUNT
    REQUEST_COUNT += 1

    return render_template_string(
        HTML_TEMPLATE,
        app_name="Flask Cloud Node",
        request_count=REQUEST_COUNT
    )

# Task 3 Requirement: Health check endpoint
@app.route("/api/health")
def health():
    return {
        "status": "ok",
        "uptime_seconds": int((datetime.now() - START_TIME).total_seconds()),
        "requests_served": REQUEST_COUNT
    }, 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="127.0.0.1", port=port, debug=True)