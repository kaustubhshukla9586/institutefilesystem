# Lacuna UI: design direction and UI specification

**Build Lacuna in a single design system called "Dossier": warm near-black, one amber signal and type-led layouts. In it, a redaction is drawn as a cut-out hole with a lit edge, not as a black bar.** On a near-black page, the black bar you proposed is close to invisible: `#1B1915` on `#0C0B09` measures **1.12:1**. A black bar on a dark page therefore fails as a meaningful graphic, and it gets the metaphor backwards. In a dark interface, a gap should look like a gap.

## TL;DR
- **Direction:** I'm choosing "Dossier". Keep your ink, bone and amber. Retire red for "denied", because a restriction is the product working, not an error; red is now kept for integrity failures only. Redaction becomes a quantised-width "cut-out" with a 3.5:1 edge, which meets non-text contrast and doesn't leak the length of the hidden text. Display type stays **Anybody**, with its width axis literally tied to clearance level. Data type is **Martian Mono**, whose width axis I verified at 75–112.5. Body stays **Hanken Grotesk**.
- **Motion and 3D:** the landing is GSAP 3.15 + ScrollTrigger driven by Lenis (all free since GSAP 3.13; I verified this).\[1\] The app uses native scroll with no Lenis and no scroll-linked motion. Clearance City is an orthographic, instanced react-three-fiber scene. It has four quality tiers (T3–T0) driven by measured frame time, and an SVG "city plan" fallback that doubles as the screen-reader and keyboard equivalent.
- **Performance:** the landing hero is text, so its LCP is a headline, not an image. That makes the 2.5 s target on mid-range Android realistic, provided you preload one subsetted display font, ship no hero image, lazy-load all WebGL behind an IntersectionObserver plus a tier check, and keep no more than 12 sized AVIF/WebP images on the whole page.

---

## 0. Skills, method and how to read the flags

- **Skills:** no `frontend-design`, design-inspiration or `dataviz` skill was available in this environment; I had no skill-loading tool. I applied their usual principles from memory: commit to one bold aesthetic, distinctive type over default stacks, spend boldness in one place, no generic card grids, and charts with direct labels, no decoration and a table fallback. Treat this as "skills not used, principles applied".
- **Internal context:** I searched Google Drive for "Lacuna" and "Thornwick" and found nothing, so everything below comes from the brief.
- **Flags used throughout:**
  - **[V]** I opened the page and read it.
  - **[S]** Taken from a search-result excerpt of the page, not opened in full.
  - **[SA]** Verified by my research sub-agent (its own source quotes).
  - **[M]** From memory, not verified this session.
- **Research budget hit:** I opened six pages in full, so the brief's target of 8–12 *opened* site studies was not met. Section R1 says which studies rest on full reads and which on excerpts.

---

## R. Research findings (tasks 1–5)

### R1. Site and product studies

| # | Site / product | Group | What it does | Technique that makes it work | Replicable with your stack | Not replicable / avoid | Flag |
|---|---|---|---|---|---|---|---|
| 1 | translate-wf.com (Weglot × Finsweet) | a | A promo story for a Webflow translation plugin, told as one long scroll. | Scroll-narrated copy beats ("IMAGINE" repeated three times, "the language barrier", "NO"). A clickable "Click to Break" bar-breaker. A word-swap gag ("pie / torta / tarte", "la montre / the watch / часы"). Heavy use of flat SVG illustrations. | The **word-swap headline** is exactly the mechanic for the clearance toggle. The "break the bar" interaction maps onto breaking a redaction bar. Scroll-sequenced statements map onto the pipeline story. | Illustration-led art direction (forbidden here). More than 30 separate SVG illustration requests. | [V] page. The claim "most viewed and cloned Webflow website of 2020" is [S] from Finsweet's portfolio.\[2\]\[3\] |
| 2 | checkpointresearch.ca | a | A Webflow marketing site for an SR&ED consultancy. | A type-led hero ("Your R&D. Our expertise. Zero anxiety."). A **bracketed rotating word**, "Unlocking capital in [Pharmaceuticals]". Bracket-wrapped nav labels ("[ Learn ]").\[4\] | Bracketed variable slots are a strong layout precedent for `[PERSON_7F3A]` tokens and the clearance-rewritten headline. | Its partner strip stacks **three image layers per logo** (WebP plus two SVGs). I counted at least 9 logos × 3 = 27 requests in the markup.\[4\] That is the anti-pattern your budget forbids. | [V] |
| 3 | igloo.inc (Abeto × Bureaux), via the Awwwards case study | b | Awwwards Site of the Year 2024: a scroll-driven WebGL journey. | They render UI text in WebGL so glitch and scramble effects don't force style recalculation. They measure performance continuously "to ensure smooth navigation on low-end devices". Custom geometry exporters. Shaders are compiled during load and in the background. The intro is real-time, not video.\[5\] | Measure while you build. Precompute geometry. Warm shaders before the reveal. Real-time intros instead of video. | WebGL-rendered UI text: it breaks screen readers and text selection, so keep all Lacuna text in the DOM. Houdini procedural pipelines. | [V] case study; the award is [S]\[6\]\[7\] |
| 4 | Linear (redesign write-up) | c | A dense, dark product UI. | "Inverted L" global chrome (sidebar plus header) that frames the main view. The redesign aimed to "reduce visual noise, maintain visual alignment, and increase the hierarchy and density". Theme colour `#08090a`.\[8\] | The admin sidebar shell, the density discipline and a surface ladder instead of shadows. | Its blue-black canvas and single cool accent are the "generic dark SaaS" look you must not be mistaken for. | [V] |
| 5 | RelativityOne Redact (help docs) | c | Professional legal redaction and review. | Typed redactions (Black, White, Text, Cross, Inverse, Full-page). A **Markup Navigation pane** that lists every redaction by page. "Quality Review" with Accept/Reject. Reports carry "Markup Reason", "Markup Created By", "Markup Timestamp" and "Original Text".\[9\]\[10\]\[11\]\[12\] | Lacuna's reveal log and version diff should copy this *information model*: every redaction has a reason, author and timestamp, and admins can see the original. Also a per-document redaction navigator. | Image-based box drawing (Lacuna redacts text before storage). | [S] |
| 6 | Google Docs "You need access" | c | A permission wall. | One clear primary action, **Request access**, an optional explanation field, and the owner is notified with the requester, file and message.\[13\] | Lacuna's Restricted state: one action, an optional reason, and a visible "what happens next". | Its generic illustration and its account-switch prompt. | [S] |
| 7 | WorkOS / Clerk / PubNub audit-log UIs | c | Admin-facing audit trails. | Tables sorted newest-first. Filter by event type and time range. Export to CSV. Stream to a SIEM. Typed event names (e.g. `instance.account_portal.updated`).\[14\]\[15\]\[16\] | Typed event names in mono, newest-first, filters, export, and an "integrity" column the others lack. | None of them show tamper-evidence, which is Lacuna's differentiator. | [S] |
| 8 | Martian Mono specimen (martians-font.webflow.io) | a | A type microsite. | Animated width and weight axes as the hero spectacle ("4 styles on the width, 7 weights").\[17\] | Axis animation as a hero mechanic. | — | [S] |

Studies 5–8 rest on excerpts only. A builder should open Relativity's "Reviewing markups" page and one audit-log UI before finalising the admin log.

### R2. Current techniques, checked against current versions

- **Lenis + ScrollTrigger:** the documented pattern is `lenis.on('scroll', ScrollTrigger.update)`, `gsap.ticker.add(t => lenis.raf(t*1000))` and `gsap.ticker.lagSmoothing(0)` [S, Lenis README].\[18\] With `lenis/react`, set `autoRaf: false` when GSAP drives the loop [S].\[19\] The old `@studio-freight/lenis` package is deprecated and renamed `lenis` [SA].\[20\]
- **Pinned sequences on mobile:**
  - `ScrollTrigger.config({ ignoreMobileResize: true })`: "vertical resizes (of 25% of the viewport height) on touch-only devices won't trigger a ScrollTrigger.refresh()" [SA, GSAP docs].\[21\]
  - `normalizeScroll(true)` "intercepts native scroll behavior and handles it on the JavaScript thread". The docs warn that iOS phones in portrait still force the address-bar show/hide [SA].\[22\]\[23\]
  - **Decision:** don't use `normalizeScroll` (it fights Lenis and native momentum). Use `ignoreMobileResize`, size with `svh` units, and keep mobile pins short.
  - `pinType` defaults to `fixed` only when the scroller is `<body>`, and any transformed ancestor breaks `fixed`.\[24\]\[25\] **Decision:** no transforms on ancestors of pinned sections [SA].
- **View/page transitions:**
  - The React Router docs are on **8.5.1** [V].
  - Per the docs page excerpt, Router's own `viewTransition` props and `useViewTransitionState` are **deprecated in favour of React's `<ViewTransition>`**, which needs React and React DOM 19.3+. Router already wraps navigations in `startTransition` [S of the page I opened; the body was truncated].\[26\]
  - React 19.3.1 is current (14 Oct 2026) [SA].\[27\]
  - **Decision:** wrap `<Outlet>` in a persistent `<ViewTransition>`. Where `document.startViewTransition` is missing, fall back to an instant swap plus a 140 ms opacity fade.
