# Stardew MCP

`stardew-mcp` is a minimal teaching example for how MCP servers work. It demonstrates the basic shape of an MCP server: a named server, a small set of tools, and a bundle of data those tools can expose to a client.

## Functionality

This example serves read-only Stardew Valley reference content from local markdown files in `references/`. It is designed to provide a model with up-to-date Stardew Valley game data to help answer gameplay questions such as _"What gift should I give Abigail?"_ and _"Devise an ideal summer planting schedule with 2000 gold."_ It includes two simple functions:

- `stardew_list_files`: lists the available reference files and what each one covers
- `stardew_fetch_file`: returns the full markdown content for a selected reference file

## Project Structure

- `server.py`: defines the `FastMCP` server and both tools
- `references/`: bundled markdown reference files derived from Stardew Valley Wiki content
- `Dockerfile`: minimal container image for local or hosted deployment

The Horizon/FastMCP entrypoint for this repo is:

```text
server.py:mcp
```

## Local Setup

This project uses `uv` and FastMCP.

1. Install dependencies:

```bash
uv sync
```

2. Inspect the server the same way Horizon will:

```bash
uv run fastmcp inspect server.py:mcp
```

3. Run the server locally:

```bash
uv run fastmcp run server.py:mcp
```

Or, if you prefer the file's `__main__` block:

```bash
uv run python server.py
```

By default the server listens on `0.0.0.0:8000`. You can override that with `HOST` and `PORT`.

## Deploying With Prefect Horizon

Prefect Horizon is the managed MCP platform from the FastMCP team. It gives you hosted deployment, authentication, access control, inspection tools, and a registry-backed way to share MCP capabilities.

To deploy this repo on Horizon:

1. Push the repo to GitHub.
2. Sign in at `horizon.prefect.io`.
3. Select this repository.
4. Configure the server with:

```text
Name: your preferred server name
Description: Stardew Valley reference MCP demo
Entrypoint: server.py:mcp
```

5. Deploy the server.

Horizon will detect Python dependencies from `pyproject.toml`, build the repo, and deploy a hosted MCP endpoint. After deployment, use Horizon Inspector to test the tools and ChatMCP to verify the conversational behavior.

## Docker

Build and run locally with Docker:

```bash
docker build -t stardew-mcp .
docker run --rm -p 8000:8000 stardew-mcp
```

## Content Attribution

The bundled reference content in `references/` is derived from `stardewvalleywiki.com`.

According to the Stardew Valley Wiki copyright and about pages, most community-contributed wiki text is licensed under Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported (`CC BY-NC-SA 3.0`). Developer-owned images, art, and lore are excluded from that text license.

Sources:

- https://stardewvalleywiki.com/Stardew_Valley_Wiki:Copyrights
- https://stardewvalleywiki.com/Stardew_Valley_Wiki:About

If you reuse or redistribute the adapted content from this repo, preserve the required attribution and share-alike terms.
