/**
 * Ying Lab Slide Template v6 — Architectural Calm
 *
 * Calibrated against the Kang job-talk deck reference style. v6
 * defaults now auto-match that deck:
 *   - Hero-image title slide (image bleeds off the left, text on the right)
 *   - Denser body type (Calibri ~13-14pt, body color 202020)
 *   - Left-aligned section dividers with a rust key word (+ quote mode)
 *   - Bold rust side-message lead on figure+text slides
 *   - Borderless icon-card rows (reasons / criteria / pillars)
 *   - Dense acknowledgments closing (collaborators / mentors / funding)
 *
 * Design:
 *   - White background by default, IPD-branded background available for IPD decks
 *   - Figures are the main player — 80%+ of slides
 *   - All images use contain sizing (NEVER stretch)
 *   - Slide numbers on content slides, citations on every slide
 *   - Section-nav top-left label stays OFF by default (opt-in)
 *   - Mermaid flowchart rendering support
 *
 * Slide types (ordered by frequency):
 *   addFigureSlide       — title + full-width figure (most common)
 *   addDualFigureSlide   — title + two figures side by side
 *   addGridFigureSlide   — title + N figures in a grid (2x2, 3x2, etc.)
 *   addFigureTextSlide   — figure one side + text (supports rust `lead`)
 *   addCalloutSlide      — large number callouts (key metrics/results)
 *   addIconCardsSlide    — 2-4 borderless icon/heading/body columns
 *   addContentSlide      — bullets only (use sparingly)
 *   addTitleSlide        — opening slide; pass heroImage for image-bleed layout
 *   addSectionSlide      — section divider (left-aligned + rust key word / quote)
 *   addOutlineSlide      — talk outline with highlighted section
 *   addThankYouSlide     — closing; pass columns for the acknowledgments wall
 *
 * Utilities:
 *   renderMermaid(code, outPath) — render mermaid diagram to PNG
 *   addImage(slide, opts)        — add image with guaranteed aspect ratio
 */

// Resolve pptxgenjs across machines: prefer the caller's node_modules, then
// fall back to common global locations. This makes the template portable
// between macOS and Linux servers.
function _resolvePptxgenjs() {
  const path = require("path");
  const fs = require("fs");
  // Bases to search for ./node_modules/pptxgenjs (Node looks in node_modules
  // from each directory upward, but only relative to the requiring file —
  // not the entry script. We replicate the entry-script search manually so
  // a deck dir's local install is found.)
  const bases = [];
  if (require.main && require.main.filename) {
    bases.push(path.dirname(require.main.filename));
  }
  if (process.env.PWD) bases.push(process.env.PWD);
  bases.push(process.cwd());
  for (const base of bases) {
    let dir = base;
    while (dir && dir !== path.dirname(dir)) {
      const candidate = path.join(dir, "node_modules", "pptxgenjs");
      if (fs.existsSync(candidate)) {
        try { return require(candidate); } catch (_) { /* keep looking */ }
      }
      dir = path.dirname(dir);
    }
  }
  // Then standard locations.
  const fallbacks = [
    "pptxgenjs",
    "/Users/A.Y/.nvm/versions/node/v22.22.0/lib/node_modules/pptxgenjs",
    "/home/kying/.local/lib/node_modules/pptxgenjs",
    "/usr/local/lib/node_modules/pptxgenjs",
    "/usr/lib/node_modules/pptxgenjs",
    path.join(process.env.HOME || "", ".local/lib/node_modules/pptxgenjs"),
  ];
  for (const c of fallbacks) {
    try { return require(c); } catch (_) { /* try next */ }
  }
  throw new Error(
    "pptxgenjs not found. Install with `npm install pptxgenjs` in the deck directory, " +
    "or globally with `npm install -g pptxgenjs`."
  );
}
const pptxgen = _resolvePptxgenjs();
const { execSync } = require("child_process");
const path = require("path");
const fs = require("fs");

// ── Color System ──
// Calibrated against the Kang job-talk deck reference style.
// Headings use warm ink (181114); body uses the slightly cooler near-black
// 202020 that dominates the manual deck (168 runs). Inline citations inside
// dense text can optionally use the steel tint 94A5A6 (Kang slide 39).
const COLORS = {
  ink:       "181114",  // warm mauve-black — headings/titles
  text:      "202020",  // body text — Kang manual main body color
  textAlt:   "3A3A3A",  // softer body gray (legacy/secondary)
  muted:     "666666",  // secondary text, captions
  light:     "999999",  // tertiary/caption/slide numbers
  steel:     "94A5A6",  // inline-citation tint inside dense text (optional)
  white:     "FFFFFF",  // background (all slides)

  // Accent — rust from nature-figure palette (hero color)
  accent:    "B3796D",  // rust 300 — primary accent
  accentDk:  "39221D",  // rust 600 — dark accent

  // Scientific palette
  rust:      "B3796D",
  rustDark:  "39221D",
  rustLight: "DFC7C2",
  sage:      "5C8F82",
  sageDark:  "22342F",
  blue:      "7689A0",
  blueDark:  "232A33",
  gold:      "C9A959",
  goldSci:   "A08344",
  plum:      "94838F",
};

// ── Typography ──
// v5: heading changed from Calibri Light → Calibri (bolder, matches NLM output)
const FONTS = {
  heading: "Calibri",
  body:    "Calibri",
  mono:    "Consolas",
};

// ── Layout (inches, 16:9) ──
const SLIDE_W = 10;
const SLIDE_H = 5.625;
const MARGIN = { left: 0.5, right: 0.5, top: 0.4, bottom: 0.35 };
const CONTENT_W = SLIDE_W - MARGIN.left - MARGIN.right; // 9.0"
const IPD_BACKGROUND_PATH = "/Users/A.Y/Desktop/Projects/2025/presentations/0825_pku/ipd_bg.png";

