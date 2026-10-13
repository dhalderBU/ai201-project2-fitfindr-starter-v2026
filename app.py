#!/usr/bin/env python3
"""
FitFindr — command line.

    python app.py ask 'vintage graphic tee under $30, size M'
    python app.py ask                     keep asking until you quit
    python app.py ask --empty-wardrobe    run as a user with nothing saved
    python app.py listings                browse the data  (Milestone 1)
    python app.py fields                  what fields a listing has
    python app.py examples                queries worth trying, including a dud
    python app.py wardrobe list           view your saved wardrobe
    python app.py wardrobe add --name 'Black jeans' --category bottoms --colors black
    python app.py wardrobe remove --id w_011

Add --trace to any `ask` to print the loop step by step.

⚠️ Quote your query with SINGLE quotes. In PowerShell, "under $30" in double
quotes silently becomes "under " — PowerShell reads $30 as a variable and
substitutes nothing, so you search with no price ceiling and get no error
telling you why. Single quotes are literal in PowerShell, bash and zsh alike.
"""

import argparse
import sys
import trace

import config

# Every query here except the last one has something real to find in
# data/listings.json. If you add your own, check it against the data first — a
# query that finds nothing because the item doesn't exist looks exactly like a
# search tool that's broken.
EXAMPLE_QUERIES = [
    "vintage graphic tee under $30",
    "90s track jacket in size M",
    "silk slip dress in midi length under $40",
    "platform sneakers size 8",
    "denim jacket under $50",
    "designer ballgown size XXS under $5",   # matches nothing, on purpose
]


def cmd_fields(args):
    """Milestone 1 — you can't filter on a field that isn't there."""
    from utils.data_loader import load_listings, get_example_wardrobe
    # adding a trace and try .. remove trace ... Deb
    #trace.step("cmd_dh fields", inputs=args, returned=None)

    listing = load_listings()[0]
    print("A listing has these fields:\n")
    for key, value in listing.items():
        shown = str(value)
        if len(shown) > 58:
            shown = shown[:58] + "…"
        print(f"  {key:<14} {type(value).__name__:<6} {shown}")

    item = get_example_wardrobe()["items"][0]
    print("\nA wardrobe item has these fields:\n")
    for key, value in item.items():
        shown = str(value)
        if len(shown) > 58:
            shown = shown[:58] + "…"
        print(f"  {key:<14} {type(value).__name__:<6} {shown}")

    print(
        "\nThese are what search_listings can filter on. Read a few whole "
        "listings\nwith `python app.py listings` before you write it."
    )


def cmd_listings(args):
    """Milestone 1 — read the data before you write tools against it."""
    from utils.data_loader import load_listings

    listings = load_listings()

    if args.full:
        import json
        for listing in listings[: args.n]:
            print(json.dumps(listing, indent=2))
            print()
        return

    print(f"{len(listings)} listings.\n")
    print(f"{'id':<6}{'price':>8}  {'size':<22}{'platform':<11}title")
    print("-" * 92)
    for listing in listings[: args.n]:
        print(
            f"{str(listing['id']):<6}"
            f"{listing['price']:>8.2f}  "
            f"{str(listing['size']):<22}"
            f"{listing['platform']:<11}"
            f"{listing['title'][:38]}"
        )
    if len(listings) > args.n:
        print(f"\n… {len(listings) - args.n} more. Use -n {len(listings)} to see them all.")
    print("\nRead five or six all the way through: python app.py listings --full -n 6")


def cmd_examples(args):
    print("Queries worth trying:\n")
    for query in EXAMPLE_QUERIES[:-1]:
        print(f"  python app.py ask '{query}'")
    print(f"\nAnd one the data cannot match — this is the empty-search branch:\n")
    print(f"  python app.py ask '{EXAMPLE_QUERIES[-1]}'")
    print(
        "\nSingle quotes on purpose. In PowerShell a query in \"double quotes\"\n"
        "loses the $30 — it gets read as a variable — and you search with no\n"
        "price ceiling, with nothing to tell you it happened."
    )


