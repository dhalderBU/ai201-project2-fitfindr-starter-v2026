# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> The agent searches listings, compares the selected item's price with its
> category average, suggests an outfit, and creates a fit card. Add `--trace`
> to see the tool calls and branches.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ──── Milestone 1   ───── -->
### Three fields in the listings file
- Title
- Description 
- Size


<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## Planned Stretch Features — Category-Average Comparison

The following declaration was committed before implementation in
[`5385159`](https://github.com/dhalderBU/ai201-project2-fitfindr-starter-v2026/commit/5385159).
The tool and branch are now implemented; actual evidence appears under
**Sample Run — Stretch features** below.

1. **Fourth tool: `compare_price(new_item: dict) -> dict`.** Use the existing
   `load_listings()` loader to compare the selected listing's price with the
   arithmetic average of all other listings in the same category, excluding
   its own listing ID. Calculate the average with `sum(prices) / len(prices)`
   and round it to two decimal places. No additional packages are needed.
   Return `listing_id` (str), `category` (str), `item_price` (float),
   `comparison_count` (int), `average_price` (float or None), `difference`
   (float or None, item price minus average), and `status` (str: `above_average`,
   `below_average`, `at_average`, or `insufficient_data`). With no other
   category listings, return a zero count, null average and difference, and
   `insufficient_data`.
2. **Additional branch: above-average price warning.** In
   `agent.py::run_agent`, after choosing an unowned item, call `compare_price`
   and store its result in `session["price_comparison"]`. If its status is
   `above_average`, store a warning in `session["price_warning"]`, trace that
   branch, and display the warning with the recommendation. Otherwise leave
   the warning unset. Both paths continue to the outfit and fit-card tools.
   Empty searches and all-owned results still stop before price comparison.

The comparison covers the supplied dataset, not current market prices. It
uses every other listing in the category, irrespective of the search budget,
size, brand, or condition; it is a broad reference rather than a valuation.
The Tool Inventory, Planning Loop, and Sample Run sections explain the changes
and include terminal evidence of the fourth-tool call and the above-average
branch. Style memory is not part of this declaration.

## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->
This application searches for clothing and garments(from listing) based on inputs like a) description b)size and c) price. 
The system generates search results from listing (if available) and then generates Outfit based on wardrobe and a fit card statement for social media postingwhich is caption on the find
It also compares the selected item's price with the average of other listings
in the same category and displays a warning when it is above that average.
This comparison uses the supplied dataset and makes no additional model call.

---

<!-- ──── Milestone 2   ───── -->

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:**  Search the listings data for items matching a description, and optionally a
    size and a price ceiling.
- **Inputs:** `description` (str), `size` (str | None), and `max_price` (float | None). where description is set of keywords describing what the user wants, Size is a string to filter like "W30 L30" or "L" . max_price is maximum price inclussive. Or one could enter None to skip priec fiktering.
- **Returns:** A list of matching listing dictionaries (sorted with best match first based on score) containing fields such as title, description,category,style tags, size, condition, price, colors, brand, and platform. If nothing is found based on the descriptive keywords put as input then returns an empty list (doesnt return none or exception)
- **When it has nothing:** Returns an empty list (`[]`).

### `suggest_outfit`

