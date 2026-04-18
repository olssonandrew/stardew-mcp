#!/usr/bin/env python3
"""
Stardew Valley MCP Server

Provides tools for looking up Stardew Valley game reference data from
bundled markdown files, plus live search and fetch against the official
Stardew Valley wiki (https://stardewvalleywiki.com, CC BY-NC-SA 3.0).
"""

import json
import os
import re
from pathlib import Path

import httpx
from fastmcp import FastMCP
from html_to_markdown import convert

# ---------------------------------------------------------------------------
# Server setup
# ---------------------------------------------------------------------------

mcp = FastMCP("stardew_mcp")

REFERENCES_DIR = Path(__file__).parent / "references"

WIKI_API = "https://stardewvalleywiki.com/mediawiki/api.php"
USER_AGENT = (
    "StardewMCP/1.0 (educational demo; contact: github.com/your-handle/stardew-mcp)"
)
HTTP_TIMEOUT = 20.0

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


_HTML_TAG_RE = re.compile(r"<[^>]+>")


def html_to_markdown(html: str, title: str) -> str:
    """Convert wiki HTML to markdown and prepend a title heading."""
    markdown = convert(html).content.strip()
    return f"# {title}\n\n{markdown}" if markdown else f"# {title}"


# ---------------------------------------------------------------------------
# Bundled reference tools
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
# Live wiki tools
# ---------------------------------------------------------------------------


@mcp.tool(
    name="stardew_search_wiki",
    annotations={
        "title": "Search the Stardew Valley Wiki",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def stardew_search_wiki(query: str, limit: int = 5) -> str:
    """Search the official Stardew Valley wiki for pages matching a query.

    Use this when the bundled reference files don't cover something — new
    patches, obscure lore, edge cases, or anything added after these files
    were packaged. Returns matching page titles with short text snippets.
    Pass a title to stardew_fetch_wiki_page to read the full page.

    Args:
        query (str): Free-text search query (e.g. "ginger island", "stardrop").
        limit (int): Maximum results to return (default 5, max 20).

    Returns:
        str: JSON array of {"title": str, "snippet": str} objects.
    """
    limit = max(1, min(int(limit), 20))
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": limit,
        "srprop": "snippet",
        "format": "json",
    }
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            resp = await client.get(
                WIKI_API, params=params, headers={"User-Agent": USER_AGENT}
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as exc:
        raise RuntimeError(f"Wiki search request failed: {exc}") from exc

    if "error" in data:
        code = data["error"].get("code", "error")
        info = data["error"].get("info", "Unknown error")
        raise RuntimeError(f"Wiki search error ({code}): {info}")

    results = []
    for hit in data.get("query", {}).get("search", []):
        raw_snippet = hit.get("snippet", "")
        clean_snippet = " ".join(_HTML_TAG_RE.sub("", raw_snippet).split())
        results.append({"title": hit["title"], "snippet": clean_snippet})

    return json.dumps(results, indent=2)


@mcp.tool(
    name="stardew_fetch_wiki_page",
    annotations={
        "title": "Fetch a Stardew Valley Wiki Page",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def stardew_fetch_wiki_page(title: str) -> str:
    """Fetch the full text of a Stardew Valley wiki page by title.

    Returns the live contents of the page, converted to clean markdown.
    Follows redirects automatically. Use stardew_search_wiki first if you're
    not sure of the exact title.

    Args:
        title (str): The exact wiki page title (e.g. "Parsnip", "Abigail",
            "Ginger Island").

    Returns:
        str: Markdown content of the page, prefixed with the resolved title.
    """
    params = {
        "action": "parse",
        "page": title,
        "prop": "text",
        "redirects": 1,
        "format": "json",
    }
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            resp = await client.get(
                WIKI_API, params=params, headers={"User-Agent": USER_AGENT}
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as exc:
        raise RuntimeError(f"Wiki page request failed: {exc}") from exc

    if "error" in data:
        code = data["error"].get("code", "error")
        info = data["error"].get("info", "Unknown error")
        raise ValueError(f"Wiki fetch failed ({code}): {info}")

    parse = data.get("parse", {})
    html = parse.get("text", {}).get("*", "")
    if not html:
        raise ValueError(f"No content returned for page: {title}")

    resolved_title = parse.get("title", title)
    return html_to_markdown(html, resolved_title)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    mcp.run(transport="streamable-http", host=host, port=port)
