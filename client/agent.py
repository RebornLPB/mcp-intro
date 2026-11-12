"""A simple agent-like client for the Programming Learning MCP server.

It receives a student question, calls the MCP tools `search_topics` and
`get_topic_details`, and writes a short answer using ONLY the data
returned by the server. It never imports the server code directly.

Usage (from the project root, with the virtual environment activated):

    python -m client.agent "I want to study Python decorators."
"""

import asyncio
import re
import sys
from pathlib import Path

from client.mcp_client import call_tool, create_client

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "output" / "sample_agent_response.md"

DEFAULT_QUESTION = "I want to study Python decorators. What should I review first?"

# Common words that are not useful to search for a topic.
STOPWORDS = {
    "the", "and", "for", "that", "this", "with", "about", "what", "how",
    "should", "would", "could", "can", "you", "your", "want", "need", "like",
    "study", "studying", "learn", "learning", "understand", "review", "first",
    "tell", "explain", "show", "help", "start", "begin", "me", "please",
    "are", "was", "does", "from", "into", "some", "any", "have", "has",
}


def extract_keywords(question: str) -> list[str]:
    """Get the useful words of the question, in order, without duplicates."""
    words = re.findall(r"[a-zA-Z][a-zA-Z\-]*", question.lower())
    keywords = []
    for word in words:
        if len(word) > 2 and word not in STOPWORDS and word not in keywords:
            keywords.append(word)
    return keywords


async def find_best_topic_id(client, keywords: list[str]) -> str | None:
    """Call search_topics for each keyword and pick the topic matched most often."""
    hits = {}
    for keyword in keywords:
        print(f"[MCP] search_topics(query={keyword!r})")
        results = await call_tool(client, "search_topics", {"query": keyword})
        for item in results:
            if "id" in item:
                hits[item["id"]] = hits.get(item["id"], 0) + 1

    if not hits:
        return None
    return max(hits, key=hits.get)


def bullet_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def build_answer(question: str, topic: dict) -> str:
    """Write the student-facing answer from the topic returned by the server."""
    return f"""# Study recommendation

**Your question:** {question}

## Recommended topic: {topic["title"]}

**Why it is relevant:** {topic["summary"]}

## Prerequisites to review first
{bullet_list(topic["prerequisites"])}

## Key concepts
{bullet_list(topic["key_concepts"])}

## Practice idea
{topic["practice_idea"]}

## Common mistakes to avoid
{bullet_list(topic["common_mistakes"])}
"""


def build_no_match_answer(question: str) -> str:
    """Answer used when the server has no topic for the question."""
    return f"""# Study recommendation

**Your question:** {question}

No matching topic was found in the learning server, so I can't recommend
anything for this question. Try again with another topic name or keyword.
"""


async def run_agent(question: str) -> str:
    """Receive a question, call the MCP server, and return the answer."""
    keywords = extract_keywords(question)
    print(f"[Agent] Question: {question}")
    print(f"[Agent] Keywords: {keywords}")

    async with create_client() as client:
        topic_id = await find_best_topic_id(client, keywords)
        if topic_id is None:
            return build_no_match_answer(question)

        print(f"[MCP] get_topic_details(topic_id={topic_id!r})")
        topic = await call_tool(client, "get_topic_details", {"topic_id": topic_id})

    if "error" in topic:
        return build_no_match_answer(question)
    return build_answer(question, topic)


def main() -> None:
    question = " ".join(sys.argv[1:]) or DEFAULT_QUESTION
    answer = asyncio.run(run_agent(question))

    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    OUTPUT_PATH.write_text(answer, encoding="utf-8")
    print(f"[Agent] Answer saved in {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
