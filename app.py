from flask import Flask, request, render_template_string, jsonify
import sqlite3
import csv
import re

app = Flask(__name__)

# -----------------------------
# DATABASE
# -----------------------------
def init_db():
    conn = sqlite3.connect('phishing.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            label TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# -----------------------------
# DETECTION LOGIC
# -----------------------------
def predict_url(url):
    url = url.lower()
    phishing_indicators = [
        r'@', r'//.*//', r'http[s]?://\d', r'login', r'confirm',
        r'update', r'free', r'bit\.ly|tinyurl', r'-',
    ]
    score = 0
    for pattern in phishing_indicators:
        if re.search(pattern, url):
            score += 1
    if score >= 2:
        return 'phishing', min(60 + score * 10, 99)
    return 'safe', 85

# -----------------------------
# DATABASE FUNCTIONS
# -----------------------------
def save_url(url, label):
    conn = sqlite3.connect('phishing.db')
    c = conn.cursor()
    c.execute('INSERT INTO urls (url, label) VALUES (?, ?)', (url, label))
    conn.commit()
    conn.close()

def get_all_urls():
    conn = sqlite3.connect('phishing.db')
    c = conn.cursor()
    c.execute('SELECT url, label FROM urls ORDER BY id DESC')
    data = c.fetchall()
    conn.close()
    return data

def get_stats():
    conn = sqlite3.connect('phishing.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM urls WHERE label="safe"')
    safe_count = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM urls WHERE label="phishing"')
    phishing_count = c.fetchone()[0]
    conn.close()
    return safe_count, phishing_count

# -----------------------------
# FILE HANDLING
# -----------------------------
def save_to_file(url, label, filename="urls.txt"):
    with open(filename, "a") as f:
        f.write(f"{url},{label}\n")

def export_to_csv(filename="exported_urls.csv"):
    urls = get_all_urls()
    with open(filename, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["URL", "Label"])
        writer.writerows(urls)

# -----------------------------
# API FOR TKINTER
# -----------------------------
@app.route("/api/predict", methods=["POST"])
def api_predict():
    data = request.get_json()
    url = data.get("message")

    label, confidence = predict_url(url)
    save_url(url, label)
    save_to_file(url, label)

    return jsonify({
        "prediction": label,
        "confidence": confidence
    })

# -----------------------------
# WEB DASHBOARD
# -----------------------------
@app.route('/')
def home():
    urls = get_all_urls()
    safe_count, phishing_count = get_stats()

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<title>Phishing Detection Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body {font-family:Arial;background:linear-gradient(135deg,#74ebd5,#ACB6E5);margin:0;padding:0;}
.container {width:90%;max-width:900px;margin:40px auto;background:white;padding:30px;border-radius:15px;box-shadow:0 10px 30px rgba(0,0,0,0.2);}
h1{text-align:center;}
form{display:flex;justify-content:center;margin-bottom:20px;}
input{padding:10px;width:60%;border-radius:8px;border:1px solid #ccc;margin-right:10px;}
button{padding:10px 20px;border:none;background:#007bff;color:white;border-radius:8px;cursor:pointer;}
button:hover{background:#0056b3;}
.safe{color:green;font-weight:bold;}
.phishing{color:red;font-weight:bold;}
</style>
</head>
<body>
<div class="container">
<h1>Phishing Detection Dashboard</h1>
<form method="POST" action="/check">
<input name="url" placeholder="Enter URL" required>
<button type="submit">Check</button>
</form>

<h3>History</h3>
<ul>
{% for url,label in urls %}
<li>{{url}} → <span class="{{label}}">{{label}}</span></li>
{% endfor %}
</ul>

<canvas id="chart"></canvas>

</div>

<script>
new Chart(document.getElementById('chart'),{
type:'doughnut',
data:{labels:['Safe','Phishing'],
datasets:[{data:[{{safe_count}},{{phishing_count}}],
backgroundColor:['green','red']}]}
});
</script>
</body>
</html>
""", urls=urls, safe_count=safe_count, phishing_count=phishing_count)

@app.route('/check', methods=['POST'])
def check():
    url = request.form['url']
    label, confidence = predict_url(url)
    save_url(url, label)
    save_to_file(url, label)
    return home()

@app.route('/export')
def export():
    export_to_csv()
    return "Exported to CSV"

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)