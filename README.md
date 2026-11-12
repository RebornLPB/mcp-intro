# MCP Servers in Python

## Description

A small project to learn how MCP (Model Context Protocol) works. It has:

- A **MCP server** made with FastMCP (`server/learning_server.py`). It gives information about programming topics from a small JSON file (`data/topics.json`), with 2 tools and 1 resource.
- A **simple agent** (`client/agent.py`) that connects to the server through MCP and writes a short answer for a student.
- A **review of a third-party MCP server** (see below).

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

## Requirements

- Python 3.10 or higher (FastMCP requires it). I used Python 3.12.
- The packages in `requirements.txt` (FastMCP 4.1.8).
- Node.js (for `npx`), only if you want to test with MCP Inspector.
- No API key and no secret is needed. The file `.env.example` is empty on purpose.

## Setup

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## How to Run the Server

```bash
python server/learning_server.py
```

The terminal will look "stuck" and that's normal. The server uses the stdio transport, so it just waits for a client to talk to it. You should see a log saying `Starting MCP server 'Programming Learning Server' with transport 'stdio'`. Stop it with `Ctrl+C`.

Note: since the server uses stdio, don't use `print()` for debugging in the server code, because it would break the communication with the client. Use `logging` or print to stderr instead.

## How to Test the Server

I tested the server with [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector), before connecting it to any agent.

With the virtual environment activated, run:

```bash
npx @modelcontextprotocol/inspector python server/learning_server.py
```

This starts the server and opens a web page. The server appears as "Disconnected" in the **Servers** list: use the toggle button next to it to start and connect it. Then use the **Tools** and **Resources** tabs.

What I checked:

- The server starts and Inspector shows "Connected".
- The 2 tools (`search_topics` and `get_topic_details`) are listed.
- `search_topics` works with a valid query.
- `get_topic_details` works with a valid id.
- The `topics://catalog` resource can be read and contains the 5 topics.
- Invalid inputs give a clear message and do not crash the server.

Sample outputs:

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

## How to Run the Agent

`client/agent.py` is a simple agent-like client. It does not use an LLM: it calls the MCP tools with deterministic code. It never imports the server code, it only talks to the server through MCP.

How it works:

1. It receives a student question (a command line argument, or a default example question).
2. It extracts the useful keywords of the question (it ignores common words like "want" or "study").
3. It starts the MCP server as a subprocess (stdio transport, using `client/mcp_client.py`) and calls `search_topics` for each keyword. The topic found by the most keywords is chosen.
4. It calls `get_topic_details` with the id of that topic.
5. It writes a short answer from the returned data and saves it in `output/sample_agent_response.md`.

If no topic matches, the answer says it clearly.

Run it from the project root, with the virtual environment activated (you don't need to start the server first, the agent starts it):

```bash
python -m client.agent
python -m client.agent "I want to learn about recursion"
```

The calls to the server are printed in the terminal (lines starting with `[MCP]`). The first command uses the default question, "I want to study Python decorators. What should I review first?".

## Available Tools

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

## Available Resources

### `topics://catalog`

A read-only resource with the list of all the available topics.

- **Content**: a JSON string with a list of topics. Each topic only has its `id` and `title`.
- **Use**: it lets a client or an agent see which topics exist before searching. The `id` values can then be used with `get_topic_details`.
- **Read-only**: reading it never changes anything in `data/topics.json`.

Example of what it returns:

```json
[{"id": "python-decorators", "title": "Python Decorators"}, {"id": "recursion", "title": "Recursion"}]
```

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

## Example Output

Command:

```bash
python -m client.agent
```

What the terminal shows (the calls to the MCP server):

```text
[Agent] Question: I want to study Python decorators. What should I review first?
[Agent] Keywords: ['python', 'decorators']
[MCP] search_topics(query='python')
[MCP] search_topics(query='decorators')
[MCP] get_topic_details(topic_id='python-decorators')
[Agent] Answer saved in output/sample_agent_response.md
```

The answer saved in [output/sample_agent_response.md](output/sample_agent_response.md):

```markdown
# Study recommendation

**Your question:** I want to study Python decorators. What should I review first?

## Recommended topic: Python Decorators

**Why it is relevant:** A decorator is a function that wraps another function to add behavior to it without changing its code.

## Prerequisites to review first
- Functions
- Scope
- First-class functions

## Key concepts
- Higher-order functions
- Wrapper functions
- The @ syntax
- functools.wraps

## Practice idea
Create a decorator that logs the name of a function each time it is called.

## Common mistakes to avoid
- Forgetting to return the wrapper function
- Forgetting to pass *args and **kwargs to the original function
- Losing the original function name and docstring by not using functools.wraps
```

If no topic matches (for example `python -m client.agent "Teach me Java generics"`), the answer says that no matching topic was found.

## Known Limitations

- **The search is simple text matching.** `search_topics` only checks if the query is written inside a title or a key concept. A typo, a different word or a synonym finds nothing. It does not search in the `summary`.
- **The agent can pick a wrong topic.** The keywords of the question are chosen with a short list of common words to ignore, and it does not understand the meaning. For the question "How do I handle errors in Python?", the words `handle` and `errors` find nothing (the topic is called "Exception Handling"), but `python` finds 2 topics. So the agent recommends `python-decorators`, which is wrong.
- **The agent is not an LLM.** It only recommends one topic, and it works only with questions in English.
- **Small data.** There are only 5 topics in a JSON file, and the file is read again at each call. The code expects that every topic has all its fields, there is no check.
- **Local only.** The server only uses stdio. There is no HTTP and no authentication. The agent starts a new server each time it runs.
- **Third-party review.** I only read the documentation, I did not run the Time server.

### Problems I had

- A tool declared with `-> dict` returned a list (`[{"error": ""}]`). FastMCP gave the error `structured_content must be a dict or None`. Fix: return a dictionary, not a list.
- Searching with a whole sentence finds nothing, because `search_topics` looks for the whole text. This is why the agent extracts keywords first.
- My global git config ignores the files `.env.*`, so `.env.example` was not added to git. Fix: `git add -f .env.example`.
- VS Code underlined `fastmcp` in yellow because it used the wrong Python. Fix: select the `.venv` interpreter.
- FastMCP showed a warning about giving the server path as a string. Fix: give a `Path` object to `Client`.

## Reflection

**1. What problem does MCP solve?**
Connecting an AI app to outside tools and data used to need a different custom connection for each one. MCP is a standard, so a server can offer its tools once, and any MCP client can use them.

**2. What is the difference between an MCP tool and an MCP resource?**
A tool is an action: the AI sends inputs and the server does something and returns a result (like `search_topics("python")`). A resource is data to read, with an address (a URI like `topics://catalog`), and it doesn't do anything.

**3. What does your MCP server expose?**
Two tools, `search_topics` and `get_topic_details`, and one read-only resource, `topics://catalog`. The data comes from `data/topics.json`.

**4. How does your agent use the MCP server?**
The agent starts the server with a FastMCP client (stdio). It calls `search_topics` for each keyword of the question, chooses the best topic, then calls `get_topic_details` and writes the answer from the returned data. It never imports the server code.

**5. What should you check before using a third-party MCP server?**
Where it comes from, what the README and the code say, if it runs locally or remotely, which tools it has, and which permissions or credentials it needs. Then use a virtual environment and a fixed version, and don't give it more access than needed.

**6. What limitation did you observe in your implementation?**
The search is only text matching, so the agent can recommend the wrong topic. For "How do I handle errors in Python?" it recommends Python Decorators, because `handle` and `errors` find nothing and only `python` matches.
