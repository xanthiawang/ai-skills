# NotebookLM Slide Generation Prompt

Use this prompt with `notebooklm generate slide-deck "... [paste prompt] ..."` every time.

---

## The Prompt

```
Design a presentation following these strict rules:

STYLE: Architectural Calm — minimal, confident, precise. Not decorative. Not busy.

BACKGROUND: Pure white (#FFFFFF) on every slide. No exceptions. No cream, no gray, no dark slides.

COLOR PALETTE (only these):
- Primary text: warm ink #181114 (not pure black)
- Body text: #3A3A3A
- Secondary text: #666666
- Tertiary/captions: #999999
- ONE accent color: rust #B3796D — used for accent bars, emphasis, indicators
- No other colors. No blue. No teal. No gold. No gradients.

TYPOGRAPHY:
- Font family: Calibri
- Headings: Calibri Bold, generous size (36pt+ for section titles, 28pt for slide titles)
- Body: Calibri Regular, 15-16pt
- Table text: 12-13pt
- Strong font-size contrast is the primary hierarchy tool
- Left-align body text. Center only title slides and section dividers.
- No serif fonts. No thin/light weights for headings — bold only.

LAYOUT RULES:
- Every content slide has a small section label top-left: "01. SECTION NAME" in light gray
- Slide number bottom-right on every content slide
- Heavy use of negative space — intentionally leave large areas empty
- Strict grid alignment
- One idea per slide
- Minimum 0.5" margins

VISUAL CONTENT (CRITICAL — this is the main purpose):
- Generate rich visuals on EVERY slide: diagrams, flowcharts, conceptual illustrations, architecture diagrams, process flows, comparison matrices
- 90%+ of slides MUST have a visual element — text-only slides are unacceptable
- Visuals should be the primary information carrier, not just decoration

CLIPPABLE LAYOUT (CRITICAL — visuals will be auto-cropped):
- Slide title MUST be ABOVE the visual with clear whitespace separation (never overlapping)
- Layout order top-to-bottom: [section label] → [title] → [whitespace gap] → [content area]
- TWO layout modes are allowed:

  MODE A — CENTERED BLOCK (preferred):
  The visual is centered on the slide. No text beside it. One cohesive region that can be cropped as a rectangle.

  MODE B — TWO-COLUMN (text left + figure right):
  Bullets or text on the LEFT column. Diagram or figure on the RIGHT column.
  There MUST be a clear vertical whitespace gap (at least 30px) between the two columns.
  Each column's content must stay entirely within its column — nothing crossing the gap.

- In BOTH modes: no content may cross or overlap the crop boundaries (top gap below title, vertical gap between columns). The auto-cropper cuts along whitespace lines, so anything on the cut line gets destroyed.
- No text floating over, overlapping, or interleaved with the visual

LAYOUT CATALOG (use variety, never repeat same layout consecutively):
- Full-width centered visual with title above (most common, best for clipping)
- Two-column: bullets left + figure right (clear vertical whitespace gap between columns)

SPECIAL SLIDES:
- Title slide: white background, title large bold and centered, subtitle centered below, speaker name + affiliation centered lower, date at bottom center
- Section dividers: white, centered large title, minimal
- Outline: list of sections with rust indicator bar on current section
- Closing: "Thank You" centered, rust divider, contact info

TONE:
- "This system already works. We are just showing you."
- Calm, modern, confident, precise
- No hype language, no marketing slogans
- Academic clarity

STRICT AVOIDANCE:
- No dark backgrounds
- No gradients or shadows
- No decorative accent lines under titles
- No thick borders or bright color blocks
- No gray borders, frames, rounded rectangles, or card-like containers around visuals. Visuals float directly on the white background with no enclosing shape.
- No collage, stickers, stamps, or pixel art
- No emojis or playful icons
- No text-only slides without visuals
- If it feels "fun" or "decorated", it's wrong
- If it feels "inevitable" and "clean", it's right
```
