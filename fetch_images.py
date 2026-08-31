"""
fetch_images.py — download Meta creative previews into ./images/

Why this exists
---------------
Meta serves creative images from scontent-*.fbcdn.net with a signed `oe=` expiry
token that dies after a few days. Linking to those URLs directly would leave the
dashboard full of broken images within a week. So we download each creative once
and commit it to the repo, where it lives permanently and loads instantly.

Input
-----
creative_urls.json — a mapping of creative_id -> image URL, produced by the
weekly Cowork run (it asks the Meta connector for `image_url` and
`thumbnail_url` for every creative in the payload and writes them here).

    {
      "1073834585131382": "https://scontent-....png?...",
      "1088519110467196": "https://scontent-....png?..."
    }

Output
------
images/<creative_id>.jpg for every URL that downloads successfully.

Behaviour
---------
- Skips anything already on disk, so re-running is cheap and only fetches new
  creatives.
- Downscales to 900px on the long edge and saves as JPEG quality 82. Full-size
  Meta creatives are 1–3 MB each; at ~700 creatives that would be a 1.5 GB repo.
  This keeps the whole image set to roughly 40–60 MB.
- Never deletes. Old creatives stay so historical windows keep their previews.

Usage
-----
    pip install pillow requests
    python fetch_images.py
"""
import json, os, sys, time

try:
    import requests
except ImportError:
    sys.exit("Missing dependency. Run:  pip install requests pillow")

try:
    from PIL import Image
    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False
    print("Pillow not installed — saving originals without resizing.")
    print("For a much smaller repo, run: pip install pillow\n")

OUT       = "images"
SRC       = "creative_urls.json"
MAX_EDGE  = 900
QUALITY   = 82
TIMEOUT   = 25
PAUSE     = 0.15          # be polite to the CDN

def main():
    if not os.path.exists(SRC):
        sys.exit(f"Can't find {SRC}. The weekly refresh should produce it before "
                 f"this script runs.")
    urls = json.load(open(SRC))
    os.makedirs(OUT, exist_ok=True)

    todo = {cid: u for cid, u in urls.items()
            if u and not os.path.exists(os.path.join(OUT, f"{cid}.jpg"))}
    have = len(urls) - len(todo)
    print(f"{len(urls)} creatives referenced · {have} already downloaded · "
          f"{len(todo)} to fetch\n")

    ok = fail = 0
    for i, (cid, url) in enumerate(todo.items(), 1):
        path = os.path.join(OUT, f"{cid}.jpg")
        tmp  = path + ".part"
        try:
            r = requests.get(url, timeout=TIMEOUT)
            r.raise_for_status()
            with open(tmp, "wb") as f:
                f.write(r.content)
            if HAVE_PIL:
                im = Image.open(tmp).convert("RGB")
                im.thumbnail((MAX_EDGE, MAX_EDGE), Image.LANCZOS)
                im.save(path, "JPEG", quality=QUALITY, optimize=True)
                os.remove(tmp)
            else:
                os.replace(tmp, path)
            ok += 1
        except Exception as e:
            fail += 1
            if os.path.exists(tmp):
                os.remove(tmp)
            print(f"  could not fetch {cid}: {type(e).__name__}")
        if i % 25 == 0 or i == len(todo):
            print(f"  {i}/{len(todo)} …")
        time.sleep(PAUSE)

    size = sum(os.path.getsize(os.path.join(OUT, f))
               for f in os.listdir(OUT) if f.endswith(".jpg")) / 1e6
    print(f"\nDone. {ok} downloaded, {fail} failed.")
    print(f"images/ now holds {len(os.listdir(OUT))} files, {size:.0f} MB total.")
    if fail:
        print("Failures are usually expired links — they'll be picked up on the "
              "next refresh with fresh URLs.")

if __name__ == "__main__":
    main()
