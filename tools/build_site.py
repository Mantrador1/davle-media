#!/usr/bin/env python3
"""Χτίζει το davlestudio.com/watches/ από τις πηγές του εργοστασίου — καμία χειρόγραφη σελίδα ρολογιού.

ΓΙΑΤΙ: Σπύρος 24/10 «η πρωτη σελιδα πρεπει να εχει ολα μας τα ρολογια που κυκλοφορουν και τα comming next. οταν παταει ο χρηστης
πανω σε ενα ρολοι θα ανοιγει την δικη του σελιδα … κορυφαια αισθητικη … γραφικα και κινηση με το scroll». Κάθε νέο ρολόι = μία
γραμμή στο FACES· τα κείμενα έρχονται από την εγκεκριμένη καταχώριση Play (μοναδική πηγή ισχυρισμών), οι εικόνες από web/<face>/manifest.json
(πιστοποιημένες λήψεις, χωρίς τυπωμένο κείμενο).
Χρήση: python3 tools/build_site.py [--factory /opt/factory]
Φύλακας: /opt/factory/hooks/tests/test_every_face_on_sale_has_a_page_that_says_install_on_watch.py
"""
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
OUT = SITE / "watches"

# slug, κατάσταση, βίντεο (μόνο όσα είναι σε πώληση)
FACES = [
    ("kyanos", "on_sale", "video/kyanos_trailer_16x9_blue.mp4"),
    ("atraktos", "on_sale", "video/atraktos_trailer_16x9.mp4"),
    ("tachos", "coming", None),
    ("pyrsos", "coming", None),
    ("orichalkos", "coming", None),
    ("talos", "coming", None),
]
PLAY = "https://play.google.com/store/apps/details?id=com.davle.{s}&amp;referrer=utm_source%3Dwebsite%26utm_campaign%3D{s}"
INSTAGRAM = "https://www.instagram.com/davlestudio/"
CDN = """<script defer src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/ScrollTrigger.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/lenis@1.3.20/dist/lenis.min.js"></script>"""
FONT = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        '<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..800&display=swap" rel="stylesheet">')
e = html.escape


def section(text: str, head: str) -> list[str]:
    m = re.search(rf"^{re.escape(head)}\n((?:•[^\n]*\n?)+)", text, re.M)
    return [ln[1:].strip() for ln in m.group(1).splitlines() if ln.startswith("•")] if m else []


def paragraph(text: str, head: str) -> str:
    m = re.search(rf"^{re.escape(head)}\n([^\n]+)", text, re.M)
    return m.group(1).strip() if m else ""


def load(factory: Path, slug: str, status: str, video: str | None) -> dict:
    lst = json.loads((factory / f"panel/state/marketing/listings/{slug}/final/en-US.json").read_text(encoding="utf-8"))
    man = json.loads((SITE / f"web/{slug}/manifest.json").read_text(encoding="utf-8"))
    full = lst["full_description"]
    paras = [p.strip() for p in full.split("\n\n")]
    lede = paras[1] if len(paras) > 1 else ""
    short = re.sub(r"^For Wear OS 5\+ watches\.\s*", "", lst["short_description"])
    cols = []
    for c in man["colours"]:
        name = c["name"] if c.get("name") and c["name"] != c.get("tag") else c.get("tag", "").replace("_", " ").replace("-", " ")
        name = "Signature" if name.lower() == "default" else name
        cols.append({"name": name[:1].upper() + name[1:], "hex": c.get("hex", "#9aa3ad"), "dial": c["dial_webp"] if c.get("dial_webp") else c["dial"],
                     "hero": c.get("hero_webp") or c.get("hero"), "hero_wide": c.get("hero_wide_webp") or c.get("hero_wide"),
                     "top": c.get("top_webp") or c.get("top")})
    aod = next((f for f in ("dial_aod.webp", "dial_aod.png") if (SITE / f"web/{slug}/{f}").exists()), None)
    if not aod:
        aod = next((f"{Path(c['dial']).stem}_aod.webp" for c in cols if (SITE / f"web/{slug}/{Path(c['dial']).stem}_aod.webp").exists()), None)
    first = next(c for c in cols if c["hero"])
    gallery = sorted(p.name for p in (SITE / f"{slug}_k11").glob("ig_0*.jpg"))
    return {"slug": slug, "name": slug.upper(), "status": status, "video": video, "short": short, "lede": lede,
            "shows": section(full, "What it shows"), "taps": section(full, "Tap shortcuts"),
            "aod_text": paragraph(full, "Always-on display"), "colours_text": paragraph(full, "Colors") or paragraph(full, "Colours"),
            "cols": cols, "aod": aod, "hero": first["hero"], "hero_wide": first["hero_wide"], "hero_col": first,
            "top": next((c["top"] for c in cols if c["top"]), None), "gallery": gallery}


