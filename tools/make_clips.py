"""Cut the source footage into the page's clips: clips/src/<name>.mp4 (1280x720, 24 fps, warm grade).

usage:  python tools/make_clips.py <folder-with-downloaded-webm-files>

The footage is real, freely licensed video from Wikimedia Commons (authors and licences are added to
assets/credits.json). Each clip is a few hand-picked shots joined with short cross-fades.
To use your own footage instead (for example from Google Flow), drop an MP4 into clips/src with the same
name and skip this step; see FLOW-PROMPTS.md.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "clips" / "src"

# light golden-hour grade: a little contrast and warmth without muddying the sky
GRADE = ("eq=contrast=1.08:saturation=1.12,colorbalance=rh=0.06:gh=0.02:bh=-0.05:rm=0.03:bm=-0.04,"
         "curves=all='0/0 0.12/0.08 0.5/0.5 1/1'")
XF = 0.5  # seconds of cross-fade between shots

# (source file, start s, end s, pre-filter). Crops drop broadcaster logos and on-screen captions.
SHOTS = {
    "03-ai-code": [
        ("hackathon-iitb.webm", 21.8, 27.4, "scale=768:576,setsar=1,crop=768:432:0:72"),
        ("hackathon-iitb.webm", 43.5, 49.3, "scale=768:576,setsar=1,crop=768:432:0:72"),
        ("hackathon-iitb.webm", 29.2, 34.2, "scale=768:576,setsar=1,crop=768:432:0:72"),
    ],
    "04-robotics": [
        ("first-robotics.webm", 47.6, 51.6, "crop=1600:900:80:150"),
        ("first-robotics.webm", 51.8, 55.8, "crop=1600:900:80:150"),
        ("first-robotics.webm", 27.2, 30.8, "crop=1600:900:80:150"),
        ("first-robotics.webm", 75.5, 79.5, "crop=1600:900:80:150"),
    ],
    "05-aerospace": [
        # ISRO's file carries a wrong pixel-aspect flag; the raw pixels have the right proportions
        ("pslv-c51.webm", 14.0, 22.0, "setsar=1,crop=704:396:8:98"),
        ("drone-race.webm", 18.9, 21.7, "crop=1600:900:0:150"),
        ("drone-race.webm", 12.6, 15.4, "crop=1600:900:0:150"),
    ],
    "06-nights": [
        ("diwali-iitb.webm", 62.0, 67.5, ""),     # fountain crackers
        ("diwali-iitb.webm", 148.0, 153.5, ""),   # smoke and sparks
        ("diwali-iitb.webm", 13.0, 18.5, ""),     # diyas
    ],
    "07-finale": [
        ("diwali-iitb.webm", 51.0, 56.5, ""),     # rangoli lit with diyas
        ("diwali-iitb.webm", 122.5, 128.0, ""),   # sparkler trails
        ("diwali-iitb.webm", 134.0, 139.5, ""),   # fountain through bokeh
    ],
}

OPTS = {}   # per-clip overrides, e.g. {"fps": 30, "slowmo": 2, "interp": True, "size": "1920:1080"}

CREDITS = {
    "hackathon-iitb.webm": ("Wiki hackathon IITB 2014", "https://commons.wikimedia.org/wiki/File:Wiki_hackathon_iitb_2014.webm", "Harish Satpute", "CC BY-SA 3.0"),
    "first-robotics.webm": ("Magnolia FIRST Robotics Competition 2026", "https://commons.wikimedia.org/wiki/File:Magnolia_FIRST_Robotics_Competition_2026_(SSC2026m000132).webm", "NASA Stennis Space Center", "Public domain"),
    "pslv-c51.webm": ("PSLV-C51 lift-off and on-board camera view", "https://commons.wikimedia.org/wiki/File:PSLV-C51_Lift-off_and_On-board_camera_view.webm", "ISRO", "GODL-India"),
    "drone-race.webm": ("Bijsterhuizen verandert in drone raceparcours", "https://commons.wikimedia.org/wiki/File:Bijsterhuizen_verandert_in_drone_raceparcours.webm", "RN7", "CC BY 3.0"),
    "diwali-iitb.webm": ("Diwali at IITB", "https://commons.wikimedia.org/wiki/File:Diwali_at_IITB.webm", "Jaseem Umar", "CC BY 3.0"),
}


def build(name, shots, src):
    opt = OPTS.get(name, {})
    fps, slow = opt.get("fps", 24), opt.get("slowmo", 1)
    size = opt.get("size", "1280:720")
    mci = "mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1"
    if slow > 1:  # motion-compensated in-between frames, then stretch time
        timing = f"minterpolate=fps={fps * slow}:{mci},setpts={slow}*(PTS-STARTPTS),fps={fps}"
    elif opt.get("interp"):  # change frame rate with new in-between frames instead of dropped/doubled ones
        timing = f"minterpolate=fps={fps}:{mci},setpts=PTS-STARTPTS"
    else:
        timing = f"fps={fps},setpts=PTS-STARTPTS"
    args = ["ffmpeg", "-y", "-v", "error"]
    chains, offset, total = [], 0.0, 0.0
    for i, (f, a, b, pre) in enumerate(shots):
        args += ["-ss", f"{a}", "-t", f"{b - a}", "-i", str(src / f)]
        pre = pre + "," if pre else ""
        chains.append(f"[{i}:v]{pre}scale={size}:force_original_aspect_ratio=increase:flags=lanczos,"
                      f"crop={size},setsar=1,setpts=PTS-STARTPTS,{timing},{GRADE},format=yuv420p[s{i}]")
    prev = "[s0]"
    total = (shots[0][2] - shots[0][1]) * slow
    for i in range(1, len(shots)):
        offset = total - XF
        chains.append(f"{prev}[s{i}]xfade=transition=fade:duration={XF}:offset={offset:.3f}[x{i}]")
        prev = f"[x{i}]"
        total = offset + (shots[i][2] - shots[i][1]) * slow
    args += ["-filter_complex", ";".join(chains), "-map", prev, "-an", "-c:v", "libx264", "-preset", "slow",
             "-crf", "17", "-pix_fmt", "yuv420p", str(OUT / f"{name}.mp4")]
    subprocess.run(args, check=True)
    print(f"{name}.mp4  {total:.1f}s")


if __name__ == "__main__":
    src = Path(sys.argv[1])
    only = set(sys.argv[2:])          # optional: names of the clips to rebuild, e.g. 04-robotics 06-nights
    OUT.mkdir(parents=True, exist_ok=True)
    for name, shots in SHOTS.items():
        if not only or name in only:
            build(name, shots, src)
    # merge the footage credits into the photo credits shown in the footer
    cpath = ROOT / "assets" / "credits.json"
    credits = [c for c in json.loads(cpath.read_text(encoding="utf-8")) if not c.get("video")] if cpath.exists() else []
    for label, page, artist, lic in CREDITS.values():
        credits.append({"label": label, "page": page, "artist": artist, "license": lic, "video": True})
    cpath.write_text(json.dumps(credits, indent=1, ensure_ascii=False), encoding="utf-8")
    print(len(credits), "credits")
