"""USB-connected Samsung video uploader. Run with --help for commands."""
import argparse
import datetime as dt
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

YT = "com.google.android.youtube"
FILES = "com.sec.android.app.myfiles"


class Pause(RuntimeError):
    pass


def timestamp(path):
    try:
        stem = Path(path).stem
        if re.fullmatch(r"\d{8}_\d{6}", stem):
            return dt.datetime.strptime(stem, "%Y%m%d_%H%M%S")
    except ValueError:
        pass
    return None


def database(path):
    db = sqlite3.connect(path, timeout=2)
    db.row_factory = sqlite3.Row
    db.execute("""CREATE TABLE IF NOT EXISTS videos (
        device TEXT, path TEXT, size INTEGER, modified INTEGER, day TEXT,
        part INTEGER, title TEXT, state TEXT DEFAULT 'pending',
        PRIMARY KEY(device,path,size,modified))""")
    return db


def inventory(db, device, clips):
    rows = []
    dated = [(timestamp(path), path, size, modified, uri)
             for path, size, modified, uri in clips]
    dated.sort(key=lambda x: (x[0] or dt.datetime.max, x[1]))
    totals = {}
    for stamp, *_ in dated:
        if stamp:
            day = stamp.date().isoformat()
            totals[day] = totals.get(day, 0) + 1
    with db:
        for stamp, path, size, modified, uri in dated:
            key = (device, path, size, modified)
            query = "SELECT rowid,* FROM videos WHERE device=? AND path=? AND size=? AND modified=?"
            row = db.execute(query, key).fetchone()
            if row is None:
                day, part, title = None, None, Path(path).stem
                if stamp:
                    day = stamp.date().isoformat()
                    last = db.execute("SELECT MAX(part) FROM videos WHERE device=? AND day=?",
                                      (device, day)).fetchone()[0]
                    part = (last or 0) + 1
                    title = f"{stamp.strftime('%B')} {stamp.day}, {stamp.year}"
                    if part > 1 or totals[day] > 1:
                        title += f" PART {part}"
                db.execute("INSERT INTO videos VALUES(?,?,?,?,?,?,?,'pending')",
                           (*key, day, part, title))
                row = db.execute(query, key).fetchone()
            rows.append((row, uri))
    return rows


def adb(*args):
    binary = shutil.which("adb") or str(Path(os.getenv("LOCALAPPDATA", ".")) /
                                        "Android/Sdk/platform-tools/adb.exe")
    if not Path(binary).is_file():
        raise Pause("Install Android SDK Platform-Tools and add its folder to PATH.")
    result = subprocess.run([binary, *args], capture_output=True, encoding="utf-8",
                            errors="replace", timeout=45)
    if result.returncode:
        raise Pause(result.stderr.strip() or result.stdout.strip())
    return result.stdout


def connected():
    lines = adb("devices").splitlines()
    devices = [line.split() for line in lines if "\t" in line]
    if len(devices) != 1 or devices[0][1] != "device":
        raise Pause("Connect one unlocked phone and accept its USB debugging prompt.")
    return devices[0][0]


def scan(serial):
    base = "content://media/external/video/media"
    output = adb("-s", serial, "shell", "content", "query", "--uri", base,
                 "--projection", "_id:_size:date_modified:_data")
    clips = []
    for line in output.splitlines():
        if line.strip() == "No result found.":
            continue
        match = re.fullmatch(r"Row: \d+ _id=(\d+), _size=(\d+), date_modified=(\d+), _data=(/.+)", line)
        if not match:
            raise Pause(f"Could not read the phone video list: {line}")
        media_id, size, modified, path = match.groups()
        if not any(component.startswith(".") for component in path.split("/")):
            clips.append((path, int(size), int(modified), f"{base}/{media_id}"))
    return clips


def change(db, row, old, new):
    with db:
        count = db.execute("UPDATE videos SET state=? WHERE rowid=? AND state=?",
                           (new, row, old)).rowcount
        if count != 1:
            raise Pause("Queue entry changed or has an unexpected status. Check preview.")


