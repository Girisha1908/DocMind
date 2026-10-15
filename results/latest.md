## Retrieval accuracy (43 answerable questions)

| Step | Strategy | Hit@3 | MRR@5 |
|---|---|---|---|
| Original DocMind | `s0_original` | **62.8%** | 0.622 |
| 1. Simple chunking | `fixed_500+vector` | **74.4%** | 0.612 |
| 2. Semantic chunking | `semantic+vector` | **67.4%** | 0.502 |
| 2b. Header-aware chunking | `headers+vector` | **88.4%** | 0.777 |
| 3. Hybrid search (headers chunks) | `headers+hybrid` | **74.4%** | 0.670 |
| 4. Reranking (headers chunks) | `headers+rerank` | **83.7%** | 0.761 |

### All strategies

| Strategy | Hit@1 | Hit@3 | Hit@5 | MRR@5 | Hit@3 direct | Hit@3 exact_term | Hit@3 paraphrase | ms/query |
|---|---|---|---|---|---|---|---|---|
| `headers+vector` | 69.8% | **88.4%** | 90.7% | 0.777 | 100.0% | 100.0% | 66.7% | 326 |
| `fixed_500+rerank` | 55.8% | **83.7%** | 86.0% | 0.680 | 90.0% | 100.0% | 66.7% | 10556 |
| `semantic+hybrid` | 44.2% | **83.7%** | 86.0% | 0.622 | 100.0% | 100.0% | 53.3% | 208 |
| `headers+rerank` | 65.1% | **83.7%** | 95.3% | 0.761 | 85.0% | 100.0% | 73.3% | 8899 |
| `semantic+rerank` | 55.8% | **81.4%** | 90.7% | 0.691 | 85.0% | 87.5% | 73.3% | 10477 |
| `fixed_500+hybrid` | 53.5% | **76.7%** | 86.0% | 0.663 | 95.0% | 100.0% | 40.0% | 250 |
| `fixed_500+vector` | 51.2% | **74.4%** | 74.4% | 0.612 | 90.0% | 87.5% | 46.7% | 269 |
| `headers+hybrid` | 58.1% | **74.4%** | 86.0% | 0.670 | 90.0% | 100.0% | 40.0% | 267 |
| `semantic+vector` | 32.6% | **67.4%** | 76.7% | 0.502 | 75.0% | 75.0% | 53.3% | 202 |
| `s0_original` | 60.5% | **62.8%** | 65.1% | 0.622 | 80.0% | 75.0% | 33.3% | 140 |

### Hardest questions (missed in top 3 by most strategies)

| id | question | strategies missing it |
|---|---|---|
| c09 | I forgot to claim something I bought four months ago. Can I still get the money back? | 9/10 |
| a08 | My mom is ill and I need to stay home to look after her. How many paid days a year can I take for that? | 8/10 |
| a11 | I'm temporarily filling in as manager while ours is away. What extra pay do I get on top of my normal salary? | 8/10 |
| c08 | I knocked part of the price off a work purchase with store points. Does the company pay me back the sticker price? | 6/10 |
| a09 | If someone just stops showing up without telling anyone, how long before it can be treated as them quitting? | 5/10 |
| b08 | I'm about to become a dad in Korea - how many days off am I legally owed after the baby arrives, and how soon do I have to use them? | 5/10 |
| b11 | In the Netherlands, if I can't work because I'm unwell for a long stretch, what share of my wages keeps being paid and for how long? | 5/10 |
| b09 | Our baby is due in mid-2026 and we live in Singapore. How much extra state-funded time off can my partner and I split between the two of us? | 5/10 |
| a12 | One of my reports will be out for about three weeks after having a kid. Should I bring in a contractor to cover their work? | 4/10 |
| a04 | If I leave GitLab, how long do I have to exercise my vested stock options? | 4/10 |

### CI gate

- ✅ All thresholds met
