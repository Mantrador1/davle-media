/* DAVLE watches — motion and small behaviours. The page works fully without this file. */
(function () {
  "use strict";

  // keep the source of the visit on every Play link (?from=instagram_bio), so the Console still sees where buyers came from
  const from = new URLSearchParams(location.search).get("from");
  if (from && /^[a-z0-9_]{2,40}$/.test(from)) {
    document.querySelectorAll('a[href*="play.google.com"]').forEach(a => { a.href = a.href.replace("utm_source%3Dwebsite", "utm_source%3D" + from); });
    document.querySelectorAll('a.card, a.mini').forEach(a => { if (!a.href.includes("from=")) a.href += (a.href.includes("?") ? "&" : "?") + "from=" + from; });
  }

  // colour swatches: show that colour's dial and tint the page
  const layers = [...document.querySelectorAll(".stage .dial-layer")];
  const swatches = [...document.querySelectorAll(".swatches button")];
  let current = 0;
  function showColour(i) {
    if (i === current || !layers[i]) return;
    current = i;
    layers.forEach((l, k) => { l.style.opacity = k === i ? 1 : 0; });
    swatches.forEach((b, k) => b.setAttribute("aria-pressed", k === i));
    const c = swatches[i] && swatches[i].style.getPropertyValue("--c");
    if (c) document.body.style.setProperty("--accent", c);
  }
  swatches.forEach((b, i) => b.addEventListener("click", () => showColour(i)));

  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  window.addEventListener("load", () => {
    if (reduce || !window.gsap || !window.ScrollTrigger) return;
    gsap.registerPlugin(ScrollTrigger);
    if (window.Lenis) {
      const lenis = new Lenis({ lerp: 0.11 });
      lenis.on("scroll", ScrollTrigger.update);
      gsap.ticker.add(t => lenis.raf(t * 1000));
      gsap.ticker.lagSmoothing(0);
      document.querySelectorAll('a[href^="#"]').forEach(a => a.addEventListener("click", ev => {
        const t = document.querySelector(a.getAttribute("href")); if (t) { ev.preventDefault(); lenis.scrollTo(t, { offset: -70 }); }
      }));
    }
    const mm = gsap.matchMedia();

    // hero: the photo drifts and the type lifts away as you scroll past it
    gsap.to(".hero-img img", { yPercent: 8, scale: 1.06, ease: "none", scrollTrigger: { trigger: ".hero", start: "top top", end: "bottom top", scrub: true } });
    gsap.to(".hero-txt", { yPercent: -18, opacity: 0.15, ease: "none", scrollTrigger: { trigger: ".hero", start: "top top", end: "bottom top", scrub: true } });
    gsap.from(".hero-txt > *", { y: 26, opacity: 0, duration: 0.9, ease: "power3.out", stagger: 0.08, clearProps: "transform,opacity" });

    // face page: readings light up one by one beside the dial; colours follow the scroll
    document.querySelectorAll(".feat").forEach(el => {
      gsap.fromTo(el, { opacity: 0.25, x: 18 }, { opacity: 1, x: 0, ease: "none",
        scrollTrigger: { trigger: el, start: "top 80%", end: "top 45%", scrub: true } });
    });
    const stage = document.querySelector(".stage");
    if (stage) gsap.fromTo(stage, { rotate: -8, scale: 0.92 }, { rotate: 0, scale: 1, ease: "none",
      scrollTrigger: { trigger: ".anatomy", start: "top 85%", end: "top 15%", scrub: true } });
    const colours = document.querySelector(".colours");
    if (colours && layers.length > 1) {
      ScrollTrigger.create({ trigger: colours, start: "top 70%", end: "bottom 40%",
        onUpdate: self => showColour(Math.min(layers.length - 1, Math.floor(self.progress * layers.length))) });
    }

    // always-on: the active dial fades down to the always-on layer as you scroll
    const on = document.querySelector(".aod-on");
    if (on) gsap.fromTo(on, { opacity: 1 }, { opacity: 0, ease: "none", scrollTrigger: { trigger: ".aod", start: "top 65%", end: "center 45%", scrub: true } });

    // home: the dial reel becomes a horizontal pinned walk on wide screens
    mm.add("(min-width: 821px)", () => {
      const reel = document.querySelector(".reel-stage");
      if (!reel) return;
      reel.style.overflow = "visible";
      const dist = () => reel.scrollWidth - window.innerWidth;
      gsap.to(reel, { x: () => -dist(), ease: "none",
        scrollTrigger: { trigger: ".reel", start: "top top", end: () => "+=" + dist(), pin: true, scrub: 0.6, invalidateOnRefresh: true } });
      gsap.utils.toArray(".reel-item img").forEach(img => gsap.fromTo(img, { rotate: -20 }, { rotate: 20, ease: "none",
        scrollTrigger: { trigger: ".reel", start: "top top", end: () => "+=" + dist(), scrub: true } }));
    });

    // cards rise in, once
    ScrollTrigger.batch(".card, .mini, .path, .steps li", { start: "top 88%", once: true,
      onEnter: els => gsap.from(els, { y: 40, opacity: 0, duration: 0.8, ease: "power3.out", stagger: 0.08, clearProps: "transform,opacity" }) });
  });
})();
