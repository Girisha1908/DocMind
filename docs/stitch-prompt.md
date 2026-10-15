# Google Stitch prompt

Paste the block below into Google Stitch (https://stitch.withgoogle.com). For follow-up screens, attach `docs/DESIGN.md` or paste its sections 2–4 and 7, so every screen uses the same tokens.

---

```text
Design a desktop web app called "DocMind": a question-answering tool over a company HR handbook (GitLab Handbook content: leave, benefits, expenses, travel, onboarding). Every answer cites its sources. It is also a portfolio piece that shows how well 10 retrieval strategies were measured against each other. Generate 3 screens with one shared design system.

DESIGN SYSTEM
- Mood: calm, evidence-first research tool; an internal wiki crossed with a lab notebook. Balanced density, left-aligned asymmetric layout, restrained motion.
- Colors: background Paper #FAFAF9, surfaces #FFFFFF, primary text Ink #1C1917, secondary Graphite #57534E, muted Pebble #A8A29E, dividers Hairline #E7E5E4. ONE accent, Evidence Teal #0F766E, used for the primary button, focus rings, citation chips, the "default" badge and the winning chart bar. Teal Wash #F0FDFA for selected rows and highlighted evidence. Green #15803D and red #B91C1C only for the CI pass/fail badge. Warm stone neutrals throughout.
- Type: Geist for everything; headings weight 600 with tight tracking. Geist Mono for all numbers, metric names, strategy IDs like "headers+rerank", question IDs and URLs. Body text 16px, line height 1.65, max 68 characters per line.
- Shape: 10–16px radii, 1px hairline borders, no drop shadows except a very faint one on the answer panel.
- Layout: top bar with the word "DocMind" (no logo, no emoji), tabs "Ask" and "Evaluation", and a GitHub link on the right. Fixed 280px left rail, content column max 760px (Ask) or 1120px (Evaluation), left-aligned.

SCREEN 1 — ASK (handbook mode)
- Left rail: a segmented control "GitLab Handbook | Your PDF". Below it, "Retrieval strategy" as a vertical list of 10 rows in two groups.
  - Baseline: s0_original.
  - Fixed 500-token, Semantic and Header-aware, each with "vector", "hybrid" and "rerank".
  - Each row shows its Hit@3 on the right in mono.
  - The selected row (headers+rerank) has a teal "default" outline badge and a Teal Wash background.
- Main column: label "Ask the handbook" above a 56px input showing "How many weeks of paid parental leave does GitLab provide?", with a teal submit button inside the input's right edge.
- Answer panel below the input: one short paragraph: "GitLab provides 16 weeks of paid parental leave, which must be used before the child's first birthday or the first anniversary of the adoption [1]. When you return, the standard guideline is two to four weeks at reduced capacity [1]." The citation markers are small teal superscript chips.
- Under the answer, a single grey meta line in mono: "headers+rerank · 3 passages · 0.9 s".
- "Sources" list: 3 rows separated by hairlines, not cards. Each row has a numbered chip, page title (e.g. "Leave Types"), handbook URL in grey mono, and an expand chevron.
  - Row 1 is expanded. It shows the passage in a tinted block, with the cited sentence highlighted in Teal Wash.
- Footer line: "Content: GitLab Handbook, CC BY-SA 4.0".

SCREEN 2 — EVALUATION
- Title "Evaluation", with the subtitle "43 answerable questions · 7 unanswerable · evidence-span matching".
- A row of 4 metric tiles. Use a large mono number with a small label and no card backgrounds, separated by vertical hairlines:
  - "Hit@3 (production)"
  - "MRR@5"
  - "Questions: 50"
  - "CI gate", shown as a green pill "passing · floor Hit@3 ≥ 0.80"
- A horizontal ladder bar chart titled "What each step added". It has 5 bars, top to bottom:
  - Original DocMind
  - 1. Simple chunking
  - 2. Semantic chunking
  - 3. Hybrid search
  - 4. Reranking
  - The value sits at the end of each bar in mono. The bars are Pebble grey except the last, which is Evidence Teal.
  - Use clearly labelled sample values, increasing but not round.
- A full comparison table with columns: Strategy (mono), Hit@1, Hit@3, Hit@5, MRR@5, Hit@3 direct, Hit@3 paraphrase, Hit@3 exact-term, ms/query.
  - Numbers are right-aligned mono, and the best value per column is bold.
  - The production row has a Teal Wash background and a 3px teal left border.
- Bottom area in a 2-column asymmetric split:
  - Left (wider): "Hardest questions", a list of question text, a small type tag (paraphrase / exact-term / direct), and "missed by 7/10 strategies".
  - Right: "Hit@3 by question type", three small horizontal bar groups.

SCREEN 3 — YOUR PDF
- Same shell, with "Your PDF" selected in the segmented control. The strategy list is replaced by the note "Uploaded PDFs use fixed chunking + vector search".
- Main column: a dashed-border drop zone ("Drop a PDF here or browse", "Indexed locally, never stored").
- Below it, an indexed-file row: file name, page count, chunk count in mono, and a "Replace" ghost button.
- The same question input and answer panel as screen 1, with an answer citing "[1] page 12".
- A skeleton-loader version of the answer panel (grey lines matching paragraph widths) to show the loading state.

MOBILE (under 768px)
- Single column. The rail becomes a "Strategy" button that opens a bottom sheet.
- Tables scroll horizontally inside their own container, never the page.
- 44px minimum touch targets.

DO NOT
- No emojis, no chat bubbles or avatars, no purple, no neon, no gradients, no glow shadows, no pure black.
- No Inter, no serif fonts.
- No 3-equal-card rows, no centered hero, no marketing copy ("elevate", "seamless", "AI-powered").
- No GitLab logo or orange brand colours.
```
