/* IIT Bombay — parallax engine.
   Lenis smooths the scroll, GSAP ScrollTrigger maps scroll to motion.
   Every layer with data-depth moves at its own speed: negative = background (lags behind the page),
   positive = foreground (rushes past). The landing hero splits one photo of IIT Bombay into depth layers. */
(() => {
  const root = document.documentElement;
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const finePointer = matchMedia("(hover: hover) and (pointer: fine)").matches;
  const small = () => innerWidth < 700;
  if (reduced) root.classList.add("reduced");

  gsap.registerPlugin(ScrollTrigger);

  /* ── smooth scroll ── */
  let lenis = null;
  if (!reduced && window.Lenis) {
    lenis = new Lenis({ duration: 1.15, easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)), smoothWheel: true });
    lenis.on("scroll", ScrollTrigger.update);
    gsap.ticker.add((t) => lenis.raf(t * 1000));
    gsap.ticker.lagSmoothing(0);
  }
  const scrollToTarget = (target) => {
    if (lenis) lenis.scrollTo(target, { duration: 1.6 });
    else if (target === 0) scrollTo({ top: 0 });
    else target.scrollIntoView();
  };
  document.querySelectorAll('a[href^="#"]').forEach((a) => {
    a.addEventListener("click", (e) => {
      const id = a.getAttribute("href");
      const target = id === "#top" ? 0 : document.querySelector(id);
      if (target === null) return;
      e.preventDefault();
      scrollToTarget(target);
    });
  });

  /* ── chrome: progress bar, nav (transparent over the hero, solid once you scroll), active section ── */
  const bar = document.querySelector(".progress span");
  const nav = document.querySelector(".nav");
  const setChrome = (y, prog) => {
    bar.style.transform = `scaleX(${prog})`;
    nav.classList.toggle("solid", y > 40);
  };
  ScrollTrigger.create({ start: 0, end: "max", onUpdate: (s) => setChrome(s.scroll(), s.progress) });
  setChrome(scrollY, 0);
  document.querySelectorAll(".nav-links a").forEach((a) => {
    const sec = document.querySelector(a.getAttribute("href"));
    if (!sec) return;
    ScrollTrigger.create({
      trigger: sec, start: "top 55%", end: "bottom 55%",
      onToggle: (s) => s.isActive && document.querySelectorAll(".nav-links a").forEach((x) => x.classList.toggle("active", x === a)),
    });
  });

  /* ═══ Landing hero: sky, name and building drift apart as you scroll ═══ */
  const hero = document.querySelector(".hero");
  const hSky = hero.querySelector(".hero-sky");
  const hWord = hero.querySelector(".hero-word");
  const hFront = hero.querySelector(".hero-front");
  let heroTl = null;
  if (!reduced) {
    // The stage is pinned (sticky) for the first 75vh; the timeline runs until the hero has left the screen.
    heroTl = gsap.timeline({
      defaults: { ease: "none", duration: 1 },
      scrollTrigger: { trigger: hero, start: "top top", end: "bottom top", scrub: 0.7, invalidateOnRefresh: true },
    });
    heroTl
      .to(hSky, { yPercent: 7, scale: 1.06 }, 0)                       // far: barely moves
      .to(hWord, { y: () => -innerHeight * 0.3 }, 0)                   // middle: the name rises into the sky…
      .to(hWord, { autoAlpha: 0, duration: 0.4 }, 0.32)                // …and fades before it reaches the nav
      .to(hFront, { scale: 1.16 }, 0)                                  // near: you walk up the path
      .to([".hero-copy", ".hero-facts"], { autoAlpha: 0, y: -60, duration: 0.42 }, 0)
      .to(".scroll-cue", { autoAlpha: 0, duration: 0.1 }, 0);

    // each layer leans toward the mouse by a different amount, so the depth reads even when you're not scrolling
    if (finePointer) {
      const lean = [[hSky, -10], [hWord, 18], [hFront, 30]].map(([el, amt]) => [gsap.quickTo(el, "x", { duration: 1.1, ease: "power3" }), amt]);
      addEventListener("pointermove", (e) => {
        const nx = (e.clientX / innerWidth) * 2 - 1;
        if (hero.getBoundingClientRect().bottom > 0) lean.forEach(([to, amt]) => to(nx * amt));
      }, { passive: true });
    }
  }

  /* ═══ generic depth parallax ═══ */
  const depthScale = () => (small() ? 0.55 : 1);
  if (!reduced) {
    document.querySelectorAll("[data-depth]").forEach((el) => {
      const d = parseFloat(el.dataset.depth);
      const host = el.closest("section") || el.parentElement;
      gsap.fromTo(el,
        { y: () => d * innerHeight * 0.5 * depthScale() },
        { y: () => -d * innerHeight * 0.5 * depthScale(), ease: "none",
          scrollTrigger: { trigger: host, start: "top bottom", end: "bottom top", scrub: true, invalidateOnRefresh: true } });
    });

    // images drifting inside their frames (window effect)
    document.querySelectorAll("[data-inner]").forEach((img) => {
      gsap.fromTo(img, { yPercent: -9 }, {
        yPercent: 9, ease: "none",
        scrollTrigger: { trigger: img.parentElement, start: "top bottom", end: "bottom top", scrub: true },
      });
    });

    /* ── venue: vertical scroll drives the lake sideways; the tags race ahead at 2× ── */
    const venue = document.querySelector(".venue");
    const track = venue.querySelector(".venue-track");
    const pano = venue.querySelector(".venue-pano");
    const tags = venue.querySelector(".venue-tags");
    const venueST = { trigger: venue, start: "top top", end: "bottom bottom", scrub: true, invalidateOnRefresh: true };
    gsap.to(track, { x: () => -Math.max(0, pano.offsetWidth - innerWidth), ease: "none", scrollTrigger: venueST });
    gsap.fromTo(tags, { x: () => innerWidth * 0.2 }, { x: () => -tags.scrollWidth, ease: "none", scrollTrigger: { ...venueST } });
    gsap.fromTo(".venue-copy", { y: 60, opacity: 0 }, {
      y: 0, opacity: 1, ease: "none", scrollTrigger: { trigger: venue, start: "top 60%", end: "top top", scrub: true },
    });
    pano.addEventListener("load", () => ScrollTrigger.refresh());

    /* ── competitions rail: vertical scroll → horizontal travel; numerals drift against it ── */
    const compete = document.querySelector(".compete");
    const rail = compete.querySelector(".rail");
    const railDist = () => Math.max(0, rail.scrollWidth - innerWidth);
    const sizeCompete = () => { compete.style.height = `${railDist() + innerHeight * 1.25}px`; };
    sizeCompete();
    ScrollTrigger.addEventListener("refreshInit", sizeCompete);
    const railTween = gsap.to(rail, {
      x: () => -railDist(), ease: "none",
      scrollTrigger: { trigger: compete, start: "top top", end: "bottom bottom", scrub: true, invalidateOnRefresh: true },
    });
    rail.querySelectorAll(".card-n").forEach((n) => {
      gsap.fromTo(n, { x: 110 }, {
        x: -110, ease: "none",
        scrollTrigger: { trigger: n.parentElement, containerAnimation: railTween, start: "left right", end: "right left", scrub: true },
      });
    });

    /* ── numbers: two marquees run against each other and lean with scroll speed ── */
    const m1 = document.querySelector(".m1 div");
    const m2 = document.querySelector(".m2 div");
    const skewTo = gsap.quickTo([m1, m2], "skewX", { duration: 0.5, ease: "power3" });
    ScrollTrigger.create({
      trigger: ".numbers", start: "top bottom", end: "bottom top",
      onUpdate: (s) => {
        gsap.set(m1, { xPercent: -s.progress * 35 });
        gsap.set(m2, { xPercent: -45 + s.progress * 35 });
        skewTo(gsap.utils.clamp(-14, 14, s.getVelocity() / -250));
      },
    });

    /* ── legends: portraits lean toward the pointer, each by its own amount ── */
    if (finePointer) {
      const legends = document.querySelector(".legends");
      const cards = [...legends.querySelectorAll("[data-tilt]")].map((el) => {
        gsap.set(el, { transformPerspective: 900 });
        return { el, t: +el.dataset.tilt, x: gsap.quickTo(el, "x", { duration: 0.8, ease: "power3" }),
          ry: gsap.quickTo(el, "rotationY", { duration: 0.8, ease: "power3" }),
          rx: gsap.quickTo(el, "rotationX", { duration: 0.8, ease: "power3" }) };
      });
      legends.addEventListener("pointermove", (e) => {
        const r = legends.getBoundingClientRect();
        const nx = ((e.clientX - r.left) / r.width) * 2 - 1;
        const ny = ((e.clientY - r.top) / r.height) * 2 - 1;
        cards.forEach((c) => { c.x(nx * c.t); c.ry(nx * 7); c.rx(-ny * 5); });
      });
      legends.addEventListener("pointerleave", () => cards.forEach((c) => { c.x(0); c.ry(0); c.rx(0); }));
    }
  }

  /* ── a photo that fails to load takes its frame with it instead of showing broken alt text ── */
  document.querySelectorAll("figure img").forEach((img) => {
    const drop = () => img.closest("figure").classList.add("missing");
    if (img.complete && img.naturalWidth === 0 && img.getAttribute("loading") !== "lazy") drop();
    img.addEventListener("error", drop);
  });

  /* ── reveal on scroll (+ fallback for skipped IO callbacks on instant jumps) ── */
  const io = new IntersectionObserver((es) => es.forEach((e) => e.isIntersecting && e.target.classList.add("in")), { threshold: 0.15 });
  document.querySelectorAll("[data-reveal]").forEach((el) => io.observe(el));
  const revealNow = () => document.querySelectorAll("[data-reveal]:not(.in)").forEach((el) => {
    const r = el.getBoundingClientRect();
    if (r.top < innerHeight * 0.9 && r.bottom > 0) el.classList.add("in");
  });
  ScrollTrigger.create({ start: 0, end: "max", onUpdate: revealNow });
  revealNow();

  /* ── counters ── */
  const counters = new IntersectionObserver((es) => es.forEach((e) => {
    if (!e.isIntersecting) return;
    counters.unobserve(e.target);
    const el = e.target;
    const to = +el.dataset.count, dec = +(el.dataset.decimals || 0), suf = el.dataset.suffix || "", pre = el.dataset.prefix || "";
    if (reduced) return;
    const o = { v: 0 };
    gsap.to(o, {
      v: to, duration: 1.8, ease: "power3.out",
      onUpdate: () => { el.textContent = pre + o.v.toLocaleString("en-IN", { minimumFractionDigits: dec, maximumFractionDigits: dec }) + suf; },
    });
  }), { threshold: 0.6 });
  document.querySelectorAll("[data-count]").forEach((el) => counters.observe(el));

  /* ── background loops: load when near, play only while visible ── */
  const vids = new IntersectionObserver((es) => es.forEach((e) => {
    const v = e.target;
    if (e.isIntersecting) {
      if (!v.src) { v.src = v.dataset.src; v.load(); }
      if (!reduced) v.play().catch(() => {});
    } else if (!v.paused) v.pause();
  }), { rootMargin: "40% 0px" });
  document.querySelectorAll("video[data-src]").forEach((v) => vids.observe(v));

  /* ── photo credits (Wikimedia Commons licences require attribution) ── */
  fetch("assets/credits.json").then((r) => r.json()).then((list) => {
    const ul = document.getElementById("credits-list");
    ul.innerHTML = "";
    list.forEach((c) => {
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = c.page; a.target = "_blank"; a.rel = "noopener"; a.textContent = c.label;
      li.append(a, ` by ${c.artist}, ${c.license}, via Wikimedia Commons`);
      ul.append(li);
    });
  }).catch(() => { document.getElementById("credits-list").innerHTML = "<li>See assets/credits.json</li>"; });

  /* ── keep measurements honest once fonts and images settle ── */
  document.fonts?.ready.then(() => ScrollTrigger.refresh());
  addEventListener("load", () => ScrollTrigger.refresh());

  // handles for testing in a background tab (rAF can be paused there)
  window.__tf = { lenis, hero: { at: (p) => heroTl && heroTl.progress(p) } };
})();
