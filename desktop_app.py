import tkinter as tk
import requests

def scan_url():
    url = entry.get()

    if not url:
        result_label.config(text="Enter URL", fg="orange")
        return

    try:
        response = requests.post(
            "http://127.0.0.1:5000/api/predict",
            json={"message": url}
        )

        data = response.json()
        prediction = data["prediction"]
        confidence = data["confidence"]

        color = "red" if prediction == "phishing" else "green"

        result_label.config(
            text=f"{prediction.upper()} ({confidence}%)",
            fg=color
        )

    except:
        result_label.config(text="Server not running", fg="orange")

app = tk.Tk()
app.title("Desktop Phishing Scanner")
app.geometry("400x250")

tk.Label(app, text="Desktop Phishing Scanner", font=("Arial", 14, "bold")).pack(pady=10)
entry = tk.Entry(app, width=40)
entry.pack(pady=10)

tk.Button(app, text="Scan", command=scan_url).pack(pady=10)
result_label = tk.Label(app, text="", font=("Arial", 12, "bold"))
result_label.pack(pady=20)

app.mainloop()