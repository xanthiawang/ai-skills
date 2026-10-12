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

- Decide the nav from a **frequency table over every reference site** (list each site's items in
  order, then count categories: product/models, pricing, docs, solutions/enterprise, news,
  about, security, login). On 2026-10-12 across ten sites: product on all, pricing and docs on
  every API platform, news in the nav on five (Dia's "What's New", PPIO, 无问芯穹, Emerald,
  Soluna), enterprise in the nav only at 无问芯穹 (footer elsewhere), login top-right on all but
  Dia. Read Dia's three items as categories, not labels: What's New = news/updates, Apps =
  what the product does, Security = trust.
- Nav holds **content pages only**, 3 to 5 items. Merge pages whose content overlaps
  (models + pricing became one page with a `#pricing` alias that scrolls to the section).
- The account entry is **secondary**: lighter colour, hairline divider, right end of the pill,
  label "登录" that becomes "控制台" once signed in. Mobile: the grey button at the bottom of
  the menu.
- "登录" lands on a **sign-in page** (phone or email + code, one entrance for personal and
  enterprise, a link to the registration wizard), never straight into the console. The console
  is a signed-in state: route `#console` to the sign-in page when the demo state is signed out,
  treat finishing the registration wizard as signed in, and give the console a sign-out.
  PPIO's "控制台" link resolves to its login page when signed out; 硅基流动 has one unified
  login page; OpenRouter puts Sign Up top-right. Dumping visitors into a mock console was
  the complaint ("只会显示这个控制台，但是我们有地方 sign in 和注册呀").
- Be ready to say, section by section, where a page's logic came from: the company's own
  materials (BP, sales deck), a measured reference (which page), or an industry pattern
  (name the sites). Anything that is an assumption (e.g. an "individual vs enterprise"
  comparison table) is labelled 示例 and listed for the client to confirm.
- A language switch is a secondary utility next to it, only when an overseas segment exists.
  It must **translate the current page in place**, never navigate to a separate English page
  (that was rejected as "切换之后就会跳到别的页面"). Pattern: a dictionary of exact text-node
  strings plus a phrase list for names inside composite strings; a TreeWalker over text nodes
  and `placeholder` attributes that stores the original on the node (`node.__zh`) so it can
  switch back; a `MutationObserver` (childList only) that re-applies after JS renders; guards
  so label updates never write identical text (observer loops). Long-form bodies that stay
  untranslated get a one-line notice via `html[lang=en] .article:before`.
- Before adding any nav item, write the user flow it serves. If you cannot, it does not exist.

### 3. Walk every page of the reference, then measure

- Capture **every** page, not just home (`scripts/capture_site.py`): nav/footer links, CTAs
  with background colours, first-screen PNG, long JPEG. Build a contact sheet and look at it.
- Classify pages: *painted* (artwork in the first screen), *mist* (soft colour haze), *paper*
  (nothing). Dia: home/apps/changelog/early-birds painted, for-work/help mist, security/release
  notes/windows paper. Assign the same mix to the prototype; a prototype that learned only the
  home page makes every page look the same.
- Measure the **hero composition** too, not just components: section height, each element's
  top offset and width as a fraction of the viewport, overlap order, translucency and blur
  of the product window, glow and curve geometry (see the Dia reference file). Our hero at
  the right colours but the wrong proportions was rejected: "元素的大小和 Dia 的也不一样".
- Measure, never eyeball: pill nav (top offset, height, radius, blur, shadow, padding, logo
  size, link size, no CTA inside), buttons (height, radius, hover colour, no lift), transition
  durations and easings, reveal timing, marquee, sticky showcase. Computed styles come from
  the CDP client (`scripts/cdp_client.py`), hover states via `CSS.forcePseudoState`.
