"""Turn the section clips (Commons footage, or your own Google Flow clips) into seamless, muted web loops + posters.

usage:  python tools/make_loops.py            (run from the site folder)

Reads clips/src/*.mp4 and writes
  assets/video/<name>.mp4      1280x720 H.264, crossfaded so the end flows back into the start
  assets/video/<name>.webp     poster frame shown before the video starts
Drop a new clip into clips/src with the same file name to replace a section's video.
Set DELOGO below if your generator stamps a watermark (x:y:w:h in 1280x720 pixels), or "" for none.
"""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "clips" / "src"
OUT = ROOT / "assets" / "video"
DELOGO = ""                                  # e.g. "delogo=x=1126:y=566:w=68:h=68," for a watermark
# per-clip overrides: name -> (size, fps, crf)
SPECIAL = {}
FADE = 1.0                                   # seconds of crossfade between the end and the start


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return float(json.loads(out)["format"]["duration"])


def loop(src):
    name = src.stem.split("-", 1)[-1]          # 04-robotics.mp4 -> robotics
    T = duration(src)
    size, fps, crf = SPECIAL.get(name, ("1280:720", 24, 25))
    base = f"{DELOGO}scale={size}:flags=lanczos,fps={fps},setsar=1,format=yuv420p"
    graph = (f"[0:v]{base},split[x][y];"
             f"[x]trim={FADE}:{T},setpts=PTS-STARTPTS[a];"
             f"[y]trim=0:{FADE},setpts=PTS-STARTPTS[b];"
             f"[a][b]xfade=transition=fade:duration={FADE}:offset={T - 2 * FADE:.3f},format=yuv420p[v]")
    mp4 = OUT / f"{name}.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-filter_complex", graph, "-map", "[v]", "-an",
                    "-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-profile:v", "high", "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart", str(mp4)], check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(mp4), "-frames:v", "1", "-q:v", "80",
                    str(OUT / f"{name}.webp")], check=True)
    print(f"{name}: {mp4.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for clip in sorted(SRC.glob("*.mp4")):
        loop(clip)
