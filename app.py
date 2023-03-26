from flask import Flask, render_template, request

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    print(request.form.get("url", "No URL"))
    return render_template("index.html")
