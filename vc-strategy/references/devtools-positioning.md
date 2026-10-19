# Devtools & AI-Infra Positioning — the technical founder's value proposition

Positioning for developer tools and AI infrastructure, where the default investor priors run *against* the founder. Where the corpus is silent, this file says so — fabricating an investor threshold is worse than naming the gap.

## Name the layer, then answer the rent-duration question

State the layer (foundation / infra / application / inference) on the first substantive claim — a pitch vague about layer inherits the scrutiny of all three. Then pre-answer the **rent-duration objection** for that layer: Moore's-law businesses had 18–24 months to collect rents on an advance; at the foundation-model layer the window is estimated at ~30 days (TechCrunch Disrupt panel, 2025). Acceptable durability answers, in order: **workflow entrenchment → usage-generated proprietary data → distribution/ecosystem position → expertise asymmetry**. A benchmark is never the answer — a benchmark *is* the 30-day asset.

Investor priors to defeat, two-sourced across three years: application/inference layers rank above infra/foundation (Siroker ≈2023: "the infrastructure level is incredibly hard to win unless you have a ton of capital… you're competing with a lot of **technology in search of a problem**"; Disrupt 2025 agrees on economics legibility). Lead with the pulled-for workload, never the architecture.

## The platform-incumbent answer ("why can't OpenAI / Microsoft / the IDE vendor build this in six months?")

The 2026 form of the default objection — "founders closing rounds right now have a crisp answer; if you cannot answer cleanly, your round stalls regardless of how strong the demo runs" (Qubit, 2026). Build it:

1. State the question yourself, in its most concrete form, before the investor does.
2. Run **Siroker's four-part test** aloud: proprietary data no model provider has · switching costs that already exist · owning the user relationship/UX · "doing more than just what OpenAI could do if they wanted to."
3. Pick the axis the incumbent cannot cross **without contradicting its own economics or strategy** — and name what the company is deliberately *not* building.
4. Choose the moat honestly from Pillar VC's taxonomy (ranked): first-mover self-reinforcing moats (network effects, scale, scope) → territorial dominance → **captive channels** → **mastering complexity** (technical or operational) → patents (weak — "scale economics enforce themselves; patents cost money to enforce") → regulatory approval. For infra without network effects, the credible defaults are mastering complexity and captive channels.
5. Bring the incumbent-at-your-size evidence (below).
6. Do not answer with: the incumbent is slow, specialists always win, or a feature comparison.