def head(title: str, desc: str, depth: str, og: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:image" content="{og}">
<link rel="icon" type="image/png" sizes="32x32" href="{depth}brand/favicon_32.png"><link rel="apple-touch-icon" href="{depth}brand/apple_touch_180.png">
{FONT}
<link rel="stylesheet" href="{depth}watches/site.css">
{CDN}
<script defer src="{depth}watches/site.js"></script>
</head>
"""


def topbar(depth: str, links: str) -> str:
    return (f'<header class="top"><a class="logo" href="{depth}watches/"><img src="{depth}brand/logo_320.png" alt="">DAVLE</a>'
            f'<nav aria-label="Site">{links}</nav></header>')


INSTALL = """
<section class="wrap install" id="install" aria-labelledby="install-h">
  <h2 id="install-h">Getting it onto your watch</h2>
  <p class="lede-s">{N} is a watch face, so it lives on the watch. Pick the way that matches where you are.</p>
  <div class="paths">
    <div class="path"><h3>On your phone, watch paired</h3><ol>
      <li>Open {N} in the Google Play app.</li>
      <li>If you see an arrow next to the price, tap it and choose your watch.</li>
      <li>Buy. Keep the watch near the phone; it can take a few minutes to arrive.</li>
      <li>On the watch, touch and hold the current face, swipe, and choose DAVLE {N}.</li></ol>
      <p class="note">No arrow? Your phone does not see a compatible watch on this Google account. Don't buy on the phone yet: use the watch or a computer instead.</p></div>
    <div class="path"><h3>On your watch</h3><ol>
      <li>Open Google Play on the watch.</li>
      <li>Search for DAVLE {N} and install it.</li>
      <li>Touch and hold the current face, swipe to the end, and add {N}.</li></ol>
      <p class="note">On Galaxy watches you can also touch and hold the face and swipe left to More watch faces.</p></div>
    <div class="path"><h3>On a computer</h3><ol>
      <li>Open the <a href="{PLAY}">{N} page on Google Play</a>, signed in with the same Google account as your watch.</li>
      <li>Choose your watch in the device list, then install.</li>
      <li>Add the face on the watch: touch and hold, swipe, choose {N}.</li></ol></div>
  </div>
  <div class="trouble">
    <details><summary>It's installed but not in my watch face list</summary><p>Give it a few minutes and keep the watch on Wi-Fi or near the phone. Then touch and hold the current face and swipe all the way to the end. If it still isn't there, restart the watch. Still missing? Write to us with your watch model.</p></details>
    <details><summary>Google Play says it isn't compatible</summary><p>{N} needs a round watch on Wear OS 5 or later. Update the watch software first. Galaxy Watch4, Watch5 and Watch6 need the One UI 6 Watch update. Square watches can't run it.</p></details>
    <details><summary>What does the phone app do?</summary><p>A small phone app comes with {N}. It shows the colours and opens the watch face's Google Play page on your watch, so you can install it there. The watch face works without it.</p></details>
    <details><summary>Customizing in the Galaxy Wearable app doesn't work</summary><p>Customize on the watch instead: touch and hold the face, then Customize. It is quicker and always shows every option.</p></details>
  </div>
</section>
<section class="wrap faq" id="faq" aria-labelledby="faq-h">
  <h2 id="faq-h">Questions</h2>
  <details><summary>Will it work on my phone?</summary><p>No. {N} is a watch face for Wear OS watches. Your phone can only help you install it.</p></details>
  <details><summary>Which watches can run it?</summary><p>Round watches with Wear OS 5 or later: Galaxy Watch4 and newer (Watch4 to Watch6 need One UI 6 Watch), Galaxy Watch Ultra, Pixel Watch, and other round Wear OS 5 watches. Not Apple Watch, not Fitbit, not square watches.</p></details>
  <details><summary>How long does it take to reach the watch?</summary><p>Usually a few minutes after buying on the phone. Keep the watch connected.</p></details>
  <details><summary>Why does heart rate or steps show nothing?</summary><p>The watch face reads the watch's own sensors. Allow the permissions when the watch asks, and wear the watch for a moment so it can take a reading.</p></details>
  <details><summary>Can I get a refund?</summary><p>Google Play lets you ask for a refund within 48 hours of buying, from your order history. After that, write to us with your watch model and order number and we'll help.</p></details>
  <details><summary>How do I contact you?</summary><p>Email <a href="mailto:studio@davlestudio.com">studio@davlestudio.com</a>. Include your watch model, so we can answer in one go.</p></details>
</section>"""


def face_page(f: dict, all_faces: list[dict]) -> str:
    s, N, d = f["slug"], f["name"], "../../"
    W = f"{d}web/{s}/"
    play = PLAY.format(s=s)
    on = f["status"] == "on_sale"
    accent = f["hero_col"]["hex"]
    nav = '<a href="#dial">On the dial</a><a href="#colours">Colours</a>' + ('<a class="keep" href="#install">Install</a><a href="#faq">Help</a>' if on else "")
    cta = (f'<a class="buy" href="{play}">Get {N} on Google Play</a><a class="after" href="#install">How to get it onto your watch</a>' if on else
           f'<span class="soon">Coming soon to Google Play</span><a class="after" href="{INSTAGRAM}">Follow DAVLE on Instagram for the release</a>')
    shows = "".join(f'<li class="feat"><span>{e(x)}</span></li>' for x in f["shows"])
    taps = ("<h3 class='taps-h'>Tap shortcuts</h3><ul class='taps'>" + "".join(f"<li>{e(x)}</li>" for x in f["taps"]) + "</ul>") if f["taps"] else ""
    swatches = "".join(f'<li><button type="button" data-i="{i}" style="--c:{c["hex"]}" aria-pressed="{str(i == 0).lower()}">{e(c["name"])}</button></li>'
                       for i, c in enumerate(f["cols"]))
    dials = "".join(f'<img class="dial-layer" data-i="{i}" src="{W}{c["dial"]}" alt="{e(N)} dial in {e(c["name"])}" width="1200" height="1200" loading="{"eager" if i == 0 else "lazy"}">'
                    for i, c in enumerate(f["cols"]))
    aod = (f'<section class="aod" id="aod" aria-labelledby="aod-h"><div class="wrap aod-in"><div class="aod-dial">'
           f'<img class="aod-on" src="{W}{f["cols"][0]["dial"]}" alt="" width="1200" height="1200" loading="lazy">'
           f'<img class="aod-off" src="{W}{f["aod"]}" alt="{e(N)} always-on display" width="1200" height="1200" loading="lazy"></div>'
           f'<div><h2 id="aod-h">When you lower your wrist</h2><p class="lede-s">{e(f["aod_text"])}</p></div></div></section>') if f["aod"] else ""
    gallery = "".join(f'<figure><img loading="lazy" src="{d}{s}_k11/{g}" alt="{e(N)} on a Galaxy Watch Ultra" width="1080" height="1350"></figure>' for g in f["gallery"])
    video = (f'<video controls preload="none" playsinline poster="{d}{s}_k11/trailer_poster.jpg" aria-label="{N} trailer"><source src="{d}{f["video"]}" type="video/mp4"></video>'
             if f["video"] else "")
    others = "".join(f'<a class="mini" href="../{o["slug"]}/"><img src="{d}web/{o["slug"]}/{o["cols"][0]["dial"]}" alt="" width="1200" height="1200" loading="lazy"><span>{o["name"]}</span>'
                     f'<small>{"On Google Play" if o["status"] == "on_sale" else "Coming soon"}</small></a>' for o in all_faces if o["slug"] != s)
    sticky = (f'<div class="sticky" role="region" aria-label="Get {N}"><small>Installs on your watch<br>Wear OS 5+, round</small><a class="buy" href="{play}">Get it on Google Play</a></div>'
              if on else "")
    return (head(f"DAVLE {N} — watch face for Wear OS", f"DAVLE {N}: {f['short']} For round watches with Wear OS 5 or later. Installs on your watch.", d,
                 f"https://davlestudio.com/web/{s}/{f['hero_col']['hero'].replace('.webp', '.jpg')}")
            + f'<body class="face {"is-on" if on else "is-soon"}" style="--accent:{accent}">' + topbar(d, nav) + f"""
<main>
<section class="hero" aria-labelledby="name">
  <picture class="hero-img"><source media="(max-width: 820px)" srcset="{W}{f['hero']}"><img src="{W}{f['hero_wide']}" alt="DAVLE {N} on a Galaxy Watch Ultra" width="2400" height="1350" fetchpriority="high"></picture>
  <div class="wrap hero-txt">
    <p class="status">{"On Google Play" if on else "Coming soon"}</p>
    <h1 id="name" style="--n:{len(N)}">{N}</h1>
    <p class="lede">{e(f['lede'])}</p>
    <div class="where"><strong>This installs on your watch, not your phone.</strong>
      <p>It needs a round watch with Wear OS 5 or later.{" Buying on a phone works when your watch is paired: choose the watch at checkout." if on else ""}</p>
      <ul class="chips" aria-label="Requirements"><li>Wear OS 5 or later</li><li>Round watches</li><li>Galaxy Watch4 and newer</li><li>Pixel Watch</li></ul></div>
    <div class="cta">{cta}</div>
  </div>
</section>

<section class="anatomy" id="dial" aria-labelledby="dial-h">
  <div class="wrap anatomy-in">
    <div class="stage" aria-hidden="false">{dials}</div>
    <div class="feats">
      <h2 id="dial-h">What's on the dial</h2>
      <ol class="feat-list">{shows}</ol>
      {taps}
      <div class="colours" id="colours">
        <h2 id="col-h">{len(f['cols'])} colours, one setting</h2>
        <p class="lede-s">{e(f['colours_text'])} Change it on the watch: touch and hold the face, then Customize.</p>
        <ul class="swatches">{swatches}</ul>
      </div>
    </div>
  </div>
</section>
{aod}
<section class="gallery" aria-label="Photos">
  <div class="wrap"><h2>On the wrist</h2></div>
  <div class="strip" tabindex="0" aria-label="Photos of {N}, scroll sideways">{gallery}</div>
  <div class="wrap">{video}</div>
</section>
{INSTALL.format(N=N, PLAY=play) if on else ""}
<section class="wrap more" aria-labelledby="more-h"><h2 id="more-h">More from DAVLE</h2><div class="minis">{others}</div></section>
</main>
<footer class="wrap"><p>DAVLE studio · <a href="../">All watch faces</a> · <a href="https://panel.davlestudio.com/privacy/{s}">Privacy</a> · <a href="mailto:studio@davlestudio.com">studio@davlestudio.com</a></p>
<p>Google Play and Wear OS are trademarks of Google LLC. Galaxy Watch is a trademark of Samsung Electronics.</p></footer>
{sticky}
</body></html>
""")


def home(faces: list[dict], from_src: str | None, depth: str) -> str:
    q = f"?from={from_src}" if from_src else ""
    on = [f for f in faces if f["status"] == "on_sale"]
    soon = [f for f in faces if f["status"] != "on_sale"]

    def card(f, big):
        return (f'<a class="card {"big" if big else ""}" href="{f["slug"]}/{q}" style="--accent:{f["hero_col"]["hex"]}">'
                f'<img src="{depth}web/{f["slug"]}/{f["hero"]}" alt="DAVLE {f["name"]} on a Galaxy Watch Ultra" width="1600" height="2000" loading="lazy">'
                f'<span class="card-txt"><span class="card-name">{f["name"]}</span><span class="card-sub">{e(f["short"])}</span>'
                f'<span class="card-status">{"On Google Play" if f["status"] == "on_sale" else "Coming soon"}</span></span></a>')
    reel = "".join(f'<figure class="reel-item" data-i="{i}"><img src="{depth}web/{f["slug"]}/{f["cols"][0]["dial"]}" alt="DAVLE {f["name"]} dial" width="1200" height="1200" loading="{"eager" if i == 0 else "lazy"}">'
                   f'<figcaption><b>{f["name"]}</b> {"On Google Play" if f["status"] == "on_sale" else "Coming soon"}</figcaption></figure>'
                   for i, f in enumerate(faces))
    lead = faces[0]
    return (head("DAVLE — watch faces for Wear OS", "Instrument-grade watch faces for round Wear OS 5+ watches. Installs on your watch.", depth,
                 f"https://davlestudio.com/web/{lead['slug']}/{lead['hero_col']['hero_wide'].replace('.webp', '.jpg')}")
            + '<body class="home">' + topbar(depth, '<a href="#collection">Watch faces</a><a class="keep" href="#install">Install</a>') + f"""
<main>
<section class="hero home-hero" aria-labelledby="brand">
  <picture class="hero-img"><source media="(max-width: 820px)" srcset="{depth}web/{lead['slug']}/{lead['hero']}"><img src="{depth}web/{lead['slug']}/{lead['hero_wide']}" alt="DAVLE {lead['name']} on a Galaxy Watch Ultra" width="2400" height="1350" fetchpriority="high"></picture>
  <div class="wrap hero-txt">
    <h1 id="brand">DAVLE</h1>
    <p class="lede">Watch faces that read like instruments. Built for round watches with Wear OS 5 or later.</p>
    <div class="where"><strong>Our watch faces install on your watch, not your phone.</strong><p>Every page below shows what each face needs and how to get it onto your watch.</p></div>
    <div class="cta"><a class="buy" href="#collection">See the watch faces</a></div>
  </div>
</section>

<section class="reel" aria-label="Every DAVLE dial">
  <div class="reel-stage">{reel}</div>
  <p class="wrap reel-note">Every dial here is a capture of the real watch face, not a drawing.</p>
</section>

<section class="wrap collection" id="collection" aria-labelledby="col-h">
  <h2 id="col-h">On Google Play now</h2>
  <div class="cards cards-on">{"".join(card(f, True) for f in on)}</div>
  <h2 class="soon-h">Coming next</h2>
  <div class="cards cards-soon">{"".join(card(f, False) for f in soon)}</div>
</section>

<section class="wrap install home-install" id="install" aria-labelledby="ins-h">
  <h2 id="ins-h">How it gets onto your watch</h2>
  <ol class="steps">
    <li><b>Check your watch.</b> Round, Wear OS 5 or later: Galaxy Watch4 and newer, Pixel Watch.</li>
    <li><b>Buy where your watch is.</b> On the watch's Google Play, on a computer, or on a phone that shows an arrow next to the price.</li>
    <li><b>Pick it on the watch.</b> Touch and hold your current face, swipe, and choose the new one.</li>
  </ol>
  <p class="lede-s">Each watch face page has the full guide and answers.</p>
</section>
</main>
<footer class="wrap"><p>DAVLE studio · <a href="mailto:studio@davlestudio.com">studio@davlestudio.com</a> · <a href="{INSTAGRAM}">Instagram</a></p>
<p>Google Play and Wear OS are trademarks of Google LLC. Galaxy Watch is a trademark of Samsung Electronics.</p></footer>
</body></html>
""")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--factory", default="/opt/factory")
    a = ap.parse_args()
    faces = [load(Path(a.factory), *row) for row in FACES]
    for f in faces:
        (OUT / f["slug"]).mkdir(parents=True, exist_ok=True)
        (OUT / f["slug"] / "index.html").write_text(face_page(f, faces), encoding="utf-8")
    (OUT / "index.html").write_text(home(faces, "instagram_bio", "../"), encoding="utf-8")
    (OUT / "fb").mkdir(exist_ok=True)
    (OUT / "fb/index.html").write_text(home(faces, "facebook_groups", "../../").replace('href="kyanos/', 'href="../kyanos/')
                                       .replace('href="atraktos/', 'href="../atraktos/').replace('href="tachos/', 'href="../tachos/')
                                       .replace('href="pyrsos/', 'href="../pyrsos/').replace('href="orichalkos/', 'href="../orichalkos/')
                                       .replace('href="talos/', 'href="../talos/'), encoding="utf-8")
    print("SITE_BUILD=OK", ", ".join(f"{f['slug']}:{f['status']}:{len(f['cols'])}c" for f in faces))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
