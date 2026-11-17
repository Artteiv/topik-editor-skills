#!/usr/bin/env python3
"""Command-line client of the TOPIK exam API for the topik-exam-upload skill.

Python 3.10+, standard library only. Reads TOPIK_API_URL and TOPIK_API_TOKEN
from the environment; never prints the token.

Every call that writes (POST, PUT, PATCH, DELETE) is appended to the file in
TOPIK_UPLOAD_LOG (method, path, status, no body), so the exam folder keeps a
trace of what the agent did even when the agent forgets to write it down.

Run `python3 topik.py -h` for the commands. Output is JSON on stdout; errors
go to stderr with the API's message, exit code 1.
"""

import argparse
import datetime as dt
import difflib
import json
import mimetypes
import os
import re
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

AREA = {"listening": "듣기", "writing": "쓰기", "reading": "읽기"}
SKILL = {v: k for k, v in AREA.items()}
MARKS = "①②③④"


# ---------------------------------------------------------------- HTTP

def base() -> str:
    url = os.environ.get("TOPIK_API_URL", "").rstrip("/")
    if not url or not os.environ.get("TOPIK_API_TOKEN"):
        sys.exit("TOPIK_API_URL and TOPIK_API_TOKEN must be set")
    return url


def log_write(method: str, path: str, status) -> None:
    target = os.environ.get("TOPIK_UPLOAD_LOG")
    if not target or method == "GET":
        return
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(target, "a", encoding="utf-8") as f:
        f.write(f"- {stamp} `{method} {path}` → {status}\n")


def request(method: str, path: str, body=None, raw: bytes | None = None,
            content_type: str | None = None, auth: bool = True,
            want_bytes: bool = False):
    url = path if path.startswith("http") else base() + path
    headers = {}
    if auth:
        headers["Authorization"] = "Bearer " + os.environ["TOPIK_API_TOKEN"]
    data = raw
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode()
        headers["Content-Type"] = "application/json"
    elif content_type:
        headers["Content-Type"] = content_type
    for attempt in range(5):
        req = urllib.request.Request(url, data=data, headers=headers,
                                     method=method)
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                payload = r.read()
                log_write(method, path, r.status)
                if want_bytes:
                    return payload
                return json.loads(payload) if payload else None
        except urllib.error.HTTPError as e:
            text = e.read().decode("utf-8", "replace")
            if e.code == 429 and attempt < 4:
                wait = int(e.headers.get("Retry-After") or 30)
                print(f"429, waiting {wait}s", file=sys.stderr)
                time.sleep(wait)
                continue
            if e.code >= 500 and attempt < 2:
                time.sleep(5)
                continue
            log_write(method, path, e.code)
            print(f"{method} {path} -> {e.code}: {text[:2000]}",
                  file=sys.stderr)
            sys.exit(1)
        except urllib.error.URLError as e:
            if attempt < 2:
                time.sleep(5)
                continue
            sys.exit(f"{method} {path}: {e.reason}")


def data(resp):
    return resp.get("data", resp) if isinstance(resp, dict) else resp


def out(value) -> None:
    json.dump(value, sys.stdout, ensure_ascii=False, indent=1)
    print()


# ---------------------------------------------------------------- exam text

def picture_text(media) -> str | None:
    return (media or {}).get("text") or None


def question_text(q: dict) -> str:
    """The question as a reader meets it on the page, one block of text."""
    g = q.get("group") or {}
    parts = [g.get("instruction"), g.get("example"), g.get("passageText"),
             picture_text(g.get("imageMedia")), q.get("passageText"),
             picture_text(q.get("imageMedia")), q.get("givenSentence"),
             *(q.get("labeledItems") or []), q.get("prompt")]
    for o in sorted(q.get("options") or [], key=lambda o: o["position"]):
        text = o.get("text") or picture_text(o.get("media")) or ""
        parts.append(f"{MARKS[o['position'] - 1]} {text}")
    return "\n".join(p for p in parts if p)


