#!/usr/bin/env python3
"""
Stardew Valley MCP Server

Provides two tools for looking up Stardew Valley game reference data
from bundled markdown files.
"""

import json
import os
from pathlib import Path
from typing import Literal

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, ConfigDict

# ---------------------------------------------------------------------------
# Server setup
# ---------------------------------------------------------------------------

mcp = FastMCP("stardew_mcp")

REFERENCES_DIR = Path(__file__).parent / "references"

# Registry maps filename stem -> description (mirrors SKILL.md index)
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
}

FileKey = Literal[
    "crops", "seasons", "fruit_trees", "artisan_goods", "cooking", "crafting",
    "fish", "mines", "tools", "villagers", "gifts", "bundles", "museum",
    "farmhouse", "achievements",
]


# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------

class FetchFileInput(BaseModel):
    """Input model for fetching a Stardew Valley reference file."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )

    file: FileKey = Field(
        ...,
        description=(
            "The reference file to fetch. Use stardew_list_files to see all "
            "available options with descriptions."
        ),
    )


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
        {"file": key, "description": desc}
        for key, desc in FILE_REGISTRY.items()
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
async def stardew_fetch_file(params: FetchFileInput) -> str:
    """Fetch the full contents of a Stardew Valley reference file.

    Returns exact game data (item names, sell prices, gift preferences, grow
    times, bundle requirements, etc.) from the bundled markdown reference file.
    Always prefer fetching the relevant file over relying on memory — the files
    contain precise, up-to-date data.

    Args:
        params (FetchFileInput):
            - file (str): The reference file key (e.g. "crops", "fish").
              Use stardew_list_files to see all valid keys.

    Returns:
        str: Full markdown content of the requested reference file.
             Returns an error string if the file cannot be read.

    Examples:
        - "What crops can I grow in summer?" -> fetch "crops", then "seasons"
        - "What does Abigail love?" -> fetch "villagers" or "gifts"
        - "How do I make wine?" -> fetch "artisan_goods"
        - "What's in the Crafts Room bundle?" -> fetch "bundles"
    """
    path = REFERENCES_DIR / f"{params.file}.md"
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return f"Error: Reference file '{params.file}.md' not found on disk."
    except OSError as e:
        return f"Error: Could not read '{params.file}.md': {e}"


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
