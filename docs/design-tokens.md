# Design tokens, pulled from scalesage.ai

Requirement R9 is "looks like it belongs on scalesage.ai, not a default template."
These were read off the live site on 2026-09-21 with computed styles, not guessed.
`web/` implements these. Where a token fails WCAG 2.2 AA it is noted and adjusted.

## Colour

| Token | Value | Use |
|---|---|---|
| `--bg` | `#0A1628` | page background, deep navy |
| `--surface` | `rgba(255,255,255,.03)` | card fill over the background |
| `--surface-2` | `rgba(244,246,249,.04)` | raised card / inset panel |
| `--accent` | `#3DD9D0` | primary action, active status, check marks, the emphasised word |
| `--on-accent` | `#04161B` | text on a teal fill |
| `--text` | `#F4F6F9` | primary text |
| `--text-2` | `#A8B2C0` | secondary text |
| `--text-3` | `#808D9E` | muted. **Adjusted, see below** |

### One deliberate deviation

The site's muted grey is `#6E7C8F`. On `#0A1628` that measures **4.26:1**, just under
the 4.5:1 AA floor for body text. `--text-3` is lifted to `#808D9E`, which measures
**5.37:1** on the same background and is visually indistinguishable at a glance.

The accessibility floor is not traded for brand fidelity. Noted in `README.md`.

## Type

- **Inter** throughout. `ui-monospace` for small meta labels, timestamps and ids.
- Weights in use: 400 body, 500, 600 for headings and buttons, 700 sparingly.
- Observed sizes cluster at 13 / 14.5 / 15.5 / 18px, with large display sizes in the hero.
- Their signature move: one word of a heading set in *italic* `--accent`.

## Shape

- Cards `border-radius: 16px`. Small controls 6-8px. Buttons are full pills.
- Borders are very low contrast; grouping is carried by fill and spacing, not rules.
  That matches Gestalt common-region, and it is how their cards read as grouped.

## Voice

Short declarative sentences, full stops, no exclamation. "Diagnose. Build. Prove."
"Three tiers. Every one accountable to a number." "Find your leak."
Copy in `web/` follows this. No SaaS filler, no "Get started in seconds!".

## The plan we sell

Their real entry tier, so the page reads as a real ScaleSage product:

- **Starter, £597/mo.** "Best for: sole traders getting more leads without hiring."
- Currency is **GBP**, not USD. The Stripe price object is created in GBP.
- Their £297 one-off setup fee is **not** implemented. The brief says "a monthly plan";
  a second one-time line item is scope the brief did not ask for. Noted in the report.
- Pro (£1,497) and Max (£4,997) are not offered. One plan means the decision is yes or
  no rather than a comparison, which is Hick's Law and also what the brief asks for.

## A pattern worth reusing

Their hero has a "LIVE ACTIVITY" card: a monospace label, a pulsing teal dot, and rows of
`timestamp · icon · event`. That is almost exactly the shape the Orbit Mini dashboard
needs for subscription status and billing history, and reusing it is the strongest
available answer to "looks like it belongs on scalesage.ai".