def exam_questions(exam: dict) -> list[dict]:
    rows = []
    for section in exam["sections"]:
        for item in sorted(section["items"], key=lambda i: i["order"]):
            q = item.get("question")
            if not q:
                continue
            g = q.get("group") or {}
            rows.append({
                "area": AREA[section["skill"]],
                "number": item["order"],
                "question_id": q["id"],
                "group_id": q.get("groupId"),
                "pages": [g.get("sourcePageFrom"), g.get("sourcePageTo")],
                "status": q.get("status"),
                "text": question_text(q),
            })
    return rows


def norm(text: str | None) -> str:
    """Words only: no whitespace, punctuation, option marks, markup, points."""
    t = text or ""
    t = re.sub(r"</?(u|b|i|strong|em)>", "", t).replace("**", "")
    t = re.sub(r"\((각\s*)?\d+\s*점\)", "", t)
    t = re.sub(r"^\s*※?\s*\[\d+\s*[~～∼]\s*\d+\]", "", t)
    t = re.sub(r"[①②③④]|<?보기>?|〈보기〉", "", t)
    return re.sub(r"[^\w㉠㉡㉢㉣()%~]", "", t)


def underlined(text: str | None) -> list[str]:
    return sorted(norm(s) for s in re.findall(r"<u>(.*?)</u>", text or "", re.S)
                  if norm(s))


def differences(a: str, b: str, context: int = 8) -> list[dict]:
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    return [{"exam": a[max(0, i1 - context):i2 + context],
             "transcript": b[max(0, j1 - context):j2 + context]}
            for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag != "equal"]


# ---------------------------------------------------------------- commands

def cmd_whoami(a):
    out(data(request("GET", "/v1/auth/me")))


def cmd_find_exam(a):
    resp = request("GET", "/v1/admin/exams?per=50&q="
                   + urllib.request.quote(a.title))
    out([{k: e[k] for k in ("id", "title", "type", "status")}
         for e in data(resp)])


def cmd_create_exam(a):
    e = data(request("POST", "/v1/admin/exams",
                     {"title": a.title, "type": a.type}))
    out({"id": e["id"], "title": e["title"],
         "sections": [{"id": s["id"], "skill": s["skill"]}
                      for s in e.get("sections") or []]})


def cmd_upload(a):
    path = Path(a.file)
    boundary = uuid.uuid4().hex
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
            f"filename=\"{path.name}\"\r\nContent-Type: {mime}\r\n\r\n"
            ).encode() + path.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    m = data(request("POST", "/v1/media", raw=body,
                     content_type=f"multipart/form-data; boundary={boundary}"))
    out({"id": m["id"], "kind": m["kind"], "originalName": m["originalName"],
         "size": m.get("size")})


def cmd_import(a):
    files = []
    for role, media in (("booklet", a.booklet), ("solution", a.solution),
                        ("answer_key", a.answer_key), ("script", a.script)):
        if media:
            files.append({"role": role, "mediaId": media})
    if a.json:
        files.append({"role": a.json_role, "result": json.load(open(a.json)),
                      "formatVersion": a.format_version})
    if not files:
        sys.exit("give at least one file")
    out(data(request("POST", f"/v1/admin/exams/{a.exam}/imports",
                     {"files": files})))


def job_summary(j: dict) -> dict:
    return {
        "id": j["id"], "status": j["status"], "error": j["error"],
        "files": [(f["role"], f["contentSource"], f["originalName"])
                  for f in j["files"]],
        "reads": [{k: r[k] for k in ("role", "readNo", "mode", "status",
                                     "expectedQuestions", "doneQuestions",
                                     "error", "report")}
                  for r in j["reads"]],
        "summary": j["summary"],
        "openFlags": sum(f["count"] for f in j.get("openFlags") or []),
    }


def cmd_job(a):
    while True:
        j = data(request("GET", f"/v1/admin/exams/{a.exam}/imports/latest"))
        if not j:
            sys.exit("no import yet")
        if not a.wait or j["status"] not in ("queued", "running"):
            break
        done = [(r["role"], r["readNo"], r["doneQuestions"]) for r in j["reads"]]
        print(f"{j['status']} {done}", file=sys.stderr)
        time.sleep(20)
    out(job_summary(j))


def listening_section(exam_id: str) -> str:
    e = data(request("GET", f"/v1/admin/exams/{exam_id}"))
    return next(s["id"] for s in e["sections"] if s["skill"] == "listening")