// ── Slide number counter ──
let _slideNum = 0;

function _addSlideNumber(s) {
  _slideNum++;
  s.addText(String(_slideNum), {
    x: SLIDE_W - 0.6, y: SLIDE_H - 0.35, w: 0.4, h: 0.25,
    fontSize: 10, fontFace: FONTS.body, color: COLORS.light, align: "right", margin: 0,
  });
}

/**
 * Add optional section navigation label top-left (e.g., "01. INTRODUCTION").
 * @param {Slide} s
 * @param {string} label — e.g., "01. INTRODUCTION"
 */
function _addSectionNav(s, label) {
  if (!label) return;
  s.addText(label, {
    x: MARGIN.left, y: 0.08, w: 5, h: 0.22,
    fontSize: 11, fontFace: FONTS.body, color: COLORS.light, margin: 0,
  });
}

function _showSectionNav(opts) {
  return Boolean(opts.showSectionNav && opts.sectionNav);
}

function _addCitation(s, citation) {
  if (!citation) return;
  s.addText(citation, {
    x: MARGIN.left, y: SLIDE_H - 0.35, w: CONTENT_W - 0.6, h: 0.25,
    fontSize: 10, fontFace: FONTS.body, color: COLORS.light, italic: true, margin: 0,
  });
}

function _applySlideBackground(s, pres, opts = {}) {
  const backgroundPath =
    opts.backgroundPath ||
    (opts.useIpdBackground ? IPD_BACKGROUND_PATH : null) ||
    pres._yingBackgroundPath;

  if (backgroundPath) {
    s.background = { path: backgroundPath };
    return;
  }

  s.background = { color: opts.backgroundColor || pres._yingBackgroundColor || COLORS.white };
}

function _usesImageBackground(pres, opts = {}) {
  return Boolean(
    opts.backgroundPath ||
    opts.useIpdBackground ||
    pres._yingBackgroundPath
  );
}

function _contentTitleY(pres, opts = {}, showSectionNav = false) {
  // Kang manual deck seats titles ~0.32" from the top (with section nav above).
  // Without nav, keep the title near the top but give it breathing room (0.28).
  if (showSectionNav) return _usesImageBackground(pres, opts) ? 0.42 : 0.32;
  return _usesImageBackground(pres, opts) ? 0.35 : 0.28;
}

function _contentBodyY(pres, opts = {}, showSectionNav = false) {
  if (showSectionNav) return _usesImageBackground(pres, opts) ? 1.0 : 0.88;
  return _usesImageBackground(pres, opts) ? 0.95 : 0.82;
}

/**
 * Get image dimensions in pixels.
 * Supports PNG, JPEG, GIF, BMP, WebP.
 */
function _getImageSize(filePath) {
  const buf = fs.readFileSync(filePath);
  // PNG: width at offset 16, height at offset 20 (4 bytes each, big-endian)
  if (buf[0] === 0x89 && buf[1] === 0x50) {
    return { w: buf.readUInt32BE(16), h: buf.readUInt32BE(20) };
  }
  // JPEG: scan for SOF markers (0xFFC0-0xFFC3)
  if (buf[0] === 0xFF && buf[1] === 0xD8) {
    let i = 2;
    while (i < buf.length - 8) {
      if (buf[i] !== 0xFF) { i++; continue; }
      const marker = buf[i + 1];
      if (marker >= 0xC0 && marker <= 0xC3) {
        return { w: buf.readUInt16BE(i + 7), h: buf.readUInt16BE(i + 5) };
      }
      const len = buf.readUInt16BE(i + 2);
      i += 2 + len;
    }
  }
  // GIF: width at 6, height at 8 (2 bytes each, little-endian)
  if (buf[0] === 0x47 && buf[1] === 0x49) {
    return { w: buf.readUInt16LE(6), h: buf.readUInt16LE(8) };
  }
  // BMP: width at 18, height at 22
  if (buf[0] === 0x42 && buf[1] === 0x4D) {
    return { w: buf.readUInt32LE(18), h: Math.abs(buf.readInt32LE(22)) };
  }
  // Fallback: assume 16:9
  return { w: 1600, h: 900 };
}

/**
 * Add image with GUARANTEED aspect ratio preservation.
 * Reads actual image dimensions and computes exact fit within bounds.
 * Image is centered within the bounding box.
 * @param {Slide} s - pptxgenjs slide
 * @param {object} opts - { path, x, y, w, h } — w/h are max bounds
 */
function addImage(s, opts) {
  const dim = _getImageSize(opts.path);
  const imgAR = dim.w / dim.h;
  const boxAR = opts.w / opts.h;

  let finalW, finalH;
  if (imgAR > boxAR) {
    // Image is wider than box — fit to width
    finalW = opts.w;
    finalH = opts.w / imgAR;
  } else {
    // Image is taller than box — fit to height
    finalH = opts.h;
    finalW = opts.h * imgAR;
  }

  // Center within the bounding box
  const finalX = opts.x + (opts.w - finalW) / 2;
  const finalY = opts.y + (opts.h - finalH) / 2;

  s.addImage({
    path: opts.path,
    x: finalX, y: finalY, w: finalW, h: finalH,
  });
}

// ── Mermaid rendering ──
// Mermaid theme config: black text + rust (#B3796D) accent on white
const MERMAID_CONFIG = {
  theme: "base",
  themeVariables: {
    primaryColor: "#DFC7C2",        // rust-100 (node fill)
    primaryBorderColor: "#B3796D",  // rust-300 (node border)
    primaryTextColor: "#181114",    // ink (text)
    lineColor: "#181114",           // ink (arrows/lines)
    secondaryColor: "#C8D0D9",      // blue-100 (alt node fill)
    secondaryBorderColor: "#7689A0",// blue-300
    secondaryTextColor: "#181114",
    tertiaryColor: "#C7DAD5",       // sage-100
    tertiaryBorderColor: "#5C8F82", // sage-300
    tertiaryTextColor: "#181114",
    noteBkgColor: "#FFFFFF",
    noteTextColor: "#181114",
    noteBorderColor: "#B3796D",
    edgeLabelBackground: "#FFFFFF",
    fontSize: "16px",
    fontFamily: "Calibri, Arial, sans-serif",
  },
};

