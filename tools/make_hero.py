"""Split the Main Building photo into parallax layers: the sky, and everything in front of it.

usage:  python tools/make_hero.py <Main_building_in_IIT_Bombay.jpg>

Writes assets/img/hero-sky.webp   (full photo, the far layer)
       assets/img/hero-front.webp (building, palms, lawn with a transparent sky, the near layer)
The page puts the giant title between the two, so the building stands in front of the words.
Sky detection: sky-coloured pixels in the upper part seed OpenCV's GrabCut, and only background
connected to the top edge counts as sky (so white walls never get punched out).
"""
import sys
from pathlib import Path

import cv2
import numpy as np

OUT = Path(__file__).resolve().parent.parent / "assets" / "img"
W_OUT = 2400


def sky_mask(img):
    h, w = img.shape[:2]
    small = cv2.resize(img, (1280, round(h * 1280 / w)), interpolation=cv2.INTER_AREA)
    sh, sw = small.shape[:2]
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    H, S, V = hsv[..., 0].astype(int), hsv[..., 1].astype(int), hsv[..., 2].astype(int)
    rows = np.arange(sh)[:, None] / sh
    blue = (H >= 90) & (H <= 130) & (S > 25) & (V > 120)
    cloud = (S < 45) & (V > 170)
    skyish = (blue | cloud) & (rows < 0.62)

    gc = np.full((sh, sw), cv2.GC_PR_FGD, np.uint8)
    gc[skyish] = cv2.GC_PR_BGD
    gc[skyish & (rows < 0.22)] = cv2.GC_BGD
    gc[np.broadcast_to(rows > 0.72, gc.shape)] = cv2.GC_FGD
    bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(small, gc, None, bgd, fgd, 6, cv2.GC_INIT_WITH_MASK)
    bg = np.isin(gc, (cv2.GC_BGD, cv2.GC_PR_BGD)).astype(np.uint8)

    # sky = background regions that touch the top edge
    n, lab = cv2.connectedComponents(bg, connectivity=4)
    top = set(np.unique(lab[0][bg[0] > 0]))
    sky = np.isin(lab, list(top)).astype(np.uint8) if top else np.zeros_like(bg)
    sky = cv2.morphologyEx(sky, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    return cv2.resize(sky.astype(np.float32), (w, h), interpolation=cv2.INTER_LINEAR)


def main(path):
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    sky = sky_mask(img)
    alpha = 1.0 - cv2.GaussianBlur(sky, (0, 0), 1.6)          # soft 1–2 px edge, no halo
    h, w = img.shape[:2]
    size = (W_OUT, round(h * W_OUT / w))
    small = cv2.resize(img, size, interpolation=cv2.INTER_AREA)
    a = cv2.resize(alpha, size, interpolation=cv2.INTER_AREA)
    OUT.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(OUT / "hero-sky.webp"), small, [cv2.IMWRITE_WEBP_QUALITY, 82])
    rgba = np.dstack([small, np.clip(a * 255, 0, 255).astype(np.uint8)])
    cv2.imwrite(str(OUT / "hero-front.webp"), rgba, [cv2.IMWRITE_WEBP_QUALITY, 86])
    for f in ("hero-sky.webp", "hero-front.webp"):
        print(f, (OUT / f).stat().st_size // 1024, "KB")
    print(f"sky covers {sky.mean() * 100:.0f}% of the frame")


if __name__ == "__main__":
    main(sys.argv[1])
