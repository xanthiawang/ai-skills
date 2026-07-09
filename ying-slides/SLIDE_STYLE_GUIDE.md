# Ying Lab Unified Slide Style Guide

**Style name:** Architectural Calm
**Influences:** JP Minimal Portfolio + Anti-Gravity Living Artifact + Academic Figure-Centric

---

## 1. Core Philosophy

This is not a slide deck. It is a **visual argument**.

- Every slide communicates one idea
- Figures are the primary carrier of meaning — text supports, never leads
- Whitespace is structural, not leftover. Use it to frame content, not to
  strand small objects.
- The feeling should be: "This already works. We are just showing you."
- Calm, confident, precise. Never flashy. Never busy.

If it feels "fun" or "decorated," it's wrong.
If it feels "inevitable" and "clean," it's right.

### Reference Deck Calibration

Use `<your-reference-deck>.pptx`
as the default local reference for all decks made with this skill. This includes
job talks, project pitches, journal clubs, paper walkthroughs, internal updates,
and single-slide visuals. It is a pacing and density reference, not a theme to
copy verbatim.

Emulate:
- Large, direct headlines at the top-left.
- Figure-first slides where the evidence panel fills the available canvas.
- Bottom-edge citations and slide numbers that do not steal space from the
  main figure.
- Dense composed panels when several figures are needed for one argument.
- Short centered transition slides only when they clarify the talk arc.

Do not emulate by default:
- The small top-left section label. Zixin prefers that removed unless asked
  for explicit section navigation.
- Any one-off serif typography or alternate accent colors from imported source
  material. Keep native slide text in the Architectural Calm system.

### IPD Background Calibration

For IPD, Institute for Protein Design, David Baker, Hannele Ruohola-Baker,
protein-design, and OpenAI x IPD decks, use
`<your-background-asset>.png` as the
background on every slide. This is the prior IPD-slide requirement: the deck
should keep the white canvas while carrying the thin IPD gradient bar at the top
and the small IPD mark near the bottom.

Implementation rule:
- Use `t.createPresentation("Title", { useIpdBackground: true })` for new IPD
  deck scripts.
- For manual slides, set `s.background = { path: t.IPD_BACKGROUND_PATH };`.
- Do not approximate the IPD background with a native rectangle or gradient.

---

## 2. Color System

| Role | Hex | Name | Usage |
|------|-----|------|-------|
| **Background** | `FFFFFF` | White | Default slide canvas. IPD decks use `ipd_bg.png` on every slide. |
| **Primary text** | `181114` | Warm ink | All headings and body text |
| **Body text** | `3A3A3A` | Dark gray | Body paragraphs, bullets |
| **Secondary** | `666666` | Muted | Subtitles, descriptions |
| **Tertiary** | `999999` | Light | Captions, citations, slide numbers |
| **Accent** | `B3796D` | Rust | Accent bars, indicators, emphasis — the ONE color |
| **Accent dark** | `39221D` | Rust dark | Rare, for contrast when needed |
| **Accent light** | `DFC7C2` | Rust light | Diagram fills, subtle backgrounds |

**Rules:**
- Rust is the only accent color. No blue, no gold, no teal.
- Never use pure black `000000` — always warm ink `181114`.
- No gradients on slides and no colored backgrounds, except the required
  IPD-branded background PNG for IPD-related decks.
- Color is used for emphasis, not decoration.

---

## 3. Typography

| Element | Font | Size | Weight | Color |
|---------|------|------|--------|-------|
| Slide title | Calibri | 28pt | Bold | `181114` |
| Section divider title | Calibri | 36pt | Bold | `181114` |
| Body text | Calibri | 13-14pt | Regular | `202020` |
| Bullet items | Calibri | 13-14pt | Regular | `202020` |
| Side-message lead | Calibri | 15pt | Bold | `B3796D` (rust) |
| Table headers | Calibri | 13pt | Bold | `181114` |
| Table cells | Calibri | 12pt | Regular | `202020` |
| Captions | Calibri | 10pt | Regular | `666666` |
| Citations | Calibri | 10pt | Italic | `999999` |
| Large callout numbers | Calibri | 48-72pt | Bold | `181114` |
| Callout labels | Calibri | 14pt | Regular | `666666` |

**Rules:**
- No serif fonts. Ever.
- Font size contrast is a primary design tool — large titles vs. small body creates hierarchy without decoration.
- **Body type is dense (13-14pt), not 15-16pt.** The manual Kang deck runs
  annotation/body text at ~12-13pt and fills the canvas. Keep body compact so
  figures dominate; do not inflate body text to fill empty space — enlarge or
  compose the figure instead.
- Body color is `202020` (cooler near-black); headings stay warm ink `181114`.
- Left-align body text. Section dividers are now LEFT-aligned (one key word in
  rust); center only the simple closing slide.
- No bold in body text except for key terms and the rust side-message lead.

---

## 4. Layout System

### 4.1 Grid & Spacing

- Slide: 10" × 5.625" (16:9)
- Margins: 0.5" left/right, 0.4" top, 0.35" bottom
- Content width: 9.0"
- Minimum gap between elements: 0.3"
- Use controlled whitespace. If more than about one third of the slide is blank
  around a small central object, enlarge, crop, split, or recompose the visual.