/**
 * Render mermaid diagram to PNG file.
 * Uses black + rust Ying Lab color scheme.
 * Requires: npm install -g @mermaid-js/mermaid-cli
 * @param {string} code — mermaid source code
 * @param {string} outPath — output PNG path
 * @returns {string} outPath
 */
function renderMermaid(code, outPath) {
  const tmpMmd = outPath.replace(/\.png$/, ".mmd");
  const tmpCfg = outPath.replace(/\.png$/, "_mermaid_config.json");
  fs.writeFileSync(tmpMmd, code);
  fs.writeFileSync(tmpCfg, JSON.stringify(MERMAID_CONFIG));
  try {
    execSync(
      `mmdc -i "${tmpMmd}" -o "${outPath}" -b transparent -w 2400 -c "${tmpCfg}"`,
      { stdio: "pipe", timeout: 30000 }
    );
  } finally {
    if (fs.existsSync(tmpMmd)) fs.unlinkSync(tmpMmd);
    if (fs.existsSync(tmpCfg)) fs.unlinkSync(tmpCfg);
  }
  return outPath;
}

// ── Create presentation ──
function createPresentation(title, authorOrOpts = "Zixin Wang", maybeOpts = {}) {
  _slideNum = 0;
  const opts = (authorOrOpts && typeof authorOrOpts === "object")
    ? authorOrOpts
    : maybeOpts;
  const author = (authorOrOpts && typeof authorOrOpts === "object")
    ? (opts.author || "Zixin Wang")
    : authorOrOpts;
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.author = author;
  pres.title = title || "Presentation";
  pres._yingBackgroundPath =
    opts.backgroundPath ||
    (opts.useIpdBackground || opts.background === "ipd" ? IPD_BACKGROUND_PATH : null);
  pres._yingBackgroundColor = opts.backgroundColor || COLORS.white;
  return pres;
}

function useIpdBackground(pres) {
  pres._yingBackgroundPath = IPD_BACKGROUND_PATH;
  return pres;
}

// ═══════════════════════════════════════════════
// SLIDE BUILDERS
// ═══════════════════════════════════════════════

/**
 * Hero-image title slide — full-bleed image on the left, text block on the
 * right. Matches the Kang job-talk title slide (image bleeds off the left
 * edge and fades into a white right column carrying the title, speaker, and
 * logos). Triggered by opts.heroImage.
 *
 * @param {object} opts adds:
 *   heroImage   — string path or { path } of the left hero image
 *   heroWidth   — image bleed width in inches (default 5.8)
 *   heroScrim   — soft white feather over the image seam (default true)
 *   heroTextX   — left edge of the right text column (default auto)
 */
function _addHeroTitleSlide(s, pres, opts) {
  const imgPath = typeof opts.heroImage === "string" ? opts.heroImage : opts.heroImage.path;
  const imgW = opts.heroWidth || 5.8;
  const imgX = -0.3;
  const imgRight = imgX + imgW;

  // Full-bleed cover image on the left (no distortion — crops overflow).
  s.addImage({ path: imgPath, x: imgX, y: 0, w: imgW, h: SLIDE_H, sizing: { type: "cover", w: imgW, h: SLIDE_H } });

  // Soft white feather over the seam so any image fades into the text column.
  if (opts.heroScrim !== false) {
    s.addShape(pres.shapes.RECTANGLE, {
      x: imgRight - 1.3, y: 0, w: 1.7, h: SLIDE_H,
      fill: { color: COLORS.white, transparency: 40 }, line: { type: "none" },
    });
  }

  const textX = opts.heroTextX != null ? opts.heroTextX : imgRight + 0.25;
  const textW = SLIDE_W - textX - MARGIN.right;

  // Title — left-aligned in the right column, rust key phrase via titleParts.
  if (opts.titleParts && opts.titleParts.length) {
    s.addText(opts.titleParts.map((p) => ({
      text: p.text,
      options: { fontSize: 34, fontFace: FONTS.heading, bold: true, color: p.accent ? COLORS.accent : COLORS.ink, breakLine: p.breakLine || false },
    })), { x: textX, y: 0.55, w: textW, h: 1.9, align: "left", valign: "top", margin: 0, shrinkText: true });
  } else {
    s.addText(opts.title || "Title", {
      x: textX, y: 0.55, w: textW, h: 1.9,
      fontSize: 34, fontFace: FONTS.heading, color: COLORS.ink, bold: true,
      align: "left", valign: "top", margin: 0, shrinkText: true,
    });
  }

  if (opts.subtitle) {
    s.addText(opts.subtitle, { x: textX, y: 2.55, w: textW, h: 0.7, fontSize: 13, fontFace: FONTS.body, color: COLORS.muted, align: "left", margin: 0 });
  }

  const info = [];
  if (opts.speaker) info.push({ text: opts.speaker, options: { bold: true, fontSize: 14, color: COLORS.ink, breakLine: true } });
  if (opts.affiliation) info.push({ text: opts.affiliation, options: { fontSize: 11, color: COLORS.muted, breakLine: true } });
  if (info.length) s.addText(info, { x: textX, y: 3.45, w: textW, h: 0.8, fontFace: FONTS.body, align: "left", margin: 0 });

  const foot = [];
  if (opts.event) foot.push({ text: opts.event, options: { fontSize: 10, color: COLORS.light, breakLine: true } });
  if (opts.date) foot.push({ text: opts.date, options: { fontSize: 10, color: COLORS.light } });
  if (foot.length) s.addText(foot, { x: textX, y: 4.35, w: textW, h: 0.4, fontFace: FONTS.body, align: "left", margin: 0 });

  // Logos — left-to-right row in the right column, tucked to the bottom.
  if (opts.logos && opts.logos.length) {
    const logoH = 0.5;
    const logoY = SLIDE_H - logoH - 0.18;
    let logoX = textX;
    for (const logo of opts.logos) {
      const lw = logo.w || 1.4;
      addImage(s, { path: logo.path, x: logoX, y: logoY, w: lw, h: logo.h || logoH });
      logoX += lw + 0.35;
    }
  }

  return s;
}