def cmd_set_audio(a):
    section = listening_section(a.exam)
    request("PUT", f"/v1/admin/exams/{a.exam}/sections/{section}/audio",
            {"audioMediaId": a.media})
    out({"section": section, "audioMediaId": a.media})


def cmd_audio_marks(a):
    section = listening_section(a.exam)
    d = data(request("GET",
                     f"/v1/admin/exams/{a.exam}/sections/{section}/audio-marks"))
    units = d.get("units", d) if isinstance(d, dict) else d
    out([{k: u.get(k) for k in ("from", "to", "startMs", "endMs", "status",
                                "reasons")} for u in units])


def cmd_pages(a):
    count = data(request("GET", f"/v1/media/{a.media}/pages"))
    total = count.get("pages") if isinstance(count, dict) else count
    first, last = a.first or 1, a.last or total
    folder = Path(a.out)
    folder.mkdir(parents=True, exist_ok=True)
    saved = []
    for n in range(first, last + 1):
        target = folder / f"page-{n:02d}.png"
        if not target.exists():
            target.write_bytes(request("GET", f"/v1/media/{a.media}/pages/{n}",
                                       want_bytes=True))
        saved.append(str(target))
    out({"pages": total, "saved": saved})


def cmd_exam(a):
    e = data(request("GET", f"/v1/admin/exams/{a.exam}"))
    Path(a.out).write_text(json.dumps(e, ensure_ascii=False, indent=1))
    out({"saved": a.out, "title": e["title"], "status": e["status"],
         "sections": [{"skill": s["skill"], "id": s["id"],
                       "questions": len(s["items"]),
                       "audioMediaId": s.get("audioMediaId")}
                      for s in e["sections"]]})


def load_exam(source: str) -> dict:
    if Path(source).exists():
        return data(json.loads(Path(source).read_text()))
    return data(request("GET", f"/v1/admin/exams/{source}"))


def cmd_text(a):
    rows = exam_questions(load_exam(a.exam))
    if a.area:
        rows = [r for r in rows if r["area"] == a.area]
    if a.numbers:
        lo, hi = map(int, a.numbers.split("-"))
        rows = [r for r in rows if lo <= r["number"] <= hi]
    out(rows)


def cmd_diff(a):
    exam = {(r["area"], r["number"]): r for r in exam_questions(load_exam(a.exam))}
    got = json.loads(Path(a.transcript).read_text())["questions"]
    report, seen = [], set()
    for q in got:
        key = (q["area"], q["number"])
        seen.add(key)
        r = exam.get(key)
        if r is None:
            report.append({"area": key[0], "number": key[1],
                           "problem": "not in the exam"})
            continue
        diffs = differences(norm(r["text"]), norm(q["text"]))
        ul_exam, ul_got = underlined(r["text"]), underlined(q["text"])
        if diffs or ul_exam != ul_got:
            item = {"area": key[0], "number": key[1],
                    "question_id": r["question_id"], "group_id": r["group_id"],
                    "pages": r["pages"], "differences": diffs}
            if ul_exam != ul_got:
                item["underline"] = {"exam": ul_exam, "transcript": ul_got}
            report.append(item)
    out({"compared": len(got), "with_difference": len(report),
         "items": report})


def cmd_flags(a):
    flags = data(request("GET", f"/v1/admin/exams/{a.exam}/flags"))
    out([{k: f.get(k) for k in ("id", "code", "number", "field", "message",
                                "groupId", "questionId", "suggestion")}
         for f in flags])


def cmd_resolve(a):
    out(data(request("POST", f"/v1/admin/exams/{a.exam}/flags/{a.flag}/resolve",
                     {"resolution": a.resolution})))


def cmd_save_group(a):
    body = json.loads(Path(a.body).read_text())
    out(data(request("PUT", f"/v1/admin/exams/{a.exam}/groups/{a.group}", body)))


def cmd_image_text(a):
    out(data(request("PATCH",
                     f"/v1/admin/exams/{a.exam}/groups/{a.group}/images/{a.media}",
                     {"text": Path(a.text_file).read_text().strip() or None})))


