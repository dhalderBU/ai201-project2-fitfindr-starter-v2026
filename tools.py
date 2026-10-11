"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

All three are stubs right now. They run and they do nothing — that's the
starting position and it's deliberate.

⚠️ Before you write any of them, fill in the **Tool Inventory** section of your
README (Milestone 2). Four lines per tool: what it does, each input with its
type, exactly what it returns, and what it returns when it has nothing to give.
That last line is what your loop branches on. "Returns a list" earns nothing —
the description has to say what is *in* the list.
"""

import config  # noqa: F401 — you'll use this in search_listings
import trace
from generate import generate
from utils.data_loader import load_listings
import re

# ── Tool 1: search_listings ───────────────────────────────────────────────────
_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",

}

_UNIVERSAL_SIZES = {"ONE SIZE", "FREE SIZE", "OS", "OSFA"}


def _keywords(test: str) -> set[str]:
    """Return lowercase, non-stopword words from a string."""
    return {
        word
        for word in re.findall(r"[a-z0-9]+", (test or "").lower())
        if word not in _STOPWORDS and len(word) > 1
    }


def _size_tokens(size: str) -> set[str]:
    """Return uppercase size parts, excluding parenthetical notes."""
    cleaned = re.sub(r"\([^)]*\)", "", size or "")
    parts = [part.strip().upper() for part in cleaned.split("/")]
    return {part for part in parts if part}


def _size_matches(wanted: str, listing_size: str) -> bool:
    """Return whether every requested size part appears in a listing size."""
    wanted_tokens = _size_tokens(wanted)
    listing_tokens = _size_tokens(listing_size)
    if not wanted_tokens:
        return True
    if listing_tokens & _UNIVERSAL_SIZES:
        return True
    return wanted_tokens <= listing_tokens


def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    This is the tool that doesn't call the model, which makes it the easiest one
    to test and the one to move onto MCP in unit 4.

    Args:
        description: keywords describing what the user wants
                     (e.g. "vintage graphic tee").
        size:        a size string to filter by, or None to skip size filtering.
                     Match case-insensitively — "M" should match "S/M".

                     ⚠️ Read the sizes in the data before you reach for a plain
                     substring test. `"s" in "us 9"` is True, and so is
                     `"l" in "xl"`. A filter that returns shoes when someone
                     asked for a small top reads like a broken search, and it
                     will quietly cost you in unit 4 when you test criterion 1.
                     What counts as a size match is part of your spec — decide
                     it and write it into your Tool Inventory.
        max_price:   maximum price, inclusive, or None to skip price filtering.

    Returns:
        A list of matching listing dicts, best match first.
        **Returns an empty list when nothing matches — an empty list, not None,
        and not an exception.** Your loop branches on this.

    Each listing dict has these fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand (str or None), platform

    Note that `brand` is None for most listings. That is deliberate and
    realistic — thrift listings often have no brand. If something you write
    assumes a brand is always there, you will find out in unit 4.

    TODO:
        1. Load every listing with load_listings().
        2. Filter by max_price and by size, when each is provided.
        3. Score what's left by keyword overlap with `description`.
        4. Drop anything scoring zero.
        5. Sort by score, highest first, and return the listing dicts —
           at most config.SEARCH_RESULT_LIMIT of them.

    Test it from a terminal before you move on:
        python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
    """
    keywords = _keywords(description)
    matches: list[tuple[int, dict]] = []

    for listing in load_listings():
        if max_price is not None and listing["price"] > max_price:
            continue

        if size and not _size_matches(size, str(listing["size"])):
            continue

        listing_words = _keywords(listing["description"])
        score = len(keywords & listing_words)
        if score:
            matches.append((score, listing))

    matches.sort(key=lambda match: match[0], reverse=True)
    return [
        listing
        for _, listing in matches[: config.SEARCH_RESULT_LIMIT]
    ]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    This one calls the model, through `generate()`. You don't need to think
    about rate limits — the adapter handles pacing for you.

    Args:
        new_item: a listing dict — the item the user is considering.
        wardrobe: a wardrobe dict with an 'items' key holding a list of items.
                  **It may be empty.** Handle that.

    Returns:
        A non-empty string with outfit suggestions.
        With an empty wardrobe, return general styling advice rather than
        raising or returning "". Unit 4 has you trigger the empty wardrobe on
        purpose, so decide now what it should do.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If it is, ask the model for general styling ideas for this item.
        3. If it isn't, format the wardrobe items into the prompt and ask for
           specific combinations naming pieces the user already owns.
        4. Return the model's response.

    Test it from a terminal before you move on:
        python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
    """
    items = wardrobe.get("items", [])
    item_details = (
        f"Title: {new_item.get('title', 'Unknown item')}\n"
        f"Description: {new_item.get('description', '')}\n"
        f"Category: {new_item.get('category', '')}\n"
        f"Style tags: {', '.join(new_item.get('style_tags', []))}\n"
        f"Colors: {', '.join(new_item.get('colors', []))}\n"
        f"Price: ${new_item.get('price', 'unknown')}"
    )

    if not items:
        prompt = (
            "Suggest one or two wearable outfits for this thrifted item. "
            "The user has no saved wardrobe, so recommend generally available "
            "pieces and explain why they work together.\n\n"
            f"New item:\n{item_details}"
        )
        system = (
            "Give practical, specific styling advice. Mention silhouettes, "
            "colors, shoes, and accessories when useful. Keep the response "
            "concise and non-empty. Never describe the thrifted item as "
            "something the user already owns; when the user has no saved "
            "wardrobe, treat it as a suggested purchase."
        )
    else:
        wardrobe_details = "\n".join(
            (
                f"- {item.get('name', 'Unnamed item')} "
                f"(category: {item.get('category', 'unknown')}; "
                f"colors: {', '.join(item.get('colors', []))}; "
                f"style: {', '.join(item.get('style_tags', []))}; "
                f"notes: {item.get('notes') or 'none'})"
            )
            for item in items
        )
        prompt = (
            "Suggest one or two outfits using the new thrifted item and only "
            "pieces from the user's wardrobe below. Name the wardrobe pieces "
            "directly and explain the styling briefly.\n\n"
            f"New item:\n{item_details}\n\n"
            f"User wardrobe:\n{wardrobe_details}"
        )
        system = (
            "Use the user's existing wardrobe items rather than inventing "
            "replacement pieces. Give practical, specific, concise outfit "
            "suggestions. Only describe the new thrifted item as owned if the "
            "user's wardrobe explicitly includes it; otherwise frame it as a "
            "purchase idea rather than something they already own."
        )

    return generate(prompt, system=system)
    


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.

    This calls the model too.

    Args:
        outfit:   the outfit suggestion string from suggest_outfit().
        new_item: the listing dict for the item.

    Returns:
        A two-to-four sentence caption.
        If `outfit` is empty or whitespace, return a descriptive message rather
        than raising.

    The caption should read like a real post rather than a product description,
    mention the item and its price and platform once each, and be specific about
    the vibe.

    It should also come out **differently for different inputs**. If you run
    this three times on the same item and get three word-for-word identical
    strings, it's one of two things, and both are near the top of `config.py`:

        • CACHE_ENABLED — the adapter handed back an answer it already had
        • TEMPERATURE   — at 0.0 the model gives the same words every time

    TODO:
        1. Guard against an empty or whitespace-only `outfit`.
        2. Build a prompt with the item details and the outfit.
        3. Call generate() and return the response.

    Test it from a terminal before you move on:
        python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
    """
    if not outfit.strip():
        return "I cannot create a fit card until an outfit suggestion is provided."

    ownership_markers = (
        "already own",
        "already owns",
        "already in my wardrobe",
        "already in my closet",
        "in my wardrobe",
        "in my closet",
        "already in my rotation",
        "my own",
    )
    outfit_lower = outfit.lower()
    explicitly_owned = any(marker in outfit_lower for marker in ownership_markers)

    title = new_item.get("title", "this thrifted find")
    price = new_item.get("price", "unknown")
    platform = new_item.get("platform", "the marketplace")
    description = new_item.get("description", "")
    style_tags = ", ".join(new_item.get("style_tags", []))

    ownership_rule = (
        "The outfit explicitly identifies the item as already owned or in the "
        "user's wardrobe, so it is okay to describe it as owned."
        if explicitly_owned
        else "Do not present the item as something the user already owns. "
        "Treat it as a suggested purchase or styling idea unless the outfit "
        "explicitly says otherwise."
    )

    prompt = (
        "Write a social-media fit-card caption for the thrifted item and outfit "
        "below. Make it two to four sentences, sound like a real person "
        "celebrating a find, and describe the outfit's specific vibe. Keep the "
        "caption to 60 words or fewer, counting hashtags as words. Mention "
        f"the item title '{title}', the price '${price}', and the platform "
        f"'{platform}' exactly once each. Do not write a product listing or "
        "invent details that are not provided.\n\n"
        f"Ownership rule: {ownership_rule}\n\n"
        f"Item: {title}\n"
        f"Description: {description}\n"
        f"Style tags: {style_tags or 'none provided'}\n"
        f"Price: ${price}\n"
        f"Platform: {platform}\n"
        f"Outfit suggestion: {outfit.strip()}"
    )
    system = (
        "Write one polished, concise caption in a warm, personal voice. "
        "Keep it to 60 words or fewer. Return only the caption."
    )
    for attempt in range(config.MAX_RETRIES):
        card = generate(prompt, system=system, cache=False).strip()
        if not card:
            trace.step(
                "create_fit_card retry",
                returned="blank caption",
                note=(
                    f"attempt {attempt + 1}/{config.MAX_RETRIES}; "
                    "retrying because the model returned blank output"
                ),
            )
            if attempt == config.MAX_RETRIES - 1:
                raise ValueError(
                    "create_fit_card returned a blank caption after "
                    f"{config.MAX_RETRIES} attempts"
                )
            continue

        word_count = len(card.split())
        if word_count > 60:
            trace.step(
                "create_fit_card length check",
                returned={"word_count": word_count, "limit": 60},
                note="caption exceeded 60 words; trimming to the first 60 words",
            )
            card = " ".join(card.split()[:60])
        return card

    raise RuntimeError("create_fit_card exited without producing a caption")
