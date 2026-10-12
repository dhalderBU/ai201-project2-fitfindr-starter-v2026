"""
Utility functions for loading the mock listings dataset and wardrobe schema.
Use these in your tool implementations to access the data without re-reading
the files each time.
"""

import json
import os
import tempfile
from typing import Optional

# Resolve the path to the data directory relative to this file
_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def load_listings() -> list[dict]:
    """
    Load all mock listings from the dataset.

    Returns:
        A list of listing dictionaries. Each listing has the following fields:
        - id (str)
        - title (str)
        - description (str)
        - category (str): one of tops, bottoms, outerwear, shoes, accessories
        - style_tags (list[str])
        - size (str)
        - condition (str): excellent, good, or fair
        - price (float)
        - colors (list[str])
        - brand (str or None)
        - platform (str): depop, thredUp, or poshmark
    """
    path = os.path.join(_DATA_DIR, "listings.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_wardrobe_schema() -> dict:
    """
    Load the wardrobe schema, including the example wardrobe and empty template.

    Returns:
        A dictionary containing:
        - schema: the field definitions for a wardrobe item
        - example_wardrobe: a sample wardrobe with 10 items
        - empty_wardrobe: a starting template for a new user
    """
    path = os.path.join(_DATA_DIR, "wardrobe_schema.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _wardrobe(name: str) -> dict:
    """
    Pull one wardrobe out of the schema file, without the documentation keys.

    The JSON uses underscore-prefixed keys (_description, _note) to explain
    itself to a human reader. Those are notes about the file, not part of a
    wardrobe, and stripping them here means both wardrobes below come back
    the same shape. Otherwise the empty one carries an extra _note key, and a
    tool that formats the whole dict into a prompt would send the model a
    sentence about templates.
    """
    wardrobe = load_wardrobe_schema()[name]
    return {k: v for k, v in wardrobe.items() if not k.startswith("_")}


def get_example_wardrobe() -> dict:
    """
    Convenience function — returns just the example wardrobe items list.

    Returns:
        A wardrobe dict with an 'items' key containing a list of wardrobe items.
    """
    return _wardrobe("example_wardrobe")


def get_empty_wardrobe() -> dict:
    """
    Convenience function — returns an empty wardrobe template.

    Returns:
        A wardrobe dict with an empty 'items' list. Same shape as the example
        wardrobe — the only difference is that 'items' is empty.
    """
    return _wardrobe("empty_wardrobe")


# --- Style memory: one editable wardrobe saved between CLI runs ---

WARDROBE_CATEGORIES = ("tops", "bottoms", "outerwear", "shoes", "accessories")


def wardrobe_path() -> str:
    """Return the local storage path; an environment override isolates tests."""
    default = os.path.join(_DATA_DIR, "..", ".fitfindr", "wardrobe.json")
    return os.path.abspath(os.path.expanduser(
        os.environ.get("FITFINDR_WARDROBE_PATH", default)
    ))


def _validate_wardrobe(wardrobe: dict) -> None:
    """Reject malformed memory before passing it to the agent or saving it."""
    # The outer structure must be a dictionary containing an "items" list.
    # An empty list is valid: the user may have removed every item.
    if not isinstance(wardrobe, dict) or not isinstance(wardrobe.get("items"), list):
        raise ValueError("Wardrobe must contain an 'items' list.")

    # Track IDs already encountered so each item can be identified uniquely.
    seen_ids = set()
    for item in wardrobe["items"]:
        # Each list entry must contain named fields, rather than plain text.
        if not isinstance(item, dict):
            raise ValueError("Each wardrobe item must be an object.")

        # Both ID and name must be strings with at least one non-space character.
        for field in ("id", "name"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise ValueError(f"Each wardrobe item needs a nonblank {field}.")

        # A repeated ID would make operations such as removal ambiguous.
        if item["id"] in seen_ids:
            raise ValueError(f"Duplicate wardrobe ID: {item['id']}.")
        seen_ids.add(item["id"])

        # Restrict categories to those understood by the listings and agent.
        if item.get("category") not in WARDROBE_CATEGORIES:
            raise ValueError(f"Category must be one of: {', '.join(WARDROBE_CATEGORIES)}.")

        # Colors and style tags must be lists, even when there is only one value.
        # Empty lists are allowed, but any supplied entries must be nonblank text.
        for field in ("colors", "style_tags"):
            values = item.get(field)
            if not isinstance(values, list) or any(
                not isinstance(value, str) or not value.strip() for value in values
            ):
                raise ValueError(f"Item {field} must be a list of nonblank strings.")

        # Notes are optional: they may be omitted, None (JSON null), or a string.
        if item.get("notes") is not None and not isinstance(item["notes"], str):
            raise ValueError("Item notes must be text or null.")

    # Successful validation returns None. Invalid data raises ValueError above;
    # this function checks the wardrobe without changing its contents.


def save_wardrobe(wardrobe: dict) -> None:
    """Validate and replace the saved wardrobe without a partial JSON write."""
    _validate_wardrobe(wardrobe)
    path = wardrobe_path()
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=directory, suffix=".tmp", delete=False
        ) as temporary:
            temporary_path = temporary.name
            json.dump(wardrobe, temporary, indent=2, ensure_ascii=False)
            temporary.write("\n")
        os.replace(temporary_path, path)
    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.remove(temporary_path)


def load_wardrobe() -> tuple[dict, str]:
    """Load saved memory, initializing once from the existing example.

    Return (wardrobe, source), where source is 'initialized' or 'saved'. An
    existing empty wardrobe is valid memory and is never refilled automatically.
    Invalid memory raises a readable error and is not overwritten.
    """
    path = wardrobe_path()
    try:
        with open(path, encoding="utf-8") as saved:
            wardrobe = json.load(saved)
    except FileNotFoundError:
        wardrobe = get_example_wardrobe()
        save_wardrobe(wardrobe)
        return wardrobe, "initialized"
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise ValueError(f"Cannot read saved wardrobe at {path}. Fix its JSON and retry.") from exc
    try:
        _validate_wardrobe(wardrobe)
    except ValueError as exc:
        raise ValueError(f"Invalid saved wardrobe at {path}: {exc} Fix it and retry.") from exc
    return wardrobe, "saved"


def add_wardrobe_item(
    name: str,
    category: str,
    colors: list[str],
    style_tags: Optional[list[str]] = None,
    notes: Optional[str] = None,
) -> tuple[dict, int]:
    """Add an owned piece, save it, and return (new item, total item count)."""
    # Trim surrounding spaces and build an item in the expected wardrobe format.
    # "pending" is a temporary ID for validation; the saved ID is assigned below.
    item = {
        "id": "pending",
        "name": name.strip(),
        "category": category,
        "colors": [color.strip() for color in colors],
        "style_tags": [tag.strip() for tag in (style_tags or [])],
        "notes": notes.strip() if notes else None,
    }
    # Check the input before loading or initializing the saved wardrobe.
    _validate_wardrobe({"items": [item]})
    wardrobe, _ = load_wardrobe()

    # Reject an item with the same name, category, and colors. Ignore differences
    # in name spacing/capitalization and color capitalization/order.
    for existing in wardrobe["items"]:
        if (
            " ".join(existing["name"].split()).casefold()
            == " ".join(item["name"].split()).casefold()
            and existing["category"] == item["category"]
            and {color.casefold() for color in existing["colors"]}
            == {color.casefold() for color in item["colors"]}
        ):
            raise ValueError(f"This item is already saved as {existing['id']}.")

    # Extract the numeric part of IDs such as "w_010" -> 10. Ignore IDs that
    # do not follow the "w_" plus digits format.
    used_numbers = [
        int(existing["id"][2:])
        for existing in wardrobe["items"]
        if existing["id"].startswith("w_") and existing["id"][2:].isdecimal()
    ]
    # Add one to the highest existing number; an empty wardrobe starts at 1.
    # :03d pads to at least three digits, so 11 becomes "w_011".
    # Because only current IDs are checked, a deleted highest ID may be reused.
    item["id"] = f"w_{max(used_numbers, default=0) + 1:03d}"

    # Append to the same wardrobe and persist the change for future runs.
    wardrobe["items"].append(item)
    save_wardrobe(wardrobe)
    # Return the assigned item and updated count so the CLI can confirm the save.
    return item, len(wardrobe["items"])


def remove_wardrobe_item(item_id: str) -> tuple[dict, int]:
    """Remove an owned piece by ID, save, and return (removed item, count)."""
    wardrobe, _ = load_wardrobe()
    for index, item in enumerate(wardrobe["items"]):
        if item["id"] == item_id:
            wardrobe["items"].pop(index)
            save_wardrobe(wardrobe)
            return item, len(wardrobe["items"])
    raise ValueError(f"No wardrobe item has ID {item_id!r}. Run 'python app.py wardrobe list'.")


# --- Quick sanity check ---
if __name__ == "__main__":
    listings = load_listings()
    print(f"Loaded {len(listings)} listings.")
    print(f"First listing: {listings[0]['title']} — ${listings[0]['price']}")

    wardrobe = get_example_wardrobe()
    print(f"\nExample wardrobe has {len(wardrobe['items'])} items.")
    print(f"First item: {wardrobe['items'][0]['name']}")
