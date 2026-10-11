"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""
import re
from copy import deepcopy

import config
import trace
from tools import search_listings, suggest_outfit, create_fit_card, compare_price
from generate import ModelUnavailable


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "price_comparison": None,    # comparison with other category listings
        "price_warning": None,       # set only for an above-average price
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "fit_card_inputs": {
            "outfit": None,
            "new_item": None,
        },                            # fixed inputs used for fit-card scoring
        "fit_card_outputs": [],       # outputs produced from those inputs
        "error": None,               # set when the run ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────


def _parse_query(query: str) -> dict:
    """Extract the description, optional size, and optional price ceiling."""
    text = query.strip()
    size_match = re.search(
        r"\b(?:in\s+)?size\s+([a-z0-9]+(?:\s*/\s*[a-z0-9]+)?)",
        text,
        flags=re.IGNORECASE,
    )

    description = text
    if size_match:
        description = description[:size_match.start()] + description[size_match.end():]

    price_match = re.search(
        r"\b(?:under|below|less\s+than|up\s+to)\s+\$?\s*(\d+(?:\.\d+)?)",
        description,
        flags=re.IGNORECASE,
    )
    if price_match:
        description = (
            description[:price_match.start()] + description[price_match.end():]
        )

    return {
        "description": re.sub(r"\s+", " ", description).strip(" ,."),
        "size": size_match.group(1).strip() if size_match else None,
        "max_price": float(price_match.group(1)) if price_match else None,
    }


def _normalize_text(value: str) -> str:
    """Collapse text so similar titles and wardrobe names compare reliably."""
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


_GENERIC_MATCH_WORDS = {
    "classic",
    "everyday",
    "faded",
    "fit",
    "great",
    "look",
    "oversized",
    "style",
    "stylish",
    "streetwear",
    "vintage",
}


def _identity_tokens(value: str) -> set[str]:
    """Return name tokens useful for identifying a particular garment."""
    return {
        token
        for token in _normalize_text(value).split()
        if token not in _GENERIC_MATCH_WORDS
    }


def _listing_in_wardrobe(listing: dict, wardrobe: dict) -> bool:
    """Return True when a search result appears to already be in the wardrobe.

    A duplicate must have the same category, a shared color, and a meaningful
    name match. Size and price are intentionally ignored.
    """
    wardrobe_items = wardrobe.get("items", []) if isinstance(wardrobe, dict) else []
    if not isinstance(listing, dict):
        return False

    listing_title = str(listing.get("title", "")).strip()
    listing_category = _normalize_text(listing.get("category", ""))
    listing_colors = " ".join(listing.get("colors", []))
    listing_color_tokens = set(_normalize_text(listing_colors).split())
    listing_name_tokens = _identity_tokens(listing_title)

    for item in wardrobe_items:
        if not isinstance(item, dict):
            continue

        item_name = str(item.get("name", "")).strip()
        item_category = _normalize_text(item.get("category", ""))
        item_colors = " ".join(item.get("colors", []))
        item_color_tokens = set(_normalize_text(item_colors).split())

        if not listing_name_tokens or not item_name or listing_category != item_category:
            continue

        color_match = bool(listing_color_tokens & item_color_tokens)
        if not color_match:
            continue

        item_name_normalized = _normalize_text(item_name)
        listing_name_normalized = _normalize_text(listing_title)
        same_name = (
            listing_name_normalized == item_name_normalized
            or item_name_normalized in listing_name_normalized
            or listing_name_normalized in item_name_normalized
        )
        name_overlap = len(listing_name_tokens & _identity_tokens(item_name)) >= 2
        if same_name or name_overlap:
            return True

    return False


