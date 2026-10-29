#!/usr/bin/env python3
"""Search & download free SFX from Mixkit / Kenney / Freesound / Pixabay.

Stdlib only, except Pixabay: it sits behind Cloudflare, so those calls re-exec under a private
venv with curl_cffi (Chrome TLS impersonation), created on first use. Goes through the shell's
http(s)_proxy (Clash), which routes freesound.org to a dedicated node — see ../references/local-setup.md.

  sfx.py mixkit <keyword> [-n N]
  sfx.py kenney [pack]
  sfx.py freesound "<query>" [--license cc0|by|any] [--sort relevance|downloads|rating|short] [-n N] [-p PAGE] [--pages K]
                                       relevance (default) is re-ranked by downloads across K pages
  sfx.py pixabay "<query>" [-n N] [-p PAGE] [--pages K]   ranked by likes across K pages
  sfx.py get <out_dir> <key>...        keys: mk:<id>  fs:<id>  kn:<pack>/<file>  px:<id>
"""
import argparse, html, json, os, re, shutil, subprocess, sys, time, urllib.parse, urllib.request, zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) sfx-sources"}
CACHE = Path.home() / ".cache" / "sfx-sources"
INDEX = CACHE / "index.json"  # search results, so `get` knows title + download url
VENV = CACHE / "venv"  # curl_cffi for Pixabay
FS_LICENSE = {"cc0": '"Creative Commons 0"', "by": '("Attribution" OR "Creative Commons 0")', "any": None}
FS_LIC_SHORT = {"Creative Commons 0": "CC0", "Attribution": "BY", "Attribution NonCommercial": "BY-NC", "Sampling+": "Sampling+"}
FS_SORT = {"downloads": "Downloads (most first)", "rating": "Rating (highest first)",
           "relevance": "Automatic by relevance", "short": "Duration (shortest first)"}


def fetch(url, timeout=60, tries=3):
    for n in range(tries):
        try:
            if "pixabay.com" in url:  # Cloudflare 403s plain urllib
                from curl_cffi import requests as cr
                r = cr.get(url, impersonate="chrome", timeout=timeout, headers={"Referer": "https://pixabay.com/"})
                if r.status_code != 200:
                    raise OSError(f"HTTP {r.status_code} {url}")
                return r.content
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                return r.read()
        except Exception as e:
            if n == tries - 1:
                raise e if isinstance(e, OSError) else OSError(repr(e))
            time.sleep(1 + n)  # Cloudflare 403s are sporadic; a short pause usually clears them


def need_cffi():
    """Re-exec this script under the private venv unless curl_cffi is already importable."""
    try:
        import curl_cffi  # noqa: F401
        return
    except ImportError:
        pass
    py = VENV / "bin" / "python"
    if not py.exists():
        print("setting up curl_cffi venv for Pixabay (one-time)…", file=sys.stderr)
        subprocess.run([sys.executable, "-m", "venv", str(VENV)], check=True)
        subprocess.run([str(py), "-m", "pip", "-q", "install", "curl_cffi"], check=True)
    os.execv(str(py), [str(py), os.path.abspath(__file__), *sys.argv[1:]])


def load_index():
    try:
        return json.loads(INDEX.read_text())
    except (OSError, ValueError):
        return {}


def save_index(rows):
    CACHE.mkdir(parents=True, exist_ok=True)
    idx = load_index()
    idx.update({r["key"]: r for r in rows})
    INDEX.write_text(json.dumps(idx, ensure_ascii=False))


def show(rows, a, lic=False, hint=""):
    save_index(rows)
    for r in rows:
        print("\t".join([r["key"], r["title"], r["dur"]] + ([r["stats"]] if "stats" in r else []) + [r["license"]] * lic + ([r["desc"]] if r.get("desc") else []) + [r["preview"]] * a.urls))
    if not rows:
        print("(none)" + hint)


def mixkit(a):
    kw = re.sub(r"\s+", "-", a.keyword.strip().lower())
    h = fetch(f"https://mixkit.co/free-sound-effects/discover/{urllib.parse.quote(kw)}/").decode()
    rows = []
    for blk in h.split('data-audio-player-item-id-value="')[1:]:
        i = blk.split('"', 1)[0]
        t = re.search(r'item-grid-card__title">\s*(.*?)\s*</h2>', blk, re.S)
        d = re.search(r'data-test-id="duration">\s*([\d:]+)', blk)
        rows.append({"key": f"mk:{i}", "title": html.unescape(t.group(1)) if t else "", "dur": d.group(1) if d else "",
                     "license": "Mixkit", "preview": f"https://assets.mixkit.co/active_storage/sfx/{i}/{i}-preview.mp3",
                     "url": f"https://assets.mixkit.co/active_storage/sfx/{i}/{i}.wav"})
    show(rows[: a.n], a, hint=" try a broader tag, or freesound")


