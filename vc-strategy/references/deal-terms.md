# Deal Terms — instruments, clauses, negotiation

Every clause is **economics** (what the investor gets) or **control** (what they can veto or dictate) — classify before negotiating (Feld, *Venture Deals*); founders who don't, trade control to protect a number. "Believe the terms" (YC): a contract allocates risk, so the terms an investor insists on reveal the risk they actually perceive, regardless of the meeting's warmth — structure-heavy economics says "I fear losing my money"; control-heavy boards say the same about the founder.

## Instrument decision matrix

**Priced round when**: valuation leverage exists and is defensible; cap-table certainty is wanted now; investors require governance. **SAFE when**: pre-PMF with no valuation leverage; speed matters; no governance needed (Stripe Atlas). Cost/clock: SAFE $5–15K and 2–3 weeks vs priced $25–75K and 6–12 weeks. Market reality: ~90% of pre-seed rounds are SAFEs; convertible notes hit a record-low 7% of pre-seed rounds (Carta Q1 2026); seed rounds >$5M are ~70% priced.

## SAFE hygiene

- **Post-money SAFEs only**, YC standard form, unmodified. Pre-money SAFE math re-computes against every other SAFE and the round — founders end up more diluted than modeled (Hustle Fund).
- Conversion math is computable at signature: $X at $Y post-money cap = X/Y of the company. Cap + discount: investor takes whichever yields more shares (worked: $500K at $5M post cap + 20% discount into a $10M A ⇒ cap wins ⇒ 10%).
- **Model every SAFE converting at its cap before signing the next one**; one cap per tranche — a ladder of rising caps ($200K@$3M → $300K@$4M → $500K@$6M) silently sells ~20% pre-A.
- **No MFN** — it lets earlier holders upgrade to any better term granted later (Westaway).
- With leverage, an **uncapped-but-discounted** SAFE is the founder ideal; market default is cap + 20% discount (range 15–25%). A higher cap is founder-favourable; the eventual priced round lands ~1.8× the cap (modal, Equidam).
- Side letters: pro-rata alone is fine; **pro-rata plus a laundry list of rights is a yellow flag**.
- Tail risks: SAFEs may never convert (no priced round, or a small acquisition can leave holders and founders badly served) — model the acquisition-before-conversion case.

## Term-sheet red-flag scan

Baseline for "clean": YC's published standard Series A term sheet — what's *absent* from it is the signal. Market prevalence: Cooley Q2 2025 (238 financings): **98% 1× preference, 95% non-participating, >90% investor vetoes present**.

**Economics — red:**
- Liquidation preference >1× · participating preferred (double dip) · cumulative/mandatory dividends · warrant coverage · **full-ratchet anti-dilution** (insist on weighted average, with carve-outs for option/employee/vendor issuances) · redemption rights · milestone/tranched funding at early stage · uncapped investor legal fees (cap them in advance).
- **Option pool is a price term in HR clothing**: created pre-money it dilutes founders only; sized above the actual hiring plan it's a back-door price cut worth 1.25–5 points of founder ownership (Toptal). Counter with a named hiring plan to the next round (AngelList data: grants of 0.25–3%, avg 1.375%, first ~34 employees ⇒ 12–15% pool defensible).

**Control — red:**
- Board **2-2-1** instead of **2-1** at Series A — the single most consequential term; this is the mechanism by which founders get fired.
- Investor-director approval required for budget/exec hires/pivots — operational control smuggled in beside the board clause; protective provisions reaching ordinary operations (a real sheet demanded approval for purchases >$10K).
- Sale-of-company veto with no sunset — negotiate a lapse once the investor clears 3–5×.
- Series-by-series vetoes instead of all-preferred-single-class — invites a late investor to block an exit earlier ones want.
- Drag-along triggerable by a bare preferred majority — raise the threshold, require board ratification, add a minimum-price covenant.
- **Super pro-rata** — "we believe in you, but not enough right now" (Toptal), and it crowds out the next lead's ownership target. Plain pro-rata should expire if unexercised.
- Board seats without sunset — lapse below ~10% ownership or on failure to maintain pro-rata; offer observer rights as the compromise.
- Founder voting rights conditioned on continued employment — counsel walks the scenarios before signing.

**Process:**
- Standard template (YC/NVCA/ACA) or bespoke paper? Ask where it came from.
- **All material terms in the sheet before signing** — signature triggers exclusivity/no-shop, and every term deferred "to the docs" is negotiated with leverage already gone (Feel the Boot). Exclusivity period defined and bounded.
- Deadline shorter than ~a week → push back.
- Stage-appropriate lead: a late-stage fund leading a pre-seed/seed is a signaling trap — their non-follow-on reads loudly; an angel's doesn't.
- Series A paper is the **precedent** for every later round — unwinding bad terms later is near-impossible (YC).

## Negotiation posture

- Draft the founder-ideal sheet first (valuation, pool, board, preference, vesting), then map investor paper clause-by-clause to plain-English impact ("affects exit payout" / "affects whether I can be fired") and triage red/yellow/green (Qubit, 2025) — fast and unemotional.
- Trade economics for control rarely and knowingly; the resale value of clean governance compounds.
- Stated vs effective pre-money: pre-money pool + converting SAFEs come off the top — evaluate any offer by the **resulting cap table**, never the headline valuation; effective pre-money can fall below an outstanding SAFE cap, flipping those SAFEs to discount conversion.
- Anchor on market data ("98% of deals are 1×, non-participating — why is this one different?").
- "No one ever built an enduring company just by winning their Series A negotiation" (YC) — clean and fast beats maximal.

**Known source error (do not propagate):** one corpus source (DAA Capital) inverts anti-dilution labels — full ratchet is the *most investor-favourable* form; weighted average is the founder-preferred one (Feld, Toptal, Feel the Boot all agree).
