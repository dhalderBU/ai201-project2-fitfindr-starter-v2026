# Acceptance criteria — FitFindr

**Status: AI-assisted draft for student review; not an evaluation result.**
The assignment supplies criteria 1 and 2 and asks you to write criteria 3–5
and explain all five. The added criteria and reasons below are proposals:
review and revise them to reflect decisions you can explain before submission.
No application tests were run to set these targets, and no passes are claimed.

## 1. A matching query completes all three tools

**Source: Provided by CodePath; original criterion retained below.**

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Pass for one try:** The call log shows `search_listings`, `suggest_outfit`,
and `create_fit_card` completing in that order. The returned session has a
nonempty `search_results` list, a `selected_item` from that list, a nonempty
`outfit_suggestion`, a nonblank string in `fit_card`, and `error` equal to
`None`. The user receives the card without re-entering the selected item.
Card quality is evaluated separately under criterion 4.

**How to test:** **How to test:** Choose one verified matching query and one 
fixed wardrobe. Run the complete agent flow five times in fresh sessions with 
caching disabled. Save the query, wardrobe, trace, final session, displayed response, 
and any exception for every try. For each completed session, use that session's
`fit_card_inputs` as the evidence for scoring its `fit_card`. Count words with
`len(session["fit_card"].split())` and mark each content check against those
saved inputs. A blank output, exception, missing fit-card inputs, card over 60
words, or any failed content check fails that try. Criterion 4 passes only if
at least 4 of 5 tries pass every check. Different wording is allowed; identical
wording is not automatically a failure.

**Why this target (proposed):** This path depends on two model calls, so an
occasional failed generation may prevent completion even when search works.
Four successes out of five requires repeatable usefulness while allowing one
failure to investigate; it is a small acceptance sample, not a reliability estimate.

## 2. An impossible query stops before the second tool

**Source: Provided by CodePath; original criterion retained below.**

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Pass for one try:** `search_listings` returns `[]`; neither `suggest_outfit`
nor `create_fit_card` is called. The final session has `selected_item`,
`outfit_suggestion`, and `fit_card` equal to `None`. Its `error` message is
shown to the user and suggests at least one concrete change: broaden the
item description, change the requested size, or raise the budget. A message
that only says “No results” fails.

**How to test:** Confirm against the listings file that the chosen query has
zero matches, then run it five times in fresh sessions. The starter's
`designer ballgown size XXS under $5` is a candidate; verify it against the
data before using it. Inspect actual tool calls as well as the final session.

**Why this target (proposed):** Once search returns an empty list, stopping
is a deterministic branch and needs no model-generated answer. Every run
should prevent invalid downstream calls and provide a usable next step.
Five out of five is the strictest target in this sample.

## 3. The selected item and outfit pass through session state unchanged

**Source: Proposed additional criterion for student review.**

Given a verified matching query, the selected listing is stored in the session 
and passed unchanged to both downstream tools, and the stored outfit is passed 
unchanged to create_fit_card — 5 of 5 tries, with zero requests for the user 
to enter the item again.

**Pass for one try:** All of these checks hold:

- `session["selected_item"]` equals a complete listing dictionary in
  `session["search_results"]`, including its `id`.
- The actual `new_item` argument received by `suggest_outfit` equals the
  selected-item snapshot saved immediately before that call.
- The actual `new_item` argument received by `create_fit_card` equals that
  same selected listing, including every field and value.
- The actual `outfit` argument received by `create_fit_card` equals the
  stored `session["outfit_suggestion"]` snapshot from before that call.


**How to test:** Record copies of the actual tool arguments and session
values at each handoff, then compare dictionary/string values rather than
Python object identity. Repeat the same verified query five times. A final
session dump alone cannot prove what arguments a tool actually received.
A missing handoff or an interrupted run fails that try.

**Why this target (proposed):** State transfer is controlled by Python code;
model wording can vary without changing which listing or saved outfit is
passed along. Any mismatch can style or caption the wrong item, so the
sample allows no incorrect handoffs.

## 4. The fit card is short, relevant, and grounded in its inputs

**Source: Proposed additional criterion for student review.**

Given the same verified matching query and wardrobe, run the complete agent flow 
five times with caching disabled. Each completed run must produce a fit card that 
is grounded in the `outfit` and `new_item` saved in that run's
 `session["fit_card_inputs"]` — at least 4 of 5 tries.

**Pass for one try:** All of these checks must hold:

- The agent completes without an exception and returns a nonblank fit card.
- The fit card contains no more than 60 whitespace-separated words, verified with `len(session["fit_card"].split())`.
- The fit card is grounded in that session's saved `fit_card_inputs`.
- The fit card identifies the item's clothing type and at least one supported 
detail, such as color, print, brand, or style.
- The fit card mentions the clothing's vibe.
- The fit card includes at least one styling idea from the saved outfit.
- The fit card contains no invented or contradictory listing facts.
- The fit card does not falsely claim that a suggested purchase is already 
  owned.
