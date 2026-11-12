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

## Testing

The server was tested with [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector), before connecting it to any agent.

With the virtual environment activated, run:

```bash
npx @modelcontextprotocol/inspector python server/learning_server.py
```

This starts the server and opens a web page. The server appears as "Disconnected" in the **Servers** list: use the toggle button next to it to start and connect it. Then use the **Tools** and **Resources** tabs.

What was checked:

- The server starts and Inspector shows "Connected".
- The 2 tools (`search_topics` and `get_topic_details`) are listed.
- `search_topics` works with a valid query.
- `get_topic_details` works with a valid id.
- The `topics://catalog` resource can be read and contains the 5 topics.
- Invalid inputs give a clear message and do not crash the server.

### Sample outputs

`search_topics` with `recursion`:

```json
[
  {
    "id": "recursion",
    "title": "Recursion",
    "summary": "A technique where a function calls itself to solve a smaller version of the same problem."
  }
]
```

`search_topics` with `java` (no match):

```json
[{"message": "No topic found for 'java'."}]
```

`get_topic_details` with `java` (unknown id):

```json
{"error": "No topic found with id 'java'. Use search_topics to find a valid id."}
```

Note: Inspector shows a list result inside `{"result": [...]}` in its "Structured Output" panel. This is added by FastMCP, because structured output must be an object.

## Agent

`client/agent.py` is a simple agent-like client. It does not use an LLM: it calls the MCP tools with deterministic code. It never imports the server code, it only talks to the server through MCP.

How it works:

1. It receives a student question (a command line argument, or a default example question).
2. It extracts the useful keywords of the question (it ignores common words like "want" or "study").
3. It starts the MCP server as a subprocess (stdio transport, using `client/mcp_client.py`) and calls `search_topics` for each keyword. The topic found by the most keywords is chosen.
4. It calls `get_topic_details` with the id of that topic.
5. It writes a short answer from the returned data and saves it in `output/sample_agent_response.md`.

If no topic matches, the answer says it clearly.

Run it from the project root, with the virtual environment activated:

```bash
python -m client.agent
python -m client.agent "I want to learn about recursion"
```

The calls to the server are printed in the terminal (lines starting with `[MCP]`). The first command uses the default question, "I want to study Python decorators. What should I review first?", and its answer is the sample saved in [output/sample_agent_response.md](output/sample_agent_response.md).

## Third-Party MCP Server Review

**Server:** the official Time MCP server (`mcp-server-time`), from the `modelcontextprotocol/servers` repo on GitHub. Reviewed on 2026-11-12.

**What I did:** I only read the documentation (the README and the main code file, `server.py`). I did not install it and I did not run it.

- **What it does:** it gives the current time and converts the time between timezones (like `Europe/Paris`).
- **Local or remote:** local. The client starts it on my computer and talks to it with stdio, like my own server.
- **Tools and resources:** 3 tools: `get_current_time`, `convert_time` and `get_time_ago`. No resources.
- **Permissions and credentials:** none. No API key and no token. The only setting is the timezone. In `server.py` I did not see any network call or any file writing.
- **One risk:** it is code from someone else and it runs on my computer. The command `uvx mcp-server-time` downloads the latest version each time, so a bad update could run without me knowing.
- **One safety measure:** use a fixed version and a separate virtual environment, and check that the package name is the right one before installing it.

### How to check a third-party server before using it

- Check where it comes from (official repo, known author).
- Read the README before running it, and the code if possible.
- Look at its tools, and see if it runs locally or remotely.
- Check what credentials or access it asks for. Don't give more than needed.
- Use a virtual environment and a fixed version.
- Remember that what a server sends back is data, not instructions for the AI.