/**
 * Title slide — centered layout by default; pass opts.heroImage for the
 * Kang-style image-bleed layout (image left, text right).
 * v6: hero-image variant; centered fallback retained.
 * @param {object} opts - { title, subtitle?, speaker?, affiliation?, event?, date?,
 *                          heroImage?, sectionNav?, showSectionNav?, logos?: [{ path, w?, h? }] }
 */
function addTitleSlide(pres, opts = {}) {
  const s = pres.addSlide();
  _applySlideBackground(s, pres, opts);

  // Kang-style hero-image title slide (image left, text right).
  if (opts.heroImage) {
    return _addHeroTitleSlide(s, pres, opts);
  }

  // Legacy opt-in section label top-left (e.g., "VISION").
  if (_showSectionNav(opts)) {
    s.addText(opts.sectionNav, {
      x: MARGIN.left, y: 0.3, w: 4, h: 0.25,
      fontSize: 10, fontFace: FONTS.body, color: COLORS.light, margin: 0,
      charSpacing: 3,
    });
  }

  // Title — centered, large. Supports highlighted key phrase in rust.
  // Use opts.titleParts = [{ text, accent? }] for mixed-color titles,
  // or opts.title for plain text.
  if (opts.titleParts && opts.titleParts.length) {
    const parts = opts.titleParts.map((p, i) => ({
      text: p.text,
      options: {
        fontSize: 36, fontFace: FONTS.heading, bold: true,
        color: p.accent ? COLORS.accent : COLORS.ink,
        breakLine: p.breakLine || false,
      },
    }));
    s.addText(parts, {
      x: MARGIN.left, y: 1.2, w: CONTENT_W, h: 1.6,
      align: "center", valign: "middle", margin: 0,
      shrinkText: true,
    });
  } else {
    s.addText(opts.title || "Title", {
      x: MARGIN.left, y: 1.2, w: CONTENT_W, h: 1.6,
      fontSize: 36, fontFace: FONTS.heading, color: COLORS.ink, bold: true,
      align: "center", valign: "middle", margin: 0,
      shrinkText: true,
    });
  }

  // Subtitle — centered below title
  if (opts.subtitle) {
    s.addText(opts.subtitle, {
      x: 1.0, y: 2.95, w: SLIDE_W - 2.0, h: 0.6,
      fontSize: 14, fontFace: FONTS.body, color: COLORS.muted,
      align: "center", margin: 0,
    });
  }

  // Speaker + affiliation — centered lower
  const info = [];
  if (opts.speaker) info.push({ text: opts.speaker, options: { bold: true, fontSize: 14, color: COLORS.ink, breakLine: true } });
  if (opts.affiliation) info.push({ text: opts.affiliation, options: { fontSize: 11, color: COLORS.muted, breakLine: true } });
  if (info.length) {
    s.addText(info, { x: 1.5, y: 3.85, w: SLIDE_W - 3.0, h: 0.7, fontFace: FONTS.body, align: "center", margin: 0 });
  }

  // Event + date — above logos or at bottom
  const foot = [];
  if (opts.event) foot.push({ text: opts.event, options: { fontSize: 10, color: COLORS.light, breakLine: true } });
  if (opts.date) foot.push({ text: opts.date, options: { fontSize: 10, color: COLORS.light } });
  if (foot.length) {
    const footY = (opts.logos && opts.logos.length) ? 4.25 : 4.7;
    s.addText(foot, { x: 1.5, y: footY, w: SLIDE_W - 3.0, h: 0.4, fontFace: FONTS.body, align: "center", margin: 0 });
  }

  // Logo row at bottom — centered
  if (opts.logos && opts.logos.length) {
    const logoH = 0.55;
    const logoY = SLIDE_H - logoH - 0.15;
    const gap = 0.4;
    // Calculate total width to center the row
    let totalW = 0;
    for (const logo of opts.logos) totalW += (logo.w || 1.6);
    totalW += gap * (opts.logos.length - 1);
    let logoX = (SLIDE_W - totalW) / 2;
    for (const logo of opts.logos) {
      const lw = logo.w || 1.6;
      const lh = logo.h || logoH;
      addImage(s, { path: logo.path, x: logoX, y: logoY, w: lw, h: lh });
      logoX += lw + gap;
    }
  }

  return s;
}

/**
 * Section divider — Kang-style: a large LEFT-aligned phrase, vertically
 * centered, with one key word in rust. Also doubles as a quote slide.
 * v6: left-aligned by default (matches "More models." / "What's Next");
 * pass opts.align: "center" for the old centered behavior.
 * @param {object} opts - { title?, titleParts?: [{ text, accent? }], subtitle?,
 *                          attribution?, align? }
 *   titleParts — mixed-color phrase, e.g. [{text:"More "},{text:"models.",accent:true}]
 *   attribution — small credit line under a quote (e.g. "Peter Drucker")
 */