- Different wording between tries is allowed; identical wording is not
  automatically a failure.

**How to test:** Save one real listing and one valid outfit suggestion as fixed 
inputs before scoring. Call the tool five times with caching disabled. Save the 
inputs and each output, count words with `len(card.split())`, and mark each 
content check using the saved inputs as evidence. A blank output, exception, 
or any failed check fails the entire try. Different wording is allowed; identical 
wording is not automatically a failure.

**Why this target (proposed):** A 60 word limit makes the output a short
caption, and grounding checks prevent fluent but misleading text from passing.
Four out of five allows one model-output failure while still requiring all
quality checks to hold together in most attempts.

## 5. An already-owned search result is skipped

**Source: Proposed by student.**

Given a query whose first matching listing is already represented in the
user's wardrobe by a matching name or description and at least one shared
color, and whose later matching listing is not represented in the wardrobe,
the agent records and skips the owned listing and selects the first unowned
matching listing — 5 of 5 tries.

**Pass for one try:** All of these checks hold:

- The saved wardrobe contains an item whose normalized name or descriptive text matches
 the first search result, and whose normalized colors share at
  least one color token with that listing.
- Size and price are not used in the duplicate comparison.
- The trace records the owned listing with a `skip wardrobe duplicate` event
  and identifies it as skipped.
- The owned listing is not passed to `suggest_outfit` or `create_fit_card`.
- `session["selected_item"]` is the first listing in `session["search_results"]` that 
does not match a wardrobe item, identified by listing `id`.
- `suggest_outfit` receives the selected unowned listing.
- No exception occurs before the `suggest_outfit` call.
- The agent does not ask the user to re-enter the item or consume a second user input.
- If every matching listing is already in the wardrobe, the agent stops and
  displays a message explaining that no new matching item remains.

**How to test:** Create and save a fixed query, search-result set, and custom wardrobe 
where the first search result matches a wardrobe item by normalized
name or descriptive text and at least one shared color, while a later search result 
does not. Confirm the expected matches against `data/listings.json` and the wardrobe 
before running the test.

Run the same query five times in fresh sessions with caching disabled. Save the query, 
wardrobe, search results, trace, tool arguments, final session, and
displayed response for every try. Confirm that the owned listing is recorded and 
skipped, that size and price do not affect the duplicate decision, and
that the first unowned listing is selected and passed to `suggest_outfit`.

A try fails if the owned listing is selected again, passed to either downstream tool, not
recorded as skipped, the duplicate check incorrectly uses size or price, an exception 
occurs before `suggest_outfit`, the agent requests a second user input, or the 
all-owned case does not produce a clear stopping message.

**Why this target (proposed):** The agent should not recommend an item the user already owns. 
Search results are deterministic, and the duplicate comparison is plain code, so the 
same inputs should produce the same ownership decision on every run. Five out of five 
is therefore appropriate. One shared color is sufficient because a garment can contain 
multiple colors, and a likely duplicate should be skipped rather than recommended.



## Evaluation procedure

- Review these targets and record them in Git before collecting formal
  evaluation results. Do not claim they predate earlier work or testing.
- Freeze the listings, query, wardrobe, model settings, and any fixed tool
  inputs for a before/after comparison. Record the commit and settings used.
- Use five fresh tries per criterion with model caching disabled. Record every
  attempt, including failures; do not silently replace failed tries.
- A try passes only if every check under that criterion passes. If the
  evidence cannot establish a required check, mark the try FAIL and explain
  the missing evidence.
- Use actual tool-call evidence for criteria 1–3. A plausible final response
  does not establish correct branching or state transfer.
- The existing `run_eval.py` disables caching and collects session/trace
  output, but does not score criteria. `scenarios.py` still needs coverage for
  criteria 3–5. Criterion 4 requires five direct calls with fixed inputs;
  repeating the full agent may change the outfit and is not an equivalent test.
- Mark a criterion MET only when its pass count reaches its target. Keep
  original criteria when recording later revisions; explain a genuine
  measurability correction instead of lowering a target after a miss.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes | At least 4/5 | — | — | — | — | — | Not evaluated |
| 2. Empty search stops safely | 5/5 | — | — | — | — | — | Not evaluated |
| 3. State survives handoffs | 5/5 | — | — | — | — | — | Not evaluated |
| 4. Fit-card quality | At least 4/5 | — | — | — | — | — | Not evaluated |
| 5. Owned result advances search | 5/5 | — | — | — | — | — | Not evaluated |

For each FAIL, save the actual output or trace and name the failed check.
Record the cause separately once investigated; a failure is evidence, not yet
a diagnosis.