- **What it does:**  Given a thrifted item and the user's wardrobe, suggest one or two outfits. This function calls the model using generate function 
- **Inputs:** `new_item` (a dictionary containing the listing's title, description, category, style tags, size, condition, price, colors, brand, and platform) and `wardrobe` (a dictionary with an `items` key whose value is a list of wardrobe-item dictionaries).
- **Returns:** A non-empty string containing outfit suggestions based on the wardrobe(as generated by the LLM) or general styling advice when there the wardrobe passed is empty.
- **When it has nothing:** If the wardrobe is empty, returns general styling advice instead of raising an error.

### `create_fit_card`

- **What it does:** Creates a two-to-four-sentence social-media caption using the LLM to describe the new find, its title, outfit, price, platform, and overall vibe.
- **Inputs:** `outfit` (a string returned by `suggest_outfit`) and `new_item` (a listing dictionary returned by `search_listings`).
- **Returns:** A two-to-four-sentence fit-card caption as a string.
- **When it has nothing:** If `outfit` is empty or contains only whitespace, returns a message asking for an outfit suggestion.

### `compare_price` — fourth tool

- **What it does:** Compare the selected listing with every other listing in
  `data/listings.json` with the same category, excluding its own ID. Search
  keywords, size, and budget do not restrict the comparison group.
- **Input:** `new_item` (dict): a complete listing returned by `search_listings`,
  including `id` (str), `category` (str), and `price` (float).
- **Returns:** A dictionary containing `listing_id` (str), `category` (str),
  `item_price` (float), `comparison_count` (int), `average_price` (float or
  None), `difference` (float or None), and `status` (str). The average is
  `sum(prices) / len(prices)`, rounded to cents. The difference is the item
  price minus that rounded average, also rounded to cents. A positive, negative,
  or zero difference gives `above_average`, `below_average`, or `at_average`.
- **When it has nothing:** Return `comparison_count=0`, `average_price=None`,
  `difference=None`, and `status="insufficient_data"`.

This tool uses `load_listings()` and Python built-ins; it adds no package or
model request. Category averages mix garment types, brands, and conditions,
so they are a broad dataset reference, not evidence of market value.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rules:** In `agent.py::run_agent`, if `search_listings` returns an empty
list, put a useful message in the session and stop. Otherwise, skip listings
that appear in the wardrobe by category, meaningful name, and shared color;
stop with a message if all results are owned. Store the first unowned result
as the selected item, then call `compare_price`.

The new stretch branch checks whether
`session["price_comparison"]["status"] == "above_average"`. If true, store
`session["price_warning"]`, record `above-average price branch` in the trace,
and display the warning in the CLI. Otherwise leave the warning as `None` and
record `price comparison: no warning`. Both paths continue to `suggest_outfit`
and `create_fit_card` with the same selected item. No comparison or model tool
is called after an empty-search or all-owned stop. If there are no comparison
peers, show that the average is unavailable and continue without a warning.

**Where it lives:** The `branch rule` is implemented in the `run_agent` function in agent.py.

**How the query is parsed:** Regular expressions extract the description, optional size, and maximum price from the user’s query. The function removes the size and price phrases from the description, converts the price to a float, and returns all three values in a dictionary.

**What moves through the session:** The parsed query and search results are
stored in `session["parsed"]` and `session["search_results"]`. The first unowned
result becomes `session["selected_item"]`. `compare_price` reads that item and
its return value is stored in `session["price_comparison"]`; the branch reads
that stored result and may set `session["price_warning"]`. The selected item
and wardrobe then go to `suggest_outfit`, whose output is stored as
`session["outfit_suggestion"]`. The outfit and a copy of the item are saved in
`session["fit_card_inputs"]` and passed to `create_fit_card`; its output is
stored as `session["fit_card"]` and appended to `session["fit_card_outputs"]`.
The price warning is displayed separately from the caption.

**Gap in specs that needs addressing :** Clothing items use different sizing systems—for example, tops may use sizes such as `S`, `M`, or `L`, while pants may use measurements such as `W30 L30`. The specification should define how each type of size is matched and how universal-size items are handled.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

### Sample Run — Stretch features

The examples below were captured from actual CLI runs on October 11, 2026,
using the existing `venv-codepath` Python environment. Commands are shown as
`python` with that environment active. The two full runs used the existing
local settings: model `gemini-3.5-flash-lite`, temperature `0`, and caching
available; each reported two actual model calls. The comparison tool itself
made no model call. These are demonstration runs, not five-trial acceptance
results.

**Fourth tool, called directly**

```bash
python -c 'import json; from tools import compare_price; from utils.data_loader import load_listings; print(json.dumps(compare_price(load_listings()[3]), indent=2))'
```

```text
{
  "listing_id": "lst_004",
  "category": "outerwear",
  "item_price": 45.0,
  "comparison_count": 7,
  "average_price": 43.86,
  "difference": 1.14,
  "status": "above_average"
}
```

**Above-average branch — full agent run**

```bash
python app.py ask --trace '90s track jacket in size M'
```

```text
Trace generated at: 2026-10-11T01:27:24-07:00
[1] 2026-10-11T01:27:24-07:00 +0.000s (step 0.000s) parse_query
      in:  90s track jacket in size M
      out: dict with keys: description, size, max_price
[2] 2026-10-11T01:27:24-07:00 +0.001s (step 0.000s) search_listings
      in:  dict with keys: description, size, max_price
      out: 4 items: 90s Track Jacket — Navy/White Stripe, 90s Leather Bomber — Black, 90s Silk Slip Dress — Floral, Midi Length … +1 more
[3] 2026-10-11T01:27:24-07:00 +0.001s (step 0.000s) select_item
      out: 90s Track Jacket — Navy/White Stripe ($45.0, poshmark)
[4] 2026-10-11T01:27:24-07:00 +0.001s (step 0.000s) compare_price
      in:  90s Track Jacket — Navy/White Stripe ($45.0, poshmark)
      out: dict with keys: listing_id, category, item_price, comparison_count, average_price, difference
      →    status=above_average; peers=7; average=43.86; difference=1.14
[5] 2026-10-11T01:27:24-07:00 +0.001s (step 0.000s) above-average price branch
      out: This item is $1.14 above the $43.86 average of 7 other outerwear listings in this dataset. This is a broad cat…
      →    show a price warning and continue to suggest_outfit
[6] 2026-10-11T01:27:27-07:00 +2.683s (step 2.682s) suggest_outfit
      in:  90s Track Jacket — Navy/White Stripe ($45.0, poshmark)
      out: Here are two outfit suggestions using the 90s track jacket and your existing wardrobe:  **Outfit 1: 90s Street…
[7] 2026-10-11T01:27:27-07:00 +3.450s (step 0.766s) create_fit_card
      in:  dict with keys: outfit, new_item
      out: Score this amazing 90s Track Jacket — Navy/White Stripe on poshmark for just $45.0! It’s the ultimate piece fo…

  Category average: $43.86 across 7 other outerwear listings in this dataset.
  Price warning: This item is $1.14 above the $43.86 average of 7 other outerwear listings in this dataset. This is a broad category comparison, not a market valuation.

  Found:    90s Track Jacket — Navy/White Stripe — $45.0 on poshmark

  Outfit:   Here are two outfit suggestions using the 90s track jacket and your existing wardrobe:

**Outfit 1: 90s Streetwear Casual**
*   **Top:** White ribbed tank top
*   **Outerwear:** 90s Track Jacket — Navy/White Stripe (worn fully or partially unzipped)
*   **Bottoms:** Baggy straight-leg jeans, dark wash
*   **Shoes:** Chunky white sneakers
*   **Accessories:** Black crossbody bag
*   **Styling:** Lean into the athletic 90s aesthetic by pairing the fitted white tank with the baggy high-waisted jeans, letting the lightweight track jacket serve as an easy outer layer. Finish with chunky sneakers and the crossbody bag.

**Outfit 2: High-Low Contrast**
*   **Top:** White ribbed tank top
*   **Outerwear:** 90s Track Jacket — Navy/White Stripe
*   **Bottoms:** Wide-leg khaki trousers
*   **Shoes:** Chunky white sneakers
*   **Accessories:** Brown leather belt, black crossbody bag
*   **Styling:** Mix athletic streetwear with minimal earth tones by layering the track jacket over the white tank tucked into the wide-leg khaki trousers. Use the brown leather belt to anchor the look and keep the sneakers white to tie in the stripe details of the jacket.

  Fit card: Score this amazing 90s Track Jacket — Navy/White Stripe on poshmark for just $45.0! It’s the ultimate piece for nailing that effortless streetwear aesthetic. Layer it over a ribbed tank and baggy denim for a vintage vibe, or dress it up with khaki trousers. Such a versatile find! #90sStreetwear #VintageStyle

2 model calls this session, 1008 prompt + 359 output tokens
```

The selected jacket costs $45.00. The seven other outerwear listings total
$307.00, so their average is $43.86 after rounding. The comparison result is
stored in `session["price_comparison"]`; the loop takes the above-average
branch, stores the $1.14 warning, and continues through both model tools.
The warning is displayed separately from the fit card.

**Below-average path — trace and comparison excerpt**

```bash
python app.py ask --trace 'butterfly print tee'
```

```text
Trace generated at: 2026-10-11T01:28:24-07:00
[1] 2026-10-11T01:28:24-07:00 +0.001s (step 0.001s) parse_query
      in:  butterfly print tee
      out: dict with keys: description, size, max_price
[2] 2026-10-11T01:28:24-07:00 +0.001s (step 0.000s) search_listings
      in:  dict with keys: description, size, max_price
      out: 6 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Low-Rise Cargo Pants — Khaki … +3 more
[3] 2026-10-11T01:28:24-07:00 +0.001s (step 0.000s) select_item
      out: Y2K Baby Tee — Butterfly Print ($18.0, depop)
[4] 2026-10-11T01:28:24-07:00 +0.001s (step 0.000s) compare_price
      in:  Y2K Baby Tee — Butterfly Print ($18.0, depop)
      out: dict with keys: listing_id, category, item_price, comparison_count, average_price, difference
      →    status=below_average; peers=14; average=22.0; difference=-4.0
[5] 2026-10-11T01:28:24-07:00 +0.001s (step 0.000s) price comparison: no warning
      out: below_average
      →    continue to suggest_outfit
[6] 2026-10-11T01:28:27-07:00 +2.304s (step 2.303s) suggest_outfit
      in:  Y2K Baby Tee — Butterfly Print ($18.0, depop)
      out: **Outfit 1: Y2K Streetwear** * **New Item:** Y2K Baby Tee — Butterfly Print * **Wardrobe Pieces:** Baggy strai…
[7] 2026-10-11T01:28:27-07:00 +3.136s (step 0.831s) create_fit_card
      in:  dict with keys: outfit, new_item
      out: Score this Y2K Baby Tee — Butterfly Print for just $18.0 on depop! Style it with baggy jeans and chunky sneake…

  Category average: $22.00 across 14 other tops listings in this dataset.

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop
```

The tee costs $18.00 and the fourteen other tops average $22.00. This path
leaves `session["price_warning"]` as `None` and still produces an outfit and
fit card. The full output, including both, is saved below.

**Empty search — existing early stop**

```bash
python app.py ask --trace 'designer ballgown size XXS under $5'
```

```text
Trace generated at: 2026-10-11T01:28:24-07:00
[1] 2026-10-11T01:28:24-07:00 +0.001s (step 0.001s) parse_query
      in:  designer ballgown size XXS under $5
      out: dict with keys: description, size, max_price
[2] 2026-10-11T01:28:24-07:00 +0.001s (step 0.000s) search_listings
      in:  dict with keys: description, size, max_price
      out: [] (empty)
[3] 2026-10-11T01:28:24-07:00 +0.001s (step 0.000s) empty-search branch
      out: No listings matched. Try broader keywords, a different size, or a higher price limit.
      →    stopping before suggest_outfit

  No listings matched. Try broader keywords, a different size, or a higher price limit.

0 model calls this session
```

Full captured outputs: [direct tool](results/stretch_price_tool.txt),
[above average](results/stretch_price_above_average.txt),
[below average](results/stretch_price_below_average.txt), and
[empty search](results/stretch_price_empty_search.txt).

**Automated verification**

`python -m unittest -v test_price_comparison` passed all eight tests. They
cover the arithmetic mean (including an outlier), ID/category exclusions,
cent rounding, above/below/equal prices, no peers, both warning paths, session
handoffs, CLI display, and the empty-search/all-owned stops. These tests use
fixture listings and replace the two model-dependent tool calls with fixed
responses, so they need no network calls or additional packages. The three
existing checks in `test_duplicate_matching.py` also passed locally.

### Earlier milestone examples (historical)

**One full query**

```text
% python app.py ask 'vintage graphic tee under $30'

  Found:    Oversized Crewneck Sweatshirt — Vintage Navy — $20.0 on thredUp

  Outfit:   Here are two practical outfit suggestions incorporating the new vintage navy oversized crewneck sweatshirt using only your existing wardrobe:

**Outfit 1: Casual Streetwear**
*   **Bottoms:** Baggy straight-leg jeans, dark wash
*   **Shoes:** Chunky white sneakers
*   **Accessories:** Black crossbody bag
*   **Styling:** Pair the oversized navy crewneck with your dark wash baggy jeans for a relaxed, tonal blue look. Finish with chunky white sneakers and the black crossbody bag for an effortless, everyday streetwear vibe.

**Outfit 2: High-Contrast Minimal**
*   **Bottoms:** Wide-leg khaki trousers
*   **Accessories:** Brown leather belt, Black crossbody bag
*   **Shoes:** Chunky white sneakers
*   **Styling:** Tuck the front hem of the navy crewneck into your wide-leg khaki trousers, defined with the brown leather belt to accent the earth tones. Complete the look with chunky white sneakers and your black crossbody bag for a balanced, smart-casual mix.

  Fit card: Score! I just found this dreamy Oversized Crewneck Sweatshirt — Vintage Navy on thredUp for only $20.0. I love its genuine faded wash and clean, classic vibe. Paired with wide-leg khakis and chunky sneakers, it creates the ultimate effortless streetwear look. #ThriftFinds #VintageStyle

2 model calls this session, 932 prompt + 282 output tokens
```

**The three tools, tested one at a time**

**`search_listings`**

```text
$ python -c "from tools import search_listings; results = search_listings('graphic tee', size='M', max_price=30); print([(x['title'], x['size'], x['price']) for x in results])"
[('Y2K Baby Tee — Butterfly Print', 'S/M', 18.0), ('Mesh Long-Sleeve Top — Black', 'S/M', 15.0)]
```

**Additional traced full run**

> This trace was captured before the duplicate matcher was tightened to
> require category, meaningful name, and shared color. It is retained as
> historical evidence; rerun it for current behavior.

```text
% python app.py ask --trace 'vintage graphic tee under $30'
Trace generated at: 2026-10-10T22:09:36-07:00
[1] 2026-10-10T22:09:36-07:00 +0.000s (step 0.000s) parse_query
      in:  vintage graphic tee under $30
      out: dict with keys: description, size, max_price
[2] 2026-10-10T22:09:36-07:00 +0.001s (step 0.000s) search_listings
      in:  dict with keys: description, size, max_price
      out: 8 items: Graphic Tee — 2003 Tour Bootleg Style, Y2K Baby Tee — Butterfly Print, Vintage Graphic Hoodie — Faded Black … +5 more
[3] 2026-10-10T22:09:36-07:00 +0.001s (step 0.000s) skip wardrobe duplicate
      in:  Graphic Tee — 2003 Tour Bootleg Style ($24.0, depop)
      out: skipped
      →    listing description/name and color match the wardrobe; size and price ignored
[4] 2026-10-10T22:09:36-07:00 +0.001s (step 0.000s) skip wardrobe duplicate
      in:  Y2K Baby Tee — Butterfly Print ($18.0, depop)
      out: skipped
      →    listing description/name and color match the wardrobe; size and price ignored
[5] 2026-10-10T22:09:36-07:00 +0.001s (step 0.000s) skip wardrobe duplicate
      in:  Vintage Graphic Hoodie — Faded Black ($26.0, depop)
      out: skipped
      →    listing description/name and color match the wardrobe; size and price ignored
[6] 2026-10-10T22:09:36-07:00 +0.001s (step 0.000s) skip wardrobe duplicate
      in:  Mesh Long-Sleeve Top — Black ($15.0, depop)
      out: skipped
      →    listing description/name and color match the wardrobe; size and price ignored
[7] 2026-10-10T22:09:36-07:00 +0.001s (step 0.000s) skip wardrobe duplicate
      in:  Vintage Band Tee — Faded Grey ($19.0, depop)
      out: skipped
      →    listing description/name and color match the wardrobe; size and price ignored
[8] 2026-10-10T22:09:36-07:00 +0.001s (step 0.000s) skip wardrobe duplicate
      in:  Low-Rise Cargo Pants — Khaki ($27.0, poshmark)
      out: skipped
      →    listing description/name and color match the wardrobe; size and price ignored
[9] 2026-10-10T22:09:36-07:00 +0.001s (step 0.000s) select_item
      out: Oversized Crewneck Sweatshirt — Vintage Navy ($20.0, thredUp)
[10] 2026-10-10T22:09:36-07:00 +0.002s (step 0.000s) suggest_outfit
      in:  Oversized Crewneck Sweatshirt — Vintage Navy ($20.0, thredUp)
      out: Here are two practical outfit suggestions incorporating the new vintage navy oversized crewneck sweatshirt usi…
[11] 2026-10-10T22:09:38-07:00 +1.714s (step 1.712s) create_fit_card
      in:  dict with keys: outfit, new_item
      out: Scored this perfectly faded Oversized Crewneck Sweatshirt — Vintage Navy on thredUp for just $20.0! I love the…

  Found:    Oversized Crewneck Sweatshirt — Vintage Navy — $20.0 on thredUp

  Outfit:   Here are two practical outfit suggestions incorporating the new vintage navy oversized crewneck sweatshirt using only your existing wardrobe:

**Outfit 1: Casual Streetwear**
*   **Bottoms:** Baggy straight-leg jeans, dark wash
*   **Shoes:** Chunky white sneakers
*   **Accessories:** Black crossbody bag
*   **Styling:** Pair the oversized navy crewneck with your dark wash baggy jeans for a relaxed, tonal blue look. Finish with chunky white sneakers and the black crossbody bag for an effortless, everyday streetwear vibe.

**Outfit 2: High-Contrast Minimal**
*   **Bottoms:** Wide-leg khaki trousers
*   **Accessories:** Brown leather belt, Black crossbody bag
*   **Shoes:** Chunky white sneakers
*   **Styling:** Tuck the front hem of the navy crewneck into your wide-leg khaki trousers, defined with the brown leather belt to accent the earth tones. Complete the look with chunky white sneakers and your black crossbody bag for a balanced, smart-casual mix.

  Fit card: Scored this perfectly faded Oversized Crewneck Sweatshirt — Vintage Navy on thredUp for just $20.0! I love the classic, effortless streetwear vibe when it's paired with baggy dark-wash jeans and chunky white sneakers. Such a timeless basic find! #thriftfinds #streetwear

1 model calls this session, 1 served from cache, 455 prompt + 63 output tokens
```

**`suggest_outfit` with the example wardrobe**

```text
% python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
Here are two outfit ideas incorporating the vintage Levi's 501 jeans and your existing wardrobe pieces:

### Outfit 1: Casual Streetwear
* **Top:** White ribbed tank top
* **Outerwear:** Vintage black denim jacket
* **Bottoms:** Vintage Levi's 501 Jeans — Medium Wash
* **Shoes:** Chunky white sneakers
* **Accessories:** Black crossbody bag

**Styling:** Tuck the white ribbed tank top into the 501s to highlight the high-waisted fit, layer the slightly cropped vintage black denim jacket on top, and finish with chunky white sneakers and the black crossbody bag for an effortless, casual streetwear look.

---

### Outfit 2: Cozy & Relaxed 
* **Top:** Oversized grey crewneck sweatshirt
* **Bottoms:** Vintage Levi's 501 Jeans — Medium Wash
* **Shoes:** Black combat boots
* **Accessories:** Brown leather belt, Black crossbody bag

**Styling:** Wear the brown leather belt with the 501s and do a simple front-tuck with the oversized grey crewneck sweatshirt. Pair with the lace-up black combat boots and the black crossbody bag to balance the cozy top with structured vintage denim and grunge footwear.
(venv-codepath) debasishhalder@Debasishs-Mac-mini CodePathweek3 % 
```

**Test with an empty wardrobe**

```text
% python -c "from tools import suggest_outfit; from utils.data_loader import get_empty_wardrobe, load_listings; item = load_listings()[0]; result = suggest_outfit(item, get_empty_wardrobe()); print(result)"
### Outfit 1: Effortless Casual Streetwear
* **Top:** A boxy-cut white cotton t-shirt tucked in loosely, layered with an oversized black leather biker jacket. 
* **Shoes:** Retro low-top sneakers like the Adidas Samba or Nike Killshot.
* **Accessories:** A minimalist black leather belt with a silver buckle and a canvas crossbody bag.
* **Why it works:** The crisp white tee and vintage wash denim create an iconic, timeless base. Adding the leather jacket and retro sneakers introduces a cool, effortless edge that matches the streetwear vibe of the 501s, while the structured belt pulls the waistline together.

### Outfit 2: Elevated Smart-Casual
* **Top:** A relaxed-fit, button-down Oxford shirt in crisp light blue or classic white, worn half-tucked.
* **Shoes:** Dark brown leather loafers or sleek suede ankle boots.
* **Accessories:** A tortoiseshell belt, delicate gold hoop earrings, and a structured structured leather tote bag.
* **Why it works:** Pairing rugged, casual denim with polished pieces like an Oxford shirt and leather shoes creates a high-low contrast that feels chic and intentional. The brown leather accessories add warmth that complements the indigo wash.
```

**Test that the return value is a string**

```text
% python -c "from tools import suggest_outfit; from utils.data_loader import get_empty_wardrobe, load_listings; result = suggest_outfit(load_listings()[0], get_empty_wardrobe()); print(type(result).__name__); print(bool(result.strip()))"
str
True
```

**Test with a manually created empty wardrobe**

```text
% python -c "from tools import suggest_outfit; from utils.data_loader import load_listings; item = load_listings()[0]; print(suggest_outfit(item, {'items': []}))"
### Outfit 1: Effortless Casual Streetwear
* **Top:** A boxy-cut white cotton t-shirt tucked in loosely, layered with an oversized black leather biker jacket. 
* **Shoes:** Retro low-top sneakers like the Adidas Samba or Nike Killshot.
* **Accessories:** A minimalist black leather belt with a silver buckle and a canvas crossbody bag.
* **Why it works:** The crisp white tee and vintage wash denim create an iconic, timeless base. Adding the leather jacket and retro sneakers introduces a cool, effortless edge that matches the streetwear vibe of the 501s, while the structured belt pulls the waistline together.

### Outfit 2: Elevated Smart-Casual
* **Top:** A relaxed-fit, button-down Oxford shirt in crisp light blue or classic white, worn half-tucked.
* **Shoes:** Dark brown leather loafers or sleek suede ankle boots.
* **Accessories:** A tortoiseshell belt, delicate gold hoop earrings, and a structured structured leather tote bag.
* **Why it works:** Pairing rugged, casual denim with polished pieces like an Oxford shirt and leather shoes creates a high-low contrast that feels chic and intentional. The brown leather accessories add warmth that complements the indigo wash.
```

**Testing of suggest_outfit multiple times from LLM and it gives different output every time**

```text
(venv-codepath) debasishhalder@Debasishs-Mac-mini CodePathweek3 % AI201_CACHE=0 python -c "from tools import suggest_outfit; from utils.data_loader import load_listings; item = load_listings()[0]; print(suggest_outfit(item, {'items': []}))"
**Outfit 1: Casual Streetwear**
*   **Top:** A crisp white, boxy-fit heavyweight cotton t-shirt.
*   **Outerwear:** An oversized black leather or nylon bomber jacket.
*   **Shoes:** Retro low-top sneakers like Adidas Samba or Nike Killshot.
*   **Accessories:** A minimalist silver chain necklace and a black canvas crossbody bag.
*   **Why it works:** The crisp white tee creates a clean, timeless contrast against the medium wash, while the bomber and sneakers lean into the streetwear vibe. The structured jacket balances the relaxed, straight-leg silhouette of the 501s.

**Outfit 2: Elevated Smart-Casual**
*   **Top:** A ribbed black cotton baby tee or a tucked-in black silk camisole.
*   **Outerwear:** An oversized, houndstooth or camel-colored blazer.
*   **Shoes:** Pointed-toe black leather ankle boots.
*   **Accessories:** A structured black leather belt with a simple gold buckle and a slouchy leather shoulder bag.
*   **Why it works:** Pairing vintage denim with tailored pieces like a blazer and boots instantly elevates the jeans for dinner or casual office settings. The structured outerwear contrasts nicely with the relaxed, broken-in feel of the 501s.
(venv-codepath) debasishhalder@Debasishs-Mac-mini CodePathweek3 % AI201_CACHE=0 python -c "from tools import suggest_outfit; from utils.data_loader import load_listings; item = load_listings()[0]; print(suggest_outfit(item, {'items': []}))"
**Outfit 1: Casual Streetwear**
*   **Top:** A crisp white, boxy-cut t-shirt tucked in casually, layered with an oversized black leather biker jacket.
*   **Shoes:** Retro low-top sneakers like Adidas Sambas or Nike Killshots.
*   **Accessories:** A minimalist silver chain necklace and a black canvas cross-body bag.
*   **Why it works:** The structured leather jacket and boxy tee elevate the relaxed, lived-in feel of the medium-wash 501s, creating a balanced, effortless streetwear aesthetic.

**Outfit 2: Elevated Smart-Casual**
*   **Top:** A relaxed-fit, oatmeal-colored merino wool crewneck sweater worn over a crisp blue-and-white striped button-down (letting the collar and hem peek out).
*   **Shoes:** Dark brown leather penny loafers worn with ribbed white cotton socks.
*   **Accessories:** A classic brown leather belt with a simple silver buckle and tortoiseshell sunglasses.
*   **Why it works:** Pairing rugged vintage denim with refined textures like knitwear and leather loafers creates a polished high-low contrast that feels timeless.
(venv-codepath) debasishhalder@Debasishs-Mac-mini CodePathweek3 % 
```


**Testing of create_fit_card using same command three time getting different results - temperature setting is 0.9**

```text
% python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
How good are these Vintage Levi's 501 Jeans — Medium Wash? Paired with crisp white sneakers, they give off the ultimate effortless streetwear vibe. Snag this classic pair for just $38.0 over on depop before someone else does! #vintage #denim

% python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
Look at this gorgeous pair of Vintage Levi's 501 Jeans — Medium Wash! Styled effortlessly with crisp white sneakers, they give off the ultimate effortless streetwear vibe. Snag this classic look right now on depop for just $38.0. 

#vintage #classic #denim #streetwear
% python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
Score! These Vintage Levi's 501 Jeans — Medium Wash bring that effortless, lived-in streetwear vibe. Pair them with fresh white sneakers for an instant classic look. Grab this gem on depop for just $38.0 before someone else does! #vintage #denim

(venv-codepath) debasishhalder@Debasishs-Mac-mini CodePathweek3 % 
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:* these are two sample criteria exlain how to write each section of critteria and why should critera be written like this:## 1. A matching query completes all three tools

**Source: Provided by CodePath; original criterion retained below.**

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Pass for one try:** The call log shows search_listings, suggest_outfit,
and create_fit_card completing in that order. The returned session has a
nonempty search_results list, a selected_item from that list, a nonempty
outfit_suggestion, a nonblank string in fit_card, and error equal to
None. The user receives the card without re-entering the selected item.
Card quality is evaluated separately under criterion 4.

**How to test:** Choose and record one query whose description, size (if
specified), and budget match a record in data/listings.json. Use the example
wardrobe and repeat that same query five times in fresh sessions. Save each
call log, final session, and displayed response.

**Why this target (proposed):** This path depends on two model calls, so an
occasional failed generation may prevent completion even when search works.
Four successes out of five requires repeatable usefulness while allowing one
failure to investigate; it is a small acceptance sample, not a reliability estimate.

## 2. An impossible query stops before the second tool

**Source: Provided by CodePath; original criterion retained below.**

Given a query that matches no listings, the agent stops before calling
suggest_outfit and returns a message naming what to change — 5 of 5 tries.

**Pass for one try:** search_listings returns []; neither suggest_outfit
nor create_fit_card is called. The final session has selected_item,
outfit_suggestion, and fit_card equal to None. Its error message is
shown to the user and suggests at least one concrete change: broaden the
item description, change the requested size, or raise the budget. A message
that only says “No results” fails.

**How to test:** Confirm against the listings file that the chosen query has
zero matches, then run it five times in fresh sessions. The starter's
designer ballgown size XXS under $5 is a candidate; verify it against the
data before using it. Inspect actual tool calls as well as the final session.

**Why this target (proposed):** Once search returns an empty list, stopping
is a deterministic branch and needs no model-generated answer. Every run
should prevent invalid downstream calls and provide a usable next step.
Five out of five is the strictest target in this sample.

- *What came back:*
Both criteria use the same structure, and each section has a different job. Here is how to write each one, using your two samples to show the reasoning.

1. Title

What to write: One plain sentence naming the behavior, not the implementation.

Your examples: “A matching query completes all three tools” and “An impossible query stops before the second tool.” Each names a situation (matching vs. impossible query) and an observable outcome (completes all three vs. stops early).

Why: A reader should know what is being tested before reading any details. Putting the input type in the title also makes it obvious that your criteria cover different situations and aren’t repeats.

2. Source line

What to write: Say whether the criterion came from the assignment or from you (or an AI draft).

Your examples: “Provided by CodePath; original criterion retained below.”

Why: It keeps authorship honest. Your status note says the AI-drafted material is a proposal for you to review and revise. For criteria 3 to 5, you would label them as your own, so a grader can tell which choices you made and can expect you to explain them.

3. The criterion statement

What to write: One sentence in the form: Given [specific input], the agent [observable behavior], in at least N of M tries.

Your examples:

“Given a query that matches at least one listing, the agent completes all three tool calls and returns a fit card — in at least 4 of 5 tries.”
“Given a query that matches no listings, the agent stops before calling suggest_outfit and returns a message naming what to change — 5 of 5 tries.”

Why each part is there:

“Given [input]” fixes the condition. Without it, “the agent works” could mean anything.
An observable behavior means you can see it in logs or output. “Handles errors well” can’t be seen, but “stops before calling suggest_outfit” can.
“N of M tries” is there because an agent built on model calls can behave differently on identical input. A single success proves little, so you count successes across repeated runs.
4. Pass for one try

What to write: A short checklist of yes/no conditions for a single run, each pointing to a place you can look: the call log, the final session, or the displayed response.

Why it’s written this way: Anyone should reach the same pass/fail verdict from your saved evidence without asking you what you meant. That is why there are no words like “good” or “reasonable,” why negative conditions are included, and why subjective ideas get a boundary example.

5. How to test

What to write: The exact procedure: what input, what setup, how many runs, and what evidence to save.

Your examples:

“Choose and record one query... that match[es] a record in data/listings.json.”
“Use the example wardrobe and repeat that same query five times in fresh sessions.”
“Save each call log, final session, and displayed response.”
“Confirm against the listings file that the chosen query has zero matches... verify it against the data before using it.”

Why each piece matters:

A fixed, recorded query means the five runs are comparable, and anyone can repeat your test.
Fresh sessions prevent leftover state from one run affecting the next.
Verifying against the data first matters most. In criterion 2, a query you assume has no matches might actually match something, which would invalidate the whole test.
Saved evidence lets you show the result later instead of just claiming it. This is also why “inspect actual tool calls as well as the final session” appears: a final session can look correct even if the agent took a wrong path to get there.
6. Why this target

What to write: Your reasoning for the threshold, naming whether the behavior depends on model calls or plain code, and what a failure would mean.

Your examples:

Criterion 1 gets 4 of 5 because “this path depends on two model calls, so an occasional failed generation may prevent completion even when search works.” It also admits the limit: “a small acceptance sample, not a reliability estimate.”
Criterion 2 gets 5 of 5 because an empty search result leads to “a deterministic branch” that needs no model-generated answer, so any failure is a real bug.

Why: The threshold is a decision, and a decision should have a reason. The explanation also tells you what to do on a failure: with a deterministic branch, any miss means a bug to fix, while with a model-dependent path, one miss is something to investigate. The honest caveat about sample size keeps you from overclaiming what five runs prove.

Why criteria are written this way overall
Testable by someone else. Every statement can be checked from saved evidence, so the criterion works as a contract.
One behavior per criterion. Splitting concerns (like sending card quality to criterion 4) means that when something fails, you know which part broke.
Honest about uncertainty. Using N of M instead of “always works” admits that model behavior varies, and the “why” explains how much variance you are tolerating and why.
Defensible. You can explain every number and wording choice, which is what the assignment asks of you before submission.
Applying it to your own criteria

For each one you write, ask in order: what situation is it (title and input)? What will I see if it works (pass conditions, tied to log, session, or response)? How will someone repeat the test (setup and evidence)? And is the behavior plain code or a model call (threshold and reason)?

If you tell me which behaviors you want to cover in criteria 3 to 5, I can help you draft the sections for each.
- *What I changed:* 

I rewrote the criteria 4 and 5 based on these understanding

**Moment 2**

- *What I asked for:* review this and tell me whaaat problems are thre in this criteria:
**Source: Proposed additional criterion for student review.**

Given a verified matching query and wardrobe={"items": []}, the agent
returns general styling advice and a nonblank fit card, without asking for
wardrobe entries or claiming the user owns unprovided pieces — at least
4 of 5 tries.

**Pass for one try:** All three tools complete, session["error"] is None,
and the outfit suggestion names at least one complementary clothing type
plus a color or fit recommendation. It presents those pieces as suggestions
(for example, “try pairing it with”), not as known wardrobe contents. The
fit card is nonblank and makes no claim of ownership for unprovided pieces.
No crash or request to fill the wardrobe occurs.

**How to test:** Record a query that matches the listings, then run it five
times in fresh sessions using the exact empty wardrobe above. Save the
session, tool arguments, and displayed output for each try.

**Why this target (proposed):** A new user may have no saved wardrobe, so
this required fallback must still be useful. Its advice and caption rely on
model calls; four successes out of five permits one generation failure while
requiring the fallback to work repeatedly.


- *What came back:*
The idea is good: an empty wardrobe is a real edge case that touches the model-dependent steps. The wording has several problems, though, and a few of them would let two reviewers score the same run differently.

Problems

1. There is no title.
The other criteria start with a ## N. Title line. This one begins at the source line. Add something like “## 5. An empty wardrobe still produces useful advice.”

2. “General styling advice” is vague in the statement.
The statement says “general styling advice,” but the pass conditions define it as “at least one complementary clothing type plus a color or fit recommendation.” Use the same wording in both places, or the statement promises something the checklist doesn’t test.

3. “A color or fit recommendation” is loose.
“Fit” could mean the cut (“oversized”), the sizing, or how the item hangs. Two reviewers could disagree. Define it with examples, such as “a named color (e.g., ‘black jeans’) or a fit word (e.g., ‘relaxed’, ‘cropped’, ‘high-waisted’).”

4. The ownership check is split and partly unclear.
The statement and the checklist both mention ownership, but they say different things. The statement forbids “claiming the user owns unprovided pieces.” The checklist has one rule about how the outfit “presents” pieces (“try pairing it with”) and another about the card making “no claim of ownership.” The “for example” phrase is a hint, not a rule. Write one concrete test applied to both the outfit suggestion and the card: “Neither describes any piece as already owned or in the user’s closet (e.g., ‘your black jeans’, ‘from your wardrobe’, ‘you already have’).” Note that “your” alone shouldn’t fail, since “your new tee” is fine.

5. Several conditions are bundled into one bullet or sentence.
“All three tools complete, error is None, and the outfit names...” mixes call-log, session, and content checks. Your other criteria use bullets, each pointing to one place to look (call log, session, response). A bullet list makes each condition separately scorable.

6. “No crash or request to fill the wardrobe occurs” is only partly checkable.
“Crash” is covered by error equal to None, so this is a repeat. “Request to fill the wardrobe” needs a place to look: “The displayed response contains no question or prompt asking the user to add, enter, or describe wardrobe items, and no second user input is consumed.”

7. The statement says “returns general styling advice,” but nothing checks that the advice stays general.
If the model invents specific items (“your white sneakers”), that is covered by the ownership check, but say so in one place so it’s clear that this is how “general” is defined.

8. The call order isn’t checked.
Your criterion 1 and 3 check the order search_listings, suggest_outfit, create_fit_card. Here you say “all three tools complete” with no order. Add it, or explain why it doesn’t matter.

9. “How to test” is missing pieces.

It doesn’t say to confirm the query matches a record in data/listings.json before running (it says “record a query that matches,” which is close, but verify it).
It doesn’t say to compare the outfit and card against the saved listing and the empty wardrobe.
Say you score the checks by hand against the saved evidence.
Say how you handle a try with an exception (it fails).

10. “Why this target” lacks the honest caveat.
Add “this is a small acceptance sample, not a reliability estimate,” like the CodePath samples. Also, “a new user may have no saved wardrobe” is a reason for the criterion, not for 4 of 5. The target reasoning is in your last clause, so keep that and move the first sentence to a short motivation line or the opening.

11. The empty wardrobe format needs verification.
wardrobe={"items": []} is a specific shape. Confirm it matches your real wardrobe structure and how the tool receives it. If the real format differs, the test won’t reflect what the agent actually gets.

12. Overlap with criterion 1.
Criterion 1 covers completion on a normal wardrobe, and this one covers the empty case. That’s fine, but say so, or a reviewer may ask why you repeat “all three tools complete.” Keep the focus on the empty-wardrobe behavior.

Revised version
5. An empty wardrobe still produces usable styling advice

Source: Proposed additional criterion for student review.

Given a verified matching query and wardrobe={"items": []}, the agent completes all three tools and returns an outfit suggestion with at least one complementary clothing type and a color or fit recommendation, plus a nonblank fit card, without asking for wardrobe entries or claiming the user owns any pieces, in at least 4 of 5 tries.

Pass for one try: All of these checks hold:

The call log shows search_listings, suggest_outfit, and create_fit_card completing in that order, and session["error"] is None.
The outfit suggestion names at least one complementary clothing type and either a named color or a fit word (such as relaxed, cropped, or high-waisted).
The fit card is a nonblank string.
Neither the outfit suggestion nor the fit card describes any piece as already owned or in the user’s closet (such as “your black jeans,” “from your wardrobe,” or “you already have”).
The displayed response contains no request to add, enter, or describe wardrobe items, and no second user input is consumed.

How to test:

Choose one query and confirm it matches a record in data/listings.json before running.
Run it five times in fresh sessions, passing the exact empty wardrobe your code expects.
Save the call log, tool arguments, final session, and displayed response for each try.
Mark each check yes or no by hand against the saved evidence.
An exception or a skipped tool fails that try.

Why this target (proposed): [Add why the empty-wardrobe case matters, such as new users having no saved wardrobe.] The advice and the caption both come from model calls, so four successes out of five allows one failed generation while still requiring the fallback to work in most attempts. This is a small acceptance sample, not a reliability estimate.

Before submitting, confirm that {"items": []} is your real empty-wardrobe format, and keep the fit and card-quality rules consistent with criterion 4 so the two don’t conflict.

- *What I changed:*
I took the guidance and I chnged the Criteria accordingly. The idea was mine but I wrote and have something and claude commented on it and i used the changed wording for the criteria

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