- **Variable-font axis animation:** animate `font-variation-settings` or `font-stretch` on headline elements only; each frame triggers text layout, so keep it to one or two elements [M]. Anybody's width axis is live on Google Fonts (shown as "Width 100" default) [S].\[28\]\[29\] Martian Mono: `wdth 75–112.5`, `wght 100–800`, OFL [S, Fontsource].\[30\] Mona Sans: `wght 200–900`, `font-stretch 75%–125%`, OFL [S].\[31\]
- **SVG/clip-path text reveals:** `clip-path: inset()` is GPU-friendly and needs no SVG. Use `inset(0 100% 0 0)` → `inset(0 0 0 0)` for the reveal wipe. SplitText is now free [V, GSAP 3.13 post].\[1\] Always restore the unsplit text for assistive tech (SplitText's `aria` handling, or keep an sr-only copy) [M].
- **Custom cursor with touch fallback:** enable only under `(hover: hover) and (pointer: fine)`. Never hide the native cursor over text inputs [M].
- **R3F instancing and LOD:** the R3F docs (v9.8.2) say "no more than 1000 [draw calls] as the very maximum, and optimally a few hundred or less". Use `<instancedMesh>`, Drei `<Detailed>` for LOD, `frameloop="demand"` with `invalidate()`, and `PerformanceMonitor` with `onIncline`/`onDecline`/`flipflops`/`onFallback`.\[32\] `performance.regress()` does nothing unless you listen to `performance.current` [V].\[32\]
- **Reduced motion with personality:** WCAG lists three sufficient routes: avoid unnecessary animation, provide a site-wide toggle, or honour the OS setting [V]. Opacity and colour changes are not "motion animation"; the definition now also no longer excludes blur, per errata [V].\[33\] So the reduced-motion mode keeps **cross-fades, colour shifts and instant redaction state changes** and drops translation, scale, parallax and pinning.
- **Licences:**
  - GSAP: "100% FREE including ALL of the bonus plugins … even for commercial use" (3.13, 29 Apr 2025) [V].\[1\]
  - The Standard "No Charge" licence forbids only use in "tools that allow users to build visual animations without code" that compete with Webflow, and explicitly permits "use of GSAP Products on any website, web application, or digital interface" [SA].\[34\] **Lacuna is a permitted use.**
  - Fonts: all four candidates are OFL-1.1.
    - Martian Mono [S].\[35\]
    - Mona Sans [S].\[36\]
    - Anybody: Fontsource lists "License: OFL-1.1", © "The Anybody Project Authors" (Etcetera Type Co., designer Tyler Finck).\[37\]
    - Hanken Grotesk: Fontsource lists "License: OFL-1.1" (Alfredo Marco Pradil / Hanken Design Co.).\[38\]

### R3. Patterns for the hard states
- **"You can't see this" without an error wall:** Google's pattern is one action, an optional reason and a stated consequence [S].\[13\] Lacuna adds to this: it *names the policy*, *refuses to confirm existence*, and puts the denial in the audit trail visibly ("This question was logged. So is this refusal.").
- **Trust in audit logs:** newest-first tables, typed events, filters, export [S].\[14\]\[16\] Tamper-evidence has to be **shown**: show the hash prefix per row, a chain status with "last verified" time, and a one-click verify that reports the exact break index.
- **Redaction review:** a reason, author and timestamp on every redaction, a navigator pane, and accept/reject QA [S].\[10\]\[11\] These feed the OCR review, version diff and reveal log.

### R4. Accessibility of motion and 3D
- SC 2.3.3 (AAA) is above your AA bar, but treat it as a design rule anyway, because vestibular reactions "include nausea, migraine headaches, and potentially needing bed rest" [V].\[33\]
- SC 2.2.2 (Level A) applies to anything that auto-plays for more than 5 s, such as the City's idle drift or a marquee: it must have pause, stop or hide [M].\[39\]
- 3D needs a DOM mirror for screen readers and keyboard, an orthographic camera (no dolly-zoom vertigo), and no auto-rotation.

### R5. Performance
- **Target:** LCP ≤ 2.5 s at the 75th percentile, segmented by mobile/desktop [S, web.dev].\[40\]
- **Budget for the landing** (my numbers; [M] for library sizes):

| Asset | Budget (gzip/brotli) |
|---|---|
| HTML + critical CSS | ≤ 30 KB |
| Initial JS (React, router, GSAP core + ScrollTrigger, Lenis, landing code) | ≤ 170 KB |
| Fonts preloaded | 1 file (Anybody, latin subset, wdth+wght), ≤ 70 KB |
| Fonts deferred | Hanken Grotesk ≤ 45 KB, Martian Mono ≤ 50 KB |
| Images on the whole landing | ≤ 12, ≤ 400 KB total, AVIF with WebP fallback, explicit `width`/`height` |
| three + R3F + Drei (lazy) | loaded only when the City teaser is 1 viewport away **and** tier ≥ 2 |
| City data | precomputed binary `Float32Array` of instance matrices, ≤ 120 KB |

- **Cut list for mid-range Android:** post-processing (bloom), shadows, `MeshStandardMaterial`, Lottie/Rive on the landing, video, and any image above the fold.

---

## A. Three design directions

### Direction 1: "Dossier" (chosen)
An archive at night, read by desk lamp. Warm ink, bone paper tones, one amber signal that means "cleared". The layout is type-led: oversized Anybody headlines whose **width tracks clearance**, ledger hairlines like a filing form, and redactions drawn as **cut-outs to the void** with a lit edge. No imagery except documents and data.
- **Colours:** ink `#0C0B09`, bone `#EDE7DA`, text `#D9D2C3`, dim `#8C857A`, amber `#FFB020`, alarm `#F06A6E`.
- **Type roles:** Anybody (display, wdth 62–138), Hanken Grotesk (body), Martian Mono (data, wdth 87.5).
- **Spacing:** 4-pt scale, 4…192.
- **Radius:** 0 by default, 2 px on controls, 12 px only on bottom-sheet top corners.
- **Lines:** 1 px hairlines carry all structure; no shadows except for floating layers.
- **Motion personality:** "clerical": decisive stamps (accelerating in), slow reveals (decelerating out), nothing bounces.

### Direction 2: "Clean Room"
Cool graphite `#0B0D10`, phosphor green `#4BE38A`, Mona Sans and JetBrains Mono, rounded 8 px panels, scanline overlays, terminal-style streaming.
- **Rejected:** it reads as "hacker dashboard" and AI-tool default. Green-means-allowed collides with traffic-light semantics and fails for red/green colour-blind users. Mona Sans is GitHub's brand face [S], so it imports someone else's identity.\[41\]

### Direction 3: "Broadsheet"
An editorial serif display (e.g. Fraunces [M]) on ink, newspaper columns, rules, drop caps, sepia accent `#C8A26B`, page-turn transitions.
- **Rejected:** it feels like a university prospectus, not a privacy system. Serifs at small sizes on dark backgrounds lose contrast. Page-turn motion is vestibular-heavy, and the direction can't scale down to table cells.

### Self-review: would Dossier be mistaken for a generic dark-mode AI landing page?
**Partly yes, at first draft.** Near-black + one accent + mono labels + a 3D scene is the default AI-landing kit. Revisions made:
1. **Warm ink, never blue-black.** Linear's is `#08090a` [V]; ours is brown-black `#0C0B09`.\[8\]
2. **No glows, gradients, particles or blur.**
3. **The hero is a sentence, not a product screenshot.**
4. **Square corners.**
5. **The signature element is a hole, not a glow:** the redaction cut-out appears from hero to table cell.
6. **The 3D is a city plan with an orthographic camera, not a floating orb.**
7. **Copy is dry and specific:** policy IDs and log numbers, not "supercharge".

---

## B. Final design system

### B1. Colour tokens (contrast against the named ground; WCAG 2.x relative luminance, computed by me)

| Token | Hex | Use | vs ink-0 `#0C0B09` | vs ink-2 `#1C1A16` |
|---|---|---|---|---|
| `ink-0` | `#0C0B09` | page | — | — |
| `ink-1` | `#14130F` | panels, sidebar | — | — |
| `ink-2` | `#1C1A16` | raised, document "page", inputs | 1.13:1 | — |
| `ink-3` | `#26231E` | hover/active rows | — | — |
| `line-soft` | `#2E2A24` | decorative hairlines only | — | — |
| `line-strong` | `#6E675C` | input borders, **redaction edge**, focusable boundaries | **3.52:1** | 3.11:1 |
| `bone` | `#EDE7DA` | headings, key numerals | **15.96:1** | 14.09:1 |
| `text` | `#D9D2C3` | body copy (less halation than bone) | **13.08:1** | 11.55:1 |
| `dim` | `#8C857A` | secondary text ≥ 12 px | **5.39:1** | **4.76:1** |
| `faint` | `#5A544B` | disabled, decorative ticks; **never information** | — | — |
| `amber` | `#FFB020` | cleared/granted, primary action, focus, live | **10.76:1** | 9.50:1 |
| `on-amber` | `#0C0B09` | text on amber | 10.76:1 | — |
| `alarm` | `#F06A6E` | integrity break, system errors **only** | **6.55:1** | **5.78:1** |

**What I changed from your proposal, and why:**
- **Redaction bar `#1B1915` → removed as a fill colour.** It measures 1.12:1 on ink, so a sighted user can't tell it apart, and it fails SC 1.4.11 non-text contrast (3:1) for a graphic that carries meaning. The new cut-out is filled `ink-0` (a hole), sits on raised `ink-2` surfaces, and has a 1 px `line-strong` edge at 3.52:1 on ink-0 and 3.11:1 on ink-2.
- **Denied `#E5484D` → retired for restrictions; renamed `alarm` and lightened to `#F06A6E`.** Two reasons:
  - **Semantic:** a restriction is the product working. Painting it red produces exactly the "error wall" you want to avoid.
  - **Measured:** `#E5484D` falls to 4.44:1 on `ink-2`, which fails AA for small text. `#F06A6E` gives 5.78:1.
- **Added `text` `#D9D2C3` for body copy.** Bone at 16:1 is fine for headings, but long paragraphs at maximum contrast on near-black cause halation for astigmatic readers [M]. `text` keeps 13:1.
- **Kept amber.** At 10.76:1 on ink, contrast is *not* the small-size risk; glare and thin strokes are. Rule: amber text only ≥ 14 px at weight ≥ 500, never for paragraphs.
- **New rule:** `dim` must not sit on `ink-3`. It drops to 4.29:1 there (fails). Use `text` on hover rows.
- **Data ramp (heatmaps only, graphics, not text):** `amb-1 #3A2A0A`, `amb-2 #6B4A0E`, `amb-3 #A86E12`, `amb-4 #E39A1A`, `amb-5 #FFB020`. Pair with a pattern for categorical states.

### B2. Type

**Final picks and why.**

| Role | Font | Axes used | Why this, over the alternatives |
|---|---|---|---|
| Display | **Anybody** (OFL-1.1 per Fontsource) | `wdth 62–138` (its full range is wdth 50–150 and wght 100–900, per Fontsource's axis table), `wght 500–800`\[37\] | It has the widest width range of the free candidates, so narrow ↔ wide can carry *meaning*: narrow = restricted, wide = broad clearance. Mona Sans/Hubot (75–125) give a timid change and carry GitHub's identity [S]. Google Sans Flex has six axes [S] but is Google's own brand face.\[41\]\[42\]\[43\] Roboto Flex is too neutral [M]. I clamp at 62–138 because the extremes lose legibility. |
| Body/UI | **Hanken Grotesk** (OFL-1.1 per Fontsource; weight axis only, wght 100–900)\[38\] | `wght 400–650` | Quiet, warm-ish and very legible at 14–16 px. Body type should not compete with two characterful faces. Instrument Sans and Mona Sans would add width axes that body copy doesn't need. |
| Data, IDs, pseudonyms | **Martian Mono** (OFL [S]) | `wdth 87.5` default, `75` in dense cells; `wght 400/600` | It's one of the few mono faces with a width axis (75–112.5 [S]).\[42\] Condensing to 75 fits `[PERSON_7F3A]` into 120 px table cells without truncating. Its "brutal" character [S] suits a records system.\[30\]\[44\] |

**Scale** (rem at a 16 px root; clamp min at 375 px, max at 1440 px):

| Token | Font | Size | Line height | Tracking | Max line length |
|---|---|---|---|---|---|
| `display-hero` | Anybody wght 700 | clamp(52px, 10.5vw, 168px) | 0.92 | −0.02em | 14ch |
| `display-xl` | Anybody wght 650 | clamp(40px, 6.5vw, 104px) | 0.96 | −0.015em | 18ch |
| `display-l` | Anybody wght 600 | clamp(32px, 4.2vw, 64px) | 1.02 | −0.01em | 22ch |
| `h1` (app) | Anybody wdth 88 wght 650 | 32px | 38px | −0.01em | — |
| `h2` | Anybody wdth 92 wght 600 | 24px | 30px | 0 | — |
| `h3` | Hanken 600 | 19px | 26px | 0 | — |
| `body-l` | Hanken 400 | 18px | 28px | 0 | 64ch |
| `body` | Hanken 400 | 16px | 24px | 0 | 68ch |
| `body-s` | Hanken 400 | 14px | 20px | 0.005em | 72ch |
| `caption` | Hanken 500 | 12px | 16px | 0.01em | — (`dim` minimum) |
| `mono` | Martian wdth 87.5 wght 400 | 14px | 20px | 0 | — |
| `mono-s` | Martian wdth 75 wght 400 | 12px | 16px | 0 | — |
| `numeral-xl` | Martian wdth 100 wght 600, `tabular-nums` | 40px | 44px | −0.01em | — |

**Rules:**
- Sentence case everywhere. **No tracked all-caps eyebrows.** Section labels, where needed, are `mono-s` in `dim`, sentence case, at most one per section.
- Anybody never goes below 24 px.
- Martian Mono never sits above 14 px next to Anybody, except `numeral-xl`.
- Number markers (`01–05`) appear **only** in the pipeline story, which is a real sequence.

**Font loading:**
- Self-host via Fontsource or subsetted WOFF2. Preload only Anybody.
- Anybody uses `font-display: swap` with a metric-matched fallback (`size-adjust`, `ascent-override`) to avoid CLS. Hanken and Martian use `font-display: optional` on the landing and `swap` in the app.

### B3. Spacing, layout, elevation, radius, lines
- **Spacing:** `0, 4, 8, 12, 16, 24, 32, 48, 64, 96, 128, 192` (tokens `s-0…s-11`).
- **Grid:**
  - Desktop: 12 columns, 24 px gutters, max 1440 px, 64 px side margins.
  - Tablet: 8 columns, 32 px margins.
  - 375 px: 4 columns, 16 px gutters, 20 px margins.
  - The app content max width is 1280 px; chat is 720 px.
- **Elevation:** three levels via the surface ladder (`ink-1/2/3`). Only *floating* layers (popover, sheet, palette, toast) get `0 16px 48px rgba(0,0,0,.6)` plus a 1 px `line-strong` border.
- **Radius:** 0 on structure; 2 px on buttons, inputs and chips; 12 px on bottom-sheet top corners. Nothing is pill-shaped.
- **Lines:** `line-soft` for layout rules; `line-strong` for anything interactive or meaningful. Dashed 1 px `line-strong` (4/3 dash) = **generated or uncertain** content. Solid = sourced.

### B4. Iconography
- **Base set:** Lucide (shadcn's default; ISC licence [M]) at 20 px, 1.5 px stroke, square caps, `currentColor`.
- **Six custom glyphs on the same grid:**
  - `record` (tool answer: a 3 × 3 grid)
  - `quote` (two vertical bars)
  - `summary` (three wavy lines; used only beside the word "Generated")
  - `restricted` (a bar with an outline)
  - `reveal` (a bar with a gap)
  - `chain` (two linked squares)
- No filled, duotone or "sparkle" icons. AI is never signified by a sparkle; it's signified by the word **Generated** plus the dashed rule.

### B5. The redaction component family

Two concepts that must never look alike:

1. **Pseudonym** (identity substituted, content still useful): a Martian Mono token `[PERSON_7F3A]` with a 1 px dotted `dim` underline. Admins also see a 4 px amber square at the right edge, meaning "revealable".
2. **Redaction** (content withheld): a **cut-out**, filled `ink-0` with a 1 px `line-strong` edge.

**Anti-leak rule:** the cut-out's width is **quantised by a hash of the token ID**, never measured from the hidden text, so the length of a name or note isn't leaked. Sizes: S = 4ch, M = 7ch, L = 11ch. Block redactions use line counts 1, 3 or 5.

| Variant | Spec | Screen reader |
|---|---|---|
| **Inline** | height 1.05em, baseline-aligned, width S/M/L in `ch` of the surrounding font, 1 px edge, no radius. Hover/focus (if focusable): tooltip "Withheld · person name · Admin clearance". | `<span class="sr-only">redacted: person name</span>`; the bar is `aria-hidden` |
| **Block** | N full-measure lines at the paragraph's line height, the last line 60% width, 4 px gaps between lines. A caption under it in `mono-s dim`: "3 lines withheld · Policy TU-PRIV-3". | One sr-only sentence for the whole block |
| **Table cell** | A bar 70% of the cell width, centred vertically, 12 px tall. Cell `aria-label="Restricted"`. Sorting puts restricted rows last and ignores their value. | "Restricted" |
| **Hero scale** | 0.82em-tall bars over whole words at display sizes. 2 px edge, `line-strong`, which brightens to amber when "cleared". | The real headline text is in the DOM for each state; bars are decorative |
| **Loading** ("redacting") | Same bar, with a 1 px amber hairline travelling left to right inside it over 1200 ms, `linear`, repeating. Reduced motion: no travel; the label "Redacting…" shows instead. | `aria-busy="true"` on the parent |
| **Revealed** (admin only) | The bar retracts by `clip-path` from left to right over 420 ms. The text appears with a 1 px amber underline and a trailing chip "Revealed · log R-0193". It re-redacts on navigation or after 120 s. | Live region: "Revealed. This reveal is logged as R-0193." |
| **Diff-added / diff-removed** | Added redaction: bar with a 2 px amber edge. Removed: amber dashed outline with the text visible (admin view). | "Redaction added / removed" |

### B6. Focus
- `:focus-visible` gets a 2 px `amber` outline with a 2 px `ink-0` offset. On amber fills, the outline switches to 2 px `bone`.
- Never remove the outline. Sticky dock, header and toasts must not obscure focus (SC 2.4.11): set `scroll-padding-bottom: 96px` (dock) and `scroll-padding-top: 72px` (top bar).
- Minimum target size is 44 × 44 px. That meets WCAG 2.2 SC 2.5.5 Target Size (Enhanced, AAA). It also clears the AA requirement in SC 2.5.8, which says "The size of the target for pointer inputs is at least 24 by 24 CSS pixels".\[45\]\[46\]

### B7. Motion tokens

| Token | Value | GSAP equivalent | Use |
|---|---|---|---|
| `dur-instant` | 80 ms | — | hover colour, press |
| `dur-fast` | 140 ms | — | toasts in, tooltips, fallback route fade |
| `dur-base` | 220 ms | — | panels, sheets, popovers |
| `dur-slow` | 420 ms | — | reveal wipe, door leaf |
| `dur-reveal` | 640 ms | — | hero headline rewrite |
| `dur-cine` | 1200 ms | — | landing set-pieces only |
| `ease-out` | `cubic-bezier(0.22,1,0.36,1)` | `expo.out` | anything entering |
| `ease-in-out` | `cubic-bezier(0.65,0,0.35,1)` | `power3.inOut` | moves between states |
| `ease-stamp` | `cubic-bezier(0.7,0,0.84,0)` | `power4.in` | redaction bar landing (it accelerates and "hits") |
| `ease-wipe` | `cubic-bezier(0.83,0,0.17,1)` | `expo.inOut` | reveal and clip wipes |
| `spring-ui` | stiffness 420, damping 40, mass 1 | — | Motion layout transitions (no overshoot) |

- **Stagger:** 24 ms per item, capped at 10 items (240 ms total); lines of text 60 ms; never stagger table rows over 20.
- **Scroll vs interaction:**
  - Scroll-linked (scrub, pin, axis changes) is allowed **only on the landing, the clearance door and the public intro**.
  - In the app, scroll moves nothing except sticky headers.
  - Interaction-triggered motion is allowed everywhere, limited to ≤ `dur-slow` in the app.
  - Ambient/looping motion: the City idle "window flicker" only, which pauses after 5 s idle and has a pause control.
- **Reduced motion** (OS setting **or** the site toggle in the footer and settings, persisted in `localStorage`):
  - Transforms → 0. Durations → `dur-fast` opacity cross-fades.
  - Pins → off (sections stack). Lenis → off. City camera moves → cuts.
  - Redaction "stamp" → instant state change with a 1-frame edge flash in amber (colour, not motion).
  - The personality survives through copy, type-width changes applied as *cuts*, and amber state changes.

---

## C. Screen-by-screen specification

Conventions: D = desktop at 1440 px, M = 375 px. `▓▓▓` = redaction cut-out. `[A]` = amber element.

### C1. Landing page

**Purpose:** in 60 seconds, show that Lacuna's value is *what it withholds, and that it proves it*.

#### C1.1 Intro ("preloader")
- **Not a blocking loader.** The hero HTML text paints in the first frame (it is the LCP). On the first visit per session only, a 900 ms choreography plays *over* the already-painted headline.
- **Sequence:**
  - 0 ms: hero words sit under hero-scale bars.
  - 120 ms: the mono line "Checking clearance…" types in (8 chars per 40 ms).
  - 520 ms: the line reads "Least privilege assumed." and the toggle settles on **Student**.
  - 640–900 ms: the bars over the *permitted* words retract (`ease-wipe`, 40 ms stagger). The words that stay redacted keep their bars.
- **Skip:** any key, click or scroll ends it instantly. Reduced motion: no sequence; the final state renders.
- **Failure:** if fonts aren't ready by 1200 ms, the fallback face is used and no swap animation runs.

#### C1.2 Hero with clearance toggle
```
D                                                             M (375)
┌──────────────────────────────────────────────────────────┐  ┌───────────────────┐
│ Lacuna                         Demo  Docs  Sign in  ◐ ♪  │  │ Lacuna        ≡   │
│                                                          │  │                   │
│ You see your grades.                                     │  │ You see           │
│ The rest is ▓▓▓▓▓▓▓.                                     │  │ your grades.      │
│                                                          │  │ The rest is       │
│ Clearance  ( Student ●)( Faculty )( Admin )              │  │ ▓▓▓▓▓▓▓.          │
│                                                          │  │                   │
│ A privacy-aware assistant for Thornwick University.      │  │ [Student][Fac][Adm]│
│ The gaps are the feature.     [A Try a persona →]  Docs  │  │ The gaps are the  │
│                                                          │  │ feature.          │
│ Scire et Tacere ─────────────────────── scroll ↓         │  │ [A Try a persona] │
└──────────────────────────────────────────────────────────┘  └───────────────────┘
```
- **Toggle:** a 3-option `radiogroup` (custom, built on Radix ToggleGroup in single mode). Arrow keys move between options; selection is instant.
- **Headline per level:**

| Level | Anybody wdth / wght | Headline |
|---|---|---|
| Student | 62 / 760 | "You see your grades. The rest is ▓▓▓▓▓▓▓." |
| Faculty | 100 / 680 | "You see your cohort. Their files stay ▓▓▓▓▓." |
| Admin | 138 / 560 | "You see everything. Everything sees you." (no bars; the subline reads "Every reveal is logged. Including this one.") |

- **The one memorable moment:** switching level physically **narrows or widens the headline** while words swap under redaction bars.
- **Motion on change** (total 640 ms):
  1. 0 ms: bars stamp *onto* every word that changes (`ease-stamp`, 140 ms, 30 ms stagger).
  2. 140 ms: the text node swaps under the bars, and `wdth`/`wght` tween to the new values over 500 ms (`ease-in-out`).
  3. 300 ms: bars over now-permitted words wipe off (`ease-wipe`, 340 ms).
  4. Admin only: at 640 ms a mono line prints "log A-000184 · clearance changed".
- **Reduced motion:** the bars and text swap in one frame and the width changes as a cut.
- **Accessibility:** the `<h1>` holds the full current sentence. A polite live region announces "Clearance set to Faculty. Headline: You see your cohort. Their files stay redacted."
- **States:** fonts not loaded → toggle works without width animation. JS off → the Student headline is static and the toggle is hidden.

#### C1.3 Pipeline scroll story (`01–05` is allowed here: a true sequence)
```
D (pinned, 500svh)                                         M (pinned, 320svh)
┌───────────────────────────────────────────────────────┐  ┌──────────────────┐
│ 01 Parse  02 Redact  03 Retrieve  04 Answer  05 Audit │  │ 02 Redact   ━━━░░ │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━░░░░░░░░░░░░░░░░░░░░░░░░░░ │  │ ┌──────────────┐ │
│  ┌─────────────┐                                      │  │ │Disciplinary  │ │
│  │ Disciplinary│   Names, IDs and notes become        │  │ │report TU-114 │ │
│  │ report      │   pseudonyms or holes before         │  │ │[PERSON_7F3A] │ │
│  │ [PERSON_7F3A]│  anything is stored.                │  │ │ ▓▓▓▓▓▓ ▓▓▓▓  │ │
│  │ ▓▓▓▓▓ ▓▓▓▓▓ │   14 spans withheld · 3 pseudonyms    │  │ └──────────────┘ │
│  └─────────────┘ ┌grade┐ ┌minutes┐ (queued, dimmed)   │  │ Names become     │
└───────────────────────────────────────────────────────┘  │ pseudonyms…      │
                                                           └──────────────────┘
```
- **Stage → document → what animates:**

| Stage | Document in focus | What animates |
|---|---|---|
| 01 Parse | all three sheets fan in from a stack | Text lines draw as `line-soft` rules that resolve into text (clip wipe, 60 ms line stagger). |
| 02 Redact | Disciplinary report | Names stamp into `[PERSON_7F3A]` tokens. Notes stamp into block cut-outs. A counter ticks "14 spans withheld". |
| 03 Retrieve | Grade report | The question "What was my CS-201 grade?" appears. One row of the grade table gets an amber edge, and the label "SQL template G-04 · no AI involved" shows. |
| 04 Answer | Meeting minutes | Three answer kinds stack: Record (solid rule), Quote (quoted passage with citation [1]), Summary (dashed rule, "Generated"). |
| 05 Audit | all three collapse into log lines | Three rows print with hash prefixes. Each row's `prev` hash flips to match the row above (character scramble, 300 ms). The final line reads "Chain intact". |

- **Scrub and pin:**
  - Desktop: `scrub: 0.6`; each stage takes 100 svh, with snap to stage centres (`snap: 1/4`, duration 0.3).
  - Mobile: pin 320 svh (64 svh per stage), no snap (snap fights momentum on touch), `ignoreMobileResize: true`.
- **Reduced motion or no JS:** five stacked static panels, each showing the stage's end state.
- **Keyboard:** stage tabs at the top are real buttons that `lenis.scrollTo` the stage's offset.

#### C1.4 Clearance City teaser
- **Layout:**
  - D: full-bleed band 80 svh tall, canvas to the right (60%), copy to the left.
  - M: canvas 56 svh on top, copy below.
- **Copy:** "Every document is a building. Every passage is a window. People are not on the map."
- **Moment:** on entering view, an orthographic camera drifts 8° over 2.4 s (tier ≥ 2) while windows light in a retrieval pattern.
- **Tier < 2 or reduced motion:** a static AVIF poster (≤ 60 KB, 1200 × 800, `srcset` 600/1200/1800) with a "Open the city" button.
- **Text alternative:** "Illustration: an isometric city of 5 districts and 42 buildings; 6 buildings are shown as empty outlines, meaning restricted."

#### C1.5 Role cards (not a card grid)
- Three tall "folders" in an **asymmetric horizontal accordion**. The selected folder takes 56% of the width; the others take 22% and show a vertical label.
- M: a vertical accordion; the selected folder expands to show its content.
- **Content per role:** what you see, what you never see, one sample question.
  - Student: "Can I see my disciplinary file?" → "Your own, yes. Anyone else's: that's a hole."
- **Motion:** width transition 420 ms `ease-in-out`; inner content fades 140 ms after.

#### C1.6 Architecture
- One SVG schematic drawn as hairlines that **draw on scroll** (`stroke-dashoffset`, scrub). The path runs: Upload → Parse/OCR → Redact (pseudonym vault) → Chunk/Embed → Store, then Question → Clearance check → Tools (SQL templates) / Retrieval → Answer kind → Audit chain.
- Every node is a DOM label (accessible). M: the diagram becomes a vertical flow.
- Reduced motion: drawn fully at once.

#### C1.7 FAQ
- shadcn Accordion; 64ch measure; questions in `h3`.
- **Six questions:**
  - "Does the AI see real names?"
  - "Can admins see everything?"
  - "What happens when I'm refused?"
  - "Is the audit log really tamper-evident?"
  - "Does it work without the AI?"
  - "Is any of this real?"
- **Answers** are specific. For example: "No. Names are replaced before storage. The model sees `[PERSON_7F3A]`, which is all it deserves."

#### C1.8 Footer
- The motto **"Scire et Tacere"** in Anybody at wdth 50 and wght 800, 22 vw tall, cropped by the viewport bottom.
- Also in the footer: the mute toggle ♪, the reduced-motion toggle ◐, links, and "Thornwick University is fictional. Its paperwork is not."

### C2. Clearance-gated entry demo

- **Purpose:** a tactile demonstration that clearance changes what you can see.
- **Layout:**
```
D                                              M
┌───────────────────────────────────────┐      ┌───────────────┐
│        ┌──────────┬──────────┐        │      │  ┌────┬────┐  │
│        │  ▓▓▓▓▓▓  │  ▓▓▓▓▓▓  │        │      │  │▓▓▓▓│▓▓▓▓│  │
│        │  door L  │  door R  │        │      │  │    │    │  │
│        └──────────┴──────────┘        │      │  └────┴────┘  │
│  Present clearance:                   │      │ [Stu][Fac][Ad]│
│  ( Student )( Faculty )( Admin )      │      │ Present       │
│  "Records Office. Knock if you must." │      └───────────────┘
└───────────────────────────────────────┘
```
- The door leaves are two giant redaction cut-outs.
- **Per clearance (the memorable moment):**
  - **Student:** the leaves part 18% (slow, 640 ms, `ease-out`). Through the crack: two lit rooms labelled "Your grades" and "Your timetable"; the rest is dark. Copy: "You may look. Briefly."
  - **Faculty:** they part 50%. Six rooms; "Student conduct" stays a black slab. Copy: "Mind the conduct files. They mind you."
  - **Admin:** they open fully (900 ms). Every room is lit. A ledger strip prints at the threshold: "Entry logged · A-000185 · 14:02:11". Copy: "Come in. Sign here. You already did."
- **Under the hood:** 2D layers (`clip-path` and `transform` on three depth planes, 0/12/24 px parallax on pointer move, desktop only). No WebGL.
- **States:** reduced motion → cross-fade to the open state. JS off → three static images with alt text.
- **Keyboard:** the radio group, then the "Enter" button, which leads to the public experience as that persona.

### C3. Public experience

- **Purpose:** let a visitor try Lacuna as three fictional personas without signing up.
- **Personas:**
  - **Ada Okafor**, second-year engineering student
  - **Dr Henrik Vale**, lecturer, CS-201
  - **M. Ferris**, registrar admin
- **Cinematic intro** (per persona, about 20 s, skippable, keyboard-controllable):
  - A scripted day in four beats. For example, Ada at 08:40: "When is my lab?" (Record answer).
  - Then 11:15: "What's Jonah's GPA?". "Jonah" is pseudonymised in the transcript, and the answer is Restricted, with Request access.
  - Then 16:00: a fees deadline toast.
  - Then 22:10: "Summarise the CS-201 minutes" (Quote + Summary).
  - Each beat is a real UI screen auto-driven by a script (no video). A 4-segment progress bar runs at the top. Controls: Pause (`Space`), Next (`→`), Skip intro.
- **Free roam:** the real shells with scripted data. A persona switcher sits in the top bar (D) or bottom sheet (M), and switching keeps the current question so you can compare.
- **Archive-mode banner:** shown when the backend is down. A full-width strip under the header, `ink-1`, 1 px amber top rule. Text: "Archive mode: the live system is asleep. You're reading recorded answers, timestamped 2 Nov 2026." Has a "Why?" link. It can't be dismissed while active, because truth beats tidiness. The answer footer adds "recorded".
- **Wireframe:**
```
D                                                          M
┌ Lacuna · Public demo   Persona: Ada ▾   ◐ ♪ ────────────┐  ┌──────────────────┐
│ ▔▔ Archive mode: the live system is asleep… Why?        │  │▔ Archive mode…   │
│ ━━━━░░░░░░░░ 08:40  11:15  16:00  22:10   ❚❚  Skip      │  │━━░░░  ❚❚  Skip   │
│ ┌ chat (as student shell) ────────────────────────────┐ │  │ chat             │
│ │ …                                                    │ │  │ …                │
│ └──────────────────────────────────────────────────────┘ │  │ [dock]           │
└──────────────────────────────────────────────────────────┘  └──────────────────┘
```

### C4. Auth

Centred single column, 400 px (D) or full width with 20 px margins (M). Wordmark top-left. A thin ledger rule at the bottom reads "This sign-in is logged." The one memorable moment: on signup, when the email matches, the role **un-redacts**.

| Screen | Fields and flow | Signature moment | States and copy |
|---|---|---|---|
| **Login** | Institutional email, password, "Sign in". Links to "Forgot password" and "Try a demo persona". | none (calm) | Error (inline, `alarm`): "That email and password don't match a Thornwick account." **Never say which one is wrong.** Locked: "Too many attempts. Try again at 14:20." Loading: button label → "Checking…". |
| **Signup step 1** | Email only → "Find my record". | Matched: "We found you." The role line un-redacts: "▓▓▓▓▓▓▓ · School of ▓▓▓▓▓▓▓" → "Student · School of Engineering" (420 ms wipe). | Not found: "No pre-created account for that address. Signup only works for emails the registrar set up." Already active: "You already have an account. Sign in instead." |
| **Signup step 2** | Password (with strength meter: 4 segments, no colours other than amber/dim), confirm, accept the data notice. | — | — |
| **Verify email** | A 6-digit code (6 single-char inputs, paste-aware, auto-advance), "Resend in 0:45". | — | Wrong: "That code doesn't match. 2 tries left." Expired: "Code expired. We sent a new one." |
| **Reset** | Email → "If that address has an account, a link is on its way" (anti-enumeration) → new password page. | — | — |

### C5. Role shells

| Role | Shell | Why it fits the user's tasks |
|---|---|---|
| **Student** | **Bottom dock** with 5 items (Ask, Grades, Timetable, Fees, Me). Floating, centred, 64 px tall on D; full-width safe-area-aware on M. | Students do a few frequent, mobile-first tasks one-handed. A dock gives thumb reach and makes Ask the centre item. |
| **Faculty** | **Top bar** (course switcher, Ask, Roster, Documents, Requests) + **⌘K command palette**. | Faculty work across several courses and many students. Their work is retrieval-led ("open CS-201 roster", "grade distribution midterm"), so typing beats navigating. |
| **Admin** | **Sidebar**, 248 px, collapsible to 64 px. Grouped: *Oversight* (Overview, Requests, Audit log, Reveal log), *Data* (Documents, Collections, Ingestion), *People* (Users), *Assurance* (Privacy tests, Analytics, Clearance City). | Many sections, used for long sessions, with high density. Persistent orientation is the "inverted L" pattern [V, Linear].\[8\] |

```
Student D                         Faculty D                          Admin D
┌──────────────────────────┐      ┌ CS-201 ▾  Ask Roster Docs Req ⌘K┐ ┌────────┬─────────────────┐
│        content           │      │            content              │ │Oversight│ content         │
│                          │      │                                 │ │ Overview│                 │
│   ┌─Ask─Grades─Time─Fees─Me┐    │                                 │ │ Requests│                 │
└───┴──────────────────────┴┘     └─────────────────────────────────┘ │ Audit   │                 │
M: dock full-width bottom         M: top bar = title + 🔍(palette   │ …       │                 │
                                     opens full-screen sheet)         └────────┴─────────────────┘
                                                                       M: bottom tabs Overview,
                                                                       Requests, Audit, More▸sheet
```
- **Shared by all shells:** the notifications bell (faculty and admin; for students it lives inside "Me"), the reduced-motion and sound toggles, a clearance badge (mono chip "Clearance: Faculty"), and the global ⌘K for all roles.

### C6. Chat

**Layout:**
```
D                                                              M
┌ History ───────┬─────────────────────────────────────────┐   ┌───────────────────┐
│ Today          │  You · 14:02                            │   │ ← Ask   18/50 ▮▮▯ │
│ ▦ My CS-201…   │  What was my CS-201 midterm grade?      │   │ You: What was…    │
│ ❙❙ Minutes…    │                                         │   │ ▦ Record          │
│ ▓ Jonah's GPA  │  ▦ Record · registrar.grades · G-04     │   │ ┌───────────────┐ │
│ Yesterday      │  │ Midterm   B+   78/100               │   │ │Midterm B+ 78  │ │
│ …              │  │ Source: grade report TU-207 · 12 ms │   │ └───────────────┘ │
│                │                                          │   │                   │
│                │ ┌──────────────────────────────────────┐ │   │ [Ask anything… ▸] │
│                │ │ Ask anything you're cleared for…  ▸ │ │   │ [dock]            │
│                │ │ 18 / 50 today ▮▮▮▮▯▯▯▯▯▯   Export   │ │   └───────────────────┘
└────────────────┴──────────────────────────────────────────┘
```
History is a 280 px panel on D and a sheet on M (from the ← button). Composer: min 56 px, grows to 6 lines. Enter sends; Shift+Enter adds a newline.

**Message states:**

| State | Visual signature | Content and copy |
|---|---|---|
| **Loading** | A mono status ticker above an empty bubble: "Checking clearance → Querying → Redacting → Writing". The current step is `bone`, done steps `dim`, with 2–3 loading-variant bars as a skeleton. | `aria-live="polite"` announces only the first and last steps. |
| **Tool answer** (Record) | `record` glyph, **solid 2 px bone left rule**, mono table, footer "Source: registrar.grades · template G-04 · 12 ms · deterministic". | No AI badge. A "Re-run query" action (not "regenerate"). |
| **Quoted answer** | `quote` glyph, passage rendered on an `ink-2` "page" with the redactions intact, citation chips `[1] [2]`, footer "Quoted verbatim from Minutes, CS Dept, 12 Oct". | Clicking a chip opens the source viewer. |
| **Summary** | `summary` glyph + the word **Generated**, **dashed 1 px left rule**, body text; footer "Generated from quotes [1]–[3] above. Check them; I'm a summary, not a source." | Stop (while streaming) and Regenerate. |
| **Restricted** | A block cut-out (3 lines), caption "Outside your clearance", the policy name, and a primary **Request access** button plus a "Why?" disclosure. | "That touches records outside your clearance. I can't say whether any exist. Policy TU-PRIV-3: conduct files are admin-only." Under it: "This question was logged. So is this refusal." |
| **Not found** | Plain text, no bar (a bar would imply hidden content). | "Nothing in the records you can see matches that. Try a course code or a date." |
| **Error** | `alarm` icon + text, Retry. | "The records office didn't answer (timeout after 20 s). Your question was still logged, because of course it was." |
| **Stopped** | Partial text with a dashed end marker. | "Stopped. The part above is incomplete." |

- **Source viewer:** a right drawer (D, 480 px) or full sheet (M).
  - It shows the whole document on `ink-2`, scrolled to the cited passage. The cited passage gets an amber 2 px left rule and an amber-tinted background (`#FFB020` at 8%).
  - Redactions show as cut-outs. A **redaction navigator** at the top ("6 withheld spans ▴▾") steps through them, borrowing Relativity's Markup Navigation pane.\[9\]
  - Admins see "Reveal" on each span: confirm dialog → reason required → logged.
- **Quota meter:** 10 segments. Amber fill up to 80%; beyond that the meter stays amber but the label changes to "4 left today". At 0: the composer is disabled with "That's today's 50. The records will still be there tomorrow. So will the log." Resets at 00:00 local.
- **Request access flow:** a dialog with: the scope (category, prefilled), the reason (required, 20–500 chars), and the duration requested (24 h / 7 days / this term). On submit, a toast reads "Request R-0412 sent to the Registrar. You'll get a notification either way." The restricted message then shows a "Pending · R-0412" chip.
- **Export:** Markdown or PDF. Redactions stay as `[REDACTED]` (text) and bars (PDF). The export ends with an "audit receipt": the entry IDs and hash prefixes.
- **Empty chat:** three suggested questions matched to the role. Header: "Ask about anything you're cleared for. I'll tell you when you aren't."

### C7. Dashboards
All dashboard charts have a "View as table" toggle. All numbers are Martian Mono with tabular numerals.

**Student** (D: 2-column asymmetric 8/4; M: single column in this order: deadlines, grades, timetable, attendance)
```
┌ Good afternoon, Ada. Two deadlines this week. ─────────────────────────┐
│ GPA trend (8 terms) ───────────────── 3.41 ▲0.12 │ Fees & deadlines     │
│  line, amber current term dot, direct labels     │ Lab fee  £40  in 3 d │
│ Attendance (weeks × Mon–Fri heatmap, amb ramp)   │ CS-201 essay  in 5 d │
│ Timetable (this week grid, now-line amber)       │                      │
└──────────────────────────────────────────────────┴──────────────────────┘
```
- Absences in the heatmap are **hatched** (pattern), not just pale.
- Moment: the GPA line draws once on first load (600 ms; reduced motion → none).
- Empty state: "No grades yet. Thornwick is still deciding."
- Restricted widget (e.g. a scholarship status that needs the bursar): a row-level cut-out plus "Ask the bursar's office".

**Faculty:**
- Roster table (real names of their own enrolled students; addresses, conduct and health fields are cut-outs).
- Grade distribution (histogram, 10 bins, amber marks the selected bin, a median line).
- Requests: their own outgoing requests and their status.
- Recent documents (list with collection and version).

**Admin:**
- **Request queue:** count + top 5, with approve/deny inline.
- **Denial counter:** `numeral-xl` "214 refusals today", labelled "Working as intended". Sparkline; **not red**.
- **Audit stream:** live, last 20 rows; pauses on hover/focus; a ❚❚ control (SC 2.2.2).
- **Integrity:** "Chain intact · 48,211 entries · verified 14:02 · [Verify now]".
- **Usage trends:** questions per day by role, 30 d, three grey lines, amber for the selected role.
- **Ingestion queue:** jobs with their current stage.

### C8. Admin screens

**Audit log:**
```
D
┌ Audit log  ─ Chain intact · verified 14:02 [Verify chain] [Export CSV] ───┐
│ Filters: Role ▾  Outcome ▾ (answered/restricted/not found/error/reveal)   │
│          Collection ▾  Actor [PERSON_…]  Date ▸ 1 Nov – 2 Nov  ✕ clear    │
├──────────┬──────────────┬─────────┬───────────────┬──────────┬───────────┤
│ 14:02:11 │ [PERSON_7F3A]│ student │ ask.grades    │ answered │ 9f2c…a1   │
│ 14:01:58 │ [PERSON_2B90]│ student │ ask.conduct   │ restricted│ 77de…03  │
└──────────┴──────────────┴─────────┴───────────────┴──────────┴───────────┘
M: each row = 3-line list item (time+outcome / actor+action / hash), filters in sheet
```
- **Row detail drawer:**
  - The question as asked (pseudonymised), clearance at the time, tools invoked (template IDs), chunks retrieved (IDs, collection), answer kind, latency.
  - `prev_hash` and `hash` in full (mono, wrapping), with a "Copy" button.
- **Verify chain:** a progress bar in blocks of 1,000. Results:
  - Success: "Intact. 48,211 entries, no gaps, no edits."
  - Failure: an `alarm` banner reading "Break at entry 41,203: hash doesn't match its predecessor. Entries after this point can't be trusted until reviewed." It has a "Jump to entry" button.
  - This is the **only** red moment in the product, which is why it lands.

**Users:**
- A table with these columns: pseudonym/real name (admin), institutional email, role, status (invited / active / locked), and last active.
- Actions: change role (confirm, logged), lock, resend invite.

**Access requests and grants:**
- A two-pane layout: the queue on the left, detail on the right.
- **Detail:** the requester, scope, reason, requested duration, and prior requests from the same person.
- **Approve:** choose the scope (narrow by default) and duration (24 h / 7 d / term / custom ≤ 90 d).
- **Deny:** requires a reason template ("Not necessary for teaching", "Ask data owner", custom).
- **Grants tab:** active grants with an expiry countdown and a "Revoke" action.

**Reveal log:**
- Every reveal is listed with: who, which pseudonym, the reason given, when, duration, and the document.
- Header: "Watching the watchers: 12 reveals this week." Other admins can flag a reveal for review.

**Privacy Test Suite:**
- A table of cases with columns: the case, its persona, the expected kind, the actual result, and pass/fail. Example case: "Student asks for another student's GPA", expected Restricted.
- **Run all:** a live progress readout ("Running case 18 of 40…").
- **On a failure:** an inline diff highlights the leaked string with an amber dashed outline. The string itself shows as a cut-out unless the viewer is an admin.
- **Summary line:** "39 / 40 passed. One leak is one too many."

**Analytics:**
- Questions by role (stacked bar, greys plus amber for the selected role).
- Answer-kind mix (100% bar: Record / Quote / Summary / Restricted / Not found).
- Denial rate over time, latency p50/p95.
- Top restricted categories, reported as counts only.

### C9. Document manager

**Upload:**
- Drop zone: a dashed `line-strong` frame on D; a full-width button on M. Accepts PDF, DOCX, PNG and JPG, up to 25 MB.
- Then pick the collection and sensitivity (default **High**; least privilege again).
- Copy: "Drop records here. We'll take the names out before we take them in."

**Ingestion theater (the memorable moment of this section):**
```
D
┌ TU-114 Disciplinary report.pdf ────────────────────── 00:07.4 ─┐
│ ┌ page thumb ┐   Parse   ✓ 6 pages                              │
│ │ ═══════    │   OCR     ✓ 2 low-confidence words               │
│ │ ═[P_7F3A]═ │   Redact  ● 14 spans withheld · 3 pseudonyms     │
│ │ ▓▓▓▓ ════  │   Chunk   ○                                      │
│ └────────────┘   Embed   ○                                      │
└─────────────────────────────────────────────────────────────────┘
```
- Driven by **real server events** over SSE: `stage.start`, `stage.progress`, `span.redacted {page, bbox_quantised}`, `stage.done`.
- Each `span.redacted` event stamps a bar onto the thumbnail (`ease-stamp`, 140 ms). Counters tick. The stage dot is amber while running and becomes ✓ when done.
- **Throttling:** at most 30 bar animations per second. Beyond that, batch them and show "+46".
- **Fallback:** if events stop for 15 s: "Still working, or quietly broken. Checking…", then retry. On failure, the `alarm` row says which stage failed, e.g. "OCR failed on page 4 (image too low resolution)", with a Retry action.
- Reduced motion: bars appear instantly; counters update without ticking.

**OCR review:**
- **D:** a split view, with the page image on the left and the text layer on the right.
- Low-confidence words get a dotted amber underline plus a confidence badge in mono (e.g. `0.62`). A threshold slider (default 0.80) controls which words are flagged.
- **Keyboard:** `J` / `K` next/previous flag, `E` edit, `A` accept.
- **M:** stacked views, with a toggle between "Image" and "Text".

**Versions:**
- A version list, then a before/after **diff**:
  - Added redactions get an amber edge.
  - Removed redactions get an amber dashed outline (admins only).
  - Text changes get a strikethrough in `dim` plus an inserted underline.
- Each change carries a reason, an author and a timestamp (Relativity's model [S]).\[11\]

**Collections:**
- A table (not cards) with columns: name, district colour swatch (grey ramp), document count, default sensitivity, and who can see it (role chips).

**Clearance simulator:**
```
D
┌ Ask as everyone: [What happened at the 12 Oct conduct hearing?        ▸] ┐
├ Student ──────────────┬ Faculty ───────────────┬ Admin ──────────────────┤
│ ▓▓▓ Restricted        │ ▓▓▓ Restricted         │ ❙❙ Quote: "The panel    │
│ Policy TU-PRIV-3      │ Policy TU-PRIV-3       │ found [PERSON_7F3A]…"   │
│                       │                        │ Reveal available        │
└───────────────────────┴────────────────────────┴─────────────────────────┘
M: three tabs with a swipeable carousel; a "differences" summary row on top
```
- One query is sent three times with simulated clearances. All three runs are audit-logged as `simulation`.
- Differences are summarised: "Faculty sees 2 of 5 passages. Student sees none."

### C10. Clearance City (3D)

- **Mapping:** collection → district (5–8 districts on a grid with streets). Document → building:
  - footprint = page count (quantised to 1, 2 or 4 cells)
  - height = chunk count (1 floor per 4 chunks)
  - windows = chunks, one per window
  - **People are never mapped.**
- **Camera:** orthographic. The **isometric** angle (pitch about 35.26°, yaw 45°) is fixed with **no rotation** (avoids vestibular issues). Zoom 0.6–3×, pan within bounds. Double-click or Enter frames the selected building (420 ms `ease-in-out`; reduced motion → cut).
- **Lighting and materials:**
  - One hemisphere light (sky `#2A2620`, ground `#0C0B09`) plus one directional light at 30°.
  - **No realtime shadows**; ambient occlusion is baked into vertex colours.
  - Buildings: `MeshLambertMaterial` in the `ink-2`/`ink-3` range.
  - Windows: instanced quads with a per-instance `aEmissive` attribute. Off = `#1C1A16`; lit = `#FFB020` (retrieved); revealed = bone.
  - Ground: `ink-0` with `line-soft` street lines.
- **Restricted for the viewer:** **empty lots**, a hairline footprint with no mass. A district label says "6 buildings outside your clearance". No titles.
- **Retrieval sync:** while an answer streams, the retrieval event `chunks: [ids]` lights those windows. Each window lights in 80 ms, staggered 30 ms, decaying to 40% after 4 s. The camera does not move unless the user pins "Follow".

**Views:**

| View | Who | What it shows |
|---|---|---|
| Their world | student, faculty | Only their districts at full mass; others as outlines. |
| Whole city | admin | Everything. |
| Split view | admin | Two synchronised orthographic viewports side by side (D) or top/bottom (M), each with a role selector. The camera is shared. |
| Redaction X-ray | admin | Building facades become 30% opacity. Windows containing redacted spans show an inner cut-out glyph, and the count per building shows on hover/focus. |

**Quality tiers** (from the `useQualityTier` hook in F4):

| Tier | Trigger | DPR | Windows | Effects | Frame loop |
|---|---|---|---|---|---|
| T3 | median frame ≤ 12 ms sustained 5 s | min(2, device) | individual instanced quads (≤ 20k) | optional bloom on lit windows (desktop only) | `always` while interacting, otherwise `demand` |
| T2 | default on capable devices | 1.5 | instanced quads ≤ 8k; far buildings via `<Detailed>` show facade texture strips | none | `demand` |
| T1 | median > 22 ms, or `deviceMemory ≤ 4`, or Save-Data | 1 | lit counts as emissive bars per building, no per-window quads | none | `demand` |
| T0 | no WebGL2, context lost twice, or user chose "Plan view" | — | **SVG City Plan** | — | — |

- **Draw-call budget:** ≤ 60 at T2 (well under the R3F docs' "few hundred" [V]).\[32\]

**Mobile layout:**
- The canvas takes the top 56 svh. A **bottom sheet** has snap points at 24%, 56% and 92%, and holds the district list → building → document detail.
- Gestures: one-finger pan, pinch to zoom, no rotate.
- Sheet drag uses the `dur-base` spring and does not move the canvas.

**Keyboard and screen reader:**
- An offscreen **DOM mirror**: a `tree` with district → building nodes, using roving tabindex.
- Focusing a node draws an amber 2 px outline around the building's projected 2D bounds (an HTML overlay).
- Keys:

| Key | Action |
|---|---|
| ↑↓ | move between buildings |
| ←→ | collapse/expand district |
| `[` `]` | previous/next district |
| Enter | open document |
| `+` `−` | zoom |
| `0` | reset camera |
| `X` | X-ray (admin) |
| `S` | split view (admin) |
| `P` | Plan view |
| `Space` | pause ambient |

- Each node's label: "Building: Minutes, CS Dept 12 Oct. 22 passages, 3 lit by your last question. Restricted spans: 4."

**Fallback without WebGL (T0), the "City Plan":**
- An SVG treemap with districts as blocks (labelled) and buildings as rectangles sized by chunk count. Windows are small squares in a grid inside each rectangle; lit windows are amber, restricted lots are hairline-only.
- It is fully interactive and uses the same tree mirror.
- It is also printed in the export ("City Plan as of 14:02").

**States:**
- Loading: the City Plan renders first, then the 3D cross-fades in (500 ms).
- Context lost: drop to Plan with the toast "The 3D city fell over. Here's the plan view; same data."
- Empty: "No documents yet. The city is zoned but unbuilt."

---

## D. Cross-cutting specs

- **Page transitions:**
  - App routes: React `<ViewTransition>` around `<Outlet>`. Default is a 140 ms cross-fade; parent→child (list→detail) uses a 220 ms shared-element morph of the row title (`view-transition-name` = `doc-{id}`). Not supported, or reduced motion → instant.
  - Landing → app: a 420 ms "bar sweep": one full-viewport cut-out wipes left to right, and the route swaps under it.
- **Preloader:** see C1.1. In the app: no preloader. A 2 px amber route progress line appears at the top after 300 ms of pending navigation.
- **Cursor and magnetic buttons** (desktop, `(hover:hover) and (pointer:fine)`, landing and public demo only):
  - The cursor is a 10 px amber square at 30% opacity, following with `lerp 0.2`. Over redactions it becomes a horizontal bar 24 × 6 px with the label "withheld".
  - Magnetic pull on primary CTAs only: max 6 px, radius 80 px.
  - The native cursor stays visible over inputs and text.
  - Off in the app, off for reduced motion, off on touch.
- **Sound** (off by default; ♪ toggle in the header and footer; persisted):
  - Three sounds only: *stamp* (redaction, 90 ms low thud), *slide* (reveal, 220 ms paper), *tick* (audit append, 40 ms).
  - Each is ≤ 25 KB Opus with an AAC fallback for Safari, played through Web Audio at −18 LUFS. Loaded only after unmuting.
  - Never sounds for errors.
- **Notifications bell:**
  - Badge: an amber square with an `on-amber` count (max "9+").
  - Panel: 360 px popover (D) or sheet (M).
  - Grouping: Requests, Ingestion, Integrity. Integrity items pin to the top in `alarm`.
  - Actions: "Mark all read". Each item links to its source.
- **Command palette:** shadcn `Command` (cmdk).
  - Groups: Go to, Ask, Documents, People (admin), Actions.
  - Typing a question and pressing Enter sends it to chat.
  - `⌘K` / `Ctrl K`; on M, the search icon opens it full-screen.
  - Results never include restricted titles; a footer reads "Some results are outside your clearance."
- **Toasts** (Sonner via shadcn):
  - Position: bottom-right on D, above the dock on M.
  - Duration: 5 s, or 8 s with an action. They pause on hover/focus and are announced with `role="status"`.
  - Errors that need action are **never** toasts; they go inline.
- **Forms:**
  - Labels above fields (14 px `text`); help text in `dim`; inputs 44 px, `ink-2` with a `line-strong` border.
  - Errors appear on blur or submit as an icon plus text in `alarm`, linked by `aria-describedby`. On submit, the first invalid field is focused.
  - Required fields are marked "(required)", not with an asterisk alone.
- **Tables** (TanStack Table + shadcn `Table`):
  - Rows 44 px (36 px compact for admin); sticky header; mono for IDs, numbers and hashes; numbers right-aligned.
  - Restricted cells use the cut-out cell. Selection is a 2 px amber left rule. Sorting via `aria-sort`.
  - Lists over 200 rows are virtualised.
  - M: rows become 2–3-line list items with the key value right-aligned.
- **Charts** (dataviz principles; skill not available):
  - Built with visx or hand-rolled SVG.
  - Direct labels instead of legends. Greys for context, amber for the focus series only.
  - No gradients, 3D, area fills over 20% opacity, or pie charts.
  - Every chart has a title, a one-sentence takeaway ("GPA up 0.12 since spring"), keyboard-focusable points with tooltips, and "View as table".
  - Colour-blind safety: never rely on hue alone; use patterns for categories.
- **Responsive rules:**
  - Breakpoints: 375 / 640 / 1024 / 1280 / 1440.
  - Dock, sheet and bottom-tab patterns below 1024. Sidebars collapse at 1024 and become sheets below 768.
  - All hover affordances have a tap or focus equivalent.
  - Display type uses `clamp()`; tables move to the list form below 640.
- **Empty and error copy guide:**
  - Empty states say *what will appear* and *how to cause it*.
  - Errors say *what failed*, *what's safe*, and *what to do*. Always state whether logging still happened.
  - Never blame the user. Never joke about people, students or cases. Joke about the system, the bureaucracy and the machine itself.

**Voice and tone: 20 sample strings**
1. "The gaps are the feature."
2. "Outside your clearance. I can't say whether anything's there."
3. "This question was logged. So is this refusal."
4. "Nothing in the records you can see matches that."
5. "Generated from the quotes above. Check them; I'm a summary, not a source."
6. "Deterministic. Same question, same answer, no imagination involved."
7. "Request sent to the Registrar. You'll hear back either way."
8. "Revealed. This reveal is logged as R-0193, and other admins can see it."
9. "Chain intact. 48,211 entries, no gaps, no edits."
10. "Break at entry 41,203. Everything after it needs a human."
11. "214 refusals today. Working as intended."
12. "We'll take the names out before we take them in."
13. "Still working, or quietly broken. Checking…"
14. "No grades yet. Thornwick is still deciding."
15. "That's today's 50. The records will still be there tomorrow. So will the log."
16. "Archive mode: the live system is asleep. You're reading recorded answers."
17. "The 3D city fell over. Here's the plan view; same data."
18. "You may look. Briefly."
19. "If that address has an account, a link is on its way."
20. "39 of 40 privacy tests passed. One leak is one too many."

---

## E. Component inventory

★ = shared by all roles. shadcn = built on a shadcn/ui primitive. Custom = built from scratch.

| Component | Variants | States | Base |
|---|---|---|---|
| ★ Button | primary (amber), secondary (outline), ghost, danger (alarm, admin only) | default, hover, focus, pressed, loading, disabled | shadcn Button |
| ★ Redaction | inline, block, cell, hero, loading, revealed, diff-added, diff-removed | static, focusable (tooltip), revealing | **Custom** |
| ★ PseudonymToken | default, revealable (admin), revealed | hover, focus, revealed | Custom |
| ★ ClearanceToggle | hero (display), compact (badge switcher in demo) | per level, disabled | Custom on Radix ToggleGroup |
| ★ ClearanceBadge | student, faculty, admin, simulation | — | Custom |
| ★ AnswerMessage | record, quote, summary, restricted, not-found, error, loading, stopped | streaming, complete | Custom |
| ★ CitationChip + SourceViewer | drawer, sheet | loading, highlighted, with navigator | shadcn Sheet + custom |
| ★ Composer + QuotaMeter | default, disabled (quota), streaming (Stop) | — | shadcn Textarea + custom |
| ★ RequestAccessDialog | — | form, submitting, sent, error | shadcn Dialog/Form |
| ★ CommandPalette | — | empty, results, no-results | shadcn Command |
| ★ Toast | info, success, action | — | shadcn Sonner |
| ★ NotificationsBell | — | none, unread, integrity alert | shadcn Popover |
| ★ DataTable | default, compact, list-mobile | loading (skeleton bars), empty, error, restricted cells | shadcn Table + TanStack |
| ★ Chart family | line, bar, histogram, heatmap, sparkline, 100% bar | loading, empty, table view | Custom SVG (visx) |
| ★ EmptyState / ErrorState | page, panel, inline | — | Custom |
| ★ ArchiveBanner | — | active | Custom |
| ★ MotionPrefs + SoundToggle | — | on/off | shadcn Switch |
| StudentDock | — | active item, badge | Custom |
| FacultyTopBar | — | course switcher open | shadcn DropdownMenu + custom |
| AdminSidebar | expanded, collapsed, sheet | active, badge | shadcn Sidebar |
| AuditRow + AuditDetail + ChainStatus | — | intact, verifying, broken | Custom + shadcn Sheet |
| IngestionTheater | — | running, stalled, failed, done | Custom |
| OcrReview | — | flags, editing | Custom |
| VersionDiff | side-by-side, inline (M) | — | Custom |
| ClearanceSimulator | 3-column, tabs (M) | — | Custom + shadcn Tabs |
| PrivacyTestTable | — | idle, running, pass, fail with diff | Custom |
| ClearanceCity | T3/T2/T1 canvas, T0 plan, split, X-ray | loading, lost, empty | Custom (R3F) |
| BottomSheet | 3 snap points | dragging | Custom (Motion) on vaul-style behaviour |
| Landing set-pieces: HeroHeadline, PipelineStory, RoleFolders, ArchitectureDiagram, Door | — | reduced-motion static | Custom (GSAP) |
| Auth: OtpInput, PasswordMeter | — | — | shadcn InputOTP + custom |

---

## F. Front-end technical plan

### F1. Libraries (versions as researched; pin exactly at install)

| Package | Version | Date | Flag |
|---|---|---|---|
| react / react-dom | 19.3.1 | 14 Oct 2026 | [SA] |
| react-router | 8.5.1 | — | [V] docs version selector\[47\] |
| vite | 8.3.5 | 21 Oct 2026 | [SA] |
| tailwindcss | 4.3.3 | 16 Jul 2026 | [SA] |
| gsap (incl. ScrollTrigger, SplitText) | 3.15.0 | 13 Apr 2026 | [SA]; v3.15 in the docs header [V]\[1\]\[48\]\[49\] |
| lenis | 1.3.27 | ≈ Oct 2026 | [SA, date approximate]\[50\] |
| motion (import `motion/react`) | 14.9.0 | ≈ early Nov 2026 | [S]. Sources conflict: the changelog shows 14.8.0 on 29 Oct 2026; other pages list 12.x. Verify with `npm view motion version`.\[51\]\[52\]\[53\]\[54\]\[55\] |
| three | 0.187.0 | — | [SA, date unverified]\[56\] |
| @react-three/fiber | 9.8.2 | ≈ Oct 2026 | [V] docs header\[32\]\[57\] |
| @react-three/drei | **unverified** | — | resolve at install |
| @fontsource-variable/martian-mono | 5.3.0 | — | [S] |
| @lottiefiles/dotlottie-react, @rive-app/react-canvas | 0.20.0, 4.36.0 | — | [SA]; **not used in v1**\[58\]\[59\] |
| shadcn/ui | CLI-generated source, not a versioned dependency | — | [M] |

### F2. Folder structure
```
src/
  app/            routes.tsx, providers/ (Theme, MotionPrefs, Quality, Sound, Lenis)
  routes/         landing/, demo-door/, public/, auth/, student/, faculty/, admin/, docs/, city/
  shells/         StudentDock/, FacultyTopBar/, AdminSidebar/
  components/
    ui/           (shadcn generated)
    redaction/    Redaction.tsx, PseudonymToken.tsx, quantise.ts
    chat/         AnswerMessage/, Composer/, SourceViewer/
    data/         DataTable/, charts/
    feedback/     EmptyState, ErrorState, ArchiveBanner, Toasts
  motion/         tokens.ts, gsap.ts (register plugins once), primitives/ (StampIn, WipeReveal,
                  AxisMorph, DrawPath, Stagger), useReducedMotionPref.ts
  three/          City/ (Canvas, Districts, Buildings, Windows, Plan.svg.tsx, Mirror.tsx),
                  useQualityTier.ts, data/city.bin
  lib/            api/, sse/, audit/, format/
  styles/         tokens.css (CSS vars), fonts.css
  test/           e2e/, visual/, a11y/
```

### F3. How the motion libraries coexist
- **One clock on the landing.** GSAP's ticker drives Lenis (`autoRaf:false`, `lenis.raf(time*1000)`, `lagSmoothing(0)`, `lenis.on('scroll', ScrollTrigger.update)`) [S].
  - R3F runs its own loop, but `frameloop="demand"` keeps it idle.
  - While the City teaser is on screen, a GSAP ticker callback calls `invalidate()` only when scroll progress changes.
  - Offscreen: `frameloop="never"`.
- **Ownership rule:** GSAP owns scroll-linked and timeline animations (landing, door, public intro). Motion owns component-state animation (presence, layout, sheets, toasts). **No element's property is animated by both.**
- **Lenis scope:** mounted only in landing, door and public intro layouts. It is destroyed on entering the app, so the app has native scroll and no scroll-jacking.
  - `lenis.stop()` while any dialog or sheet is open.
  - `data-lenis-prevent` on inner scrollers.
  - `ScrollTrigger.refresh()` after fonts load (`document.fonts.ready`) and after the hero width changes.
- **React lifecycle:** use `@gsap/react` `useGSAP()` with scoped contexts for cleanup [M]. Kill all ScrollTriggers on route leave.

### F4. Build order: motion primitives first
1. `tokens.ts` (durations and easings mirrored as CSS variables and GSAP strings) and `useMotionPrefs()` (OS setting + site toggle).
2. `<Redaction>` with quantised widths and all variants. Every screen depends on it.
3. `StampIn`, `WipeReveal` (`clip-path`), `AxisMorph` (variable-font tween with reduced-motion cut), `DrawPath`, `Stagger`.
4. `useQualityTier()`:
   - **Initial guess:** WebGL2 support, `navigator.deviceMemory`, `hardwareConcurrency`, Save-Data, reduced motion → start at T2 or T1.
   - **Runtime:** after a 2 s warm-up, sample 90 frames of `performance.now()` deltas in `useFrame`, using the median.
     - Downgrade when the median is > 22 ms.
     - Upgrade when it is < 12 ms for 5 s.
     - At most 3 flips, then lock (mirrors Drei's `flipflops`/`onFallback` [V]).\[60\]
   - Persist in `sessionStorage`. Expose `{ tier, reason, setTier }`. The user can force "Plan view".
5. `<ViewTransition>` route wrapper with its fallback.

### F5. Testing plan
- **Visual:** Playwright screenshots of each screen × {375, 1440} × {motion, reduced} × {student, faculty, admin}. Animations are frozen by setting `prefers-reduced-motion` and a `data-test-freeze` flag that jumps GSAP timelines to their end.
- **Reduced-motion checks:** run with `page.emulateMedia({ reducedMotion: 'reduce' })` and assert:
  - no pinned elements (`.pin-spacer` absent)
  - Lenis not instantiated
  - all content reachable by Tab
  - no `transform` animations (inspect computed `animation-name`).
- **Accessibility:** axe-core on every route, which must report no "serious" or "critical" issues. A manual NVDA + Firefox and VoiceOver + iOS Safari pass on chat, the restricted state, the audit log and the City mirror. Keyboard-only run-throughs.
- **Contrast:** a token unit test recomputes every text/background pair in B1 and fails below 4.5:1 (text) or 3:1 (UI).
- **Performance:**
  - Lighthouse CI on the landing with mobile throttling: LCP ≤ 2.5 s, CLS ≤ 0.05, TBT ≤ 200 ms.
  - WebPageTest on a real mid-range Android (e.g. a Moto G-class device, 4G profile).
  - Field RUM with web-vitals sent to your own endpoint (no third parties).
- **Devices:** Chrome on Android (mid-range and flagship), Chrome on desktop (Windows/macOS), Safari on iPhone (address-bar show/hide during the pinned story, safe areas around the dock), Firefox on desktop (view-transition fallback, variable-font axes).
  - Degrade check: Samsung Internet and an old iPad. The site must still work at T0 with no pins.
- **3D:** force each tier via a `?tier=` query string. Simulate context loss with `WEBGL_lose_context`.

---

## G. Risks and anti-patterns, with fixes

| Risk | Fix |
|---|---|
| Redaction bars invisible on ink (1.12:1) | Cut-out on `ink-2` with a 3.52:1 `line-strong` edge (B5). |
| Bar width leaks the hidden text's length | Hash-quantised S/M/L widths and 1/3/5 line blocks. |
| "Restricted" reads as an error wall | No red; name the policy; one action; log transparency copy. |
| Restricted vs not-found leaks that a record exists | Category-level copy: "I can't say whether any exist". The palette never lists restricted titles. City shows counts, not titles. |
| Motion blocks reading (hero choreography) | Text painted at frame 0; any input skips; ≤ 900 ms; first visit only. |
| Text unreadable over 3D | No text over the canvas except focus outlines; copy sits beside or below it; labels on `ink-1` chips with a 1 px border. |
| Scroll-jacking inside the app | Lenis is unmounted in the app; no scroll-linked motion there. |
| Pinned story janks on iOS when the address bar toggles | `ignoreMobileResize`, `svh` units, short mobile pin, no `normalizeScroll`, no transformed ancestors on pins.\[23\] |
| Amber glare at small sizes | Amber text ≥ 14 px and ≥ 500 weight; never in paragraphs; amber fills carry ink text. |
| `dim` on hover rows fails (4.29:1) | Use `text` on `ink-3`. |
| Font-loading flash or CLS in the hero | Preload Anybody, metric-matched fallback, `swap`. Width changes happen only on discrete clicks or keypresses on the toggle. Per web.dev's CLS article, "Layout shifts that occur within 500 milliseconds of user input will have the hadRecentInput flag set, so they can be excluded"; scroll-driven width changes would not be excluded, so there are none in the hero.\[61\] |
| Variable-axis animation costs layout per frame | Animate one headline element only; never axis-animate body or table text. |
| Too many images (the Checkpoint logo-stack pattern) | ≤ 12 images on the landing, AVIF/WebP, sized, lazy; no layered hover images. |
| 3D drains battery on idle | `frameloop="demand"`, pause offscreen, idle flicker stops after 5 s. |
| Vestibular triggers in the City | Orthographic camera, no rotation, no auto-fly; reduced motion → cuts. |
| Live audit stream moves on its own | Pause control; auto-pause on hover/focus (SC 2.2.2). |
| Summary mistaken for a source | Dashed rule plus the word "Generated" plus a "Check them" footer; Record/Quote are visually distinct. |
| Archive mode mistaken for live data | Banner that can't be dismissed while active; "recorded" in every answer footer. |
| Two characterful fonts clash | Martian never above 14 px next to Anybody; Anybody never below 24 px. |
| GSAP licence misread | Permitted for websites and web apps [SA]; don't build a no-code animation builder on it.\[34\] |

---

## Self-critique (as a demanding outsider), and what I changed
1. *"Your signature redaction bar is invisible."* True of the proposal. I measured it and changed it to a cut-out with an edge.
2. *"Red for 'denied' contradicts your own thesis."* Removed. Red now appears only for integrity breaks, so it actually means something.
3. *"Bars leak name length."* Added hash quantisation.
4. *"The preloader will tank LCP."* I made it non-blocking, with the text painted first.
5. *"A perspective camera with a fly-through is vestibular bait."* Switched to a fixed orthographic camera.
6. *"Not-found vs restricted is an existence oracle."* Rewrote the copy to the category level.
7. *"Lenis in a data app is scroll-jacking."* Scoped Lenis to the marketing surfaces.
8. *"Snap on mobile pins fights momentum."* Removed snap on touch.
9. *"This is the generic dark AI kit."* Warmed the ink, banned glows, made type the hero and the hole the motif. Still weak: role folders risk reading as "cards". Keep them asymmetric and text-led, or cut them.

---

## H. Sources

| Page | What I took | Flag |
|---|---|---|
| https://www.translate-wf.com/ | Word-swap gag, scroll-narrated beats, bar-breaker, SVG-heavy illustration | [V] |
| https://finsweet.com/portfolio/weglot | "Most viewed and cloned Webflow website of 2020" | [S] |
| https://www.checkpointresearch.ca/ | Bracketed rotating word, type-led hero, 3-layer logo stack (≥ 27 requests) | [V] |
| https://www.awwwards.com/igloo-inc-case-study.html | WebGL UI text rationale, continuous low-end performance measurement, shader warm-up, real-time intro | [V] |
| Awwwards WebGL collection / abeto post | Igloo Inc Site of the Year 2024 | [S] |
| https://linear.app/now/how-we-redesigned-the-linear-ui | Inverted-L chrome, noise reduction and density, `#08090a` theme colour | [V] |
| https://gsap.com/blog/3-13/ | GSAP 100% free incl. all plugins, commercial use; docs at v3.15 | [V] |
| https://gsap.com/community/standard-license/ | Prohibited use limited to no-code visual animation builders; websites and web apps permitted | [SA] |
| GSAP docs: `config()`, `normalizeScroll()`, `scrollerProxy()` | `ignoreMobileResize`, `normalizeScroll` iOS caveat, `pinType` behaviour | [SA] |
| https://github.com/darkroomengineering/lenis | GSAP ticker integration snippet | [S] |
| https://r3f.docs.pmnd.rs/advanced/scaling-performance | Draw-call guidance, instancing, `<Detailed>`, `PerformanceMonitor`, `regress`, `frameloop="demand"`, v9.8.2 | [V] |
| https://reactrouter.com/how-to/view-transitions | 8.5.1 current [V]; router viewTransition APIs deprecated in favour of React 19.3 `<ViewTransition>` [S] | [V]/[S]\[26\] |
| https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html | SC 2.3.3 intent, three sufficient routes, motion-animation definition, blur errata | [V] |
| https://web.dev/articles/lcp | LCP ≤ 2.5 s at p75, mobile/desktop segmented | [S] |
| https://fonts.google.com/specimen/Anybody | Width axis present; designer Tyler Finck | [S] |
| https://www.npmjs.com/package/@fontsource-variable/martian-mono, fontsource.org | Martian Mono wdth 75–112.5, wght 100–800, OFL | [S] |
| https://github.blog/…/introducing-mona-sans-and-hubot-sans/ and the github/mona-sans README | Mona/Hubot axes, OFL | [S] |
| abduzeedo.com (Google Sans Flex) | Six-axis OFL font | [S] |
| Relativity help: Markups, Reviewing markups, Redact Reports | Redaction types, navigator, QA, reason/author/timestamp/original text | [S] |
| Google Docs Help: "You need access" | Request access, optional reason, owner notification | [S] |
| WorkOS Admin Portal / Platform Audit Logs; Clerk Admin Logs; PubNub Audit log | Audit-UI conventions | [S] |
| npm / deps.dev / Snyk / endoflife.date pages (via sub-agent) | Package versions in F1 | [SA] |
| Grafana Labs blog, "3 tips to improve your Grafana dashboard design" (via Owler) | "around 8% of men are color-blind"; "Using red on black is similarly tricky for people with certain kinds of color blindness"; limit colours\[62\] | [S] |

## Assumptions
- Roles are exactly student, faculty and admin. Faculty may see real names of their own enrolled students; everything else about people is pseudonymised or withheld.
- Clearance is role-based, not per-document ACLs, except for time-boxed grants.
- The backend exposes SSE ingestion events, a retrieval event listing chunk IDs, and a hash-chained audit API with a verify endpoint.
- The daily quota is 50 questions per user.
- Personas, documents and policy IDs (TU-PRIV-3, TU-114, G-04) are fictional placeholders I invented.
- Display uses English only (latin subset).
- A reveal stays visible for at most 120 s, or until navigation.

## Could not verify
- Exact current versions of @react-three/drei, and the exact publish dates for lenis, motion, three and R3F. The motion version is also conflicting across sources.
- The full body of the React Router view-transitions page (deprecation details came from its excerpt).
- Anybody's and Hanken Grotesk's axis ranges and licences are now settled from Fontsource listings: Anybody is wdth 50–150, wght 100–900, OFL-1.1; Hanken Grotesk is wght 100–900, OFL-1.1.\[37\]\[38\] Those listings came through the enrichment step, not pages I opened.
- Firefox's current View Transitions support (from memory, hence the fallback).
- Library gzip sizes in the budget. The CLS input exclusion now cites web.dev's 500 ms `hadRecentInput` rule.\[61\]
- Fewer than 8 site studies were fully opened (4 opened, 4 from excerpts); Webflow's own showcase was not opened.

## Sources

1. [3.13 release](https://gsap.com/blog/3-13/)
2. [Webflow Project for Weglot](https://finsweet.com/portfolio/weglot)
3. [Weglot for Webflow](https://www.translate-wf.com/)
4. [SR&ED Tax Credit Consultants in Canada | Checkpoint Research](https://www.checkpointresearch.ca/)
5. <https://www.awwwards.com/igloo-inc-case-study.html>
6. [abeto on X: "We won Site of the Year and Developer Site of the Year on @awwwards with our project for Igloo Inc. Thank you to everyone who voted for it! 🎉 #threejs #webgl" / X](https://x.com/abeto_co/status/1900152588768579701?lang=en)
7. [Awwwards Nominees](https://www.awwwards.com/inspiration_search/igloo/)
8. [How we redesigned the Linear UI (part Ⅱ) – Linear](https://linear.app/now/how-we-redesigned-the-linear-ui)
9. [Markups](https://help.relativity.com/RelativityaiR/Content/Relativity/Viewer/Markups.htm)
10. [Reviewing markups to ensure accuracy - RelativityOne](https://help.relativity.com/RelativityOne/Content/Relativity/Relativity_Redact/Reviewing_markups_to_ensure_accuracy.htm)
11. [Redact Reports - RelativityOne](https://help.relativity.com/RelativityOne/Content/Relativity/Relativity_Redact/Redact_Reports.htm)
12. [My experience with RelativityOne Redact - CCL](https://www.cclsolutionsgroup.com/post/my-experience-with-relativityone-redact)
13. [Learn more about access to Google files - Computer - Google Docs Editors Help](https://support.google.com/docs/answer/16722399?hl=en&co=GENIE.Platform%3DDesktop)
14. [Platform Audit Logs](https://workos.com/docs/audit-logs/platform-audit-logs)
15. [Admin Logs](https://clerk.com/docs/guides/dashboard/logs/admin-logs)
16. [audit log](https://www.pubnub.com/docs/security/audit-log.md)
17. [martians-font - Webflow](https://martians-font.webflow.io/)
18. [GitHub - darkroomengineering/lenis: Smooth scroll as it should be · GitHub](https://github.com/darkroomengineering/lenis)
19. [lenis-react](https://lobehub.com/skills/orkait-ai-skill-agent-lenis-react)
20. [@studio-freight/lenis - npm](https://www.npmjs.com/package/@studio-freight/lenis)
21. [static-config](<https://gsap.com/docs/v3/Plugins/ScrollTrigger/static.config()/>)
22. [gsap.com](<https://gsap.com/docs/v3/Plugins/ScrollTrigger/static.normalizeScroll()>)
23. [3.10 release](https://gsap.com/blog/3-10/)
24. [Translating a scrolltrigger pin - GSAP - GreenSock](https://gsap.com/community/forums/topic/37507-translating-a-scrolltrigger-pin/)
25. [ScrollTrigger - Pin element and custom scroller jerky a lot - GSAP - GreenSock](https://gsap.com/community/forums/topic/40089-scrolltrigger-pin-element-and-custom-scroller-jerky-a-lot/)
26. [View Transitions](https://reactrouter.com/how-to/view-transitions)
27. [react](https://deps.dev/npm/react)
28. [Anybody Font — Free Download & Preview](https://everythingfonts.com/font/anybody)
29. [Anybody - Google Fonts](https://fonts.google.com/specimen/Anybody)
30. [Martian Mono — Font Details & License](https://fontsource.org/fonts/martian-mono/about)
31. [GitHub - ValentinaEgorova/mona-sans-mm: Mona Sans, a variable font from GitHub · GitHub](https://github.com/ValentinaEgorova/mona-sans-mm)
32. [Scaling performance - React Three Fiber](https://r3f.docs.pmnd.rs/advanced/scaling-performance)
33. [Understanding Success Criterion 2.3.3: Animation from Interactions | WAI | W3C](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html)
34. [Standard License](https://gsap.com/community/standard-license/)
35. [@fontsource-variable/martian-mono - npm](https://www.npmjs.com/package/@fontsource-variable/martian-mono)
36. [@fontsource-variable/mona-sans - npm](https://www.npmjs.com/package/@fontsource-variable/mona-sans)
37. [Anybody — Font Details & License](https://fontsource.org/fonts/anybody/about)
38. [Hanken Grotesk — Font Details & License](https://fontsource.org/fonts/hanken-grotesk/about)
39. [How Do You Meet WCAG 2.3.3 Animation from Interactions?](https://testparty.ai/blog/wcag-animation-interactions-guide)
40. [Largest Contentful Paint (LCP) | Articles | web.dev](https://web.dev/articles/lcp)
41. [Introducing Mona Sans and Hubot Sans - The GitHub Blog](https://github.blog/news-insights/company-news/introducing-mona-sans-and-hubot-sans/)
42. [Best Variable Fonts on Google Fonts in 2026 — FontFYI](https://fontfyi.com/blog/best-variable-fonts/)
43. [Google Sans Flex Free Font: Six Variable Axes, One File](https://abduzeedo.com/google-sans-flex-free-font-six-variable-axes-one-file)
44. [Martian Mono at Evil Martians](https://evilmartians.com/products/martian-mono)
45. [What Is the WCAG 2.5.8 Target Size Minimum and How Do You Meet It?](https://testparty.ai/blog/wcag-target-size-guide)
46. [Target Size (Minimum) — WCAG 2.2 SC 2.5.8 (AA)](https://wcag22aa.org/new-criteria/target-size/)
47. [CHANGELOG.md](https://reactrouter.com/changelog)
48. [gsap package versions](https://security.snyk.io/package/npm/gsap/versions)
49. [Archive](https://gsap.com/blog/archive/)
50. [lenis - npm](https://www.npmjs.com/package/lenis)
51. [motion - npm](https://www.npmjs.com/package/motion)
52. [framer-motion](https://snyk.io/advisor/npm-package/framer-motion)
53. [framer-motion - npm](https://www.npmjs.com/package/framer-motion)
54. [Motion (prev Framer Motion): JavaScript & React animation library](https://www.framer.com/motion/)
55. [framer-motion](https://security.snyk.io/package/npm/framer-motion)
56. [three - npm](https://www.npmjs.com/package/three)
57. [@react-three/fiber - npm](https://www.npmjs.com/package/@react-three/fiber)
58. [@lottiefiles/dotlottie-react - npm](https://www.npmjs.com/package/@lottiefiles/dotlottie-react)
59. [npm](https://www.npmjs.com/~rive-engineering)
60. [100 Three.js Tips That Actually Improve Performance (2026)](https://www.utsubo.com/blog/threejs-best-practices-100-tips)
61. [Cumulative Layout Shift (CLS) | Articles | web.dev](https://web.dev/articles/cls)
62. [Owler Reports - Grafana Blog 3 tips to improve your Grafana dashboard design](https://www.owler.com/reports/grafana/grafana-blog-3-tips-to-improve-your-grafana-dashbo/1598385121363)
