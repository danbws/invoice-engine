# DraftLine — Product Brief

> **Send it once. It can't be changed. Get paid for it.**

Audit-proof invoicing, retainage tracking, and lien waivers for the specialty
subcontractors who bill general contractors.

---

## Positioning

DraftLine is invoicing built for the way construction subs actually get paid:
progress billing against a schedule of values, **retainage held back** on every
draw, **lien waivers** exchanged for each check, and AR that stretches out to
net-60/90. The invoice you send is **immutable** — once issued it gets a
locked, gap-free number and can never be silently edited, so when a GC or an
auditor asks "is this the document you sent us on the 14th?", the answer is
provably yes.

QuickBooks and FreshBooks treat a construction draw like any other invoice.
DraftLine treats retainage, progress billing, and the sub-to-GC paper trail as
first-class objects.

**Tagline:** *Send it once. It can't be changed. Get paid for it.*

---

## Ideal Customer Profile (ICP)

The owner-operator of a **1–15 person specialty subcontractor** doing
**$300k–$3M/year** in revenue — electrical, mechanical, drywall, concrete,
framing, glazing, HVAC, painting, flooring. They:

- Bill **general contractors** (not homeowners), often via AIA-style progress
  billing against a schedule of values.
- Have **5–10% retainage** held back on every draw until the job closes out.
- Trade **conditional and unconditional lien waivers** for each payment.
- Wait **net-60 to net-90** to get paid and chase money by phone and email.
- Run the office themselves (or with one bookkeeper/spouse) and are done with
  QuickBooks fighting them on how construction actually bills.

They feel the pain most at three moments: submitting a draw, reconciling what a
GC actually paid vs. what they held, and closing out a job to collect retainage.

---

## Pricing

| Tier | Price | For | What's included |
|------|-------|-----|-----------------|
| **Solo** | **$19/mo** | One owner-operator | 1 user, up to ~15 active invoices/mo, immutable issued invoices, per-GC numbering series, payment tracking, PDF invoices, CSV export |
| **Crew** | **$39/mo** | A small sub with an office helper | 3 users, unlimited invoices, retainage & progress billing, lien-waiver PDFs, org-branded PDFs, email delivery, AR aging by GC |
| **Shop** | **$79/mo** | An established sub running multiple jobs | 10 users, everything in Crew, multi-crew/job tagging, QuickBooks export, priority support, per-GC statements & retainage-release tracking |

Annual billing gives two months free. Overage on Solo nudges to Crew rather than
hard-blocking — the goal is to grow with the shop, not fence it in.

---

## Three differentiators vs. QuickBooks / FreshBooks / Wave

1. **Retainage & progress billing are first-class objects — not a workaround.**
   Every invoice knows its schedule-of-values line, the % complete this draw,
   and the retainage withheld. DraftLine tracks *retainage held* separately from
   *balance due*, and surfaces the retainage you're owed across every open job —
   so closeout collection stops falling through the cracks. In QuickBooks you
   fake this with a negative line item and a spreadsheet.

2. **Audit-grade immutability + lien-waiver generation.**
   An issued invoice gets a concurrency-safe, gap-free number and becomes
   read-only forever; corrections happen as new documents, cancellations as
   logged events with a mandatory reason. Each payment can generate the matching
   **conditional/unconditional lien waiver** PDF automatically. The whole chain
   — invoice, payment, waiver — is tamper-evident and exportable for a GC or an
   auditor. Wave and FreshBooks let you quietly edit a sent invoice.

3. **A real sub-to-GC workflow with per-GC numbering series.**
   Each general contractor gets its own numbering series and its own statement,
   so your paperwork lines up with *their* AP system and job numbers. Retainage,
   waivers, and AR aging all roll up per GC — the way a sub's receivables
   actually work — instead of a flat customer list.

---

## Brand Identity

**Name:** DraftLine — the "draw line" a sub bills to, and the plumb/chalk line
of the trades.

**Tone:** plainspoken, dependable, protective. Talks like a good foreman, not a
SaaS growth deck. Short sentences. No jargon it doesn't have to use. Every
message quietly reassures the user that their paper trail has their back.

**Palette**

| Token | Hex | Use |
|-------|-----|-----|
| Ink Navy | `#12203A` | Primary text, headers, dark surfaces |
| Steel Blue | `#2E5A88` | Primary actions, links, accents |
| Safety Amber | `#F5A524` | Highlight, the "draw line" underline, CTAs |
| Concrete | `#F4F2ED` | App background / paper |
| Slate | `#6B7683` | Secondary text, borders, muted UI |
| Paid Green | `#1F9D6B` | Paid status, positive balances |
| Overdue Red | `#D64545` | Overdue / cancelled / error states |

**Type**

- **Space Grotesk** — headings and the wordmark (industrial, a little
  mechanical).
- **Inter** — body and UI copy (clean, legible at small sizes).
- **IBM Plex Mono** — numbers, money, and invoice IDs (fixed-width so
  `A-000142` and `$12,204.50` always align in tables).

**Logo concept**

A bold **"D"** whose counter is a **plumb-line drop** — a plumb bob hanging on a
string, nodding to trades and to "true/level." Alternate mark: the **DraftLine**
wordmark with an **amber "draw line"** drawn underneath it, like a chalk snap —
the line you bill to.

---

## Roadmap to Sellable

### P0 — SaaS shell (before anyone can pay us)
- Multi-tenant **Organization** model (data scoped per org).
- **Auth** (email + password / magic link) and org membership + roles.
- **Next.js** frontend (App Router + Tailwind + shadcn/ui) on the existing API.
- **Stripe** billing wired to the Solo/Crew/Shop tiers.

### P1 — Get-paid core (this commit and its neighbors)
- **Payment tracking** — record payments, derive `amount_paid`, `balance_due`,
  and `payment_status` (unpaid / partially_paid / paid). ✅ *shipped this commit*
- **Email delivery** of issued-invoice PDFs to the GC.
- **Org-based PDF branding** (logo, colors, remit-to).
- **Alembic** migrations (replace the demo `create_all`).
- Security hardening pass — CSV formula-injection and PDF markup escaping. ✅

### P2 — Construction differentiators (the reason to switch)
- **Retainage & progress-billing objects** — schedule of values, % complete per
  draw, retainage held vs. balance due, per-GC retainage-release tracking.
- **Lien-waiver PDF generation** (conditional/unconditional, tied to payments).
- **QuickBooks export** so the bookkeeper stops complaining.