def freesound(a):
    # Like pixabay(): pull several relevance pages and rank them by downloads, since sorting by downloads
    # server-side lets globally popular but off-topic sounds (gunshots, ambiences) win on a loose tag match.
    q = {"q": a.query, "s": FS_SORT[a.sort]}
    if FS_LICENSE[a.license]:
        q["f"] = "license:" + FS_LICENSE[a.license]
    pages = range(a.page, a.page + a.pages)
    with ThreadPoolExecutor(len(pages)) as ex:
        htmls = list(ex.map(lambda n: fetch("https://freesound.org/search/?" + urllib.parse.urlencode({**q, "page": n})).decode(), pages))
    rows = []
    for blk in (b for h in htmls for b in h.split('class="bw-search__result"')[1:]):
        g = lambda k: (re.search(rf'data-{k}="([^"]*)"', blk) or [None, ""])[1]
        lic = re.search(r'title="License: ([^"]+)"', blk)
        rt = re.search(r'aria-label="Average rating of ([\d.]+)"', blk)
        rn = re.search(r'bw-rating__count[^>]*>\((\d+)\)', blk)
        desc = re.search(r'<div class="max-h-60px[^"]*"\s*>\s*(.*?)\s*</div>', blk, re.S)
        sid, user, dl = g("sound-id"), g("username"), int(g("num-downloads") or 0)
        rows.append({"key": f"fs:{sid}", "title": html.unescape(g("title")), "dur": f"{float(g('duration') or 0):.1f}s",
                     "author": user, "license": FS_LIC_SHORT.get(lic.group(1), lic.group(1)) if lic else "?", "preview": g("mp3").replace("-lq.mp3", "-hq.mp3"),
                     "url": g("mp3").replace("-lq.mp3", "-hq.mp3"), "downloads": dl,
                     "stats": f"↓{dl} ★{rt[1]}({rn[1]})" if rt and rn else f"↓{dl} ★-",
                     # the uploader's own words (mic, source, processing) are the closest thing to hearing it
                     "desc": html.unescape(re.sub(r"<[^>]+>|\s+", " ", desc[1])).strip()[:90] if desc else ""})
    if a.sort == "relevance":
        rows.sort(key=lambda r: -r["downloads"])
    show(rows[: a.n], a, lic=a.license != "cc0")


def k_num(t):  # "2.4K" -> 2400
    m = re.match(r"([\d.]+)\s*([KM]?)", t or "")
    return int(float(m[1]) * {"": 1, "K": 1e3, "M": 1e6}[m[2]]) if m else 0


def pixabay(a):
    # Pixabay can't sort by likes server-side, so pull several relevance pages, rank their cards by
    # the rounded like counter, then open only the top n detail pages for exact numbers + mp3.
    q = urllib.parse.quote(a.query.strip())
    pages = range(a.page, a.page + a.pages)
    with ThreadPoolExecutor(len(pages)) as ex:
        htmls = list(ex.map(lambda n: fetch(f"https://pixabay.com/sound-effects/search/{q}/" + (f"?pagi={n}" if n > 1 else "")).decode(), pages))
    seen, cards = set(), []
    for h in htmls:
        for blk in h.split('<div class="nameAndTitle')[1:]:
            t = re.search(r'<a href="(/sound-effects/[^"]*?-(\d+)/)" class="title[^"]*">(.*?)</a><a href="/users/[^"]*" class="name[^"]*">(.*?)</a>', blk)
            if t and t[2] not in seen:
                seen.add(t[2])
                cards.append((t[1], t[2], html.unescape(t[3]), html.unescape(t[4]), k_num((re.search(r'counter="([^"]*)"', blk) or [0, ""])[1])))
    cards.sort(key=lambda c: -c[4])

    def detail(c):  # duration, exact likes/downloads and mp3 url only live in the detail page's JSON-LD
        path, sid, title, user, likes = c
        dl, dur, url = 0, "?", ""
        try:
            d = fetch("https://pixabay.com" + path).decode()
            j = next(x for x in map(json.loads, re.findall(r'<script type="application/ld\+json">(.*?)</script>', d, re.S))
                     if x.get("@type") == "AudioObject")
            st = {i["interactionType"].rsplit("/", 1)[-1]: i["userInteractionCount"] for i in j.get("interactionStatistic", [])}
            likes, dl = st.get("LikeAction", likes), st.get("DownloadAction", 0)
            m = re.match(r"PT(?:(\d+)M)?(\d+)S", j.get("duration", ""))
            dur, url = f"{int(m[1] or 0) * 60 + int(m[2])}s" if m else "", j["contentUrl"]
        except Exception:
            pass
        return {"key": f"px:{sid}", "title": title, "dur": dur, "author": user, "license": "Pixabay", "likes": likes,
                "stats": f"♥{likes} ↓{dl}", "page": "https://pixabay.com" + path, "preview": url, "url": url}

    with ThreadPoolExecutor(6) as ex:
        rows = [r for r in ex.map(detail, cards[: a.n]) if r["url"]]
    rows.sort(key=lambda r: -r["likes"])
    show(rows, a, hint=" try a broader English query")


