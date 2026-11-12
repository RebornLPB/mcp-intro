"""Tools for searching and retrieving programming topic information."""

import json
from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("Programming Learning Server")

TOPICS_PATH = Path(__file__).resolve().parent.parent / "data" / "topics.json"


def load_topics() -> list[dict]:
    """Read all the topics from the local JSON file.
    """
    with open(TOPICS_PATH, encoding="utf-8") as f:
        return json.load(f)


@mcp.tool
def search_topics(query: str) -> list[dict]:
    """Search programming topics by title or key concept.

    Returns a short list of matching topics (id, title, summary).
    If nothing matches, returns a single item with a "message" field.
    """
    query = query.strip().lower()
    if not query:
        return [{"message": "Empty query. Please give a word to search for."}]

    results = []
    for topic in load_topics():
        searchable = [topic["title"]] + topic["key_concepts"]
        if any(query in text.lower() for text in searchable):
            results.append(
                {
                    "id": topic["id"],
                    "title": topic["title"],
                    "summary": topic["summary"],
                }
            )

    if not results:
        return [{"message": f"No topic found for '{query}'."}]
    return results


@mcp.tool
def get_topic_details(topic_id: str) -> dict:
    """Get the full details for a topic by its ID.
    The ID should come from search_topics function.
    """
    new_topic_id = topic_id.strip().lower()
    for topic in load_topics():
        if topic["id"] == new_topic_id:
            return topic

    return {"error": f"No topic found with id '{topic_id}'. Use search_topics to find a valid id."}


@mcp.resource("topics://catalog")
def get_topic_catalog() -> str:
    """Return the list of available topic ids and titles, as a JSON string."""
    catalog = [
        {"id": topic["id"], "title": topic["title"]}
        for topic in load_topics()
    ]
    return json.dumps(catalog)


if __name__ == "__main__":
    mcp.run()