The Series A "algorithm" for infra (a seed investor's stated model): team history · TAM · product advantage · **how AI is involved — will the company generate data, is there a moat** · distribution · margins. For an "AI enabler, not application layer," investors overweight technical background and founder pedigree, and rule-of-thumb benchmarks go "out the window" (Disrupt, 2025).

## Open-source → commercial narrative

The corpus's best answer is Michael Seibel's reframe (SaaStr, 2023), answering the HashiCorp/Elastic question directly:

> "It's far more useful to think about how these incumbents got their **first million and ten million in revenue**… What did HashiCorp do on the path to ten million, and should you copy it? … I don't think they made a lot of revenue early. **So maybe you don't have to.**"

The pitch judo: "if an investor asks *why aren't you doing what HashiCorp does* — your comeback is: on their path to their first million, this is what they did, and we're copying that strategy. **You taught the investor something. You sound smart.**"

The funding-trigger template (David Aronchick, Expanso/Bacalhau — $7.5M seed, Nov 2023, General Catalyst + Hetz): OSS project traction → **enterprise-shaped demand appears** ("once you start getting into that enterprise motion, instead of a bottoms-up motion, you end up having a conversation about how to fund it") → the company exists to fund engineering + sales + solutions engineering → round sized to the sales cycle (~3 years runway, pre-revenue acceptable). Plus his process rules: a pre-process of advice conversations ("careful not to start before you start"), then a hard 60–90-day window ("after a certain amount of time, you're like a dead fish"); on valuation, comps not formulas ("*this many downloads so your valuation should be Z* — it really is about what the market will bear"); take 10–20% of investor feedback, max.

OSS narrative checklist: the motion changed (observable enterprise pull) · what's free vs paid, and why the paid boundary sits where the buyer's cost actually sits · the incumbent's early path, not its current license posture · **never lead with license strategy** (no source in the corpus argues license changes as an investment thesis) · community metrics framed as pull evidence, not valuation inputs.

Cautionary teardown: Cloudera's 2008 Series A deck ($5M, later a $1.9B IPO) — "the epitome of a tech deck… for normal people it's painful. There isn't a narrative. It's a series of nerd slides" (Jarvis). The partnership-repeatability test: every sentence must be repeatable by the non-technical partner who has 30 seconds on Monday.

## Usage-based revenue as a fundraising argument

The corpus's one substantive treatment (Graham & Walker, 2026): "**clarity matters more than hype**" — transparent baselines, normalized usage volatility, clean recurring-vs-variable split. "Run-rates inflated by a single strong month don't build conviction. Precision, consistency, and honest reporting do." Segment calibration siblings: enterprise = a non-founder seller has closed; consumer = "revenue can come later, behavior cannot." Still missing from the corpus: consumption-margin economics, credit/commit structures, usage-specific NDR benchmarks.

## Developer-adoption metrics — trusted vs discounted

**Trusted:** true recurring revenue · cohort expansion · usage depth/habit inside accounts (active projects, workloads, API calls) · workflow entrenchment · flattening retention curves · NRR ≥100% (≥105% strong) · CAC payback <12 months · revenue per employee (now asked at seed — Qubit 2026) · burn multiple · deals closed by a non-founder · unsolicited integrations and unprompted feature requests ("customers pulling at you instead of you pulling at them" — CRV).

**Discounted or penalized:** TCV presented as ARR · run-rate spikes · volatile usage without a stable baseline · headcount as ambition · demo polish without retention · big-tech hires as the lead signal · year-one projections anchored to TAM.

**GitHub stars and downloads — unresolved, be honest:** no first-party investor in the 625-source corpus states a star or download bar. They appear only as narrative proof of pull (YC's solo-founder cohort headlines "20,000 stars + 3M downloads") and are dismissed as valuation inputs (Aronchick). Treat them as pull evidence; any implied threshold would be fabricated.

## Why-now for infra: technical discontinuity

Template (CRV's Stripe example, in `narrative-playbook.md`): platform shift → mismatch created → artifact incumbents can't retrofit. "AI is assumed" (2025–26): >40% of pitches lead with AI, so the mechanism — what is automated, what augmented, what stays human, and what breaks without it — is the differentiation, never the label.

## Investor mapping for devtools

- Thesis tailoring (2026, Qubit): Sequoia-shaped = applied AI with enterprise distribution — a named customer list beats demo quality; YC-shaped = narrow vertical, fast time to revenue, FMF; a16z-shaped = defensibility and domain literacy over growth rate. One deck for all three is a triple pass.
- Named devtools-active funds — thin list, flagged: the corpus's only dedicated list (Rho, Apr 2026) names boldstart (genuinely day-one devtools/infra), Tola, MAGIC Fund, Vela, Expa, Trajectory, 500 EE, plus Point Nine/Seedcamp (EU) and .406/Glasswing (Boston) — but omits most canonical devtools funds. Treat it as a seed for portfolio archaeology, not a target list (VCSheet's devtools + infra sheets add 43 + 40 funds). Homebrew's repeatedly funded pattern: **bottom-up adoption + top-down sales**. Sequoia seed explicitly hunts infra/open-source/devtools with "contrarian insight" (Balkansky). 2025 marker: a16z's public Cluely memo underwrote a demonstrated distribution engine as the primary asset — an audience is now financeable proof. Feed the list-building itself to vc-outreach.
- Capital-stack anchors for AI-infra rounds carry different agendas (Qubit, 2026): traditional VC (ownership, team+market) · crossover (public-market-shaped proof) · asset manager (governance, clean cap table) · strategic/hyperscaler (workload capture — **accepting a hyperscaler anchor often carries a soft or explicit commitment to run on their platform: model the lock-in before signing, not after**).

## Corpus gaps (state these instead of guessing)

No open-core pricing-boundary guidance (free vs paid design) · no license-strategy-as-thesis source · no OSS conversion benchmarks (stars→users→paid) from any investor · no enterprise-infra sales-cycle benchmarks (cycle length, ACV bands, pilot→production) · no consumption gross-margin or inference-cost curve data · no measured developer-GTM funnel (docs→signup, community→design partner). When one of these is needed, say the corpus is silent and reason from the general frameworks (Casado's maturity ladder, usage-depth principles) explicitly as inference.
