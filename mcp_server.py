"""
Your MCP server. ← UNIT 4, MILESTONE 1

Right now your tools only exist inside your own program. Nothing else can reach
them. MCP is an agreed shape you wrap a tool in so that anything speaking the
same protocol can call it — your agent today, a different agent tomorrow,
someone else's app after that.

**You're moving one tool. Not three.** The point is to see the seam.
`search_listings` is the one to move: it doesn't call the model, so nothing is
slow and nothing changes between runs while you're learning the shape.

    python mcp_server.py        starts the server (it will just sit there — that's right)
    python mcp_client.py        asks the server what it offers

─────────────────────────────────────────────────────────────────────────────
TODO — register one tool.

Uncomment the block below and fill it in. Three things matter:

  1. **The name.** Exactly what your agent will ask for.

  2. **The description.** This is the part that isn't code and matters most.
     Write it before you look at the example. You are not writing it for your
     agent — you're writing it for an agent someone else builds, that will
     never see your implementation. That isn't hypothetical; it's what every
     MCP server on the registry is.

     Two things to get right: name units and types ("price" is ambiguous,
     "max_price, in whole dollars" isn't), and state the empty case. Last unit
     the empty case was on your spec sheet for your loop's benefit. Here it's
     part of a published contract.

  3. **The typed inputs.** These come straight from your Tool Inventory. If the
     types here don't match your README, one of the two is wrong — fix it.

Then point your agent at it. In `run_agent()`, swap the direct call:

    results = search_listings(description, size, max_price)

for the MCP one:

    from mcp_client import call_tool
    results = call_tool("search_listings", {
        "description": description,
        "size": size,
        "max_price": max_price,
    })

**What comes back should not change.** If it does, that difference is your
first clue about what your tool was really returning before.

🛑 Stop rule: if this isn't connecting after 40 minutes, stop. Keep your direct
call, and write down in your README exactly where it broke — the error text and
the last thing that worked. Then carry on to Milestone 2. Everything after this
works with a direct call, and **a documented failure earns the point in full.**
─────────────────────────────────────────────────────────────────────────────
"""

from contextlib import redirect_stdout
import sys
import os
from copy import deepcopy

from mcp.server.fastmcp import FastMCP

import trace as fitfindr_trace
import config
from tools import suggest_outfit as _suggest_outfit_impl
from tools import search_listings as _search_listings_impl  # noqa: F401 — you'll use this below

# log_level="WARNING" keeps the server from printing an INFO line for every
# request. Without it your terminal fills with "Processing request of type
# CallToolRequest" and the output you actually care about scrolls away.
mcp = FastMCP("fitfindr", log_level="WARNING")


# ── TODO: uncomment and fill this in ──────────────────────────────────────────
#
@mcp.tool()
def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search for listings matching the given criteria based on description, size, and maximum price.
    """
    # MCP uses stdout for its protocol messages, so send trace output to stderr.
    with redirect_stdout(sys.stderr):
        fitfindr_trace.start_trace(enabled=os.getenv("AI201_MCP_TRACE", "0") == "1",
                                  minimal=os.getenv("AI201_MCP_TRACE_MINIMAL", "0") == "1")
        fitfindr_trace.step(
            "[MCP:SERVER:SEARCH] search_listings received",
            inputs={
                "description": description,
                "size": size,
                "max_price": max_price,
            },
            note="received request; executing listing search",
        )
        results = _search_listings_impl(description, size, max_price)
        fitfindr_trace.step("[MCP:SERVER:SEARCH] search_listings completed",
                           returned=results, note=f"matches={len(results)}")
    return results
#
# ──────────────────────────────────────────────────────────────────────────────
#
# Two notes on the block above.
#
# The registered name is the *function* name — so the block above registers
# "search_listings", which is exactly what call_tool("search_listings", ...)
# asks for. That is also why the import at the top of this file brings the real
# implementation in under an alias: without it, the registered function and the
# one it calls would be the same name, and the tool would call itself.
#
# FastMCP builds the input schema from your type hints, which is why the hints
# are not optional here. `description: str` becomes a required string;
# `max_price: float | None = None` becomes an optional number. Getting these
# wrong is the most common reason a call is rejected.


@mcp.tool()
def suggest_outfit(new_item: dict, wardrobe: dict) -> dict:
    """Suggest outfits for a complete listing and wardrobe.items.

    Empty wardrobes receive general purchase suggestions. Returns outfit text,
    received input snapshots, and the server's cache setting for handoff checks.
    """
    received = deepcopy({"new_item": new_item, "wardrobe": wardrobe})
    with redirect_stdout(sys.stderr):
        fitfindr_trace.start_trace(enabled=os.getenv("AI201_MCP_TRACE", "0") == "1",
                                  minimal=os.getenv("AI201_MCP_TRACE_MINIMAL", "0") == "1")
        fitfindr_trace.step(
            "[MCP:SERVER:OUTFIT] suggest_outfit received",
            inputs={"new_item": new_item, "wardrobe": wardrobe},
            note="received request; executing outfit suggestion",
        )
        outfit = _suggest_outfit_impl(new_item, wardrobe)
        fitfindr_trace.step("[MCP:SERVER:OUTFIT] suggest_outfit completed", returned=outfit,
                           note=f"characters={len(outfit)}")
    return {"outfit": outfit, "received": received,
            "cache_enabled": config.CACHE_ENABLED}


if __name__ == "__main__":
    mcp.run()