def _ask_one(query, wardrobe, use_trace, wardrobe_source="provided"):
    from agent import run_agent
    import trace as trace_module

    trace_module.start_trace(enabled=bool(use_trace), minimal=use_trace == "minimal")
    trace_module.step(
        "wardrobe memory",
        returned=f"source={wardrobe_source}; items={len(wardrobe['items'])}",
        note="; ".join(f"{item.get('id', '?')}: {item.get('name', '?')}"
                       for item in wardrobe["items"]),
    )

    session = run_agent(query, wardrobe)
    session["wardrobe_source"] = wardrobe_source

    print()
    if session.get("search_notice"):
        print(f"  {session['search_notice']}")
    comparison = session["price_comparison"]
    if comparison:
        if comparison["average_price"] is None:
            print("  Price comparison: no other listings in this category.")
        else:
            print(
                f"  Category average: ${comparison['average_price']:.2f} "
                f"across {comparison['comparison_count']} other "
                f"{comparison['category']} listings in this dataset."
            )
        if session["price_warning"]:
            print(f"  Price warning: {session['price_warning']}")
        print()
    if session["error"]:
        print(f"  {session['error']}")
    else:
        item = session["selected_item"] or {}
        print(f"  Found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
        print()
        print(f"  Outfit:   {session['outfit_suggestion']}")
        print()
        print(f"  Fit card: {session['fit_card']}")
    print()

    if use_trace:
        text = trace_module.get_trace()
        if not text:
            print(
                "  (--trace printed nothing. You haven't added trace.step() calls to\n"
                "   run_agent() yet — that's unit 4, Milestone 2.)\n"
            )
    return session


def cmd_ask(args):
    from utils.data_loader import get_empty_wardrobe, load_wardrobe
    import generate

    if args.empty_wardrobe:
        wardrobe, source = get_empty_wardrobe(), "empty override"
        print("(running with an empty wardrobe; saved wardrobe unchanged)")
    else:
        wardrobe, source = load_wardrobe()
        action = "Initialized and saved" if source == "initialized" else "Loaded saved"
        print(f"({action} wardrobe: {len(wardrobe['items'])} items)")

    try:
        if args.query:
            _ask_one(args.query, wardrobe, args.trace, source)
        else:
            print("Ask for something, or press Enter on an empty line to quit.\n")
            while True:
                try:
                    query = input("> ").strip()
                except (EOFError, KeyboardInterrupt):
                    print()
                    break
                if not query:
                    break
                # Pick up edits made by a separate wardrobe command between queries.
                if not args.empty_wardrobe:
                    wardrobe, source = load_wardrobe()
                _ask_one(query, wardrobe, args.trace, source)
    finally:
        print(generate.usage())


def cmd_wardrobe(args):
    # argparse stores the chosen subcommand (add, remove, or list) in
    # args.wardrobe_action. The helpers below manage the same saved wardrobe.
    from utils.data_loader import (
        add_wardrobe_item, load_wardrobe, remove_wardrobe_item,
    )

    if args.wardrobe_action == "add":
        # Pass the CLI values to the helper, which validates the item, assigns
        # an ID, and saves it. It returns the new item and updated item count.
        item, count = add_wardrobe_item(
            args.name, args.category, args.colors, args.style_tags, args.notes,
        )
        print(f"Added {item['id']}: {item['name']}")
        print(f"Saved wardrobe: {count} items. Future searches will use this wardrobe.")
    elif args.wardrobe_action == "remove":
        # Remove by the ID shown by add/list. The helper saves the change and
        # raises an error if that ID does not exist.
        item, count = remove_wardrobe_item(args.id)
        print(f"Removed {item['id']}: {item['name']}")
        print(f"Saved wardrobe: {count} items. Future searches will use this wardrobe.")
    else:
        # The parser permits only three actions, so this path handles "list".
        # On first use, load_wardrobe initializes and saves the existing example;
        # on later runs, it loads the user's saved additions and removals.
        wardrobe, source = load_wardrobe()
        action = "Initialized and saved" if source == "initialized" else "Loaded saved"
        print(f"{action} wardrobe: {len(wardrobe['items'])} items\n")
        # Display each item's ID so the user can select it for removal.
        for item in wardrobe["items"]:
            print(f"{item['id']}  {item['name']} | {item['category']} | "
                  f"colors: {', '.join(item['colors']) or 'unspecified'}")
        if not wardrobe["items"]:
            print("Your wardrobe is empty. Add a piece with 'python app.py wardrobe add --help'.")


def build_parser():
    from utils.data_loader import WARDROBE_CATEGORIES

    parser = argparse.ArgumentParser(
        prog="app.py",
        description="FitFindr",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_fields = sub.add_parser("fields", help="what fields the data has")
    p_fields.set_defaults(func=cmd_fields)

    p_list = sub.add_parser("listings", help="browse the listings data")
    p_list.add_argument("-n", type=int, default=15, help="how many to show")
    p_list.add_argument("--full", action="store_true", help="print whole records")
    p_list.set_defaults(func=cmd_listings)

    p_ex = sub.add_parser("examples", help="queries worth trying")
    p_ex.set_defaults(func=cmd_examples)

    # Add the top-level "wardrobe" command, then require an action after it:
    # for example, "python app.py wardrobe add". Store that action in
    # args.wardrobe_action so cmd_wardrobe can choose the correct helper.
    p_wardrobe = sub.add_parser("wardrobe", help="list, add, or remove owned clothing")
    wardrobe_sub = p_wardrobe.add_subparsers(dest="wardrobe_action", required=True)

    # "wardrobe list" needs no additional arguments.
    wardrobe_sub.add_parser("list", help="show your saved wardrobe")

    # "wardrobe add" requires a name, a supported category, and at least one color.
    p_add = wardrobe_sub.add_parser("add", help="add an owned item and save it")
    p_add.add_argument("--name", required=True)
    # choices rejects category values outside the wardrobe schema's categories.
    p_add.add_argument("--category", choices=WARDROBE_CATEGORIES, required=True)
    # nargs="+" collects one or more values into a list, e.g. --colors black white.
    # Quote multiword values such as "dark blue" to keep them as one list entry.
    p_add.add_argument("--colors", nargs="+", required=True)
    # --style-tags becomes args.style_tags; omitting it produces an empty list.
    # If the option is supplied, nargs="+" requires at least one tag.
    p_add.add_argument("--style-tags", nargs="+", default=[])
    # Notes are optional text; argparse supplies None when they are omitted.
    p_add.add_argument("--notes")

    # "wardrobe remove" identifies an existing item using its saved ID.
    p_remove = wardrobe_sub.add_parser("remove", help="remove an owned item and save")
    p_remove.add_argument("--id", required=True, help="item ID from wardrobe list")
    # All wardrobe actions share this handler. main() invokes it with args.func(args).
    p_wardrobe.set_defaults(func=cmd_wardrobe)

    p_ask = sub.add_parser("ask", help="run the agent")
    p_ask.add_argument("query", nargs="?")
    p_ask.add_argument("--trace", action="store_true", help="print the loop step by step")
    p_ask.add_argument("--trace-minimal", dest="trace", action="store_const", const="minimal",
                       help="print step names and decisions without tool payloads")
    p_ask.add_argument(
        "--empty-wardrobe",
        action="store_true",
        help="run as a user with nothing saved — one of unit 4's failure modes",
    )
    p_ask.set_defaults(func=cmd_ask)

    return parser


def main():
    args = build_parser().parse_args()
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\nStopped.")
        sys.exit(130)
    except Exception as exc:  # noqa: BLE001 — students read this, not a traceback
        print(f"\n{type(exc).__name__}: {exc}\n", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
