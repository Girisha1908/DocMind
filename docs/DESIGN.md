# Design System: DocMind

## 1. Visual Theme & Atmosphere

A calm, evidence-first research tool. It should feel like a well-run internal wiki crossed with a lab notebook: quiet neutral surfaces, one confident accent, and numbers that are easy to trust. Every answer shows its sources, and every metric shows its sample size.

- **Density:** 6 ("Daily App Balanced"). The Ask screen breathes; the Evaluation screen is tighter and table-led.
- **Variance:** 5 ("Offset Asymmetric"). Content is left-aligned on a 12-column grid with a fixed left rail. Nothing is centered except empty states.
- **Motion:** 4 ("Fluid CSS"). Restrained transitions only. This is a tool people read, not a showcase.

There is no marketing hero. The first screen is the product: a question box with an answer area below it.

## 2. Color Palette & Roles

- **Paper** (#FAFAF9): app background.
- **Surface** (#FFFFFF): answer panel, source passages, table body.
- **Ink** (#1C1917): primary text and headings. Never pure black.
- **Graphite** (#57534E): secondary text, labels, metadata.
- **Pebble** (#A8A29E): placeholder text, disabled states, chart gridlines.
- **Hairline** (#E7E5E4): 1px dividers, table rules, input borders.
- **Evidence Teal** (#0F766E): the only accent. Used for the primary button, focus rings, citation markers [1], the production-strategy badge, and the winning bar in charts.
- **Teal Wash** (#F0FDFA): background of the selected strategy row and of highlighted evidence text.
- **Status Pass** (#15803D) and **Status Fail** (#B91C1C): used only for the CI gate badge and the regression column. They are never decorative.

Stick to warm stone neutrals throughout and don't mix in cool grays. Don't use purple, neon or gradients.

## 3. Typography Rules

- **Display and headings:** Geist, weight 600, tracking -0.02em. Sizes: page title 1.75rem, section title 1.125rem. Hierarchy comes from weight and color, not size.
- **Body:** Geist 400, 1rem, line height 1.65, max width 68ch. Answers are body text, not cards of bullet points.
- **Mono:** Geist Mono for all metrics (Hit@3, MRR, ms per query), strategy IDs (`headers+rerank`), question IDs (a01), file paths, and the tabular figures in tables.
- **Banned:** Inter, system-ui as a design choice, and any serif.

## 4. Component Stylings

- **Question input:** full width of the content column, 56px tall, 12px radius, 1px Hairline border. The label "Ask the handbook" sits above it. The focus ring is a 2px Evidence Teal ring offset by 2px. The submit button sits inside the right edge of the input.
- **Primary button:** Evidence Teal fill, white Geist 500 text, 10px radius, no shadow, translateY(1px) when pressed. Use one per screen.
- **Secondary button:** ghost style with Ink text and a Hairline border.
- **Answer panel:** Surface background, 16px radius, 1px Hairline border, 28px padding.
  - Citations appear inline as small Evidence Teal superscript chips [1] [2]. Hovering a chip highlights the matching source below.
  - Below the answer, a single Graphite meta line: strategy used, the 3 passages retrieved, and latency.
- **Source passage:** a list rather than cards, with border-top dividers.
  - Each row shows: a citation number chip, page title (Geist 500), handbook URL in Graphite mono, and a chevron to expand.
  - When expanded, the passage text shows in a Paper-tinted block, with the cited sentence highlighted in Teal Wash.
- **Strategy selector (left rail):** a vertical list of 10 strategies grouped under "Chunking" and "Retrieval" captions.
  - The production strategy carries a small "default" badge in Evidence Teal outline.
  - Each row shows its Hit@3 in mono on the right, so choosing a strategy is an informed choice.
- **Documents switcher:** a two-option segmented control at the top of the rail: "GitLab Handbook" and "Your PDF".
- **Metric tile:** no card. Use a large mono number (2rem), a Graphite label under it, and a tiny delta ("+24.4 pp vs original"). Tiles sit in a row separated by vertical hairlines.
- **Tables:** zebra-free, with Hairline row rules and right-aligned mono numbers.
  - The best value in each column is bold Ink.
  - The production row has a Teal Wash background and a 3px Evidence Teal left border.
- **CI gate badge:** a pill showing "CI gate: passing" in Status Pass, or "failing" in Status Fail, with the threshold in mono: "Hit@3 ≥ 0.80".
- **Loaders:** skeleton lines matching the answer panel's paragraph widths. Don't use spinners.
- **Empty state (no question yet):** three example questions as plain text links under the input, e.g. "How many weeks of paid parental leave does GitLab provide?"
- **Error state:** an inline Status Fail message under the input, e.g. "No Mistral API key: showing retrieved passages only."

## 5. Layout Principles

- **Desktop grid:** a fixed left rail 280px wide, and a content column with a max width of 760px for the Ask screen and 1120px for Evaluation. The whole layout is left-aligned inside a 1400px container.
- **Top bar:** product name "DocMind" in Geist 600 on the left, tabs "Ask · Evaluation" on the right of it, and a GitHub link at the far right. The top bar has no logo glyph or emoji.
- **Evaluation screen:**
  - First, a row of 4 metric tiles: production Hit@3, MRR@5, questions evaluated, and the CI gate.
  - Then a horizontal "ladder" bar chart, 5 bars from Original to Reranking, with the value at the end of each bar in mono. Only the final bar is Evidence Teal; the rest are Pebble.
  - Then the full comparison table.
  - Then a "Hardest questions" list (question text, type tag, how many strategies missed it).
  - The Hit@3-by-question-type small multiples sit in a 2-column asymmetric split beside the hardest-questions list. Don't use a 3-equal-card row.
- **Below 768px:** the rail becomes a top sheet (the strategy picker opens as a bottom drawer), everything goes to one column, the table scrolls inside its own container, and the page never scrolls horizontally. Touch targets are at least 44px.
- **Spacing:** an 8px base unit, with section gaps of 48px on desktop and 32px on mobile.

## 6. Motion & Interaction

- Use a 150–200ms ease-out for hover and expand, and animate transform and opacity only.
- When an answer streams in, source rows reveal with a 40ms stagger.
- Ladder bars grow from 0 width once, on first view, with a spring (stiffness 100, damping 20). There are no looping animations.
- Hovering a citation chip highlights its source row. Hovering a table row highlights the matching ladder bar.

## 7. Anti-Patterns (Banned)

- No emojis anywhere, including the product name and the empty state.
- No Inter and no serif fonts.
- No pure black (#000000).
- No purple, no neon, no glow shadows, and no gradient text.
- No chat-bubble UI with avatars. This is a question-and-cited-answer tool, not a messenger.
- No 3-equal-card feature rows, and no centered hero.
- No made-up round metrics. Use the real numbers from `results/latest.json`, or clearly labelled sample values.
- No GitLab logo or brand colours. The content is from the GitLab Handbook, but this is not a GitLab product. Show the attribution line "Content: GitLab Handbook, CC BY-SA 4.0" in the footer.
- No copywriting clichés ("elevate", "seamless", "unleash", "next-gen", "AI-powered magic").
- No "scroll to explore" prompts or bouncing chevrons.