def kenney(a):
    if not a.pack:
        h = fetch("https://kenney.nl/assets/category:Audio").decode()
        packs = sorted({p for p in re.findall(r"kenney\.nl/assets/([a-z0-9-]+)['\"]", h)})
        print(" ".join(packs))
        return
    d = CACHE / "kenney" / a.pack
    if not d.exists():
        h = fetch(f"https://kenney.nl/assets/{a.pack}").decode()
        z = re.search(r"https://kenney\.nl/media/[^\"']+\.zip", h)
        if not z:
            sys.exit(f"no zip found for pack '{a.pack}' (run `kenney` to list packs)")
        zp = d.with_suffix(".zip")
        zp.parent.mkdir(parents=True, exist_ok=True)
        zp.write_bytes(fetch(z.group(0), timeout=300))
        zipfile.ZipFile(zp).extractall(d)
    files = sorted(p.relative_to(d).as_posix() for p in d.rglob("*") if p.suffix.lower() in (".ogg", ".wav", ".mp3"))
    groups = {}
    for f in files:  # collapse click_001..click_005 into one line to keep output short
        m = re.match(r"(.*?)(\d+)(\.\w+)$", f)
        groups.setdefault((m[1], m[3]) if m else (f, ""), []).append(m[2] if m else "")
    top = {f.split("/")[0] for f in files}
    pre = next(iter(top)) + "/" if len(top) == 1 and all("/" in f for f in files) else ""
    exts = {e for _, e in groups}
    ext = exts.pop() if len(exts) == 1 else ""  # print a shared extension once
    print(f"key kn:{a.pack}/{pre}<name>{ext}")
    print(" ".join(stem[len(pre):] + (f"{{{n[0]}..{n[-1]}}}" if len(n) > 1 else n[0]) + (e if not ext else "")
                   for (stem, e), n in groups.items()))


def get(a):
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    idx = load_index()

    def one(key):
        src, _, ref = key.partition(":")
        if src == "kn":
            p = CACHE / "kenney" / ref
            if not p.exists():
                return key, None, "not cached — run `kenney <pack>` first"
            dst = out / f"kn_{ref.replace('/', '_')}"
            shutil.copy(p, dst)
            return key, dst, None
        r = idx.get(key)
        if not r and src == "px":
            return key, None, "unknown key — run `pixabay <query>` first"
        if not r and src == "mk":
            r = {"title": "", "url": f"https://assets.mixkit.co/active_storage/sfx/{ref}/{ref}.wav"}
        if not r:
            return key, None, "unknown key — search first"
        slug = re.sub(r"[^\w]+", "-", r["title"]).strip("-")[:40]
        dst = out / f"{src}_{ref}{'_' + slug if slug else ''}{Path(urllib.parse.urlparse(r['url']).path).suffix}"
        if not dst.exists():
            tmp = dst.with_suffix(dst.suffix + ".part")
            tmp.write_bytes(fetch(r["url"], timeout=300))
            tmp.rename(dst)
        lic = r.get("license", "CC0")
        return key, dst, f"credit {r.get('author', '?')}" if src == "fs" and lic != "CC0" else None

    def safe(key):
        try:
            return one(key)
        except Exception as e:  # one bad file shouldn't sink the batch
            return key, None, repr(e)

    # Freesound caps ~80 KB/s per connection, so parallelism is the only speed lever.
    with ThreadPoolExecutor(6) as ex:
        for key, dst, note in ex.map(safe, a.keys):
            print(f"FAIL {key}: {note}" if not dst else f"{dst.name}  [{note}]" if note else dst.name)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    m = sp.add_parser("mixkit"); m.add_argument("keyword"); m.add_argument("-n", type=int, default=10); m.add_argument("--urls", action="store_true"); m.set_defaults(fn=mixkit)
    k = sp.add_parser("kenney"); k.add_argument("pack", nargs="?"); k.set_defaults(fn=kenney)
    f = sp.add_parser("freesound"); f.add_argument("query"); f.add_argument("--license", choices=FS_LICENSE, default="any")
    f.add_argument("--sort", choices=FS_SORT, default="relevance"); f.add_argument("-n", type=int, default=8); f.add_argument("--urls", action="store_true")
    f.add_argument("-p", "--page", type=int, default=1)
    f.add_argument("--pages", type=int, default=3, help="relevance pages (15 each) to rank by downloads"); f.set_defaults(fn=freesound)
    x = sp.add_parser("pixabay"); x.add_argument("query"); x.add_argument("-n", type=int, default=8); x.add_argument("--urls", action="store_true")
    x.add_argument("-p", "--page", type=int, default=1)
    x.add_argument("--pages", type=int, default=3, help="relevance pages (20 each) to rank by likes"); x.set_defaults(fn=pixabay)
    g = sp.add_parser("get"); g.add_argument("out_dir"); g.add_argument("keys", nargs="+"); g.set_defaults(fn=get)
    a = ap.parse_args()
    if a.cmd == "pixabay" or (a.cmd == "get" and any(k.startswith("px:") for k in a.keys)):
        need_cffi()
    try:
        a.fn(a)
    except OSError as e:
        sys.exit(f"network error: {getattr(e, 'reason', e)}" + (" — try clash_freesound.py --fix" if a.cmd == "freesound" else ""))


if __name__ == "__main__":
    main()
