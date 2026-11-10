#!/usr/bin/env python3
"""Tell IndexNow (Bing, Yandex, Seznam, Naver) which pages changed.

    python3 tools/indexnow.py --all             every URL in sitemap.xml
    python3 tools/indexnow.py --since REV       URLs that are new, or whose <lastmod>
                                                changed, since sitemap.xml at REV
    python3 tools/indexnow.py --since REV --dry-run   print the URLs, send nothing
    add --wait to wait until the live key file answers (after a deploy)

The key is the <32 hex>.txt file in the site root; its text is its name.
.github/workflows/indexnow.yml runs this after each Pages deploy.
Exit 1 when IndexNow refuses the list, so the run shows red.
"""
import argparse, glob, json, os, re, subprocess, sys, time, urllib.error, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://skiff.solutionscay.com/"
HOST = "skiff.solutionscay.com"
ENDPOINT = "https://api.indexnow.org/indexnow"
# Cloudflare answers 403 to the default Python-urllib agent.
UA = {"User-Agent": "skiff-web-indexnow/1.0 (+https://skiff.solutionscay.com/)"}

def key():
    for f in glob.glob(os.path.join(ROOT, "*.txt")):
        name = os.path.basename(f)[:-4]
        if re.fullmatch(r"[0-9a-f]{32}", name) and open(f).read().strip() == name:
            return name
    sys.exit("indexnow: no <key>.txt in the site root")

def entries(xml):
    """{url: lastmod} from a sitemap's text."""
    out = {}
    for block in re.findall(r"<url>(.*?)</url>", xml, re.S):
        loc = re.search(r"<loc>(.*?)</loc>", block)
        mod = re.search(r"<lastmod>(.*?)</lastmod>", block)
        if loc:
            out[loc.group(1).strip()] = mod.group(1).strip() if mod else ""
    return out

def changed(rev, now):
    try:
        old = subprocess.run(["git", "show", f"{rev}:sitemap.xml"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"indexnow: cannot read sitemap.xml at {rev}; sending every URL")
        return list(now)
    before = entries(old)
    return [u for u, m in now.items() if before.get(u) != m]

def wait_for(k, minutes=10):
    url = f"{SITE}{k}.txt"
    last = "no answer"
    for _ in range(minutes * 4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=10) as r:
                if r.read().decode().strip() == k:
                    return
                last = f"{r.status}, other text"
        except urllib.error.HTTPError as e:
            last = str(e.code)
        except (urllib.error.URLError, TimeoutError) as e:
            last = str(e)
        time.sleep(15)
    sys.exit(f"indexnow: {url} did not answer with the key in {minutes} min (last: {last})")

def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--all", action="store_true")
    g.add_argument("--since", metavar="REV")
    ap.add_argument("--wait", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    k = key()
    now = entries(open(os.path.join(ROOT, "sitemap.xml")).read())
    urls = list(now) if a.all else changed(a.since, now)
    urls = [u for u in urls if u.startswith(SITE)]
    if not urls:
        print("indexnow: no URL changed")
        return
    print("\n".join(urls))
    if a.dry_run:
        print(f"indexnow: dry run, {len(urls)} URLs not sent")
        return
    if a.wait:
        wait_for(k)
    body = json.dumps({"host": HOST, "key": k, "keyLocation": f"{SITE}{k}.txt", "urlList": urls}).encode()
    req = urllib.request.Request(ENDPOINT, data=body, headers={"Content-Type": "application/json; charset=utf-8", **UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f"indexnow: {r.status}, {len(urls)} URLs sent")
    except urllib.error.HTTPError as e:
        print(f"indexnow: {e.code} {e.read().decode(errors='replace')[:300]}")
        sys.exit(1)

if __name__ == "__main__":
    main()