def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    ─────────────────────────────────────────────────────────────────────────
    TODO — build this, following the branch rule you wrote in Milestone 2.

      1. Start a session with new_session().

      2. Count the times round the loop, and call trace.check_iterations(count)
         on each one before you go again. It raises when the count passes
         MAX_ITERATIONS in config.py — see trace.py.

      3. Parse the query into a description, a size, and a max_price. Regex,
         string splitting, or asking the model are all fine — say which you
         chose in your README. Put the result in session["parsed"].

      4. Call search_listings() with what you parsed.
         Put the results in session["search_results"].

         ⚠️ THIS IS THE BRANCH. If nothing came back:
              - put a message in session["error"] saying what the user could
                change — "No results" is not that message
              - return the session
              - do NOT call suggest_outfit with nothing

      5. Choose an item — the first result is fine. Put it in
         session["selected_item"].

      6. Call suggest_outfit() with the selected item and the wardrobe.
         Put the result in session["outfit_suggestion"].

      7. Call create_fit_card() with the outfit and the item.
         Put the result in session["fit_card"].

      8. Return the session.

    ─────────────────────────────────────────────────────────────────────────
    IN UNIT 4 you come back and add two things:

      • Trace calls. One per step. `trace.step("search_listings", inputs=...,
        returned=...)` — see trace.py. Your README needs the output.

      • A handler for ModelUnavailable, so a bad key produces a message rather
        than a stack trace. The import is already at the top of this file.
    """
    session = new_session(query, wardrobe)
    iteration = 0

    while True:
        iteration += 1
        trace.check_iterations(iteration)

        parsed = _parse_query(session["query"])
        session["parsed"] = parsed
        trace.step("parse_query", inputs=session["query"], returned=parsed)

        results = search_listings(
            parsed["description"],
            parsed["size"],
            parsed["max_price"],
        )
        session["search_results"] = results
        trace.step("search_listings", inputs=parsed, returned=results)

        #_________ Branch rule: if nothing came back, stop and propose change__________________
        #_________ RULE : If search_listings returns an empty list, put a message in the session and stop. Otherwise, take the first result and go to suggest_outfit______
        
        if not results:
            session["error"] = (
                "No listings matched. Try broader keywords, a different size, "
                "or a higher price limit."
            )
            trace.step(
                "empty-search branch",
                returned=session["error"],
                note="stopping before suggest_outfit",
            )
            return session

# Skip a result only when category, a meaningful name match, and a shared
# color indicate that it is already represented in the wardrobe. Size and
# price are not part of this check.

        selected = None
        for candidate in results:
            if _listing_in_wardrobe(candidate, session["wardrobe"]):
                trace.step(
                    "skip wardrobe duplicate",
                    inputs=candidate,
                    returned="skipped",
                    note=(
                        "category, meaningful name, and color match the "
                        "wardrobe; size and price ignored"
                    ),
                )
                continue
            selected = candidate
            break

        if selected is None:
            session["error"] = (
                "All matching listings already appear in the user's wardrobe. "
                "Try a different description, size, or price limit."
            )
            trace.step(
                "wardrobe-owned branch",
                returned=session["error"],
                note="skipping owned results and stopping",
            )
            return session

        session["selected_item"] = selected
        trace.step("select_item", returned=session["selected_item"])

        session["price_comparison"] = compare_price(session["selected_item"])
        comparison = session["price_comparison"]
        trace.step(
            "compare_price",
            inputs=session["selected_item"],
            returned=comparison,
            note=(
                f"status={comparison['status']}; "
                f"peers={comparison['comparison_count']}; "
                f"average={comparison['average_price']}; "
                f"difference={comparison['difference']}"
            ),
        )
        # Second Branch (stretch): warn when the price exceeds the category average.
        if comparison["status"] == "above_average":
            session["price_warning"] = (
                f"This item is ${comparison['difference']:.2f} above the "
                f"${comparison['average_price']:.2f} average of "
                f"{comparison['comparison_count']} other "
                f"{comparison['category']} listings in this dataset. "
                "This is a broad category comparison, not a market valuation."
            )
            trace.step(
                "above-average price branch (Second Branch)",
                returned=session["price_warning"],
                note="show a price warning and continue to suggest_outfit",
            )
        else:
            trace.step(
                "price comparison: no warning",
                returned=comparison["status"],
                note="continue to suggest_outfit",
            )

        try:
            session["outfit_suggestion"] = suggest_outfit(
                session["selected_item"],
                session["wardrobe"],
            )
            trace.step(
                "suggest_outfit",
                inputs=session["selected_item"],
                returned=session["outfit_suggestion"],
            )

# the starter repo code was copying reference to the selected item into the fit card inputs, which could lead to unexpected mutations. Using deepcopy ensures that the fit card inputs are independent of the selected item.

            session["fit_card_inputs"] = {
                "outfit": session["outfit_suggestion"],
                "new_item": deepcopy(session["selected_item"]),
            }
            session["fit_card"] = create_fit_card(
                session["fit_card_inputs"]["outfit"],
                session["fit_card_inputs"]["new_item"],
            )
            
            #This line saves the generated fit card into the session’s output history:
            session["fit_card_outputs"].append(session["fit_card"])
            trace.step(
                "create_fit_card",
                inputs=session["fit_card_inputs"],
                returned=session["fit_card"],
            )
        except ModelUnavailable as exc:
            session["error"] = f"Unable to complete the styling request: {exc}"
            trace.step("model error", returned=session["error"])
        except ValueError as exc:
            session["error"] = f"Unable to create a fit card: {exc}"
            trace.step("fit-card validation error", returned=session["error"])
        return session


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["price_warning"]:
        print(f"  Price warning: {session['price_warning']}")
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