function addSectionSlide(pres, opts = {}) {
  const s = pres.addSlide();
  _applySlideBackground(s, pres, opts);

  const align = opts.align || "left";
  const x = align === "center" ? MARGIN.left : MARGIN.left + 0.2;
  const w = align === "center" ? CONTENT_W : CONTENT_W - 0.2;

  if (opts.titleParts && opts.titleParts.length) {
    s.addText(opts.titleParts.map((p) => ({
      text: p.text,
      options: { fontSize: 40, fontFace: FONTS.heading, bold: true, color: p.accent ? COLORS.accent : COLORS.ink, breakLine: p.breakLine || false },
    })), { x, y: 1.7, w, h: 1.7, align, valign: "middle", margin: 0, shrinkText: true });
  } else {
    s.addText(opts.title || "Section", {
      x, y: 1.7, w, h: 1.7,
      fontSize: 40, fontFace: FONTS.heading, color: COLORS.ink, bold: true,
      align, valign: "middle", margin: 0, shrinkText: true,
    });
  }

  if (opts.subtitle) {
    s.addText(opts.subtitle, {
      x, y: 3.5, w, h: 0.45,
      fontSize: 14, fontFace: FONTS.body, color: COLORS.muted, align, margin: 0,
    });
  }
  if (opts.attribution) {
    s.addText(opts.attribution, {
      x, y: 3.55, w, h: 0.4,
      fontSize: 13, fontFace: FONTS.body, color: COLORS.light, italic: true, align, margin: 0,
    });
  }

  return s;
}

/**
 * Outline slide — highlighted current section with rust indicator.
 * v5: auto-scales font and spacing to prevent overflow with many sections.
 */
function addOutlineSlide(pres, opts = {}) {
  const s = pres.addSlide();
  _applySlideBackground(s, pres, opts);

  s.addText(opts.title || "Outline", {
    x: MARGIN.left, y: 0.4, w: CONTENT_W, h: 0.6,
    fontSize: 26, fontFace: FONTS.heading, color: COLORS.ink, bold: true, margin: 0,
  });

  const sections = opts.sections || [];
  const current = opts.current != null ? opts.current : -1;
  const startY = 1.4;
  const availH = SLIDE_H - startY - 0.5; // available vertical space
  const maxLineH = 0.55;
  const lineH = Math.min(maxLineH, availH / Math.max(sections.length, 1));
  const fontSize = sections.length > 7 ? 14 : sections.length > 5 ? 16 : 18;

  sections.forEach((sec, i) => {
    const isActive = i === current;
    s.addText(`${i + 1}.  ${sec}`, {
      x: MARGIN.left + 0.3, y: startY + i * lineH, w: CONTENT_W - 0.6, h: lineH,
      fontSize, fontFace: FONTS.body,
      color: isActive ? COLORS.ink : COLORS.light,
      bold: isActive,
      margin: 0,
    });
    if (isActive) {
      const barH = Math.min(0.3, lineH * 0.6);
      s.addShape(pres.shapes.RECTANGLE, {
        x: MARGIN.left, y: startY + i * lineH + (lineH - barH) / 2, w: 0.15, h: barH,
        fill: { color: COLORS.accent },
      });
    }
  });

  _addSlideNumber(s);
  return s;
}

/**
 * Figure slide — THE workhorse. Title + large figure filling the slide.
 * Set opts.titleless = true when the image already contains its own title
 * (e.g., NLM clips where title couldn't be auto-removed).
 */
function addFigureSlide(pres, opts = {}) {
  const s = pres.addSlide();
  _applySlideBackground(s, pres, opts);
  const showSectionNav = _showSectionNav(opts);

  if (!opts.titleless) {
    if (showSectionNav) _addSectionNav(s, opts.sectionNav);

    const titleY = _contentTitleY(pres, opts, showSectionNav);
    s.addText(opts.title || "", {
      x: MARGIN.left, y: titleY, w: CONTENT_W, h: 0.52,
      fontSize: 28, fontFace: FONTS.heading, color: COLORS.ink, bold: true, margin: 0,
    });
  }

  if (opts.imagePath) {
    const figY = opts.titleless ? 0.15 : _contentBodyY(pres, opts, showSectionNav);
    const figH = SLIDE_H - figY - (opts.titleless ? 0.15 : 0.42);
    addImage(s, { path: opts.imagePath, x: MARGIN.left, y: figY, w: CONTENT_W, h: figH });
  }

  if (!opts.titleless) {
    _addCitation(s, opts.citation);
  }
  _addSlideNumber(s);
  return s;
}

/**
 * Dual figure slide — two figures side by side
 */
function addDualFigureSlide(pres, opts = {}) {
  const s = pres.addSlide();
  _applySlideBackground(s, pres, opts);
  const showSectionNav = _showSectionNav(opts);

  if (showSectionNav) _addSectionNav(s, opts.sectionNav);

  const titleY = _contentTitleY(pres, opts, showSectionNav);
  s.addText(opts.title || "", {
    x: MARGIN.left, y: titleY, w: CONTENT_W, h: 0.52,
    fontSize: 28, fontFace: FONTS.heading, color: COLORS.ink, bold: true, margin: 0,
  });

  const figY = _contentBodyY(pres, opts, showSectionNav);
  const figH = SLIDE_H - figY - 0.62;
  const gap = 0.3;
  const figW = (CONTENT_W - gap) / 2;

  if (opts.left && opts.left.imagePath) {
    addImage(s, { path: opts.left.imagePath, x: MARGIN.left, y: figY, w: figW, h: figH });
    if (opts.left.caption) {
      s.addText(opts.left.caption, {
        x: MARGIN.left, y: figY + figH + 0.05, w: figW, h: 0.25,
        fontSize: 9, fontFace: FONTS.body, color: COLORS.muted, align: "center", margin: 0,
      });
    }
  }

  if (opts.right && opts.right.imagePath) {
    addImage(s, { path: opts.right.imagePath, x: MARGIN.left + figW + gap, y: figY, w: figW, h: figH });
    if (opts.right.caption) {
      s.addText(opts.right.caption, {
        x: MARGIN.left + figW + gap, y: figY + figH + 0.05, w: figW, h: 0.25,
        fontSize: 9, fontFace: FONTS.body, color: COLORS.muted, align: "center", margin: 0,
      });
    }
  }

  _addCitation(s, opts.citation);
  _addSlideNumber(s);
  return s;
}

