# Dia (diabrowser.com) measured values, 2026-10-12

Taken with headless Chrome computed styles and pixel sampling. Starting point for a
"paper editorial" prototype; re-measure before reuse, sites change.

## Pill navigation (desktop)
- `position:fixed; top:28px`, height 52px, radius 16px, background #F8F8F8, 1px rgba(0,0,0,.08)
- shadow `0 2px 8px rgba(0,0,0,.06), 0 0 2px rgba(0,0,0,.04)`, `backdrop-filter: blur(12px)`
- padding `0 24px 0 6px`, logo 40×40, links 16px, gap ~34px, **no CTA inside the pill**
- links on 2026-10-12: What's New / Apps / Security (three only)

## Pill navigation (mobile ≤800px)
- full width, top 14px, radius 30px; "+" button rotates 45° and the pill grows to
  `calc(100vh - 20px)`; menu links 56–72px light weight, grey (rgba(0,0,0,.3)), current one black;
  two full-width buttons at the bottom: black primary, grey secondary

## Buttons
- primary: black pill, height 45px, padding 0 32px, 16px/500, hover background #424242, no lift
- secondary: `rgba(235,235,235,.7)`, radius 20px
- a white pill on dark pages (Early Birds)

## Motion
- `transition: .2s cubic-bezier(.4,0,.2,1)` for colour; `transform .22s / box-shadow .42s cubic-bezier(.22,1,.36,1)` on cards
- reveal on scroll: `opacity 1s cubic-bezier(0,0,.2,1)`, translateY ~10px, IntersectionObserver
- marquee keyframes L/R/U/D, pause on hover; chroma sweep on the hero (background-position + blur)
- sticky feature showcase: `position:sticky; top:20vh`, 3px moving indicator bar
- product cards: `rounded-t-12`, `mask-image: linear-gradient(#000, #000 50%, transparent)`

## Page types (first screen)
- painted: home (yellow mottled field, giant serif wordmark), apps (dark-green landscape band
  fading to paper, headline on paper), changelog (dark painting, white serif title),
  early birds (planet horizon: blue sky → pink rim → charcoal, white sans title)
- mist: for work, help (soft lavender/peach haze)
- paper: security, release notes, windows

## Early Birds horizon geometry (1440×900 capture)
- arc apex ≈ 16% of viewport height at centre, edges ≈ 37%: sag ≈ 180px over 720px half-width → radius ≈ 1440px (≈100vw)
- sampled colours: sky #5284D7 → #85A8E0 → #AAC5CF, rim haze #B7A8A3, dusk #3D314F, body #212021, cards #3B3A3B, button white
- CSS that reproduced it: `radial-gradient(circle at 50% calc(210px + 100vw), #212021 0 calc(100vw - 1px), #3D314F calc(100vw + 26px), #7E6474 +50px, #A88F93 +72px, #B7A8A3 +92px, #DCC4BE +116px, #EDE3E0 +146px, #D6DFE6 +180px, #A9C3DF +230px, #7FA6E2 +330px, #5284D7 +520px)`; mobile radius 140vw

## Apps page band (sampled)
- band average #808880 (left #68746B, right #6E766C), fade zone #ECECE8, card thumbnails
  #CFD5C0 / #C9C8C5 / #707D6A / #E1E6EC

## Fonts
- ABC Oracle / Exposure VAR / ABC Favorit Mono (commercial). Open mapping used:
  Fraunces + Noto Serif SC (display), DM Sans + Noto Sans SC (body), DM Mono (numbers)
