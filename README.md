# IIT Bombay: parallax scroll page

A one-page parallax scroll through the Indian Institute of Technology Bombay: its history, campus,
student life, departments, people and admissions. Plain HTML, CSS and JavaScript, no build step.

## Run it

```
python tools/serve.py
```

Then open http://localhost:4190. Any static host works too (GitHub Pages, Netlify, …).

## What's on the page

| Section | Parallax trick |
|---|---|
| Landing | The Main Building split into three layers: sky at the back, a giant "IIT BOMBAY" in the middle, building and palms in front. Scrolling lifts the name into the sky while you walk up the path; every layer leans toward the mouse |
| About | Photo collage where every frame floats at its own depth over a giant drifting "1958" |
| History | Split layout; the Convocation Hall photo drifts inside its frame |
| Campus | Vertical scroll slides the Powai Lake panorama sideways while the tags race ahead |
| Life | Four chapters (code & startups, engineering teams, space, festivals): video background (slow), outlined numeral (medium), photo card (fast) |
| Departments | Pinned horizontal rail; each card's numeral drifts against the rail |
| People | Portraits at three depths that tilt toward the pointer, plus notable alumni |
| Numbers | Counters plus two marquees running opposite ways and leaning with scroll speed |
| At a glance, gallery, admissions | Background layers lag behind; gallery tiles each scroll at their own speed |

Respects `prefers-reduced-motion`: no smooth scrolling and no parallax, only the final readable layout.

## Files

```
index.html  css/style.css  js/main.js        the page
vendor/                                      GSAP 3.12.5 + ScrollTrigger, Lenis 1.1.13
assets/img/                                  graded photos + the two hero layers
assets/video/                                section background loops
assets/credits.json                          photo and video credits shown in the footer
tools/                                       serve, make_hero, make_images, make_clips, make_loops
FLOW-PROMPTS.md                              where each video comes from + prompts to replace them
```

## Credits

Photos and video footage are from Wikimedia Commons (CC BY, CC BY-SA, CC0, public domain and
GODL-India); each author and licence is listed in the footer (from `assets/credits.json`).
Facts come from public sources; check iitb.ac.in for the official ones. This is a fan-made concept,
not an official IIT Bombay website.