/**
 * Grid figure slide — N figures arranged in rows/columns
 * @param {object} opts - { title, images: [{ path, caption? }],
 *                          cols?: number (default: auto), citation? }
 */
function addGridFigureSlide(pres, opts = {}) {
  const s = pres.addSlide();
  _applySlideBackground(s, pres, opts);
  const showSectionNav = _showSectionNav(opts);

  if (showSectionNav) _addSectionNav(s, opts.sectionNav);

  const titleY = _contentTitleY(pres, opts, showSectionNav);
  s.addText(opts.title || "", {
    x: MARGIN.left, y: titleY, w: CONTENT_W, h: 0.52,
    fontSize: 28, fontFace: FONTS.heading, color: COLORS.ink, bold: true, margin: 0,
  });

  const images = opts.images || [];
  if (!images.length) { _addSlideNumber(s); return s; }

  const n = images.length;
  const cols = opts.cols || (n <= 2 ? n : n <= 4 ? 2 : 3);
  const rows = Math.ceil(n / cols);
  const gap = 0.2;
  const captionH = 0.22;
  const areaY = _contentBodyY(pres, opts, showSectionNav);
  const areaH = SLIDE_H - areaY - 0.42;
  const cellW = (CONTENT_W - (cols - 1) * gap) / cols;
  const cellH = (areaH - (rows - 1) * gap - rows * captionH) / rows;

  images.forEach((img, i) => {
    const col = i % cols;
    const row = Math.floor(i / cols);
    const cx = MARGIN.left + col * (cellW + gap);
    const cy = areaY + row * (cellH + captionH + gap);

    addImage(s, { path: img.path, x: cx, y: cy, w: cellW, h: cellH });

    if (img.caption) {
      s.addText(img.caption, {
        x: cx, y: cy + cellH + 0.02, w: cellW, h: captionH,
        fontSize: 8, fontFace: FONTS.body, color: COLORS.muted, align: "center", margin: 0,
      });
    }
  });

  _addCitation(s, opts.citation);
  _addSlideNumber(s);
  return s;
}

/**
 * Figure + text slide — figure on one side, text on the other
 */
function addFigureTextSlide(pres, opts = {}) {
  const s = pres.addSlide();
  _applySlideBackground(s, pres, opts);
  const showSectionNav = _showSectionNav(opts);

  if (showSectionNav) _addSectionNav(s, opts.sectionNav);

  const titleY = _contentTitleY(pres, opts, showSectionNav);
  s.addText(opts.title || "", {
    x: MARGIN.left, y: titleY, w: CONTENT_W, h: 0.52,
    fontSize: 28, fontFace: FONTS.heading, color: COLORS.ink, bold: true, margin: 0,
  });

  const figFrac = opts.split || 0.6;
  const gap = 0.3;
  const figW = CONTENT_W * figFrac - gap / 2;
  const textW = CONTENT_W * (1 - figFrac) - gap / 2;
  const bodyY = _contentBodyY(pres, opts, showSectionNav) + 0.04;
  const bodyH = SLIDE_H - bodyY - 0.42;

  const imgOnRight = (opts.imagePosition || "right") === "right";
  const figX = imgOnRight ? MARGIN.left + textW + gap : MARGIN.left;
  const textX = imgOnRight ? MARGIN.left : MARGIN.left + figW + gap;

  if (opts.imagePath) {
    addImage(s, { path: opts.imagePath, x: figX, y: bodyY, w: figW, h: bodyH });
  }

  // Optional bold rust side-message lead (Kang pattern: a short conclusion
  // heading above the supporting text). No "Take home" label.
  let textTop = bodyY + 0.2;
  if (opts.lead) {
    s.addText(opts.lead, {
      x: textX, y: textTop, w: textW, h: 0.7,
      fontSize: 15, fontFace: FONTS.heading, color: COLORS.accent, bold: true,
      margin: 0, valign: "top",
    });
    textTop += 0.72;
  }

  if (opts.bullets && opts.bullets.length) {
    s.addText(opts.bullets.map((b, i) => ({
      text: b,
      options: { bullet: true, breakLine: i < opts.bullets.length - 1, fontSize: 13, color: COLORS.text },
    })), { x: textX, y: textTop, w: textW, h: bodyY + bodyH - textTop, fontFace: FONTS.body, margin: 0, lineSpacingMultiple: 1.2 });
  } else if (opts.body) {
    s.addText(opts.body, {
      x: textX, y: textTop, w: textW, h: bodyY + bodyH - textTop,
      fontSize: 12.5, fontFace: FONTS.body, color: COLORS.text, margin: 0, lineSpacingMultiple: 1.2,
    });
  }

  _addCitation(s, opts.citation);
  _addSlideNumber(s);
  return s;
}

/**
 * Content slide — bullets only (use sparingly)
 */
