"""Download a pinned slice of the GitLab Handbook and write cleaned markdown to corpus/.

Re-running this script reproduces corpus/ exactly. Content is CC BY-SA 4.0 (see corpus/NOTICE.md).

    python scripts/fetch_corpus.py
"""

import io
import re
import shutil
import tarfile
import urllib.parse
import urllib.request
from pathlib import Path

PROJECT_ID = 42817607  # gitlab-com/content-sites/handbook
SHA = "29350f826f2a6af03a83a3c212410ce918bdf115"
API = f"https://gitlab.com/api/v4/projects/{PROJECT_ID}/repository"

DIRS = [
    "total-rewards",
    "people-group/time-off-and-absence",
    "people-group/general-onboarding",
    "people-group/offboarding",
    "finance/travel",
]
FILES = [
    "finance/expenses.md",
    "finance/spending-company-money.md",
    "people-group/anti-harassment.md",
    "people-group/relocation.md",
    "people-group/visas.md",
    "people-group/contracts-probation-periods.md",
    "people-group/promotions-transfers.md",
    "people-group/acceptable-use-policy.md",
]

OUT = Path(__file__).resolve().parent.parent / "corpus"
MIN_CHARS = 300  # drop stubs that only link elsewhere


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "docmind-fetch"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def fetch_raw() -> dict[str, str]:
    """Return {path relative to content/handbook: raw markdown}."""
    raw = {}
    for d in DIRS:
        path = urllib.parse.quote(f"content/handbook/{d}", safe="")
        data = get(f"{API}/archive.tar.gz?sha={SHA}&path={path}")
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
            for m in tar.getmembers():
                if m.isfile() and m.name.endswith(".md"):
                    rel = m.name.split("/content/handbook/", 1)[1]
                    raw[rel] = tar.extractfile(m).read().decode("utf-8")
    for f in FILES:
        path = urllib.parse.quote(f"content/handbook/{f}", safe="")
        raw[f] = get(f"{API}/files/{path}/raw?ref={SHA}").decode("utf-8")
    return raw


TAGS = r"details|summary|div|span|br|p|i|b|em|strong|a|img|sup|sub|u|center|font|hr|iframe"


def clean(text: str) -> str:
    title = ""
    fm = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if fm:
        t = re.search(r"^title:\s*[\"']?(.*?)[\"']?\s*$", fm.group(1), re.M)
        title = t.group(1) if t else ""
        text = text[fm.end():]
    # keep the label of collapsible/panel shortcodes as a bold line, drop the rest
    text = re.sub(r"\{\{[%<]\s*\w+\s+(?:summary|header|title)=\"([^\"]*)\"[^}]*[%>]\}\}",
                  lambda m: f"\n**{m.group(1).strip('* ')}**\n", text)
    text = re.sub(r"\{\{[%<].*?[%>]\}\}", "", text, flags=re.S)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(rf"</?(?:{TAGS})\b[^>]*>", " ", text, flags=re.I)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)          # images
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)      # links -> link text
    text = re.sub(r"\[([^\]]+)\]\[[^\]]*\]", r"\1", text)     # reference links
    text = re.sub(r"^\[[^\]]+\]:\s*\S+.*$", "", text, flags=re.M)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return f"# {title}\n\n{text}\n" if title else text + "\n"


def main() -> None:
    raw = fetch_raw()
    if OUT.exists():
        for p in OUT.rglob("*.md"):
            if p.name != "NOTICE.md":
                p.unlink()
    kept = 0
    for rel, text in sorted(raw.items()):
        cleaned = clean(text)
        if len(cleaned) < MIN_CHARS:
            print(f"skip (stub) {rel}")
            continue
        dest = OUT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(cleaned, encoding="utf-8", newline="\n")
        kept += 1
    for d in sorted(OUT.rglob("*"), reverse=True):
        if d.is_dir() and not any(d.iterdir()):
            shutil.rmtree(d)
    print(f"wrote {kept} files to {OUT}")


if __name__ == "__main__":
    main()
