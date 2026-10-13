"""
The runs your test needs. ← UNIT 4, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
the empty-search branch needs an impossible query. One about the fit card needs
the same item run more than once. Working that out is Milestone 3's first step,
and this file is where you write it down.

`run_eval.py` runs everything here five times and writes the run log — five
because your criteria are written out of five.

Criteria 3 and 4 reuse a matching query for state and fit-card checks.
Criterion 5 uses fixed owned-item fixtures for both duplicate branches.
"""

SCENARIOS = [
    {
        # A query the data can match. Criterion 1.
        "name": "matching query completes",
        "query": "vintage graphic tee under $30",
        "wardrobe": "example",
        "criterion": 1,
    },
    {
        # A query nothing can match. Criterion 2 — the branch.
        "name": "impossible query stops early",
        "query": "designer ballgown size XXS under $5",
        "wardrobe": "example",
        "criterion": 2,
    },
    {
        # A user with nothing saved. One of unit 4's three failure modes.
        "name": "empty wardrobe",
        "query": "denim jacket under $50",
        "wardrobe": "empty",
        "criterion": None,
    },
    {
        # Compare the complete selected item and outfit at each tool handoff.
        # Actual call arguments are required evidence, not just final state.
        # I will use trace output to check that the selected item and outfit survive handoffs.
        "name": "selected item and outfit survive handoffs",
        "query": "vintage graphic tee under $30",
        "wardrobe": "example",
        "criterion": 3,
    },
    {
        # The agent runner repeats this query five times with caching disabled.
        # Score each card against that run's fit_card_inputs: <=60 words,
        # supported item detail, vibe, styling idea, and no invented ownership.
        # Each generated outfit can differ; use that run's saved inputs.
        "name": "fit card stays short and grounded",
        "query": "vintage graphic tee under $30",
        "wardrobe": "example",
        "criterion": 4,
    },
    {
        # lst_006 is owned; skip it and select the next result, lst_002.
        "name": "owned first result advances to unowned result",
        "query": "vintage graphic tee under $30",
        "wardrobe": "first_match_owned",
        "criterion": 5,
    },
    {
        # Criterion 5 also requires stopping when every match is owned.
        "name": "all matching results owned stops early",
        "query": "vintage graphic tee under $30",
        "wardrobe": "all_matches_owned",
        "criterion": 5,
    },
]

# Freeze the fixture IDs rather than deriving ownership from each live search.
OWNED_LISTING_IDS = {
    "first_match_owned": ("lst_006",),
    "all_matches_owned": (
        "lst_006", "lst_002", "lst_015", "lst_017",
        "lst_033", "lst_011", "lst_012", "lst_030",
    ),
}
WARDROBES = ("example", "empty", *OWNED_LISTING_IDS)


def get_wardrobe(name: str) -> dict:
    """Build a fresh evaluation wardrobe without changing saved user data."""
    from utils.data_loader import (
        get_empty_wardrobe, get_example_wardrobe, load_listings,
    )

    if name == "empty":
        return get_empty_wardrobe()
    if name == "example":
        return get_example_wardrobe()
    if name not in OWNED_LISTING_IDS:
        raise ValueError(f"Unknown evaluation wardrobe: {name!r}")

    wardrobe = get_example_wardrobe()
    listings = {item["id"]: item for item in load_listings()}
    for listing_id in OWNED_LISTING_IDS[name]:
        listing = listings[listing_id]
        wardrobe["items"].append({
            "id": f"owned_{listing_id}",
            "name": listing["title"],
            "category": listing["category"],
            "colors": listing["colors"][:1],
            "style_tags": list(listing["style_tags"]),
            "notes": "Owned evaluation fixture; size and price are omitted.",
        })
    return wardrobe


def validate() -> list[str]:
    """Complain about anything malformed, before a long run rather than during."""
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("query", "").strip():
            problems.append(f"scenario {i} has no query")
        if scenario.get("wardrobe") not in WARDROBES:
            problems.append(
                f"scenario {i} has wardrobe {scenario.get('wardrobe')!r} — "
                f"it should be one of {WARDROBES}"
            )
    return problems