### 4.2 Section navigation

Do not use top-left section labels by default. They make the slide feel more
generic and reduce the clean first impression.

Use section navigation only when Zixin explicitly asks for it. In that case,
pass both `sectionNav` and `showSectionNav: true` to the template. Use Calibri,
11pt, color `999999`, positioned above the title in the top-left corner.

### 4.3 Slide Number & Citation

- Slide number: bottom-right, 9pt, `999999`
- Citation: bottom-left, 9pt, italic, `999999`
- Both present on every content slide

### 4.4 Layout Catalog

**Primary layouts (ordered by frequency):**

| Layout | Description | When to use |
|--------|-------------|-------------|
| **Figure** | Title + full-width figure | 80%+ of slides — the workhorse |
| **Dual Figure** | Title + two figures side by side | Comparisons, before/after |
| **Grid Figure** | Title + N figures in rows/cols | Multiple panels, methods overview |
| **Figure + Text** | Figure one side, rust `lead` + bullets other | When figure needs a side conclusion |
| **Large Number Callout** | Big stat (48–72pt) + label + context | Key metrics, results highlights |
| **Icon Cards** | 2–4 borderless icon/heading/body columns | Reasons, criteria, pillars |
| **Asymmetric Split** | 60/40 or 70/30 text-visual split | When one side dominates |
| **Timeline** | Vertical or horizontal axis with events | Chronology, process steps |
| **Content** | Bullets only | Use sparingly — last resort |

**Special layouts:**

| Layout | Description |
|--------|-------------|
| **Title** | Opening — centered, or `heroImage` for image-bleed (image left, text right) |
| **Section Divider** | Large LEFT-aligned phrase, one key word in rust; `attribution` for a quote |
| **Outline** | Talk structure with rust indicator on current section |
| **Thank You** | Closing — simple centered, or `columns` for the dense acknowledgments wall |

---

## 5. Figure Handling

### 5.1 Sizing (CRITICAL)

- **NEVER stretch or distort** — always preserve aspect ratio
- Use contain sizing: fit within bounds, center in bounding box
- Figures should fill maximum available space below the title
- For conceptual diagrams, the main visual should occupy roughly 75-90% of the
  available figure slot in at least one dimension.
- Read actual pixel dimensions and compute exact fit
- In journal-club decks, make the paper figure the dominant object. Use a short side conclusion only after the figure has enough scale.
- Do not leave large unused blank space around a small figure. If the source aspect ratio wastes space, recompose complete panels on a white canvas instead of shrinking the whole page figure.

### 5.2 Figure Sources (priority order)

1. **Real data plots** — matplotlib/R output from actual analysis
2. **Saved figures** — existing PNGs/PDFs from papers or projects
3. **Nature schematic** — use `nature-schematic` for biomedical/scientific
   workflow figures, mechanism cartoons, graphical abstracts, and conceptual
   panels. Generate a no-text base, inspect it, add labels deterministically,
   and embed the PNG preview while keeping the editable master.
4. **Mermaid diagrams** — rendered locally via `renderMermaid()` for exact-text
   flowcharts
5. **Generic image generation** — non-biomedical abstract visuals and icons

### 5.3 Diagram Style (Mermaid)

- Node fill: rust-light `DFC7C2`
- Node border: rust `B3796D`
- Text: warm ink `181114`
- Lines/arrows: warm ink `181114`
- Secondary nodes: blue-light `C8D0D9` / sage-light `C7DAD5`
- Background: transparent (inherits white)
- Font: Calibri, 16px

### 5.4 Journal Club Paper Figures

Use these rules when the deck is primarily a paper walkthrough:

- Use the paper title/author page as a screenshot on the paper-introduction slide.
- Each result slide should usually show one paper figure, one complete subfigure, or a few complete related panels.
- Write a short headline and a compact side conclusion. Do not add a "Take home" label.
- Keep extracted paper figures in their original colors. Do not recolor data figures to match the template.
- Crop from the outer edges to remove page headers, page numbers, captions, and article body text.
- Do not cut through the middle of a figure to remove unwanted text. If text or captions are embedded between panels, crop complete panels separately and recompose them.
- Never clip axes, legends, panel letters, scale bars, or in-panel labels.
- If a source figure is too tall or too complex, focus the slide on the relevant complete panel rather than compressing the full page until it becomes unreadable.
- After building the deck, render to PDF/PNG and inspect the actual slide images for clipping, stranded whitespace, and text overlap.

---

## 6. Icons

- Thin-line, outline style only (not filled)
- Consistent stroke weight
- Rendered via react-icons → sharp → PNG
- Color: accent `B3796D` or muted `666666`
- Used sparingly — only when they add information, not decoration
- No pixel art. No emojis. No playful icons.

---

## 7. What to Avoid (Strict)

- No dark backgrounds (not even for title/closing)
- No gradients, shadows, or transparency effects
- No cards with borders or rounded corners
- No decorative accent lines under titles
- No thick borders or bright color blocks
- No centered body text (center only titles/dividers)
- No text-only slides without any visual element
- No repeating the same layout for consecutive slides
- No low-contrast elements
- No collage, stickers, or stamps
- No serif fonts
- No stretched or distorted images
