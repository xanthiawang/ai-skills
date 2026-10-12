---
name: reference-site-prototype
description: "Build a client-facing website or product prototype by measuring a reference site page by page, mapping the company's products and customers to the information architecture (To B / To C doors, login, language), writing content-marketing pages (guides vs FAQ), switching colour schemes for review, and verifying every route with a headless-Chrome walkthrough before publishing. Use when Zixin asks for a website demo, landing page, brand-site prototype, UX flow redesign from a reference, colour-scheme switcher, or a clickable walkthrough for a client (e.g. 'imitate Dia', '做成可点击的网站给甲方 walk through')."
---

# Reference-site prototype

Lessons from the 沐仞 / FathomPeak site (2026-10-12), where a Dia-style prototype went
through nine rounds of correction. Follow this file before the first pixel, and re-read
"Pitfalls" before every publish.

## Outputs

- One self-contained HTML prototype (hash router, scheme switcher in the footer), published as
  an Artifact at a stable URL and opened in Zixin's browser with `open -a Dia <url>`.
- A research board with **screenshots** of every reference page (Zixin: "我需要有它的截图，而不只是你的话语阐述").
- An audit file in the project (`…自检_<date>.md`) that records each round: what was asked, what changed, why.
- Memory entries: project profile + feedback file. Write them the moment a direction is rejected or confirmed.

## Workflow

### 1. Products × customers → doors (before any UI)

Read the company's own materials first and fill this table; every entrance on the site must
come from a row in it.

| Product line | Customer | How they buy | Entrance on the site |
|---|---|---|---|

- Self-serve product (developers, individuals): home page speaks only to them, one black CTA.
- Sales-led segment (enterprise, overseas): its own page, Dia-For-Work shape: one sentence →
  "individual vs enterprise" comparison table → trust FAQ (licence, data residency, invoices,
  SLA, private deployment) → sales form. Secondary links under the hero CTA route them there.
- Supply side / partners (e.g. power plants): its own page with a form; no console login.
- **One console, one login.** Account type (个人 / 企业) is chosen at registration and unlocks
  invoices, contracts, sub-accounts, custom quotes. Do not design two login flows.
- Reference evidence: Dia has no login on the site because accounts live in the app; its B
  story is Security in the nav + For Work and Trust Center in the footer. 无问芯穹 puts B on the
  corporate site and C on a separate console domain joined by one "登录平台" button.

### 2. Navigation rules

- Nav holds **content pages only**, 3 to 5 items. Merge pages whose content overlaps
  (models + pricing became one page with a `#pricing` alias that scrolls to the section).
- The account entry is **secondary**: lighter colour, hairline divider, right end of the pill,
  label "登录" that becomes "控制台" once a key exists in this browser. Mobile: the grey button
  at the bottom of the menu.
- A language switch is a secondary utility next to it, only when an overseas segment exists.
  It leads to an English landing page (overview, models, cross-border sales flow, sales form);
  nav and button labels swap via `data-zh` / `data-en`; deeper pages may stay Chinese, say so on the page.
- Before adding any nav item, write the user flow it serves. If you cannot, it does not exist.

### 3. Walk every page of the reference, then measure

- Capture **every** page, not just home (`scripts/capture_site.py`): nav/footer links, CTAs
  with background colours, first-screen PNG, long JPEG. Build a contact sheet and look at it.
- Classify pages: *painted* (artwork in the first screen), *mist* (soft colour haze), *paper*
  (nothing). Dia: home/apps/changelog/early-birds painted, for-work/help mist, security/release
  notes/windows paper. Assign the same mix to the prototype; a prototype that learned only the
  home page makes every page look the same.
- Measure, never eyeball: pill nav (top offset, height, radius, blur, shadow, padding, logo
  size, link size, no CTA inside), buttons (height, radius, hover colour, no lift), transition
  durations and easings, reveal timing, marquee, sticky showcase. Computed styles come from
  the CDP client (`scripts/cdp_client.py`), hover states via `CSS.forcePseudoState`.
- Colour fields: sample pixels at several points **and measure the geometry** (apex height,
  edge sag, band widths). "晨昏" in Dia's Early Birds page is not parallel bands; it is a planet
  horizon: a large-radius radial gradient, charcoal inside, dusk → mauve → pink → pale → sky
  blue outward. Matching the colours but not the shape was rejected.
- Measured values for Dia (2026-10-12) are in `references/dia-measured-2026-10-12.md`; reuse
  them as a starting point for the "paper editorial" look.

### 4. Colour schemes

- Scheme A stays as decided unless Zixin says otherwise. New schemes come from sampled
  reference pixels, not from memory.
- Transitions, never hard blocks (`feedback-color-transitions`): OKLab ramps or radial fields.
  White stays the dominant base; a dark scheme touches the hero and accents, not the whole site.
