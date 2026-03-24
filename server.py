#!/usr/bin/env python3
"""
Stardew Valley MCP Server

Provides two tools for looking up Stardew Valley game reference data
from bundled markdown files.
"""

import json
import os
from pathlib import Path

from fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Server setup
# ---------------------------------------------------------------------------

mcp = FastMCP("stardew_mcp")

REFERENCES_DIR = Path(__file__).parent / "references"

# Registry maps filename stem -> description for the discovery tool.
FILE_REGISTRY: dict[str, str] = {
    "crops": (
        "All farmable crops — grow times, seasons, sell prices, regrow behavior, "
        "trellis crops, multi-season crops, giant crops, fertilizer interactions"
    ),
    "seasons": (
        "What's available each season — forageables, crop windows, fish, festivals, "
        "NPC schedules, season transitions"
    ),
    "fruit_trees": (
        "All fruit trees — growth stages, produce, star quality over time, placement "
        "rules, seasonal behavior"
    ),
    "artisan_goods": (
        "Artisan products made in kegs, preserves jars, cheese press, mayonnaise "
        "machine, loom, oil maker, etc. — inputs, outputs, sell prices, processing times"
    ),
    "cooking": (
        "All cooking recipes — ingredients, how to obtain each recipe, buffs/effects, "
        "energy/health restore"
    ),
    "crafting": (
        "All crafting recipes — materials, how to unlock, what each item does"
    ),
    "fish": (
        "All fish — location, season, time of day, weather conditions, difficulty, "
        "sell price, fish pond behavior"
    ),
    "mines": (
        "The mines and Skull Cavern — floor structure, monsters, ore/gem drops, "
        "elevator, ladders, bombs, Dwarf, Krobus"
    ),
    "tools": (
        "All tools — upgrade levels (copper/steel/gold/iridium), effects of each "
        "upgrade, energy costs, Clint's upgrade schedule, watering can capacity"
    ),
    "villagers": (
        "All 34 villagers — birthdays, locations, marriage eligibility, "
        "loved/liked/disliked/hated gifts, heart events, schedules"
    ),
    "gifts": (
        "Gift-giving mechanics — universal loves/likes/neutrals/dislikes/hates, "
        "gift wrapping, spouse gifts, birthday multipliers"
    ),
    "bundles": (
        "All Community Center bundles — required items, rooms, rewards, remixed "
        "bundle variants, Joja route"
    ),
    "museum": (
        "Museum donations — all artifacts and minerals, how to find each, Gunther "
        "rewards, donation milestones"
    ),
    "farmhouse": (
        "Farmhouse upgrades — cost, what each upgrade unlocks (kitchen, children's "
        "room, cellar), Robin's schedule, cask aging"
    ),
    "achievements": (
        "All in-game achievements — requirements and rewards (hats, titles)"
    ),
    "animals": (
        "Farm animals and pets — buildings required (coop, barn), animal products, "
        "friendship/happiness mechanics, Marnie's shop, incubator hatching, pigs/truffles"
    ),
    "foraging": (
        "Foraging skill — wild resources by season and location, quality mechanics, "
        "Botanist/Tracker professions, Wild Seeds, salmonberry and blackberry seasons"
    ),
    "skills": (
        "All five skills (Farming, Mining, Foraging, Fishing, Combat) — XP thresholds, "
        "level-up rewards, profession choices at levels 5 and 10, tool proficiency bonuses"
    ),
}


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool(
    name="stardew_list_files",
    annotations={
        "title": "List Stardew Valley Reference Files",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def stardew_list_files() -> str:
    """List all available Stardew Valley reference files with descriptions.

    Call this first to discover which file(s) to fetch for a given question.
    Returns a JSON array of objects, each with 'file' (the key to pass to
    stardew_fetch_file) and 'description' (what topics it covers).

    Returns:
        str: JSON array of {"file": str, "description": str} objects.

    Example output:
        [
          {"file": "crops", "description": "All farmable crops — ..."},
          {"file": "fish",  "description": "All fish — ..."},
          ...
        ]
    """
    entries = [
        {"file": key, "description": desc} for key, desc in FILE_REGISTRY.items()
    ]
    return json.dumps(entries, indent=2)


@mcp.tool(
    name="stardew_fetch_file",
    annotations={
        "title": "Fetch Stardew Valley Reference File",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def stardew_fetch_file(file: str) -> str:
    """Fetch the full contents of a Stardew Valley reference file.

    Returns exact game data (item names, sell prices, gift preferences, grow
    times, bundle requirements, etc.) from a bundled markdown reference file.
    Use stardew_list_files first to find the best file for the question, then
    pass the chosen file key here.

    Args:
        file (str): The exact reference file key.
            Use stardew_list_files to see all valid keys.

    Returns:
        str: Full markdown content of the requested reference file.

    """
    file = file.strip().lower()
    if file not in FILE_REGISTRY:
        raise ValueError(
            "Unknown reference file. Call stardew_list_files first to "
            "discover valid file keys."
        )
    path = REFERENCES_DIR / f"{file}.md"
    if not path.is_file():
        raise FileNotFoundError(f"Bundled reference file is missing: {file}.md")

    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"Could not read '{file}.md': {exc}") from exc


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    mcp.run(transport="streamable-http", host=host, port=port)