def cmd_confirm(a):
    out(data(request("POST",
                     f"/v1/admin/exams/{a.exam}/groups/{a.group}/confirm", {})))


def cmd_checklist(a):
    out(data(request("GET", f"/v1/admin/exams/{a.exam}/checklist")))


def cmd_answers(a):
    e = load_exam(a.exam)
    out({s["skill"]: {str(i["order"]): (i.get("question") or {}).get("correctOption")
                      for i in sorted(s["items"], key=lambda i: i["order"])}
         for s in e["sections"]})


def cmd_writing_guide(a):
    path = f"/v1/admin/questions/{a.question}/writing-guide"
    if a.body:
        out(data(request("PUT", path, json.loads(Path(a.body).read_text()))))
    else:
        out(data(request("GET", path)))


def cmd_call(a):
    body = json.loads(Path(a.body).read_text()) if a.body else None
    out(data(request(a.method.upper(), a.path, body)))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    def add(name, fn, help_, *args):
        sp = sub.add_parser(name, help=help_)
        for arg in args:
            sp.add_argument(*arg[0], **arg[1])
        sp.set_defaults(fn=fn)

    E = (["exam"], {"help": "exam id"})
    add("whoami", cmd_whoami, "check the token: role must be editor")
    add("find-exam", cmd_find_exam, "exams whose title contains TITLE",
        (["title"], {}))
    add("create-exam", cmd_create_exam, "create a draft exam",
        (["title"], {}), (["--type"], {"default": "topik_2",
                                       "choices": ["topik_1", "topik_2"]}))
    add("upload", cmd_upload, "upload a file (pdf, mp3, png…), print media id",
        (["file"], {}))
    add("import", cmd_import, "send files to the exam import", E,
        (["--booklet"], {"help": "exam booklet PDF media id"}),
        (["--solution"], {"help": "answer/transcript/explanation PDF media id"}),
        (["--answer-key"], {"help": "answer key PDF media id"}),
        (["--script"], {"help": "listening script PDF media id"}),
        (["--json"], {"help": "JSON result file instead of a PDF"}),
        (["--json-role"], {"default": "answer_key"}),
        (["--format-version"], {"default": "key-v1"}))
    add("job", cmd_job, "latest import job of the exam", E,
        (["--wait"], {"action": "store_true",
                      "help": "poll until it is no longer queued or running"}))
    add("set-audio", cmd_set_audio, "attach the listening audio", E,
        (["media"], {}))
    add("audio-marks", cmd_audio_marks, "audio marks of the listening units", E)
    add("pages", cmd_pages, "save PDF pages as PNG", (["media"], {}),
        (["--first"], {"type": int}), (["--last"], {"type": int}),
        (["--out"], {"default": "pages"}))
    add("exam", cmd_exam, "save the whole exam JSON", E,
        (["--out"], {"default": "exam.json"}))
    add("text", cmd_text, "questions as text blocks (exam id or saved JSON)", E,
        (["--area"], {"choices": list(SKILL)}),
        (["--numbers"], {"help": "e.g. 1-20"}))
    add("diff", cmd_diff, "compare a blind transcript with the exam", E,
        (["transcript"], {}))
    add("flags", cmd_flags, "open review flags", E)
    add("resolve", cmd_resolve, "resolve a flag", E, (["flag"], {}),
        (["resolution"], {"choices": ["applied", "kept", "dismissed"]}))
    add("save-group", cmd_save_group, "PUT a group and its changed questions", E,
        (["group"], {}), (["body"], {"help": "JSON file"}))
    add("image-text", cmd_image_text, "set the text printed in a picture", E,
        (["group"], {}), (["media"], {}), (["text_file"], {}))
    add("confirm", cmd_confirm, "confirm a group", E, (["group"], {}))
    add("checklist", cmd_checklist, "what still blocks publishing", E)
    add("answers", cmd_answers, "correct option of every question", E)
    add("writing-guide", cmd_writing_guide, "get or put a writing guide",
        (["question"], {}), (["--body"], {"help": "JSON file to PUT"}))
    add("call", cmd_call, "any other route", (["method"], {}), (["path"], {}),
        (["--body"], {}))
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