function addContentSlide(pres, opts = {}) {
  const s = pres.addSlide();
  _applySlideBackground(s, pres, opts);
  const showSectionNav = _showSectionNav(opts);

  if (showSectionNav) _addSectionNav(s, opts.sectionNav);

  const titleY = _contentTitleY(pres, opts, showSectionNav);
  s.addText(opts.title || "", {
    x: MARGIN.left, y: titleY, w: CONTENT_W, h: 0.52,
    fontSize: 28, fontFace: FONTS.heading, color: COLORS.ink, bold: true, margin: 0,
  });

  if (opts.bullets && opts.bullets.length) {
    const bodyY = _contentBodyY(pres, opts, showSectionNav) + 0.18;
    s.addText(opts.bullets.map((b, i) => ({
      text: b,
      options: { bullet: true, breakLine: i < opts.bullets.length - 1, fontSize: 14, color: COLORS.text },
    })), { x: MARGIN.left + 0.2, y: bodyY, w: CONTENT_W - 0.4, h: SLIDE_H - bodyY - 0.55, fontFace: FONTS.body, margin: 0, valign: "top", lineSpacingMultiple: 1.25 });
  } else if (opts.body) {
    const bodyY = _contentBodyY(pres, opts, showSectionNav) + 0.18;
    s.addText(opts.body, {
      x: MARGIN.left + 0.2, y: bodyY, w: CONTENT_W - 0.4, h: SLIDE_H - bodyY - 0.55,
      fontSize: 14, fontFace: FONTS.body, color: COLORS.text, margin: 0, valign: "top",
    });
  }

  _addCitation(s, opts.citation);
  _addSlideNumber(s);
  return s;
}

/**
 * Large number callout slide — big stat with label and optional context.
 * Inspired by JP Minimal "Text + Data Emphasis" pattern.
 * @param {object} opts - { title, sectionNav?, callouts: [{ value, label }],
 *                          body?, citation? }
 *   callouts: 1–3 items, each with a large number and a small label
 */
function addCalloutSlide(pres, opts = {}) {
  const s = pres.addSlide();
  _applySlideBackground(s, pres, opts);
  const showSectionNav = _showSectionNav(opts);

  if (showSectionNav) _addSectionNav(s, opts.sectionNav);

  const titleY = _contentTitleY(pres, opts, showSectionNav);
  s.addText(opts.title || "", {
    x: MARGIN.left, y: titleY, w: CONTENT_W, h: 0.52,
    fontSize: 28, fontFace: FONTS.heading, color: COLORS.ink, bold: true, margin: 0,
  });

  const callouts = opts.callouts || [];
  const n = callouts.length || 1;
  const colW = CONTENT_W / n;
  const calloutY = _contentBodyY(pres, opts, showSectionNav) + 0.28;

  callouts.forEach((c, i) => {
    const cx = MARGIN.left + i * colW;
    // Large number
    s.addText(String(c.value), {
      x: cx, y: calloutY, w: colW, h: 1.8,
      fontSize: 60, fontFace: FONTS.heading, color: COLORS.ink, bold: true,
      align: "center", valign: "bottom", margin: 0,
    });
    // Label below
    s.addText(c.label || "", {
      x: cx, y: calloutY + 1.85, w: colW, h: 0.4,
      fontSize: 14, fontFace: FONTS.body, color: COLORS.muted,
      align: "center", margin: 0,
    });
  });

  if (opts.body) {
    s.addText(opts.body, {
      x: MARGIN.left, y: 3.8, w: CONTENT_W, h: 1.0,
      fontSize: 14, fontFace: FONTS.body, color: COLORS.text, margin: 0,
    });
  }

  _addCitation(s, opts.citation);
  _addSlideNumber(s);
  return s;
}

/**
 * Icon-card row — 2 to 4 borderless columns, each with an optional thin-line
 * icon, a bold rust heading, and small supporting body text. Matches the Kang
 * "Limitations of current aging clocks" pattern (reasons / criteria / pillars).
 * Borderless by design (no boxes) per the Architectural Calm rules.
 * @param {object} opts - { title, cards: [{ icon?, heading, body }], citation? }
 *   icon — optional image path (rust line icon PNG); omit for text-only columns
 */
function addIconCardsSlide(pres, opts = {}) {
  const s = pres.addSlide();
  _applySlideBackground(s, pres, opts);
  const showSectionNav = _showSectionNav(opts);

  if (showSectionNav) _addSectionNav(s, opts.sectionNav);

  const titleY = _contentTitleY(pres, opts, showSectionNav);
  s.addText(opts.title || "", {
    x: MARGIN.left, y: titleY, w: CONTENT_W, h: 0.52,
    fontSize: 28, fontFace: FONTS.heading, color: COLORS.ink, bold: true, margin: 0,
  });

  const cards = opts.cards || [];
  const n = cards.length || 1;
  const gap = 0.5;
  const colW = (CONTENT_W - (n - 1) * gap) / n;
  // Icon columns sit near the top; text-only columns drop lower so the block
  // reads centered instead of stranded against the title.
  const anyIcon = cards.some((c) => c.icon);
  const areaY = _contentBodyY(pres, opts, showSectionNav) + (anyIcon ? 0.5 : 1.05);
  const iconH = 0.75;

  cards.forEach((c, i) => {
    const cx = MARGIN.left + i * (colW + gap);
    let y = areaY;
    if (c.icon) {
      addImage(s, { path: c.icon, x: cx + (colW - iconH) / 2, y, w: iconH, h: iconH });
      y += iconH + 0.25;
    }
    s.addText(c.heading || "", {
      x: cx, y, w: colW, h: 0.6,
      fontSize: 15, fontFace: FONTS.heading, color: COLORS.accent, bold: true,
      align: "center", valign: "top", margin: 0,
    });
    y += 0.62;
    if (c.body) {
      s.addText(c.body, {
        x: cx, y, w: colW, h: SLIDE_H - y - 0.6,
        fontSize: 12.5, fontFace: FONTS.body, color: COLORS.text,
        align: "center", valign: "top", margin: 0, lineSpacingMultiple: 1.15,
      });
    }
  });

  _addCitation(s, opts.citation);
  _addSlideNumber(s);
  return s;
}