- Colour fields: sample pixels at several points **and measure the geometry** (apex height,
  edge sag, band widths). "晨昏" in Dia's Early Birds page is not parallel bands; it is a planet
  horizon: a large-radius radial gradient, charcoal inside, dusk → mauve → pink → pale → sky
  blue outward. Matching the colours but not the shape was rejected; so was a version with the
  right shape but the wrong proportions (glow band 330px wide pushed the blue sky off-screen,
  "黑色占比太多"). Measure all three: shape, band widths, and how much sky sits under the nav.
- Measured values for Dia (2026-10-12) are in `references/dia-measured-2026-10-12.md`; reuse
  them as a starting point for the "paper editorial" look.

### 4. Colour schemes

- Scheme A stays as decided unless Zixin says otherwise. New schemes come from sampled
  reference pixels, not from memory.
- Transitions, never hard blocks (`feedback-color-transitions`): OKLab ramps or radial fields.
  White stays the dominant base; a dark scheme touches the hero and accents, not the whole site.
- Compute WCAG contrast for text colours (`scripts/color_tools.py`) and put the numbers in the audit.
- Put a scheme switcher in the footer ("配色（评审用）") so A/B/C can be compared in one build.
  At sign-off, fix the chosen scheme in code, delete the switcher, and hand over a palette +
  type spec page: swatches in groups with usage, a computed WCAG table (compute greys as
  alpha-blended colours, not guessed), three type families with a size ladder and the
  component text sizes, the hero composition numbers, and the CSS tokens. Client-facing, so
  no reference names.
- **Keep rejected directions as a selectable scheme instead of deleting them.** The painted
  hero was called ugly in one round and asked back as "方案三" two rounds later.
- Do not fake artwork with filters. Procedural "oil paint" (SVG turbulence + displacement) was
  rejected on the home page; if a page needs a painting, use a real image (image generation
  needs Zixin's explicit go-ahead because of cost) or an illustrator.

### 5. Home page narrative

- Pull the h1/h2/h3 order of every reference home page (`scripts/headings.py`) before writing
  one. The shared narrative on 2026-10-12: one-sentence solution → product / core capability
  (with a showcase) → why us or technology → scenarios or industries → proof (customers, news)
  → CTA. Dia: tagline → "reads between the tabs" → six work scenarios → privacy → CTA.
- **Pick the hook from what buyers compare, not from the company's favourite concept.**
  Survey the competitors' heroes and "why us" lists first (2026-10-12: OpenRouter "Better
  prices, better uptime"; 硅基流动 高速 / 高性价比 / 高稳定 / 高安全; PPIO 高性价比 / 超弹性 / 低延迟;
  nobody sells green power). The hero then leads with the dimension where the company wins
  (price and capacity at peak) and keeps the signature concept (绿电) as the reason it is
  credible plus a bonus (ESG receipt). A green-first hero was rejected: "消费者并不是特别关心绿电".
- Scenario cards state the **problem and the answer as two labelled lines** ("问题 …" /
  "沐仞 …"); a single paragraph that mixes both was read as unclear. Section labels like
  "六个场景 · 示例" are placeholders and never appear on the page.
