# MCP Intro

A small project to learn how MCP works.

## Setup and Run

You need Python 3.10 or higher (FastMCP requires it).

1. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install the dependencies:

```bash
pip install -r requirements.txt
```

3. Start the server:

```bash
python server/learning_server.py
```

The terminal will look "stuck" and that's normal. The server uses the stdio transport, so it just waits for a client to talk to it. You should see a log saying `Starting MCP server 'Programming Learning Server' with transport 'stdio'`. Stop it with `Ctrl+C`.

Note: since the server uses stdio, don't use `print()` for debugging in the server code, because it would break the communication with the client. Use `logging` or print to stderr instead.

## MCP Architecture Summary

**What is MCP?**
MCP (Model Context Protocol) is a standard way for an AI app to talk to things outside of itself, like files, data or actions. Before, every tool needed its own custom connection. With MCP, everyone uses the same rules, so it just works. It's a bit like USB: one plug for everything.

**Host, client, server**

- **Host**: the AI app the user is using (a chat app, an IDE, an agent). It runs the conversation and decides when it needs something from outside.
- **Client**: made by the host to talk to one server. If the host uses 3 servers, it has 3 clients. It sends the requests and gets the answers back.
- **Server**: a program that offers some capabilities (tools, resources, prompts) so the AI can use them.

**Tools and resources**

- **Tools** are things the AI can ask the server to do, like `search_topics("python")`. You give an input, the server does something and returns a result.
- **Resources** are data the AI can read, like a text file in `data/`. It only gives information, it doesn't do anything.

**Why only expose what's needed?**
Everything a server exposes can be used by the AI, even by mistake, or if someone tricks it with a bad prompt. So the fewer things there are, the fewer things can go wrong (leaked data, actions nobody wanted). It also helps the AI: with fewer tools, it's easier for it to pick the right one.

**Example**
A user asks an agent: "Tell me about the topic MCP".

1. The agent (the host) sees it needs info about a topic.
2. Its client sends the request to the topic server.
3. The server runs its `search_topics` tool, then `get_topic_details` for the full content, and sends back the results.
4. The result goes back through the client to the host, which writes the final answer for the user.

## Tools

### `search_topics(query: str)`

Searches the programming topics in `data/topics.json`.

- **Input**: `query`, a word or phrase. The search ignores upper/lower case.
- **Where it searches**: in the topic `title` and in the `key_concepts`.
- **Output**: a short list of matching topics, each with `id`, `title` and `summary`. The `id` can be used later to ask for more details.
- **No match or empty query**: returns a single item with a `message` field explaining what happened.
- The results are always in the same order as in the file, so the same query always gives the same answer.

Example: `search_topics("decorator")` returns the `python-decorators` topic.

### `get_topic_details(topic_id: str)`

Returns the full information about one topic.

- **Input**: `topic_id`, the id of a topic (for example `recursion`). The id should come from the results of `search_topics`. Extra spaces and upper/lower case are ignored.
- **Output**: the complete topic, with all its fields: `id`, `title`, `summary`, `prerequisites`, `key_concepts`, `common_mistakes` and `practice_idea`.
- **Unknown id**: returns a dictionary with an `error` field that explains that no topic was found and suggests using `search_topics`. The tool never crashes on a bad id.

Example: `get_topic_details("recursion")` returns everything about the recursion topic.

Typical use: first call `search_topics` to find candidates, then call `get_topic_details` with the `id` of the one you want.

## Resources

### `topics://catalog`

A read-only resource with the list of all the available topics.

- **Content**: a JSON string with a list of topics. Each topic only has its `id` and `title`.
- **Use**: it lets a client or an agent see which topics exist before searching. The `id` values can then be used with `get_topic_details`.
- **Read-only**: reading it never changes anything in `data/topics.json`.

Example of what it returns:

```json
[{"id": "python-decorators", "title": "Python Decorators"}, {"id": "recursion", "title": "Recursion"}]
```
