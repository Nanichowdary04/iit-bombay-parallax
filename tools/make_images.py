"""Convert downloaded Wikimedia Commons photos into graded WebP files + a credits list.

usage:  python tools/make_images.py <download-folder>
The download folder holds the original JPEGs and the credits.json lines written by the fetch step.
"""
import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "img"

# source file -> (output name, max width, warm grade 0..1)
PLAN = {
    "Powai_Lake_Panorama.jpg": ("powai-pano.webp", 7200, 0.8),
    "Main_building_in_IIT_Bombay.jpg": (None, 0, 0),      # landing hero: cut into layers by make_hero.py
    "Campus_view.jpg": ("campus-view.webp", 1600, 0.3),
    "Powai_lake_IIt.jpg": ("powai-night.webp", 2000, 0.25),
    "IITBConvocationHall.JPG": ("convocation.webp", 1400, 0.35),
    "Powai_lake_iit_bombay.jpg": ("powai-shore.webp", 1600, 0.45),
    "IITCampusPano.JPG": ("campus-hill.webp", 2200, 0.6),
    "Techfeast_2014_Mumbai.JPG": ("techfest-2014.webp", 1400, 0.2),
    "Serge_Haroche_at_Techfest_IIT_Bombay.jpg": ("haroche.webp", 900, 0.0),
    "Technoholix_Crowd_at_Techfest_IIT_Bombay.jpg": ("technoholix-crowd.webp", 1400, 0.1),
    "Robowars_bots.jpg": ("robowars.webp", 1200, 0.15),
    "IIT_B_Techfest_Robowars_Competition.jpg": ("robowars-arena.webp", 1000, 0.15),
    "Queue_for_exhibitions_at_Techfest_IIT_Bombay_Mumbai_India.JPG": ("exhibition-queue.webp", 1200, 0.2),
    "Technoholics_IITB_TECHFEST2012.JPG": ("technoholix-2012.webp", 1600, 0.1),
    "Pep_Bou_s_bubble_show_at_Techfest_2012.jpg": ("bubble-show.webp", 1000, 0.1),
    "Competitions.jpg": ("competitions.webp", 960, 0.15),
    "Dr._APJ_Abdul_Kalam_in_Techfest-2015.jpg": ("kalam.webp", 1000, 0.0),
    "Pranav_Mistry.jpg": ("pranav-mistry.webp", 960, 0.0),
}


def warm(img, k):
    """Golden-hour grade: lift reds, pull blues, a touch more contrast. k = strength."""
    if k <= 0:
        return img
    r, g, b = img.split()
    r = r.point(lambda v: min(255, int(v * (1 + 0.10 * k) + 6 * k)))
    g = g.point(lambda v: min(255, int(v * (1 + 0.02 * k))))
    b = b.point(lambda v: int(v * (1 - 0.16 * k)))
    img = Image.merge("RGB", (r, g, b))
    img = ImageEnhance.Contrast(img).enhance(1 + 0.12 * k)
    return ImageEnhance.Color(img).enhance(1 - 0.08 * k)


def label(title):
    name = title.split(":", 1)[1].rsplit(".", 1)[0]
    return re.sub(r"\s+", " ", name).strip()


def main(src):
    src = Path(src)
    OUT.mkdir(parents=True, exist_ok=True)
    meta = {}
    for line in (src / "credits.json").read_text(encoding="utf-8").splitlines():
        if line.strip():
            c = json.loads(line)
            meta[c["file"]] = c
    credits = []
    for name, (out, width, k) in PLAN.items():
        p = src / name
        if not p.exists():
            print("missing", name)
            continue
        if out:
            img = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
            if img.width > width:
                img = img.resize((width, round(img.height * width / img.width)), Image.LANCZOS)
            warm(img, k).save(OUT / out, "WEBP", quality=80, method=6)
            print(f"{out}: {img.width}x{img.height} {(OUT / out).stat().st_size // 1024} KB")
        c = meta.get(name)
        if c:
            credits.append({"label": label(c["title"]), "page": c["page"], "artist": c["artist"] or "unknown",
                            "license": c["license"], "used_as": out or "hero-sky.webp + hero-front.webp"})
    cpath = ROOT / "assets" / "credits.json"
    if cpath.exists():  # keep the footage credits written by make_clips.py
        credits += [c for c in json.loads(cpath.read_text(encoding="utf-8")) if c.get("video")]
    cpath.write_text(json.dumps(credits, indent=1, ensure_ascii=False), encoding="utf-8")
    print(len(credits), "credits written")


if __name__ == "__main__":
    main(sys.argv[1])