/**
 * Thank you / closing slide. Two modes:
 *   1. Simple (default): centered "Thank You", rust rule, contact line.
 *   2. Acknowledgments wall (Kang style): pass opts.columns for a dense
 *      multi-column credit layout (collaborators / mentors / funding) with an
 *      optional logo row and contact box.
 * @param {object} opts adds for mode 2:
 *   columns  — [{ heading, items: [string] }] laid left-to-right
 *   logos    — [{ path, w?, h? }] centered row near the bottom
 *   contact  — string shown in a small rust contact line/box
 */
function addThankYouSlide(pres, opts = {}) {
  if (opts.columns && opts.columns.length) {
    return _addAcknowledgmentsSlide(pres, opts);
  }
  return _addSimpleThankYouSlide(pres, opts);
}

/**
 * Dense acknowledgments closing (Kang style): title + rust rule, then N
 * columns of credits, optional contact line and logo row.
 */
function _addAcknowledgmentsSlide(pres, opts) {
  const s = pres.addSlide();
  _applySlideBackground(s, pres, opts);

  s.addText(opts.title || "Thank You", {
    x: MARGIN.left, y: 0.3, w: CONTENT_W, h: 0.7,
    fontSize: 32, fontFace: FONTS.heading, color: COLORS.ink, bold: true, align: "left", margin: 0,
  });
  if (!_usesImageBackground(pres, opts)) {
    s.addShape(pres.shapes.LINE, { x: MARGIN.left, y: 1.05, w: 2.2, h: 0, line: { color: COLORS.accent, width: 1.5 } });
  }

  const cols = opts.columns;
  const n = cols.length;
  const hasLogos = opts.logos && opts.logos.length;
  const gap = 0.4;
  const colW = (CONTENT_W - (n - 1) * gap) / n;
  const colY = 1.35;
  const colH = SLIDE_H - colY - (hasLogos ? 1.0 : 0.45);

  cols.forEach((col, i) => {
    const cx = MARGIN.left + i * (colW + gap);
    const runs = [];
    if (col.heading) runs.push({ text: col.heading, options: { bold: true, fontSize: 13, color: COLORS.accent, breakLine: true } });
    (col.items || []).forEach((it) => runs.push({ text: it, options: { fontSize: 11.5, color: COLORS.text, breakLine: true } }));
    s.addText(runs, { x: cx, y: colY, w: colW, h: colH, fontFace: FONTS.body, valign: "top", margin: 0, lineSpacingMultiple: 1.12 });
  });

  if (opts.contact) {
    s.addText(opts.contact, {
      x: MARGIN.left, y: SLIDE_H - (hasLogos ? 1.0 : 0.45), w: CONTENT_W, h: 0.3,
      fontSize: 12, fontFace: FONTS.body, color: COLORS.accent, align: "left", margin: 0,
    });
  }

  if (hasLogos) {
    const logoH = 0.5;
    const logoY = SLIDE_H - logoH - 0.18;
    let totalW = 0;
    for (const logo of opts.logos) totalW += (logo.w || 1.4);
    totalW += 0.4 * (opts.logos.length - 1);
    let logoX = (SLIDE_W - totalW) / 2;
    for (const logo of opts.logos) {
      const lw = logo.w || 1.4;
      addImage(s, { path: logo.path, x: logoX, y: logoY, w: lw, h: logo.h || logoH });
      logoX += lw + 0.4;
    }
  }

  return s;
}

function _addSimpleThankYouSlide(pres, opts = {}) {
  const s = pres.addSlide();
  _applySlideBackground(s, pres, opts);

  if (!_usesImageBackground(pres, opts)) {
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 0, w: SLIDE_W, h: 0.03,
      fill: { color: COLORS.accent },
    });
  }

  s.addText("Thank You", {
    x: MARGIN.left, y: 1.4, w: CONTENT_W, h: 0.8,
    fontSize: 36, fontFace: FONTS.heading, color: COLORS.ink, bold: true, align: "center", margin: 0,
  });

  s.addShape(pres.shapes.LINE, {
    x: 3.5, y: 2.4, w: 3, h: 0,
    line: { color: COLORS.accent, width: 1.5 },
  });

  const info = [];
  if (opts.name) info.push({ text: opts.name, options: { bold: true, fontSize: 16, color: COLORS.ink, breakLine: true } });
  if (opts.email || opts.website) {
    const contact = [opts.website, opts.email].filter(Boolean).join("  |  ");
    info.push({ text: contact, options: { fontSize: 12, color: COLORS.accent, breakLine: true } });
  }
  if (opts.urls && opts.urls.length) {
    info.push({ text: "", options: { fontSize: 4, breakLine: true } });
    info.push({ text: opts.urls.join("  |  "), options: { fontSize: 12, color: COLORS.muted } });
  }
  if (info.length) {
    s.addText(info, { x: MARGIN.left, y: 2.7, w: CONTENT_W, h: 1.4, fontFace: FONTS.body, align: "center", margin: 0 });
  }

  if (opts.collaborators) {
    s.addText(opts.collaborators, {
      x: MARGIN.left, y: 4.3, w: CONTENT_W, h: 0.6,
      fontSize: 11, fontFace: FONTS.body, color: COLORS.light, align: "center", margin: 0,
    });
  }

  return s;
}

// ── Exports ──
module.exports = {
  createPresentation,
  useIpdBackground,
  IPD_BACKGROUND_PATH,
  COLORS,
  FONTS,
  MARGIN,
  CONTENT_W,
  SLIDE_W,
  SLIDE_H,
  addImage,
  renderMermaid,
  addTitleSlide,
  addSectionSlide,
  addOutlineSlide,
  addFigureSlide,
  addDualFigureSlide,
  addGridFigureSlide,
  addFigureTextSlide,
  addCalloutSlide,
  addContentSlide,
  addIconCardsSlide,
  addThankYouSlide,
};