- Partner strips use **real logos** from the company's own decks (extract `ppt/media` from the
  pptx, check which slide they sit on, crop, greyscale, 2× height), not text; universities stay
  as serif wordmarks. Note what each logo actually says (NVIDIA's was "Inception Program").
- **The first line says what the product is**, in the category's plain words (Dia: "More than a
  browser"; 无问芯穹: "通用人工智能基础设施服务商"; 英灵殿: "给生物分子一个世界模型"). The brand
  line or slogan goes second, smaller. A slogan-first hero ("谷时发电，峰时平价") was rejected as
  "没有写清楚我们这产品是什么".
- Under the hero, a strip of **who stands behind it**: one scrolling row of names, founding
  team origin first (清华大学, 北京大学), then partner / ecosystem names from the company's own
  site or materials; repeat the list three times so the loop has no gap. No static label row.
  **Internal caveats never go on the page** ("来自商业计划书，关系待公司确认" was rejected with
  "你这算什么呀"); they go in the audit file / claims ledger for the client to confirm.
  A live-data ticker there was replaced by this strip on request.
- **No guides, tutorials or events on the home page.** None of ten references does it; the
  closest is OpenRouter's three-step "How it works". The home section that listed guides was
  rejected ("Dia 也没有在这放指南，他们放的是功能"). Guides live under Docs and in the footer;
  events live inside a News / What's new page.
- Scenarios come from the company's own buyer list and vertical use cases; "why us" from its
  stated selling points; news items from facts in its materials, with dates marked as pending
  rather than invented.
- Write copy **pain first, fix second**, but in the reference's register, not in slogans.
  Dia's feature copy (measured 2026-10-12): a plain title ("Dia reads between the tabs"), then
  two sentences: a concrete moment ("Before the day kicks in…", "Ask once."), what the product
  does with named specifics in parentheses ("(calendar, inbox, key links)"), and the outcome
  with "so you…" ("so you know exactly what you're walking into"). Scenario cards are full
  sentences about the moment, ending in a short payoff ("All you have to do is show up.").
  Clever-but-opaque titles ("别人涨价排队的时候，你的价格不动", "老板只认结果，不认 token") were
  rejected as "写得都看不懂"; the plain versions ("高峰时段，价格还是那个价格", "按结果付费，而不是按 token")
  passed. Solution-only copy was earlier rejected as "不够吸引人，痛点也没有写清楚".
- Chinese labels for "What's New": 新闻中心 / 新闻动态 (无问芯穹), 新闻资讯 / 公司动态 (PPIO).
  "动态" alone is not used as a top-level nav label; use 新闻动态.
- Footer is four columns on every reference: 产品 · 资源 · 公司 (about, news, careers, contact,
  legal) · 关注 (social, newsletter). A prototype without the 公司 column is missing an
  About page too.
- **Contact details get their own footer column at body size**, labelled by purpose, the way
  PPIO (媒体垂询 / 资源合作 / 投资者关系 / 业务咨询 + QR) and 无问芯穹 (业务 / 媒体 / 人才 emails,
  phone, addresses) do; the copyright line is not the place for the email. "写得太小了".
- **Before building any new module, open the references' version of that module first**
  (Zixin: "你每做一个新的模块之前，你要先参考一下我们的案例"). Home-page blocks on B2B API sites
  are 产品 / 为什么选我们 / 行业与场景 (short tiles by industry) / 客户案例与伙伴 / 新闻; Dia's
  six narrative scenario cards are a consumer-product device. Problem/answer story cards were
  replaced by industry tiles plus a project-cases row on request.
- Keep a **claims ledger** for the whole site and be ready to hand it over on request: A from
  company materials, B from public sources with date, C example numbers (labelled 示例 on the
  page), D placeholders (toast on click), E your own assumptions (labelled, listed for the
  client to confirm). Fix any claim that is none of these.

### 6. Content pages

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

### 7. Build conventions

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
- A dark-mode token block from an early round can silently swap the signed-off palette on a
  dark-mode OS. Before sign-off, verify under emulated `prefers-color-scheme: dark`
  (`Emulation.setEmulatedMedia`) and force the light theme if the design is light-only.
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
- `scripts/headings.py <cdp_client.py> <url> <port>` — h1/h2/h3 of a page in document order with
  y offsets, for reading a reference home page's narrative.
- `scripts/walkthrough.py <prototype.html> <outdir> route[:js] …` — wraps the fragment, runs
  desktop and mobile, reports JS errors and overflow, saves screenshots and `walkthrough.json`.
- `scripts/color_tools.py '#hex' '#hex' …` — CIEDE2000 distances, WCAG contrast against white
  and black, OKLab ramp between two colours.

## Related skills

`impeccable` for general frontend craft, `anti-ui-slop` for the finish gate, `nature-figure`
is not for this. `feedback-color-transitions` and `fathompeak-*` memories hold the project
history behind these rules.
