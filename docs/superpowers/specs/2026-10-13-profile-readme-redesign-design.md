# GitHub Profile README Redesign — "Terminal / Phosphor"

Date: 2026-10-13 · Owner: Amiel Acuña (Emyol) · Status: approved design, pending spec review

## 1. Intent

**What the owner said:** the current profile (monochrome "Silver Field" SVGs) feels basic and plain. It is missing motion, personality *and* dynamic/fun elements ("all of the above"). The profile should impress **both** recruiters and fellow developers equally.

**Success looks like:**
- A first-time visitor sees something alive and distinctive within ~3 seconds, then the page settles and is easy to read.
- A recruiter skimming for ~20 seconds can find: who Amiel is, the four pinned projects, the stack, and how to make contact, without waiting for any animation.
- Parts of the page refresh themselves daily, with no manual upkeep.
- It looks right in GitHub light **and** dark themes and on mobile.

**Direction chosen:** B1 · Terminal — Phosphor. The page reads as one terminal session in muted mint on near-black, with a matching light palette. Rejected alternatives: Silver Field Alive (too close to today's design), Manila Terminal palette, Manila Night, and Bento.

## 2. Page content (top to bottom)

| # | Section | Terminal command shown | Form | Notes |
|---|---------|------------------------|------|-------|
| 1 | Hero | `whoami` → **Amiel Acuña.** → `cat role.txt` → "Student leader · web & mobile · FEU Tech, Manila" → `$ ▌` | Animated SVG (`hero`) | Followed by a markdown link row (below) |
| 1b | Links | — | Markdown | [Portfolio](https://project-miel.vercel.app) · [LinkedIn](https://www.linkedin.com/in/amiel-acu%C3%B1a) · [Email](mailto:acunaamieljosiah@gmail.com) |
| 2 | Work | `ls ~/work --pinned` | One header SVG + **one linked SVG strip per project** + one markdown line under each | Strips: `01 KitaKo`, `02 iCARE Reservation`, `03 BekiLang`, `04 CitySense`. Each strip shows a short tagline and tinted stack icons (see §2.1) |
| 3 | Stack | `neofetch` | SVG (`stack`) | ASCII sun (Philippine flag nod) on the left. Grouped icon+label rows on the right (see §2.2). Colour swatch row at the bottom |
| 4a | Stats | `gh stats` | SVG generated daily (`stats`) | Contributions this year · current streak · longest streak · public repos (non-fork) · language share bar (top 5 by bytes, non-fork repos). **Not shown:** followers, stars |
| 4b | Commit grid | `git log --graph --all` | Platane/snk snake SVG, generated daily | Phosphor palette, dark + light outputs |
| 5 | Recent | `git log --oneline -3` | Markdown between `<!-- recent:start -->` / `<!-- recent:end -->`, rewritten daily | The last 3 public commits by Emyol, excluding the profile repo itself and merge commits. Format: `` `sha7` repo: message `` |
| 6 | Footer | `exit` — "salamat sa pagbisita · thanks for stopping by" | SVG (`footer`) | |

There is no hand-written "now" section for now. It can be added later as markdown above §5.

### 2.1 Work strip content

| Strip | Tagline | Icons | Link | Markdown line (kept from current README) |
|---|---|---|---|---|
| KitaKo | find a photo in your own words | Flutter, Dart, ONNX | github.com/Emyol/KitaKo_Codebase | On-device semantic photo search with Taglish support. |
| iCARE Reservation | room bookings for 700+ STEM students | Next.js, React, JavaScript | github.com/Emyol/iCARE-Reservation | AVR and Training Room scheduling with JavaScript, React, and Next.js. |
| BekiLang | Swardspeak, compiled | Python, Flask | github.com/Emyol/BekiLang | A Swardspeak-inspired programming language with a Python compiler and interpreter, and a Flask web interface. |
| CitySense | urban heat & greenspace from orbit | TypeScript, React, Leaflet, Vite | github.com/Emyol/city-sense | Earth observation layers for exploring urban heat, greenspace, water, and population. |

### 2.2 Stack groups (taken from the repos' package.json / requirements.txt)

- **Languages:** TypeScript, JavaScript, Python, Dart, C++
- **Web:** Next.js, React, Tailwind CSS, shadcn/ui, GSAP
- **Mobile:** Flutter, ONNX Runtime
- **Data:** Supabase, Prisma, Flask, pandas, scikit-learn
- **Testing:** Playwright, Vitest
- **Tools:** Git, Vercel, Figma, Leaflet

Framer Motion is deliberately left out: no accurate monochrome logo exists, and the Framer logo would mislabel it.

## 3. Visual system

**Palette tokens**

| Token | Dark | Light |
|---|---|---|
| bg | `#0c100e` | `#f4f7f4` |
| chrome (title bar) | `#151b17` | `#e8eee9` |
| fg | `#d7e4da` | `#1d2a21` |
| dim | `#7d8f82` | `#5d6e62` |
| prompt / accent | `#7ee2a0` | `#1f7a43` |
| string | `#a8d8ff` | `#0b5cad` |
| line | `#223028` | `#cfdcd2` |
| heat c0–c4 (stats bar, snake dots) | `#141a16 #1d3a28 #2b6a44 #4fa36e #7ee2a0` | `#e3e9e4 #b9dcc4 #7cc296 #3f9a62 #1f7a43` |

**Type:** Geist (existing, OFL) for the name and project titles. **Geist Mono** (OFL, to be vendored) for all terminal text. All text is converted to `<path>`, because SVGs rendered via `<img>` cannot load fonts. Every text group carries `aria-label`, and every SVG has a `<title>`.

**Frame:** a terminal window with three dots in the title bar, 12-unit corner radius, 1-unit `line` border. Canvas width is 1200 units (same as today).

**Legibility floor:** secondary text is ≥ 22 units and body/terminal text ≥ 26 units on the 1200-unit canvas.

**Icons:** single-colour paths from `tools/icons/`, inlined into the SVG and filled with `prompt` (or `dim` where secondary).

## 4. Motion rules (Emil Kowalski design-engineering principles)

- **Play once, then settle.** The intro choreography finishes in ≤ 3.2 s. The SVG's static (non-animated) state *is* the final frame, so no-animation renderers still show complete content.
- **Easing:** entrances use `cubic-bezier(.23,1,.32,1)`, about 420 ms, translateY 6 units + opacity. Typing uses `steps(n)`, done with a transform-animated clip rect rather than layout properties.
- **Stagger:** rows *inside* one SVG (neofetch groups, stats lines) stagger at 60 ms. Work strips are separate images, so each strip `i` bakes in a start delay of `i × 60 ms`. They load together, so this reads as a cascade.
- **Only `transform` and `opacity`** are animated.
- **Infinite motion is allowed in only two places:** the hero cursor (`1.06s steps(1)` blink) and the snake (inherent to snk; it sits below the fold).
- **`@media (prefers-reduced-motion: reduce)`** inside each SVG disables all animation. The final frame shows.
- **No hover affordances** (no ↗ arrows, no "button" styling), because README images are not interactive.

## 5. Architecture

```
README.md                      ← hand-authored layout + <picture> tags + recent markers
assets/
  static/{name}-{dark,light}.svg   ← committed, built locally
  live/stats-{dark,light}.svg      ← committed by the Action
tools/
  svg.py            ← primitives: text→path, rect/circle/path, icon inlining, palette tokens, animation CSS
  build_static.py   ← hero, work header, 4 work strips, stack (neofetch), footer
  build_live.py     ← fetches GitHub data → stats SVGs + rewrites README recent block
  icons/            ← vendored icon SVGs + ICONS-LICENSE.md (Simple Icons 16.30.0 CC0; Devicon v2.16.0 MIT for Playwright)
  fonts/            ← Geist[wght].ttf (existing), GeistMono[wght].ttf (new), OFL.txt
  tests/            ← pytest: stats maths + README marker rewrite, with JSON fixtures
.github/workflows/profile.yml
```

`tools/build_visuals.py` is split into `svg.py` + `build_static.py`. The old Silver Field assets (`silver-field`, `kitako`, `icare`, `bekilang`, `citysense`, `toolkit`) are deleted.

**Theme switching:** every image is embedded as

```html
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/static/hero-dark.svg">
  <img alt="…" src="assets/static/hero-light.svg">
</picture>
```

Work strips wrap the `<picture>` in `<a href="repo-url">`.

**Daily workflow (`profile.yml`):** runs on `schedule` (daily, 16:00 UTC = midnight Manila) + `workflow_dispatch`, with `permissions: contents: write`.

1. `Platane/snk` (pinned major version) generates `github-snake-dark.svg?palette=github-dark&color_snake=#7ee2a0&color_dots=<c0..c4 dark>` and `github-snake.svg?color_snake=#1f7a43&color_dots=<c0..c4 light>`. These are pushed to the `output` branch with `crazy-max/ghaction-github-pages`, and the README references them via `raw.githubusercontent.com/Emyol/Emyol/output/…`.
2. `python tools/build_live.py` uses `GITHUB_TOKEN` (public data only):
   - GraphQL `user.contributionsCollection.contributionCalendar` → total this year, current streak, longest streak.
   - GraphQL `user.repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC)` → count, and `languages` edges (bytes) → top 5 share.
   - REST `GET /users/Emyol/events/public` → PushEvents → newest 3 commits, excluding repo `Emyol/Emyol` and messages starting with `Merge`.
3. Commit `assets/live/*` + `README.md` only if the diff is non-empty, as `github-actions[bot]`.

**Error handling:** `build_live.py` builds everything in memory first. If any fetch or render fails, it writes nothing and exits non-zero, so the previous SVGs and README stay in place and the failed run shows in the Actions tab. The README recent block is replaced only between the markers. If the markers are missing, the script fails rather than appending.

**Streak definition:** consecutive days ending today (Asia/Manila) with ≥ 1 contribution. If today has 0 but yesterday > 0, the streak counts through yesterday, so the morning doesn't read as zero.

## 6. Verification

- `pytest tools/tests`: streak (gap days, today-zero rule, year boundary), language share (rounding sums to 100, forks excluded), recent-commit filtering, README marker rewrite (idempotent, fails on missing markers).
- `python tools/build_live.py --fixtures tools/tests/fixtures` produces stats SVGs offline.
- Every generated SVG parses as XML, has a `<title>`, and is < 300 KB.
- Contact sheet PNG of all assets in both themes (`previews/`, git-ignored) for visual review, including a 360 px-wide render to check mobile legibility.
- After pushing: trigger the workflow manually, confirm it goes green, and check the live profile in GitHub light, GitHub dark and on a phone.

## 7. Out of scope

Visitor counters, badge walls, third-party stats services (github-readme-stats, streak-stats, trophies), WakaTime, and a hand-written "now" section.

## 8. Deployment assumption

The work happens in the `polyp` worktree (branch `Emyol/create-github-profile-readme`), and the finished result is pushed to `Emyol/Emyol` `main`. The local repo currently has no remote, so the remote is configured at implementation time.
