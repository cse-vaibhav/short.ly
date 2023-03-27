from flask import Flask, render_template, request, abort, redirect

app = Flask(__name__)
# app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.sqlite3"
# app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

urls = {}
_id = 1


def shorten(url: str) -> str:
    global _id
    _id += 1
    return f"{_id - 1}"


@app.route("/<string:_id>")
def goto_url(_id):
    original_url: str = urls.get(_id, None)
    if not original_url:
        abort(404)
    else:
        return redirect("https://" + original_url)


@app.route("/", methods=["GET", "POST"])
def index():
    url = request.form.get("url", None)
    print("URL: ", url)

    # Add to database
    if url:
        short_url = shorten(url)
        urls[short_url] = url

    return render_template("index.html")


@app.get("/display")
def display():
    global urls
    return render_template("display.html", urls=urls.items())


if __name__ == "__main__":
    app.run(debug=True)