class Screen:
    def __init__(self, phone):
        self.phone = phone

    def nodes(self):
        root = ET.fromstring(self.phone.dump_hierarchy())
        return [n for n in root.iter("node") if n.get("package") == YT]

    def find(self, labels):
        matches = [n for n in self.nodes() if n.get("enabled") == "true" and
                   any(n.get(field, "").casefold() in labels
                       for field in ("text", "content-desc"))]
        return matches[0] if len(matches) == 1 else None

    def tap(self, labels):
        node = self.find(labels)
        if node is None:
            return False
        bounds = list(map(int, re.findall(r"\d+", node.get("bounds", ""))))
        if len(bounds) != 4:
            raise Pause("Cannot locate the selected YouTube control.")
        x, y, right, bottom = bounds
        self.phone.click((x + right) // 2, (y + bottom) // 2)
        time.sleep(0.7)
        return True

    def title_field(self):
        fields = [n for n in self.nodes() if n.get("class") == "android.widget.EditText"
                  and "title" in " ".join(n.get(k,"") for k in
                  ("resource-id","hint","content-desc","text")).lower()]
        if len(fields) == 1:
            return fields[0]
        return None

    def prepare(self, title):
        for _ in range(12):
            field = self.title_field()
            if field is not None:
                break
            self.tap({"next"})
            time.sleep(0.5)
        else:
            raise Pause("Cannot identify the YouTube title field.")
        selector = {"className": "android.widget.EditText"}
        for attr, key in (("resource-id","resourceId"), ("content-desc","description"), ("text","text")):
            if field.get(attr):
                selector[key] = field.get(attr)
        edit = self.phone(packageName=YT, **selector)
        if edit.count != 1:
            raise Pause("Cannot identify a unique title editor.")
        edit.set_text(title)
        if not self.phone(packageName=YT, className="android.widget.EditText", text=title).exists:
            raise Pause("YouTube did not retain the requested title.")
        if self.find({"unlisted"}) is None:
            if not self.tap({"visibility","public","private","select visibility"}):
                raise Pause("Cannot identify the visibility setting.")
            if not self.tap({"unlisted"}):
                raise Pause("Cannot select Unlisted.")
            if self.find({"unlisted"}) is None:
                raise Pause("Cannot verify Unlisted visibility.")
            if not self.phone(packageName=YT, className="android.widget.EditText", text=title).exists:
                self.phone.press("back")
                time.sleep(0.7)
        if self.find({"unlisted"}) is None:
            raise Pause("Cannot verify visibility on the details screen.")
        kids = {"no, it's not made for kids", "no, it’s not made for kids"}
        if self.find(kids) is None:
            if not (self.tap({"select audience","audience"}) or self.tap({"next"})):
                raise Pause("Cannot open audience settings.")
        if not self.tap(kids):
            raise Pause("Cannot select the audience setting.")
        root = ET.fromstring(self.phone.dump_hierarchy())
        selected = False
        for parent in root.iter("node"):
            children = [parent, *list(parent)]
            label = any(n.get("package") == YT and
                        any(n.get(k,"").casefold() in kids for k in ("text","content-desc"))
                        for n in children)
            controls = [n for n in children if n.get("checkable") == "true"]
            if label and len(controls) == 1 and controls[0].get("checked") == "true":
                selected = True
        if not selected:
            raise Pause("Cannot verify the selected audience.")
        submit = {"upload","upload video","upload short"}
        if self.find(submit) is None:
            self.phone.press("back")
            time.sleep(0.7)
        if self.find(submit) is None:
            raise Pause("Cannot identify the final upload button.")
        return submit


def confirmations(serial, title):
    data = adb("-s", serial, "shell", "dumpsys", "notification", "--noredact")
    active = data.partition("Notification List:")[2].split("  Ranking Config", 1)[0]
    result = set()
    for block in re.split(r"(?m)^\s*NotificationRecord\(", active)[1:]:
        if "pkg=" + YT + " " not in block.splitlines()[0]:
            continue
        values = re.findall(r"android\.(?:title|text)=String \(([^\n]*)\)", block)
        if title in values and any(v.casefold() in {"upload complete","video uploaded","short uploaded",
                                                    "upload completed"} for v in values):
            result.add((block.splitlines()[0], tuple(re.findall(r"postTime=(\d+)", block)), tuple(values)))
    return result


def run(db, serial, rows):
    import uiautomator2
    phone = uiautomator2.connect(serial)
    phone.app_start(FILES)
    videos = phone(packageName=FILES, text="Videos")
    if not videos.wait(timeout=6):
        phone.press("back")
    if not videos.wait(timeout=3):
        raise Pause("Open the My Files home screen with Videos visible, then rerun.")
    videos.click()
    screen = Screen(phone)
    for row, uri in rows:
        if row["state"] == "done":
            continue
        if row["state"] == "review":
            raise Pause(f"Check YouTube for entry {row['rowid']} and resolve its status.")
        title = row["title"]
        print(f"Preparing {row['path']} -> {title}", flush=True)
        adb("-s", serial, "shell", "am", "start", "-W", "-a", "android.intent.action.SEND",
            "-t", "'video/*'", "--eu", "android.intent.extra.STREAM", uri,
            "--grant-read-uri-permission", "-p", YT)
        submit = screen.prepare(title)
        previous = confirmations(serial, title)
        change(db, row["rowid"], "pending", "review")
        if not screen.tap(submit):
            raise Pause("Submit control changed. Check YouTube before retrying.")
        deadline = time.monotonic() + 1800
        while time.monotonic() < deadline:
            if confirmations(serial, title) - previous:
                change(db, row["rowid"], "review", "done")
                print(f"Confirmed {title}", flush=True)
                break
            if any("daily" in n.get("text","").lower() and "limit" in n.get("text","").lower()
                   for n in screen.nodes()):
                raise Pause("Daily upload limit reached. Check this entry before resuming.")
            time.sleep(5)
        else:
            raise Pause(f"No confirmed completion for {title}. Check the upload in YouTube.")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("preview", "upload"):
        sub.add_parser(name)
    resolve = sub.add_parser("resolve")
    resolve.add_argument("entry", type=int)
    resolve.add_argument("result", choices=["done","retry"])
    args = p.parse_args()
    directory = Path(os.getenv("LOCALAPPDATA") or Path.home()) / "PocketUploader"
    directory.mkdir(exist_ok=True)
    import msvcrt
    with (directory / "run.lock").open("a+b") as lock:
        lock.seek(0)
        try:
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            raise Pause("Another Pocket Uploader command is running.") from None
        db = database(directory / "queue.sqlite3")
        if args.command == "resolve":
            change(db, args.entry, "review", "done" if args.result == "done" else "pending")
            return
        serial = connected()
        if args.command == "preview":
            # Plan new titles without reserving numbers until the upload run.
            preview = database(":memory:")
            db.backup(preview)
            db = preview
        rows = inventory(db, serial, scan(serial))
        for row, _ in rows:
            print(f"{row['rowid']:4}  {row['state']:8}  {row['path']} -> {row['title']}")
        print(f"{len(rows)} videos found.")
        if args.command == "upload" and any(r["state"] != "done" for r, _ in rows):
            run(db, serial, rows)


if __name__ == "__main__":
    try:
        main()
    except (Pause, ImportError, OSError, sqlite3.Error, subprocess.SubprocessError) as exc:
        sys.exit(f"Paused: {exc}")