- Compute WCAG contrast for text colours (`scripts/color_tools.py`) and put the numbers in the audit.
- Put a scheme switcher in the footer ("配色（评审用）") so A/B/C can be compared in one build.
- **Keep rejected directions as a selectable scheme instead of deleting them.** The painted
  hero was called ugly in one round and asked back as "方案三" two rounds later.
- Do not fake artwork with filters. Procedural "oil paint" (SVG turbulence + displacement) was
  rejected on the home page; if a page needs a painting, use a real image (image generation
  needs Zixin's explicit go-ahead because of cost) or an illustrator.

### 5. Content pages

- **Card covers are content previews** generated from the card's own data: first checklist
  items with boxes, a mini price curve with the window shaded, a two-line diff, a two-row
  table, three receipt fields, a step chain. Never a single big character or abstract glyph
  (峰 / √ / 站 / 碳 was unreadable and 峰 read as 封).
- **Guides answer "how"**: verb-phrase titles (从 OpenAI 切到沐仞 / 把任务排进平价窗口 /
  上线前检查清单), a "什么时候看 / 读完你拿到" block, body with a checklist or table, a
  next-step CTA per audience. Each guide maps to one pre-decision question; otherwise cut it.
- **FAQ answers "what / whether"**: question titles, two or three sentences, placed where the
  objection appears (home bottom, pricing, enterprise page), each answer linking to the guide.
  Question-titled guides duplicate the FAQ; that was the complaint.
- Formats to cover for content marketing: checklists, guides, events, video (placeholder
  until real), infographic, newsletter with archive, conversation guide for buyers.
- Every number is an example and says so (示例); prices come from live or official pages with
  the date; client-facing files never name the reference site or competitors.

### 6. Build conventions

- Single file, hash router (`#home #models #model-<id> …`), `data-route` sections, `data-nav`
  links, tokens on `:root` with `:root[data-scheme="B"]` overrides, `prefers-reduced-motion`.
- Artifact fragment convention: the file starts with `<title>` and has no doctype. For local
  headless tests wrap it in `<!doctype html><html><head><meta charset><meta viewport>` first,
  or the mobile viewport renders at 980px wide.
- Use `scripts/walkthrough.py <file> <outdir> route[:js] …` for every route × desktop/mobile:
  JS errors, horizontal overflow, full-page screenshots. Then **look at the screenshots**.
- Shoot each scheme separately (set `localStorage` scheme key, reload) and lay them side by
  side with the reference crop before publishing.
- Publish with the same `file_path` to keep the URL; `open -a Dia <url>`; append the round to
  the audit file and memory.

## Pitfalls (each one cost a round)

- In-page anchors: `href="#id"` is a route in a hash-router site and falls back to home. Use
  `data-scrollto` + `scrollIntoView`.
- An absolutely positioned colour band paints above static content: give the content wrapper
  `position:relative; z-index:1` and the band `z-index:0`.
- Class-name collisions inside one file (`.code` was already the dark docs code block). Prefix
  new utility classes.
- Mobile wordmark wrapped inside a 40px logo box: `white-space:nowrap` and `width:auto` on mobile.
- Opening the mobile menu in a test: setting `location.hash` fires `hashchange`, which closes
  the menu; set the hash, wait, then click.
- `.top{display:contents}` written after the mobile media query overrode the mobile layout;
  scope desktop-only rules with `@media (min-width:801px)`.
- Headless Chrome on a reused port/profile returns a wrong count or blank shots; `pkill` the
  old instance and delete the profile dir before rerunning.
- Two sessions editing one prototype file: message the other session, let it finish, use
  string-replace patches with assertions (`count == 1`), never whole-file writes.
- `t:'…'` replacements must not match `fmt:'…'`; anchor regexes on a preceding non-word char.
- Reference pages gate content behind IntersectionObserver; scroll through the page before
  capturing or infer from the stylesheet.

## Scripts

- `scripts/cdp_client.py` — stdlib WebSocket CDP client (`WS` class, `CHROME` path). Import by
  path; other scripts take its path as the first argument.
- `scripts/capture_site.py <cdp_client.py> <url> <out_prefix> <port> [width]` — header/footer
  links, CTAs with colours, first-screen PNG, long JPEG, JSON.
- `scripts/walkthrough.py <prototype.html> <outdir> route[:js] …` — wraps the fragment, runs
  desktop and mobile, reports JS errors and overflow, saves screenshots and `walkthrough.json`.
- `scripts/color_tools.py '#hex' '#hex' …` — CIEDE2000 distances, WCAG contrast against white
  and black, OKLab ramp between two colours.

## Related skills

`impeccable` for general frontend craft, `anti-ui-slop` for the finish gate, `nature-figure`
is not for this. `feedback-color-transitions` and `fathompeak-*` memories hold the project
history behind these rules.
