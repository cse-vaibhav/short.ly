from flask import Flask, render_template, request, abort, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from typing import Optional, Dict, List, Tuple
import clipboard as clip
import os

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = "sqlite:///" + os.path.join(basedir, "users.sqlite3")

# App Configurations
app.secret_key = "32flkf98379ry2ksc38fy"
app.config["SQLALCHEMY_DATABASE_URI"] = db_path
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Flask-Sqlite3 Database Integration
db = SQLAlchemy(app)
Migrate(app, db)


# App Config and settings
class Config(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True)
    _property = db.Column("property", db.String())
    value = db.Column("value", db.String)

    def __init__(self, property: str, value: str):
        self._property = property
        self.value = value

    def __repr__(self):
        return f"{self._property}: {self.value}"


# URLs Table Model
class URL(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True)
    original_url = db.Column(db.String())
    short_url = db.Column(db.String(8), unique=True)

    def __init__(self, original, short) -> None:
        self.original_url = original
        self.short_url = short

    def __repr__(self) -> str:
        return f"{self.original_url} - {self.short_url}"

    def get_tuple(self):
        return (self.original_url, self.short_url)


# URL Handler
class URLShortener:
    url_db: Dict[str, str] = {}

    def __init__(self, host_name: str, port: int, database) -> None:
        self.hostname = host_name
        self.port = port
        self.base_url = f"http://{self.hostname}:{self.port}/"
        self.db = database
        # self.setid()

    def getID(self) -> int:
        value: int = 0
        try:
            counter = Config.query.filter_by(_property="id_count").first()
            if not counter:
                counter = Config(property="id_count", value="10000000")
                self.db.session.add(counter)

            value = int(counter.value) + 1
            counter.value = f"{value}"
            self.db.session.commit()
            return value
        except Exception as e:
            print("ERROR", e)
            pass
        return 0

    def getURLS(self) -> List[Tuple[str, str]]:
        # urls = list(self.url_db.items())
        all_items = URL.query.all()
        all_items = list(map(lambda x: x.get_tuple(), all_items))
        print("URLS", all_items)
        return all_items

    def shorten_url(self, original_url: str) -> str:
        _id: str = ""
        # Filter by original_url
        filter_items = URL.query.filter_by(original_url=original_url).all()

        print("Filter Items: ", filter_items)
        # Generate and add if not exists

        if not filter_items:
            _id = self.encode(self.getID())

            # create a url object
            url = URL(original=original_url, short=_id)

            # add it to the database session
            try:
                self.db.session.add(url)
                self.db.session.commit()
            except Exception as e:
                print("Original: ", original_url)
                print("ID: ", _id)
                print(e)
                self.db.session.rollback()
            print(_id)
        else:
            _id = filter_items[0].short_url

        # Old code
        # if original_url in self.url_db:
        #     _id: str = self.url_db[original_url]

        # else:
        #     _id = self.encode(self._id)
        #     self.url_db[original_url] = _id
        #     URLShortener._id += 1

        return self.base_url + _id

    def encode(self, _id: int) -> str:
        characters: str = (
            "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        )
        base: int = len(characters)

        ret: List[str] = []
        while _id > 0:
            val = _id % base
            ret.append(characters[val])
            _id = _id // base

        return "".join(ret[::-1])

    def get_original_url(self, _id: str) -> Optional[str]:
        filter_items = URL.query.filter_by(short_url=_id).all()
        if not filter_items:
            return None

        return filter_items[0].original_url

        # OLD Code
        # if _id not in self.url_db.values():
        #     return None

        # original_url = list(filter(lambda x: x[1] == _id, self.url_db.items()))[0][0]
        return original_url

    def delete_url(self, short_url: Optional[str]) -> None:
        item = URL.query.filter_by(short_url=short_url).all()

        if not item:
            return None

        item = item[0]

        print("ITEM: ", item)

        try:
            self.db.session.delete(item)
            self.db.session.commit()
        except Exception as e:
            print("EROR", e)
            self.db.session.rollback()


# URL and Database Handler
shortener = URLShortener(host_name="localhost", port=5000, database=db)


def add_protocol(url: Optional[str]):
    if not url:
        return None

    if not any(
        [url.startswith("ftp"), url.startswith("http"), url.startswith("https")]
    ):
        return "http://" + url
    return url


@app.route("/<string:_id>", methods=["GET", "POST"])
def goto_url(_id: str):
    """
    Redirect to the URL with the '_id'
    """

    original_url: Optional[str] = shortener.get_original_url(_id)
    original_url = add_protocol(original_url)
    if not original_url:
        return redirect(url_for("index"))
    else:
        return redirect(original_url)


# Home Page
@app.route("/", methods=["GET", "POST"])
def index():
    url = request.form.get("url", None)

    # Add to database
    short_url: str = ""
    copied = False  # Flag to check if copied to show a message
    if url:
        short_url = shortener.shorten_url(url)
        clip.copy(short_url)
        copied = True

    params = {"url": short_url, "copied": copied}
    return render_template("index.html", **params)


@app.route("/delete", methods=["POST"])
def deleteEntry():
    url = request.form.get("url", None)
    short_url = request.form.get("short_url", None)

    print(url, short_url)

    # TODO: Delete the entry
    shortener.delete_url(short_url)
    return redirect(url_for("display"))


@app.get("/display")
def display():
    global shortener
    urls = shortener.getURLS()

    params = {"base_url": shortener.base_url, "urls": urls}
    return render_template("display.html", **params)


if __name__ == "__main__":
    app.run(debug=True)
