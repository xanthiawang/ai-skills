---
name: ying-slides
description: "Ying Lab slide pipeline: pptxgenjs template calibrated against the Kang job-talk reference deck, with IPD-branded background support and nature-schematic routing for scientific workflow figures. Architectural Calm style for talks, journal clubs, paper-figure walkthroughs, decks requiring PDF figure extraction, clean cropping, editable PPTX output, and visual QA."
---

# Ying Lab Slide Pipeline

Build editable PPTX decks with `ying_template.js`. Route biomedical and
scientific schematics through `nature-schematic`, use Mermaid for deterministic
flowcharts, and reserve generic image generation for non-biomedical abstract
visuals or icons. Calibrate every deck against the Kang job-talk reference deck.
Use the IPD-branded background for IPD, David Baker, Hannele Ruohola-Baker,
protein-design, and OpenAI x IPD decks.

## When to Use

Any time Albert asks to create a presentation, slide deck, or pitch deck.

## Style: Architectural Calm

- **Background**: Pure white (#FFFFFF) by default. For IPD-related decks, use
  the IPD-branded background on every slide.
- **Accent**: Rust `#B3796D` only — no blue, no teal, no gold
- **Text**: Warm ink `#181114` (not pure black), body `#3A3A3A`
- **Font**: Calibri Bold headings (28pt), Calibri Regular body (13-14pt) — no serif, no light/thin weights. Body type is intentionally dense to match the Kang manual deck, which runs body/annotation text at ~12-13pt. Do not inflate body text back to 15-16pt; the manual style is compact, figure-led, and canvas-full.
- **Body text color is `202020`** (cooler near-black) to match the manual deck; headings stay warm ink `181114`.
- **Titles 28pt, body 13-14pt, captions ~9-10pt, citations 10pt.** Keep titles large; keep body compact. A slide should feel full, not sparse.
- **Layout**: Figure-centric (80%+ slides have visuals), canvas-efficient
  whitespace, one idea per slide
- **No top-left labels by default**: Do not use `sectionNav` on content or title
  slides unless Albert explicitly asks for it. If needed, pass both
  `sectionNav` and `showSectionNav: true`.
- **Title slide**: Centered, key phrase in rust accent color via `titleParts`
- **No decoration**: No shadows, gradients, borders, cards, accent lines under titles
- **Images**: NEVER stretch — always use contain sizing to preserve aspect ratio

### IPD Background Requirement

For IPD, Institute for Protein Design, David Baker, Hannele Ruohola-Baker,
protein-design, and OpenAI x IPD decks, every slide must use the IPD-branded
background from the previous IPD slides:

`<your-background-asset>.png` (e.g. an IPD/lab branded background)

This background is mostly white, with a thin blue-to-purple bar across the top
and a small IPD mark near the bottom. It replaces the plain white slide
background for these decks. Do not recreate it with a native line or gradient;
use the PNG as the slide background.

In new deck scripts, set it once when creating the presentation:

```javascript
const t = require("~/programs/ai-skills/ying-slides/ying_template.js");
const pres = t.createPresentation("OpenAI x IPD deck", {
  useIpdBackground: true,
});
```

For an existing presentation object, call:

```javascript
t.useIpdBackground(pres);
```

If a slide is built manually with `pres.addSlide()`, call
`s.background = { path: t.IPD_BACKGROUND_PATH };` before adding content. All
standard `ying_template.js` slide builders inherit the IPD background from the
presentation automatically.

### Reference Deck: Kang Job Talk

For every deck built with this skill, use the Kang job-talk deck as the local
calibration reference:

`<your-reference-deck>.pptx`

This applies to job talks, project pitches, journal clubs, paper walkthroughs,
internal updates, and single-slide visuals. Use the reference for pacing,
density, and canvas use, not as a literal theme file:

- Prefer title-first slides: one direct headline, then a large evidence panel.
- Let figures occupy most of the slide. A normal content slide should feel
  visually full, with citations and slide numbers tucked against the bottom
  edge rather than consuming the main canvas.
- Use dense, composed evidence panels when the argument needs multiple pieces
  of evidence on one slide. Avoid shrinking a single figure into a sea of
  whitespace.
- Use one-line transition slides sparingly to reset the audience between
  sections.
- Keep paper/data colors as-is inside imported figures, but keep native slide
  text and accents in the Architectural Calm palette.
- Do not copy the reference deck's top-left section labels unless Albert
  explicitly asks for section navigation. The current default is no top-left
  label.

### v6 Kang-style defaults (auto-applied)

The template (v6) now reproduces the manual Kang-deck signatures automatically.
Reach for these instead of rebuilding them by hand:

- **Hero title slide**: pass `heroImage` to `addTitleSlide` for the image-bleed
  layout (image off the left edge, title/speaker/logos in a right-hand column).
  A left-weighted or right-fading image works best; a soft white scrim feathers
  the seam. Omit `heroImage` for the centered fallback.
- **Section dividers**: `addSectionSlide` is now left-aligned with the key word
  in rust via `titleParts` (e.g. `[{text:"More "},{text:"models.",accent:true}]`).
  Pass `attribution` for a quote slide; pass `align:"center"` for the old look.
- **Side-message lead**: `addFigureTextSlide` takes a `lead` (bold rust mini-
  heading above the bullets/body). Do not label it "Take home"; state the
  conclusion. Body/bullets render at ~12-13pt.
- **Icon-card rows**: `addIconCardsSlide({ title, cards:[{icon?,heading,body}] })`
  builds 2-4 borderless columns (reasons, criteria, pillars). `icon` is an
  optional rust line-icon PNG; text-only columns are fine.
- **Acknowledgments closing**: pass `columns` (and optional `logos`, `contact`)
  to `addThankYouSlide` for the dense credit wall (mentors / collaborators /
  funding). Omit `columns` for the simple centered "Thank You".
- **Claim titles ending in a period** ("Aging is the foundation of disease.")
  read as the manual style. Keep titles as direct claims.
- **Section nav stays OFF by default** even though the manual deck uses it.
  Albert's standing preference is no top-left label unless he asks; enable with
  `showSectionNav:true` + `sectionNav` per slide.

### Research 1-on-1 / project update override

Use this mode for Albert's internal research updates, advisor 1-on-1s, project
steering decks, and small group review decks. These decks must read like
scientific research presentations, not administrative status reports.

- Start from the final audience question. Build the deck around what Albert
  needs the audience to decide, inspect, or believe after the meeting.
- Use research titles, not meeting titles. The title slide should name the
  scientific object, method, or prioritization problem. Avoid generic wording
  such as "1-on-1 update," "progress report," or "agent demo."
- Use claim titles on content slides. Each title must make a scientific claim,
  define a method boundary, or ask a decision question. Reject vague labels such
  as "Overview," "Results," "Pipeline," or "Agent" unless they are section
  dividers.
- Add a method-onboarding ramp before unfamiliar platforms, assays, agents, or
  browsers. Cover what it is, why this source is authoritative, what it
  measures or ranks, what it cannot answer, and how it changes the next action.
- Use authoritative source visuals before local derivative views. If Albert asks
  for Open Targets, screenshot the official Open Targets Platform page first.
  Use local browsers only after the upstream source and scoring contract are
  clear.
- Crop and zoom screenshots to the claim-relevant region. A full browser
  screenshot is acceptable only if the labels remain readable at presentation
  distance. Otherwise, crop to the title, selected tab, ranked rows, and
  evidence columns that support the slide claim.
- Prefer one large evidence panel plus one compact interpretation or decision
  callout. Avoid card grids and rectangular box layouts unless comparing
  choices or showing a deterministic pipeline.
- End each section with a decision slide. Show the current evidence, the
  residual uncertainty, and the recommended next action. Highlight the
  recommendation rather than leaving every option visually equal.
- Add speaker notes for every assay, platform, agent, or source-introduction
  slide. Notes must be presenter-ready: introduce the method, explain why the
  slide exists, and bridge to the decision.
- If Albert provides a concrete reference deck or slide folder, that reference
  takes precedence over generic style defaults, including the IPD background
  rule, unless Albert explicitly asks to keep the default branding.

### Journal Club / Paper-Figure Deck Override

Use this mode when Albert asks for a journal club, paper walkthrough, or "slides from the paper."
This is a content-routing override, not a visual-style override: still calibrate
spacing, title scale, figure density, and bottom-edge citations against the
Kang reference deck.

- Let the paper figures carry the deck. Most result slides should be one paper figure, one subfigure, or a small set of related panels.
- Use the paper title/author page as a screenshot on the paper-introduction slide. Do not recreate the title and author block as typed text unless the source screenshot is unavailable.
- Use a short slide headline plus a compact side message. Do not label the side message "Take home"; just write the conclusion.
- Keep the figure large. Use the available canvas before adding explanatory text. A side message is acceptable, but it must not shrink the figure more than needed.
- Omit section-nav/top-left labels and decorative horizontal bars unless Albert
  explicitly asks for them. They read as generic/AI-like in this format.
- Keep formatting quiet: white background by default, or the IPD-branded
  background when the deck is IPD-related. No cards, no borders around the
  figure, no dividers, no decorative rules.
- Use paper colors as-is. Do not recolor extracted data figures to match the template.
- Use `nature-schematic` for biomedical conceptual aids, workflow figures,
  mechanism cartoons, graphical abstracts, or schematic panels. Use Mermaid
  only for deterministic flowcharts with exact node text. Keep these on a white
  canvas, or the IPD-branded background when the deck is IPD-related, and avoid
  fabricated data.

### Clean Paper-Figure Extraction

- Prefer PDF-rendered page images or source figure files over browser screenshots.
- Crop only from the outer edges unless intentionally isolating a complete panel. Do not mask or cut through the middle of a figure to remove labels, captions, or page text.
- Never clip axis labels, legends, panel letters, scale bars, or in-panel text. If a panel is crowded, keep more margin and use slide scale/layout to fit it.
- If a paper figure is too wide, tall, or multi-panel for one slide, crop complete panels separately and recompose them on a white canvas. Preserve each panel intact.
- Remove article headers, page numbers, captions, and body text from the edges. If removing them would cut figure content, split panels instead of forcing one crop.
- For paper title slides, screenshot the title/author block cleanly and avoid clipping author lines or abstract text mid-line.
- Before finalizing, inspect both the source crop and the rendered slide. A crop can look acceptable alone but still appear too small, clipped, or stranded after slide scaling.

### Writing Rules (avoid AI slop)

- No em dashes (—) in slide text — use commas, periods, or line breaks
- No filler phrases: "In this slide," "Let's explore," "It's worth noting"
- No marketing language: "revolutionary," "game-changing," "cutting-edge"
- Short, direct statements. Academic clarity over persuasion.
- Cite sources on every content slide (bottom-left, italic, light gray)

### Color System

| Role | Hex | Usage |
|------|-----|-------|
| Background | `FFFFFF` | Every slide |
| Primary text | `181114` | Headings (warm ink, not pure black) |
| Body text | `202020` | Paragraphs, bullets (Kang-deck near-black) |
| Secondary | `666666` | Subtitles, descriptions |
| Tertiary | `999999` | Captions, citations, slide numbers |
| Accent | `B3796D` | Rust — accent bars, key phrase color, emphasis |
| Accent light | `DFC7C2` | Diagram fills (mermaid nodes) |

## Pipeline

### Step 1: Plan slide structure

Outline the deck. For each slide, decide which `addXxxSlide` function it uses and what visual goes in each slot. Use the **Slot Sizing** table below to know how big each visual will be on the slide.

For journal clubs, plan figure-first:

1. Paper title/author screenshot
2. One slide per main result figure or important subfigure
3. A short headline stating the result
4. A side conclusion sentence, no "Take home" heading
5. A brief discussion slide only after the figures

### Step 2: Generate visuals through the right visual route

For biomedical or scientific schematic plots, workflow figures, mechanism
cartoons, graphical abstracts, or conceptual panels, invoke the
`nature-schematic` skill first. Follow its workflow: generate a no-text base,
inspect it, add exact labels deterministically, and save both an editable
master plus a PNG preview. A figure like a scientific workflow schematic belongs
there, not in the generic image-generation path.

For deterministic flowcharts where exact node text and arrows matter, use
Mermaid through `renderMermaid()`.

Use generic image generation only for non-biomedical abstract visuals,
transitions, decorative icons, or framework diagrams that `nature-schematic`
does not cover. For those visuals, include:

1. **Target slot** — pick from the Slot Sizing table (e.g. "full-width banner", "half-column inline", "tiny icon")
2. **Aspect ratio** — wide landscape (about 2:1), standard landscape (16:9),
   portrait (2:3), or square (1:1) — pick to match the slot
3. **Style constraints** — Architectural Calm: white background, rust
   `#B3796D` accent only, warm ink line work, no shadows/gradients,
   Calibri-compatible labels if any, and the main visual using most of the
   image canvas
4. **Content description** — what the diagram should show
5. **Output path** — where to save the PNG (typically `./figures/<slide_name>.png`)

For generated PNG previews, always request maximum resolution and highest
quality. Tell the generator to use `quality: "high"` and the largest dimensions
it supports for the chosen aspect. For full-width figure slides, use a wide 2:1
final image, for example `2048×1024` or larger if supported. If the generator
cannot directly return 2:1, place the generated diagram on a final 2:1 white
canvas before embedding it. pptxgenjs handles final fit via `contain` sizing,
so oversized source images improve sharpness.

**Generic image prompt template:**

```
Generate an image and save it to ./figures/<name>.png.

Use this generic prompt only for non-biomedical abstract visuals. If this is a
scientific or biomedical schematic, use the nature-schematic skill instead.

Slot: <full-width banner | half | third | quarter | inline-with-text | tiny icon>
Aspect: <wide landscape 2:1 | standard landscape 16:9 | square 1:1 |
portrait 2:3>

Resolution: maximum available for this aspect. For full-width banners, use a
2:1 output such as 2048×1024 or larger if supported. Use the highest quality
tier the model supports (quality="high" or equivalent). Do not downscale —
pptxgenjs will fit it.

Style: Architectural Calm — pure white background (#FFFFFF), rust #B3796D as the
only accent color, warm ink #181114 for line work and labels, Calibri-style
sans-serif labels. No shadows, no gradients, no borders, no decoration. Clean
diagrammatic.

Canvas use: make the main visual occupy roughly 75-90% of the image width or
height, depending on the composition. Keep only enough white margin for
legibility. Do not strand a small diagram in the center of a mostly empty
canvas.

Content: <describe the diagram/schematic/flowchart>

Do not include slide titles, page numbers, or watermarks in the image — only
the diagram itself.
```

### Slot Sizing

`ying_template.js` uses a 10" × 5.625" widescreen layout. The slot dimensions
below are the **rendered slide regions** — always generate at max resolution
above and let pptxgenjs scale via `contain`.

| Slot type | Slide region (in) | Aspect to request | Used by |
|---|---|---|---|
| Full-width banner | ~9.0 × 4.5 | wide landscape 2:1 | `addFigureSlide` |
| Spanning (titleless) | ~9.7 × 5.3 | standard landscape 16:9 | `addFigureSlide({titleless:true})` |
| Half (side-by-side) | ~4.3 × 4.1 | square | `addDualFigureSlide` |
| Inline with text | ~5.0 × 4.5 | square | `addFigureTextSlide` |
| Third (3-col grid) | ~2.9 × 3.0 | square | `addGridFigureSlide` (3 cols) |
| Quarter (2×2 grid) | ~4.3 × 2.0 | wide landscape 2:1 | `addGridFigureSlide` (2×2) |
| Tiny inline icon | ~1.0 × 1.0 | square | inline `addImage` |

**Pick aspect to match the slot, not the other way around.** Square stretched into a banner wastes space; landscape cropped to square loses content. Even tiny icons should be generated at max source res — sharper on retina displays and zoom.

### Step 3: Semantic and visual verification (MANDATORY)

**Read every generated image before using it.** This is not optional.

Before visual QA, run a semantic QA pass on the rendered deck:

1. **Source authority**: Does every screenshot or figure come from the source
   the audience would recognize as authoritative for the claim?
2. **Claim title**: Can the audience understand the point from the title alone?
3. **Method ramp**: For every unfamiliar assay, platform, or agent, does the
   deck first explain what it is and why it is being used?
4. **Decision clarity**: Does each section end with a concrete ask, decision, or
   next action?
5. **Screenshot readability**: Are product screenshots cropped and zoomed so
   the relevant labels, rows, and columns are readable from the back of a room?
6. **Speaker bridge**: Do speaker notes explain assays, platforms, agents, and
   source screenshots in complete presenter language?

Check each image for:

1. **Style adherence** — white background by default, IPD-branded background
   when required, rust accent, no shadows/gradients, no rogue colors
2. **No spurious text** — no AI-generated slide titles, watermarks, page numbers
3. **Correct content** — diagram matches what was requested
4. **Aspect matches slot** — image dimensions roughly match the target slot aspect
5. **Canvas is used well** — the visual occupies most of the slot, with no
   large empty bands around a small central diagram

If a check fails, refine through the same route: `nature-schematic` for
scientific schematic bases, Mermaid for deterministic diagrams, and image
generation follow-up only for generic images.

For paper figures, also check:

1. **No middle cuts** — no masks, crop edges, or white strips running through the middle of panels
2. **No clipped text** — axes, legends, panel letters, and labels remain intact
3. **No article debris** — page headers, captions, body text, and page numbers are removed from edges
4. **Slide scale** — the rendered slide uses most of the canvas and does not strand a small figure in whitespace
5. **Side message fit** — the conclusion text does not overlap the figure or force it too small

Render the deck to PDF and slide PNGs before final delivery. Inspect figure-heavy slides at rendered size, and make a contact sheet when there are more than a few slides.

### Step 4: Build editable deck with ying_template.js

```javascript
const t = require("~/programs/ai-skills/ying-slides/ying_template.js");
const pres = t.createPresentation("Title");

// Title slide with rust-colored key phrase
t.addTitleSlide(pres, {
  titleParts: [
    { text: "EpiJEPA: ", accent: true },
    { text: "A World Model\nfor the Epigenome" },
  ],
  subtitle: "...",
  speaker: "Zixin Wang",
  affiliation: "Peking University",
});

// Figure slide with a nature-schematic PNG preview or extracted figure
t.addFigureSlide(pres, {
  title: "Latent prediction beats reconstruction.",
  imagePath: "./figures/latent_prediction.png",
  citation: "Assran et al., CVPR 2023",
});

// Spanning visual (no title)
t.addFigureSlide(pres, {
  titleless: true,
  imagePath: "./figures/hero_diagram.png",
});
```

## When to Use Which Method

| Content type | Method |
|---|---|
| Tables, comparisons | Native `pptxgenjs` |
| Large number callouts | Native `addCalloutSlide` |
| Bullet/text slides | Native `addContentSlide` |
| Biomedical/scientific schematics, workflow figures, mechanism cartoons, graphical abstracts | `nature-schematic` → editable master + PNG preview → embed |
| Deterministic flowcharts with exact text | Mermaid via `renderMermaid` |
| Non-biomedical transition/connection visuals | Generic image generation |
| Non-biomedical summary/framework diagrams | Generic image generation, or Mermaid if exact text matters |
| Inline icons / decorative graphics | Generic image generation at small size |
| Real paper figures (data plots, heatmaps, etc.) | Extract from PDF or existing PPTX → embed directly |
| Real scientific data figures (matplotlib) | `nature-figure` skill (real data → PNG) |
| Title / section / thank you | Native template |

Generative tools create conceptual visuals only. They must never reproduce or
approximate real data figures from papers. Real data plots come from
`nature-figure` (matplotlib on real data) or are extracted from source PDFs.
`nature-schematic` bases must not contain generated exact labels, numbers,
axes, sample sizes, p-values, or claims; add those deterministically.

When planning the deck, mark data slides explicitly as
"[DATA FIGURE: description]" so they get routed to extraction or matplotlib,
not generic image generation.

## Template Reference

All files live in this skill directory (`~/programs/ai-skills/ying-slides/`):
- **Template**: `ying_template.js` (v5)
- **Style guide**: `SLIDE_STYLE_GUIDE.md`
- **Outdated** (legacy NotebookLM pipeline, kept for reference): `outdated/`, `scripts/outdated/`

Symlinked into `~/Desktop/Projects/2026/presentation/` for use in deck scripts.

### Slide types

| Function | Purpose | Frequency |
|---|---|---|
| `addTitleSlide` | Title; `heroImage` for image-bleed layout, else centered | 1x |
| `addFigureSlide` | Title + full-width figure (supports `titleless`) | 80%+ |
| `addDualFigureSlide` | Two figures side by side | Occasional |
| `addGridFigureSlide` | N figures in grid | Occasional |
| `addFigureTextSlide` | Figure + text; rust `lead` side-message + bullets | Occasional |
| `addCalloutSlide` | Large numbers (1-3 stats with labels) | For key metrics |
| `addIconCardsSlide` | 2-4 borderless icon/heading/body columns | Reasons/criteria |
| `addContentSlide` | Bullets only (top-aligned) | Sparingly |
| `addSectionSlide` | Divider, left-aligned + rust key word / quote | Between sections |
| `addOutlineSlide` | Auto-scaling talk outline (overflow-safe) | Start/transitions |
| `addThankYouSlide` | Closing; `columns` for the acknowledgments wall | 1x |

### Default title slide setup

Albert is at Peking University, Stanford, and IPD. Always include logos and full affiliation:

```javascript
t.addTitleSlide(pres, {
  titleParts: [
    { text: "Key Phrase: ", accent: true },
    { text: "Rest of Title" },
  ],
  subtitle: "...",
  speaker: "Zixin Wang",
  affiliation: "Peking University · Stanford University · Institute for Protein Design",
  logos: [
    { path: logos + "/stanford_logo.png", w: 1.8 },
    { path: logos + "/ipd_logo.png", w: 1.5 },
    // { path: logos + "/pku_logo.png", w: 1.2 },  // add when valid file available
  ],
});
```

**Hero-image title slide (Kang style)** — pass `heroImage` for the image-bleed
layout (image off the left edge, text in the right column). Use a left-weighted
or right-fading image; logos move to the bottom of the right column:

```javascript
t.addTitleSlide(pres, {
  heroImage: figures + "/title_hero.png",   // bleeds off the left, scrim feathers the seam
  titleParts: [
    { text: "AI for Brain Aging:", accent: true, breakLine: true },
    { text: "From Quantification\nto Intervention" },
  ],
  speaker: "Zixin Wang, PhD",
  affiliation: "Stanford · UW",
  logos: [{ path: logos + "/stanford_logo.png", w: 1.6 }, { path: logos + "/ipd_logo.png", w: 1.3 }],
});
```

**Logos available** at `~/Desktop/Projects/2026/presentation/_logos/`:
- `stanford_logo.png` (1024x335)
- `ipd_logo.png` (800x265)
- `pku_logo.png` (currently corrupt, needs replacement)

### Title slide key phrase coloring

```javascript
// Plain title (single color)
t.addTitleSlide(pres, { title: "My Talk Title" });

// Key phrase in rust accent (mixed colors)
t.addTitleSlide(pres, {
  titleParts: [
    { text: "EpiJEPA: ", accent: true },       // rust color
    { text: "A World Model", breakLine: true }, // dark ink
    { text: "for the Epigenome" },              // dark ink
  ],
});
```

### Outline slide overflow protection

The outline slide auto-scales font size and row spacing based on section count:
- Up to 5 sections: 18pt
- 6-7 sections: 16pt
- 8+ sections: 14pt with compressed spacing

Never overflows regardless of section count.

### Mermaid diagrams

The template includes `renderMermaid(code, outPath)` for flowcharts:
- Uses rust palette: node fill `#DFC7C2`, border `#B3796D`, text `#181114`
- Requires `npm install -g @mermaid-js/mermaid-cli`
- Output PNG embeds via `addFigureSlide`
- Use mermaid for **deterministic** flowcharts where you control exact node
  text. Use `nature-schematic` for scientific workflow figures and organic
  biomedical schematics where layout/style flexibility helps.

## Dependencies

- `npm install -g pptxgenjs` — slide generation
- `nature-schematic` — biomedical/scientific workflow figures, mechanism
  cartoons, graphical abstracts, and conceptual panels
- Image generation — non-biomedical abstract visuals and icons
- LibreOffice (`soffice`) — PDF conversion for QA (optional)
- Poppler (`pdftoppm`) — PDF to slide images for QA (optional)
- `npm install -g @mermaid-js/mermaid-cli` — mermaid diagram rendering (optional)
