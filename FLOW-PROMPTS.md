# Videos: where they come from, and how to replace them

Every video on the page is built from five clips in `clips/src/`. Right now they are **real,
freely licensed footage from Wikimedia Commons** (authors and licences are listed in the page footer):

| Clip | Used for | Current footage |
|---|---|---|
| `03-ai-code.mp4` | Life 01, code & startups | Wiki hackathon at IIT Bombay, 2014 (Harish Satpute, CC BY-SA 3.0) |
| `04-robotics.mp4` | Life 02, engineering teams | FIRST Robotics Competition 2026 (NASA, public domain) |
| `05-aerospace.mp4` | Life 03, space | ISRO PSLV-C51 lift-off (GODL-India) + FPV drone racers (RN7, CC BY 3.0) |
| `06-nights.mp4` | Life 04, festivals | Diwali at IIT Bombay (Jaseem Umar, CC BY 3.0) |
| `07-finale.mp4` | Admissions | Diwali at IIT Bombay (Jaseem Umar, CC BY 3.0) |

To rebuild after changing anything:

```
python tools/make_clips.py <folder with the downloaded .webm files>   # only for the Commons footage
python tools/make_loops.py     # section loops (03–07)
```

## Swapping in your own Google Flow clips

Sign in at flow.google.com → New project → Text to video. Use **16:9, 8 seconds**. Download the MP4,
save it in `clips/src/` under the clip's name (e.g. `04-robotics.mp4`), then run
`make_loops.py`. The page plays everything muted, so the audio Flow adds doesn't matter. Keep the look
realistic and warm: golden-hour light, slow camera, no text or logos.

**03-ai-code**
> Students coding on laptops through the night at a university hackathon in India, warm desk lamps,
> code reflecting on glasses, slow dolly along the tables. Photorealistic, no text or logos.

**04-robotics**
> A student-built combat robot sends sparks flying inside a glass-walled arena, crowd silhouettes
> behind, warm stage lights. Slow-motion, photorealistic, no text or logos.

**05-aerospace**
> A rocket lifting off from a coastal launch pad in India at dusk, bright plume and billowing smoke,
> then FPV racing drones slicing through glowing gates. Photorealistic, no text.

**06-nights**
> Night festival on an Indian university campus: fountain fireworks, sparklers and drone lights over
> a cheering crowd, warm gold bokeh. Photorealistic, slow camera, no text.

**07-finale**
> A rangoli lit with clay diyas on a campus lawn at night, fireworks blooming softly in the
> background. Photorealistic, warm, slow push-in, no text.

If you replace a Commons clip with your own, also remove its line from `CREDITS` in
`tools/make_clips.py` (or delete its entry from `assets/credits.json`).
