# MCP Architecture Guide for plorp

**Date:** October 6, 2025
**Purpose:** Comprehensive guide to MCP servers, agents, and architectural patterns for plorp

---

## Table of Contents

1. [MCP Server Setup](#mcp-server-setup)
2. [MCP Servers vs Agents](#mcp-servers-vs-agents)
3. [The Stochastic vs Deterministic Principle](#the-stochastic-vs-deterministic-principle)
4. [Technical Definition of Agents](#technical-definition-of-agents)
5. [Architectural Patterns for Multi-Tool Workflows](#architectural-patterns-for-multi-tool-workflows)
6. [Reliability and Consistency](#reliability-and-consistency)
7. [Recommended Architecture for plorp](#recommended-architecture-for-plorp)

---

## MCP Server Setup

### What We Installed

1. **mcp-obsidian** - MCP server for Obsidian integration
2. **mcp-server-taskwarrior** - MCP server for TaskWarrior integration

### Installation Process

#### mcp-obsidian Installation

```bash
# Example MCP server installation (reference only, not used by plorp)
# git clone https://github.com/MarkusPfundstein/mcp-obsidian

# Install with uv
cd mcp-obsidian
uv sync

# Create .env file
cat > .env << 'EOF'
OBSIDIAN_API_KEY=ff62b68f8ed1570204faaf36b8fc8e8a9b46323d738ddb8dd40d10f10e5d11ea
OBSIDIAN_HOST=127.0.0.1
OBSIDIAN_PORT=27124
EOF
```

#### Claude Desktop Configuration

**Location:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "taskwarrior": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-server-taskwarrior"
      ]
    },
    "mcp-obsidian": {
      "command": "/Users/jsd/.local/bin/uv",
      "args": [
        "--directory",
        "/path/to/mcp-server",
        "run",
        "server-name"
      ],
      "env": {
        "OBSIDIAN_API_KEY": "ff62b68f8ed1570204faaf36b8fc8e8a9b46323d738ddb8dd40d10f10e5d11ea",
        "OBSIDIAN_HOST": "127.0.0.1",
        "OBSIDIAN_PORT": "27124"
      }
    }
  }
}
```

**Key Point:** Use full path to `uv` (`/Users/jsd/.local/bin/uv`) because Claude Desktop has limited PATH.

#### Multiple MCP Servers

MCP servers are configured in a single JSON object with multiple server entries:

```json
{
  "mcpServers": {
    "server1": { ... },
    "server2": { ... },
    "server3": { ... }
  }
}
```

**Not** separate JSON objects for each server.

### Requirements

- **Obsidian Local REST API Plugin** - Must be installed and enabled in Obsidian
- **TaskWarrior 3.4.1+** - Must be installed via system package manager
- **uv** - Python package manager (installed at `~/.local/bin/uv`)

---

## MCP Servers vs Agents

### Core Relationship

```
┌─────────────────────────────────────────────────────────┐
│                     Claude (Agent)                      │
│  - Reasons about user requests                          │
│  - Decides which tools to call                          │
│  - Orchestrates multiple tool calls                     │
│  - Synthesizes results into responses                   │
└────────────┬────────────────────────────────────────────┘
             │
             │ Uses tools from...
             │
    ┌────────┴────────┬──────────┬──────────────┐
    │                 │          │              │
┌───▼────┐     ┌──────▼───┐  ┌──▼────┐    ┌───▼────┐
│TaskWar-│     │Obsidian  │  │ Plorp │    │ Other  │
│rior MCP│     │   MCP    │  │  MCP  │    │  MCP   │
│        │     │          │  │       │    │ Servers│
└────────┘     └──────────┘  └───────┘    └────────┘
  Tools          Tools         Tools        Tools
```

### Key Distinctions

| | MCP Server | Agent (Claude) |
|---|---|---|
| **Role** | Tool provider | Orchestrator |
| **Behavior** | Executes specific functions | Makes decisions |
| **Intelligence** | None (just code) | LLM reasoning |
| **Your Plorp Server** | Provides plorp_* tools | Uses plorp tools strategically |
| **Complexity** | Simple, focused operations | Complex workflow coordination |
| **Nature** | Deterministic | Stochastic |

### MCP Servers: Tools, Not Agents

**MCP servers provide capabilities:**
- Expose specific functions (tools)
- No decision-making
- Just execute when called
- Return data/results

**Example:**

```python
# plorp MCP server (NOT an agent - just provides tools)
@server.call_tool()
async def plorp_start(date: str):
    """Generate daily note"""
    # Execute workflow
    return {"daily_note_path": "vault/daily/2025-10-06.md"}

@server.call_tool()
async def plorp_review(date: str):
    """Get uncompleted tasks"""
    return {"uncompleted_tasks": [...]}
```

### Agents: Orchestrators with Intelligence

**Claude acts as the agent that uses these tools:**

```
User: "Start my day and show me what's urgent"

Claude (agent):
  1. Calls plorp_start(today)
  2. Calls plorp_get_uncompleted_tasks()
  3. Analyzes which are urgent
  4. Presents summary to user
```

### Design Principles

**MCP Servers Should:**
- ✅ Provide atomic, focused tools
- ✅ Return structured data
- ✅ Execute specific operations
- ✅ Be stateless and predictable

**MCP Servers Should NOT:**
- ❌ Try to "figure out" what the user wants
- ❌ Make decisions about workflow
- ❌ Chain multiple operations automatically
- ❌ Have complex conditional logic

**Let the agent handle orchestration.**

### Example: Good vs Bad Tool Design

**Bad MCP Tool Design** (too much agent-like behavior):

```python
@server.call_tool()
async def plorp_do_morning_routine():
    """Does everything for morning - checks inbox,
    creates daily note, prioritizes tasks, etc."""
    # ❌ Too much decision-making in the tool!
```

**Good MCP Tool Design** (simple, atomic):

```python
@server.call_tool()
async def plorp_start(date: str):
    """Generate daily note for specified date"""

@server.call_tool()
async def plorp_inbox_process():
    """Return unprocessed inbox items"""

@server.call_tool()
async def plorp_create_task(description: str, ...):
    """Create single task"""
```

Claude (agent) orchestrates these to build the morning routine.

---

## The Stochastic vs Deterministic Principle

### Core Principle

> **Agents are stochastic, MCP servers are deterministic.**

This should guide every design decision.

```
┌─────────────────────────────────┐
│         Agent (Claude)          │
│                                 │
│  🎲 STOCHASTIC                  │
│  - Non-deterministic reasoning  │
│  - Different responses each time│
│  - Creative problem solving     │
│  - Context-dependent decisions  │
└─────────────┬───────────────────┘
              │
              │ calls
              ↓
┌─────────────────────────────────┐
│      MCP Server (plorp)         │
│                                 │
│  ⚙️  DETERMINISTIC               │
│  - Same input → same output     │
│  - Predictable behavior         │
│  - Reliable operations          │
│  - Testable with unit tests     │
└─────────────────────────────────┘
```

### Why This Matters for Design

#### MCP Servers Should Be Deterministic

```python
# Good: Deterministic MCP tool
@server.call_tool()
async def plorp_create_task(
    description: str,
    due: str,
    priority: str
):
    """Given these exact inputs,
    always creates the same task"""
    result = subprocess.run([
        'task', 'add', description,
        f'due:{due}',
        f'priority:{priority}'
    ])
    return {"uuid": "abc-123"}  # Deterministic

# ✅ Testable:
assert plorp_create_task("Buy milk", "today", "H")
    == plorp_create_task("Buy milk", "today", "H")
```

```python
# Bad: Stochastic behavior in MCP tool
@server.call_tool()
async def plorp_create_task_smart(description: str):
    """Tries to be "smart" about task creation"""

    # ❌ Non-deterministic decisions in the tool
    if "urgent" in description.lower():
        priority = "H"  # Maybe?
    elif len(description) > 50:
        priority = "M"  # Heuristic guess?
    else:
        priority = "L"  # Who knows?

    # ❌ Tool is making agent-like decisions
    # ❌ Same input might give different results
    # ❌ Hard to test, debug, trust
```

#### Agents Should Be Stochastic

```
User: "Help me plan my day"

Claude (stochastic agent):
  Run 1:
    - Calls plorp_start()
    - Analyzes urgent tasks
    - Suggests prioritization
    - Offers to create focus blocks

  Run 2 (same request):
    - Calls plorp_start()
    - Suggests time-blocking
    - Offers to defer low-priority items
    - Different but equally valid approach

Both valid! Agent adapts to nuance, context, user history.
```

### Testing Benefits

**Deterministic MCP tools are easily testable:**

```python
def test_plorp_create_task():
    result = plorp_create_task(
        description="Test task",
        due="2025-10-07",
        priority="H"
    )

    # ✅ Can assert exact results
    assert result["description"] == "Test task"
    assert result["due"] == "2025-10-07"
    assert result["priority"] == "H"
```

**Stochastic agents are hard to test:**

```python
def test_claude_helps_user():
    response = claude.respond("Help me with my tasks")

    # ❌ Can't assert exact response
    # ❌ Response varies each time
    # ❌ Can only test that it's "helpful-ish"
    assert "task" in response.lower()  # Weak test
```

### Architecture Insight

This separation enables:

```
┌─────────────────────────────────────────┐
│  Stochastic Layer (Agent)               │
│  - Understands user intent              │
│  - Handles ambiguity                    │
│  - Makes judgment calls                 │
│  - Provides flexibility                 │
└──────────────┬──────────────────────────┘
               │
               │ Uses tools from
               ↓
┌─────────────────────────────────────────┐
│  Deterministic Layer (MCP)              │
│  - Reliable operations                  │
│  - Testable behavior                    │
│  - Predictable results                  │
│  - No surprises                         │
└─────────────────────────────────────────┘
```

**Best of both worlds:**
- Flexibility where you need it (agent)
- Reliability where you need it (tools)

### Decision Heuristic

When in doubt, ask: "Could I write a unit test with exact assertions for this function?"
- **Yes** → Good MCP tool (deterministic)
- **No** → Agent behavior (stochastic)

---

## Technical Definition of Agents

### What is an Agent?

**An agent is a system that:**
1. Perceives its environment
2. Reasons about what actions to take
3. Acts on the environment
4. Iterates (perception → reasoning → action loop)

### Core Components

```
┌─────────────────────────────────────────────────────┐
│                      AGENT                          │
│                                                     │
│  ┌──────────────┐                                  │
│  │   LLM Core   │  ← Language model (reasoning)    │
│  │  (Claude,    │                                   │
│  │   GPT, etc)  │                                   │
│  └──────┬───────┘                                   │
│         │                                            │
│  ┌──────▼───────┐                                   │
│  │   Tool       │  ← Decides which tools to use     │
│  │   Selection  │                                   │
│  └──────┬───────┘                                   │
│         │                                            │
│  ┌──────▼───────┐                                   │
│  │   Tool       │  ← Executes tool calls            │
│  │   Execution  │                                   │
│  └──────┬───────┘                                   │
│         │                                            │
│  ┌──────▼───────┐                                   │
│  │   Response   │  ← Synthesizes results            │
│  │   Synthesis  │                                   │
│  └──────────────┘                                   │
└─────────────────────────────────────────────────────┘
```

### Technical Implementation

#### The Reasoning Loop (Agentic Loop)

```python
# Simplified agent implementation
class Agent:
    def __init__(self, llm, tools):
        self.llm = llm              # Language model
        self.tools = tools          # Available tools/functions
        self.conversation = []      # Context/memory

    def run(self, user_input: str):
        """Main agentic loop"""
        self.conversation.append({"role": "user", "content": user_input})

        while True:
            # 1. REASONING: Ask LLM what to do
            response = self.llm.generate(
                messages=self.conversation,
                tools=self.tools,           # Tool descriptions
                tool_choice="auto"          # Let model decide
            )

            # 2. DECISION: Did model want to use tools?
            if response.tool_calls:
                # 3. ACTION: Execute tool calls
                tool_results = []
                for tool_call in response.tool_calls:
                    result = self.execute_tool(
                        tool_call.name,
                        tool_call.arguments
                    )
                    tool_results.append(result)

                # 4. PERCEPTION: Add results to context
                self.conversation.append({
                    "role": "assistant",
                    "tool_calls": response.tool_calls
                })
                self.conversation.append({
                    "role": "tool",
                    "content": tool_results
                })

                # 5. LOOP: Go back to step 1 with new context
                continue

            else:
                # No more tools needed - final response
                return response.content

    def execute_tool(self, name: str, args: dict):
        """Execute a tool and return result"""
        tool_func = self.tools[name]
        return tool_func(**args)
```

#### How Claude Desktop Works with MCP

```python
# Conceptual implementation of Claude as an agent

class ClaudeAgent:
    def __init__(self):
        self.model = "claude-sonnet-4.5"
        self.mcp_tools = self.discover_mcp_servers()
        self.context = []

    def discover_mcp_servers(self):
        """Load MCP servers from config"""
        config = load_config("~/Library/Application Support/Claude/claude_desktop_config.json")

        tools = {}
        for server_name, server_config in config["mcpServers"].items():
            # Start MCP server process
            server = start_mcp_server(server_config)

            # Get available tools
            tool_list = server.call_method("tools/list")

            for tool in tool_list:
                tools[tool["name"]] = {
                    "server": server,
                    "schema": tool["inputSchema"],
                    "description": tool["description"]
                }

        return tools

    def chat(self, user_message: str):
        """Process user message"""
        self.context.append({"role": "user", "content": user_message})

        max_iterations = 25  # Prevent infinite loops
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            # Ask Claude to reason
            response = anthropic.messages.create(
                model=self.model,
                messages=self.context,
                tools=self.format_tools_for_api(self.mcp_tools),
                max_tokens=4096
            )

            # Check if Claude wants to use tools
            if response.stop_reason == "tool_use":
                # Extract tool calls from response
                tool_uses = [
                    block for block in response.content
                    if block.type == "tool_use"
                ]

                # Execute each tool
                tool_results = []
                for tool_use in tool_uses:
                    result = self.call_mcp_tool(
                        tool_use.name,
                        tool_use.input
                    )
                    tool_results.append({
                        "tool_use_id": tool_use.id,
                        "content": result
                    })

                # Add to context and loop again
                self.context.append({
                    "role": "assistant",
                    "content": response.content
                })
                self.context.append({
                    "role": "user",
                    "content": tool_results
                })

                continue  # Loop back for more reasoning

            else:
                # Final response
                return response.content

    def call_mcp_tool(self, tool_name: str, args: dict):
        """Call MCP server tool via JSON-RPC"""
        tool_info = self.mcp_tools[tool_name]
        server = tool_info["server"]

        # Send JSON-RPC request to MCP server
        result = server.send_request({
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": args
            },
            "id": generate_id()
        })

        return result
```

### Actual Protocol Flow

```
You: "Start my plorp daily note"
  │
  ↓
┌─────────────────────────────────────────┐
│ Claude Agent (Running in Desktop App)  │
│                                         │
│ 1. Receives user message                │
│ 2. Sends to Anthropic API:             │
│    - Conversation history               │
│    - Available tools (from MCP)         │
│    - System prompt                      │
│                                         │
│ ← API Response:                         │
│   {                                     │
│     "content": [                        │
│       {                                 │
│         "type": "tool_use",             │
│         "name": "plorp_start",          │
│         "input": {"date": "2025-10-06"} │
│       }                                 │
│     ]                                   │
│   }                                     │
│                                         │
│ 3. Agent sees tool_use response         │
│ 4. Calls MCP server:                    │
└────────┬────────────────────────────────┘
         │
         │ JSON-RPC over stdio
         ↓
┌─────────────────────────────────────────┐
│ Plorp MCP Server (Subprocess)           │
│                                         │
│ Receives:                               │
│ {                                       │
│   "method": "tools/call",               │
│   "params": {                           │
│     "name": "plorp_start",              │
│     "arguments": {"date": "2025-10-06"} │
│   }                                     │
│ }                                       │
│                                         │
│ Executes: plorp_start("2025-10-06")    │
│                                         │
│ Returns:                                │
│ {                                       │
│   "content": [{                         │
│     "type": "text",                     │
│     "text": "Daily note created at..."  │
│   }]                                    │
│ }                                       │
└────────┬────────────────────────────────┘
         │
         │ Result back to agent
         ↓
┌─────────────────────────────────────────┐
│ Claude Agent                            │
│                                         │
│ 5. Adds tool result to context          │
│ 6. Sends back to API with result        │
│                                         │
│ ← API Response:                         │
│   {                                     │
│     "content": "I've created your..."   │
│     "stop_reason": "end_turn"           │
│   }                                     │
│                                         │
│ 7. Returns final response to user       │
└─────────────────────────────────────────┘
```

### Key Technical Components

1. **LLM (Large Language Model)**
   - The "brain" of the agent
   - Claude Sonnet 4.5, GPT-4, etc.
   - Generates text, reasons about problems
   - **Not** the agent itself - just the reasoning engine

2. **Tool/Function Calling**
   - API feature that lets LLM request tool execution
   - LLM outputs structured JSON instead of text
   - Agent framework parses this and executes the tool

3. **Context/Memory**
   - Conversation history
   - Tool results
   - System instructions
   - Passed to LLM each iteration

4. **Control Loop**
   - Agent runtime that orchestrates:
     - LLM calls
     - Tool execution
     - Context management
     - Termination conditions

### Agents vs Simple API Calls

#### Simple API Call (Not an Agent)

```python
# Just a single LLM call
response = client.messages.create(
    model="claude-sonnet-4.5",
    messages=[{"role": "user", "content": "Hello"}]
)
print(response.content)
# Done - no loop, no tools, no autonomy
```

#### Agent (Multi-step, Tool-using)

```python
# Agentic system
agent = Agent(llm=claude, tools=[plorp_start, plorp_review])

response = agent.run("Help me plan my day")

# Internally does:
# 1. LLM call: "I should check tasks"
# 2. Calls plorp_get_tasks()
# 3. LLM call: "User has 10 tasks, I should prioritize"
# 4. LLM call: "Let me create the daily note"
# 5. Calls plorp_start()
# 6. LLM call: "Here's your plan..."
# 7. Returns final response

# Multiple iterations, tool calls, reasoning steps
```

### ReAct Pattern (Common Agent Architecture)

Most agents use **ReAct** (Reasoning + Acting):

```
┌─────────────────────────────────────────┐
│ Iteration 1                             │
│                                         │
│ Thought: "I need to check the user's    │
│           overdue tasks first"          │
│                                         │
│ Action: plorp_get_overdue_tasks()       │
│                                         │
│ Observation: [5 overdue tasks returned] │
└─────────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────┐
│ Iteration 2                             │
│                                         │
│ Thought: "These tasks are urgent. I     │
│           should create a daily note"   │
│                                         │
│ Action: plorp_start(today)              │
│                                         │
│ Observation: Daily note created         │
└─────────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────┐
│ Iteration 3                             │
│                                         │
│ Thought: "I have all the info I need"   │
│                                         │
│ Action: None (final response)           │
│                                         │
│ Response: "I've created your daily      │
│            note with 5 overdue tasks..." │
└─────────────────────────────────────────┘
```

### Summary: What is an Agent?

An **agent** is:

**Architecturally:**
- Control loop (perception → reasoning → action)
- LLM for reasoning
- Tool execution capability
- Context management
- Termination logic

**Behaviorally:**
- Autonomous (makes own decisions)
- Goal-oriented (works toward objective)
- Multi-step (can iterate)
- Tool-using (can take actions)

**In Code:**
```python
while not done:
    thought = llm.reason(context)
    if thought.requires_action:
        result = execute_tool(thought.action)
        context.append(result)
    else:
        return thought.response
```

**What It's NOT:**
- Just an LLM (that's the reasoning engine)
- Just a chatbot (that's single-turn)
- Just an API wrapper (that's a tool/function)
- Deterministic (uses stochastic LLM for decisions)

---

## Architectural Patterns for Multi-Tool Workflows

When you have multiple MCP servers (TaskWarrior, Obsidian, Airtable, Analytics, etc.) and want to create workflows, there are three main architectural patterns:

### Pattern 1: One Agent Gateway + Many Domain MCP Servers

```
                    ┌─────────────────┐
                    │  Claude Agent   │
                    │   (Gateway)     │
                    └────────┬────────┘
                             │
                             │ Orchestrates everything
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼────┐          ┌───▼────┐          ┌───▼────┐
   │TaskWar- │          │Obsidian│          │Airtable│
   │rior MCP │          │  MCP   │          │  MCP   │
   └─────────┘          └────────┘          └────────┘

   - Simple tools        - Simple tools      - Simple tools
   - No workflow logic   - No workflow       - No workflow
```

**Characteristics:**
- Each MCP server provides **atomic operations only**
- Agent does **all** orchestration
- MCP tools are pure, deterministic functions

**Example:**

```python
# TaskWarrior MCP - atomic operations only
@server.call_tool()
async def taskwarrior_create_task(description, due, priority):
    """Just creates a task, nothing else"""

@server.call_tool()
async def taskwarrior_get_tasks(filter):
    """Just queries tasks, nothing else"""

# Obsidian MCP - atomic operations only
@server.call_tool()
async def obsidian_create_note(path, content):
    """Just creates a note, nothing else"""

@server.call_tool()
async def obsidian_read_note(path):
    """Just reads a note, nothing else"""
```

**Claude orchestrates the workflow:**

```
User: "Start my day"

Claude (agent):
  1. Call taskwarrior_get_tasks(status:pending, due:today)
  2. Format the task list
  3. Call obsidian_create_note("daily/2025-10-06.md", formatted_content)
  4. Return summary to user
```

**Pros:**
- ✅ Maximum flexibility - agent can combine tools creatively
- ✅ Simple MCP servers - easy to build/maintain
- ✅ Composable - any combination of tools possible
- ✅ Each domain server is pure and focused

**Cons:**
- ❌ Agent must learn workflow patterns each time
- ❌ Complex workflows require many LLM calls
- ❌ No encapsulation of domain expertise
- ❌ Can be slower (multiple reasoning steps)

---

### Pattern 2: Bounded-Context Servers (Domain-Specific Workflows)

```
                    ┌─────────────────┐
                    │  Claude Agent   │
                    └────────┬────────┘
                             │
                             │ Calls domain workflows
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼─────┐         ┌───▼─────┐         ┌───▼─────┐
   │  Plorp   │         │Analytics│         │ Finance │
   │   MCP    │         │   MCP   │         │   MCP   │
   │          │         │         │         │         │
   │ Workflows│         │Workflows│         │Workflows│
   └────┬─────┘         └────┬────┘         └────┬────┘
        │                    │                    │
   ┌────▼─────┐         ┌───▼─────┐         ┌───▼─────┐
   │TaskWarr. │         │Google   │         │Airtable │
   │Obsidian  │         │Analytics│         │QuickBooks│
   └──────────┘         └─────────┘         └─────────┘
```

**Characteristics:**
- Each MCP server encapsulates a **domain/bounded context**
- Server provides both **atomic tools** and **workflow tools**
- Internal implementation uses multiple systems

**Example - Plorp MCP Server:**

```python
# High-level workflow tools
@server.call_tool()
async def plorp_start_day(date: str):
    """Complete morning workflow

    Internally:
    1. Queries TaskWarrior for tasks
    2. Formats as markdown
    3. Creates Obsidian daily note
    4. Returns summary
    """
    # Direct integrations (subprocess for TaskWarrior, file ops for Obsidian)
    tasks = get_tasks_from_taskwarrior()
    note_content = format_daily_note(tasks)
    write_obsidian_note(f"daily/{date}.md", note_content)
    return {"status": "created", "path": f"daily/{date}.md", "task_count": len(tasks)}

@server.call_tool()
async def plorp_review_day(date: str):
    """Complete review workflow"""
    # Encapsulates entire workflow internally

# Also atomic tools for flexibility
@server.call_tool()
async def plorp_create_task(description: str, ...):
    """Create single task (atomic operation)"""

@server.call_tool()
async def plorp_create_note(title: str, ...):
    """Create single note (atomic operation)"""
```

**Pros:**
- ✅ Encapsulates domain expertise
- ✅ Faster execution (one tool call = complete workflow)
- ✅ Deterministic workflows (testable)
- ✅ Can optimize internally
- ✅ Domain logic lives in domain server

**Cons:**
- ❌ Less flexible (predefined workflows)
- ❌ More complex MCP servers
- ❌ Agent can't remix workflows easily
- ❌ Duplication if workflows overlap

---

### Pattern 3: Planner/Executor Split

```
                    ┌─────────────────┐
                    │  Claude Agent   │
                    │   (Planner)     │
                    └────────┬────────┘
                             │
                             │ Creates execution plan
                             ↓
                    ┌─────────────────┐
                    │   Workflow      │
                    │   Executor MCP  │  ← Deterministic execution
                    └────────┬────────┘
                             │
                             │ Executes plan steps
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼────┐          ┌───▼────┐          ┌───▼────┐
   │TaskWar. │          │Obsidian│          │Airtable│
   │  MCP    │          │  MCP   │          │  MCP   │
   └─────────┘          └────────┘          └────────┘
```

**Characteristics:**
- Agent creates a **workflow plan** (stochastic)
- Workflow Executor executes plan (deterministic)
- Domain MCP servers provide atomic tools

**Example:**

```python
# Workflow Executor MCP Server
@server.call_tool()
async def execute_workflow(plan: dict):
    """Execute a workflow plan

    plan = {
      "steps": [
        {"tool": "taskwarrior_get_tasks", "args": {...}},
        {"tool": "obsidian_create_note", "args": {...}},
        {"tool": "airtable_log_completion", "args": {...}}
      ]
    }
    """
    results = []
    context = {}

    for step in plan["steps"]:
        # Execute each step
        result = await call_mcp_tool(step["tool"], step["args"])
        results.append(result)
        context[step["id"]] = result

        # Handle conditionals
        if step.get("condition"):
            if not evaluate_condition(step["condition"], context):
                continue

    return {"results": results, "status": "completed"}
```

**Usage:**

```
User: "Start my day and log it to Airtable"

Claude (planner):
  1. Creates execution plan:
     {
       "steps": [
         {"id": "1", "tool": "taskwarrior_get_tasks", "args": {"status": "pending"}},
         {"id": "2", "tool": "obsidian_create_note", "args": {"path": "daily/today.md", "content": "{1.tasks}"}},
         {"id": "3", "tool": "airtable_create_record", "args": {"table": "daily_logs", "fields": {"date": "today", "task_count": "{1.count}"}}}
       ]
     }

  2. Calls: execute_workflow(plan)

  3. Workflow Executor deterministically executes all steps
```

**Pros:**
- ✅ Separates planning (stochastic) from execution (deterministic)
- ✅ Can retry/resume workflows
- ✅ Workflows are auditable/loggable
- ✅ Can optimize execution (parallel steps, etc.)
- ✅ Agent provides flexibility, executor provides reliability

**Cons:**
- ❌ Additional complexity (workflow DSL/format)
- ❌ Debugging across layers
- ❌ Need to design workflow specification format
- ❌ Overkill for simple use cases

---

### Recommended Pattern: Hybrid Approach

**Hybrid: Bounded-Context Servers + Atomic Tools**

```
                    ┌─────────────────┐
                    │  Claude Agent   │
                    └────────┬────────┘
                             │
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼─────┐         ┌───▼─────┐         ┌───▼─────┐
   │  Plorp   │         │TaskWarr.│         │Obsidian │
   │   MCP    │         │  MCP    │         │  MCP    │
   │          │         │         │         │         │
   │Workflows:│         │Atomic:  │         │Atomic:  │
   │- start   │         │- create │         │- create │
   │- review  │         │- list   │         │- read   │
   │- inbox   │         │- mark   │         │- search │
   │          │         │  done   │         │         │
   │Atomic:   │         └─────────┘         └─────────┘
   │- task    │
   │- note    │
   │- link    │
   └──────────┘
```

**Why this works best:**

1. **Domain servers (TaskWarrior, Obsidian)** - Atomic tools only
   - Pure building blocks
   - Reusable across workflows
   - Simple to maintain

2. **Workflow servers (Plorp)** - Domain-specific workflows + atomic tools
   - Encapsulates your specific use cases
   - Can call domain servers OR implement directly
   - Provides both high-level and low-level access

3. **Agent (Claude)** - Orchestrates when needed
   - Can use high-level workflows: `plorp_start_day()`
   - Can use low-level tools: `taskwarrior_create_task()` + `obsidian_create_note()`
   - Flexibility when workflows don't fit

**Usage patterns:**

```
# Pattern 1: Use high-level workflow
User: "Start my day"
Claude: plorp_start_day("2025-10-06")
→ Fast, one call, deterministic

# Pattern 2: Custom workflow from atomic tools
User: "Create a task for 'Buy milk' and make a note about it"
Claude:
  1. taskwarrior_create_task("Buy milk")
  2. obsidian_create_note("notes/milk.md", "...")
  3. plorp_link_note_to_task("notes/milk.md", uuid)
→ Flexible, novel combinations

# Pattern 3: Mix both
User: "Start my day but skip the overdue tasks"
Claude:
  1. taskwarrior_get_tasks("due:today -OVERDUE")
  2. obsidian_create_note("daily/today.md", format_tasks(tasks))
→ Customizes existing workflow
```

### Decision Framework

**Use Pattern 1 (Agent Gateway)** if:
- ✅ Workflows are constantly changing
- ✅ You want maximum flexibility
- ✅ You're okay with slower execution (multiple LLM calls)
- ✅ Domain servers are third-party (can't modify)

**Use Pattern 2 (Bounded-Context)** if:
- ✅ You have stable, repeated workflows
- ✅ Performance matters (fewer tool calls)
- ✅ You control all the servers
- ✅ Workflows are domain-specific

**Use Pattern 3 (Planner/Executor)** if:
- ✅ You need workflow observability/auditing
- ✅ Workflows are long-running or complex
- ✅ You need retry/resume capabilities
- ✅ You want to version control workflows

**Use Hybrid** if:
- ✅ You want common workflows to be fast
- ✅ You want novel workflows to be possible
- ✅ You're building for your own use case
- ✅ **Recommended for plorp**

---

## Reliability and Consistency

### The Real Problem

For daily workflow systems, **consistency is critical**.

```
Monday: "Start my day"
→ Creates daily note ✓
→ Shows 7 tasks ✓
→ Clean output ✓

Tuesday: "Start my day"
→ Creates daily note ✓
→ "I notice you have several overdue tasks from yesterday..."
→ Starts analyzing your productivity patterns
→ Suggests reorganizing your priorities
→ 3 minutes of back-and-forth
❌ You just wanted your daily note

This is a real problem for daily workflows.
```

### What IS Deterministic

```python
# Plorp MCP Server Tool
@server.call_tool()
async def plorp_start_day(date: str):
    """This part is deterministic"""
    tasks = subprocess.run(['task', 'export', 'due:today'])
    note = format_daily_note(tasks)
    write_file(f"daily/{date}.md", note)
    return {"created": True, "tasks": len(tasks)}

# ✅ Same inputs → Same outputs
# ✅ Testable
# ✅ Predictable
```

### What is NOT Deterministic

```
User: "Start my day"

Claude (Agent) decides:
  Run 1:
    - Calls plorp_start_day("2025-10-06")
    - Returns: "I've created your daily note with 7 tasks"

  Run 2 (same request):
    - Calls plorp_start_day("2025-10-06")
    - Returns: "Your daily note is ready! You have 7 tasks due today.
               The most urgent one is 'Finish report' - would you like
               me to help you break that down?"

  Run 3 (same request):
    - Notices it's 6am
    - Calls plorp_start_day("2025-10-06")
    - Calls taskwarrior_get_tasks("priority:H")
    - Returns: "Good morning! Created your daily note. I see you have
               3 high-priority items. Want to tackle those first?"

# ❌ Different responses each time
# ❌ Different tool combinations
# ❌ Different conversational style
```

### Why This Happens

1. **LLM Generation is Stochastic** - Temperature > 0 means non-deterministic sampling
2. **Agent Makes Decisions** - Which tools, in what order, with what parameters
3. **Context Influences Behavior** - Previous conversations affect current behavior

### Solutions: Making It Reliable

#### Solution 1: MCP Tool Returns Structured Data (Recommended)

The key is: **MCP tool returns all the data, agent just presents it consistently**

```python
# Plorp MCP Server
@server.call_tool()
async def plorp_start_day(date: str) -> dict:
    """Generate daily note and return structured summary"""

    # Execute workflow (deterministic)
    overdue = get_overdue_tasks()
    due_today = get_due_today()
    recurring = get_recurring_today()

    note_path = create_daily_note(date, overdue, due_today, recurring)

    # Return structured data
    return {
        "status": "created",
        "note_path": str(note_path),
        "summary": {
            "overdue_count": len(overdue),
            "due_today_count": len(due_today),
            "recurring_count": len(recurring),
            "total_count": len(overdue) + len(due_today) + len(recurring)
        },
        "overdue_tasks": [
            {"description": t["description"], "uuid": t["uuid"]}
            for t in overdue[:5]  # First 5 only
        ],
        "due_today_tasks": [
            {"description": t["description"], "uuid": t["uuid"]}
            for t in due_today[:5]
        ]
    }
```

**Then constrain the agent's output format:**

```yaml
# System prompt or custom instruction
When user says "Start my day" or uses plorp_start_day:

1. Call plorp_start_day(today)
2. Present results in EXACTLY this format:

   ✅ Daily note created: {note_path}

   Summary:
   • {overdue_count} overdue tasks
   • {due_today_count} due today
   • {recurring_count} recurring

   [If overdue_count > 0:]
   Overdue:
   - {task 1 description}
   - {task 2 description}

   [If due_today_count > 0:]
   Due today:
   - {task 1 description}
   - {task 2 description}

3. Do NOT add commentary, suggestions, or analysis unless user asks
4. Do NOT call additional tools
```

This gives you **consistent presentation** with **reliable data**.

#### Solution 2: Custom Slash Command (Most Reliable)

Create a slash command that **guarantees** consistent behavior:

```bash
# .claude/commands/start-day.md
Call plorp_start_day with today's date.

Present the results in this exact format:

✅ Daily note created: {note_path}

Tasks for today:
• {overdue_count} overdue
• {due_today_count} due today
• {recurring_count} recurring

Do not add any additional commentary or call other tools.
```

Usage:
```
User: /start-day

Claude: [Follows exact format specified in command]
```

**This is more reliable** because:
- Slash command prompt is injected directly
- Overrides general agent behavior
- Specific, clear instructions
- Still uses stochastic agent but constrains it heavily

#### Solution 3: Separate Commands for Different Modes

```bash
# .claude/commands/start-day.md
Call plorp_start_day(today). Show only summary, no analysis.

# .claude/commands/start-day-detailed.md
Call plorp_start_day(today). Provide detailed analysis and suggestions.

# .claude/commands/start-day-interactive.md
Call plorp_start_day(today). Review tasks interactively with me.
```

```
User: /start-day          → Quick, consistent
User: /start-day-detailed → Agent analyzes
User: /start-day-interactive → Back-and-forth
```

#### Solution 4: Hybrid - MCP Tool + CLI Fallback

Most reliable approach:

```python
# Plorp MCP Server provides the tool
@server.call_tool()
async def plorp_start_day(date: str):
    """Agent can call this"""
    return create_daily_note(date)

# Also provide direct CLI (bypasses agent entirely)
$ plorp start
✅ Daily note created: /path/to/vault/daily/2025-10-06.md

Summary:
• 2 overdue tasks
• 5 due today
• 3 recurring

# 100% deterministic
```

**Use cases:**
- **Morning routine** → Use CLI directly (fast, consistent)
- **Ad-hoc requests** → Use agent (flexible, helpful)
- **Automation** → Use CLI (reliable, scriptable)

#### Solution 5: Workflow Engine Pattern

For maximum reliability, implement a **workflow specification** in the MCP tool:

```python
@server.call_tool()
async def plorp_start_day(date: str, mode: str = "summary"):
    """
    Modes:
    - summary: Just the facts (default)
    - detailed: Include task details
    - silent: Just create, return path only
    """

    result = create_daily_note(date)

    if mode == "silent":
        return {"note_path": result["path"]}

    elif mode == "summary":
        return {
            "note_path": result["path"],
            "summary": result["summary"]
            # No task details
        }

    elif mode == "detailed":
        return {
            "note_path": result["path"],
            "summary": result["summary"],
            "tasks": result["tasks"]  # Full details
        }
```

Then agent behavior is constrained by the tool's output.

### The Reliability Spectrum

```
Least Predictable ←――――――――――――――――――――――――→ Most Predictable

Natural language       Explicit              System           Deterministic
to agent              instructions          prompts          wrapper

"Start my day"     "Start my day,        System prompt:    $ plorp start
                   just call the         "When user
Agent interprets   tool"                 says X,           Pure CLI,
freely                                   always do Y"      no agent
                   Agent guided
                                         Agent              100%
Varies most                              constrained       deterministic

                                         Still some
                                         variation
```

### Summary: Reliability Strategies

**For Critical Daily Workflows:**

1. **The MCP tool will be deterministic:**
   ```python
   plorp_start_day("2025-10-06")
   # Always creates same note given same date and tasks
   ✅ Reliable
   ```

2. **The agent invocation will vary:**
   ```
   "Start my day" → Claude's interpretation
   # Might call plorp_start_day()
   # Might also analyze, prioritize, suggest
   # Might add helpful commentary
   # Might ask clarifying questions
   ⚠️ Variable
   ```

3. **But it's not a bug, it's a feature:**
   ```
   Monday: "Start my day"
   Claude: [Straightforward execution]

   Friday: "Start my day"
   Claude: "Created your daily note. I notice you've been crushing
            your goals this week - just 3 tasks today. Light day!"

   # Context-aware, adaptive, helpful
   ✨ This is why you use an agent
   ```

4. **When You Need Determinism:**
   ```bash
   # Option A: Direct CLI (bypass agent)
   $ plorp start

   # Option B: Cron job (scheduled)
   0 6 * * * /usr/local/bin/plorp start

   # Option C: Keyboard shortcut → script
   alias start-day='plorp start'

   # 100% deterministic, no agent variability
   ```

---

## Recommended Architecture for plorp

### The Three-Tier Architecture

#### Tier 1: Core Workflows (Maximum Reliability)

```bash
# Direct CLI - 100% deterministic
$ plorp start
$ plorp review
$ plorp inbox process

# Or cron/scheduled
0 6 * * * /usr/local/bin/plorp start
0 18 * * * /usr/local/bin/plorp review
```

#### Tier 2: Slash Commands (High Reliability)

```
User: /start-day
User: /review-day
User: /process-inbox

# Slash commands constrain agent behavior
# ~95% consistent presentation
# Still have agent flexibility for edge cases
```

#### Tier 3: Natural Language (Flexible, Variable)

```
User: "Start my day"
User: "Help me review my tasks"
User: "What's in my inbox?"

# Agent interprets freely
# May call additional tools
# May provide analysis
# Adaptive, conversational
# Variable presentation
```

### Usage Pattern

```
Morning (routine):
  $ plorp start                    ← Direct CLI, instant, consistent

During day (ad-hoc):
  "Create a task for 'Buy milk'"   ← Natural language to agent

Evening (routine):
  /review-day                      ← Slash command, consistent

Novel workflow:
  "Can you analyze my task completion rate this week?"
                                   ← Agent uses multiple tools
```

### Plorp MCP Server Design

Tools designed for reliability:

```python
# plorp MCP Server - tools designed for reliability

@server.call_tool()
async def plorp_start_day(date: str, verbose: bool = False):
    """
    verbose=False: Returns minimal summary (default)
    verbose=True: Returns detailed task info
    """
    result = execute_daily_start_workflow(date)

    if verbose:
        return result  # Full details
    else:
        return {
            "note_path": result["note_path"],
            "task_counts": result["summary"]
            # Minimal data = consistent agent output
        }

@server.call_tool()
async def plorp_review_day(date: str):
    """Returns uncompleted tasks for review"""
    # Returns structured list
    # Agent just presents the list
    # No room for creative interpretation

@server.call_tool()
async def plorp_complete_task(uuid: str):
    """Mark task complete - simple, atomic"""
    # Can't vary - just does the thing

@server.call_tool()
async def plorp_defer_task(uuid: str, new_date: str):
    """Defer task - simple, atomic"""
    # Can't vary - just does the thing
```

### Slash Commands

```markdown
# .claude/commands/start.md
Call plorp_start_day(today, verbose=false).

Output format:
✅ Daily note created: {note_path}
• {overdue} overdue, {due_today} due today, {recurring} recurring

Stop. Do not analyze or suggest.
```

```markdown
# .claude/commands/review.md
Call plorp_review_day(today).

For each task, ask me: [Done / Defer / Skip]
Then call the appropriate tool (plorp_complete_task or plorp_defer_task).

Do not provide analysis unless I ask.
```

### Three Interfaces

Build plorp with **three interfaces**:

1. **CLI** (`plorp start`) - Production use, automation, maximum reliability
2. **MCP + Slash Commands** (`/start-day`) - Daily interactive use, high reliability
3. **MCP + Natural Language** ("help me plan my day") - Ad-hoc, flexible

The MCP server code is the same for all three. You just choose the interface based on how much consistency vs flexibility you want.

### Implementation Recommendation

**Start with CLI for your core workflows.** Add MCP/agent interaction for the workflows that benefit from intelligence and adaptability.

### Project Structure

```
plorp/
├── src/plorp/
│   ├── cli.py                    # CLI interface (Tier 1)
│   ├── mcp_server.py             # MCP server interface (Tier 2 & 3)
│   ├── workflows/
│   │   ├── daily.py              # Core workflow logic
│   │   ├── inbox.py
│   │   └── notes.py
│   ├── integrations/
│   │   ├── taskwarrior.py        # Direct TaskWarrior integration
│   │   └── obsidian.py           # Direct Obsidian integration
│   └── ...
│
├── .claude/
│   └── commands/
│       ├── start-day.md          # Slash commands
│       ├── review-day.md
│       └── process-inbox.md
│
└── scripts/
    └── install.sh
```

### Compatibility with Current Spec

The current plorp specification (Phases 0-5) is **highly compatible** with building an MCP server as Phase 6.

**Strong Compatibility Factors:**

1. **Clean Module Separation**
   - `integrations/taskwarrior.py` - Already designed as wrapper functions
   - `workflows/daily.py`, `workflows/inbox.py` - Self-contained workflow logic
   - These modules can become MCP tools with minimal refactoring

2. **Stateless Design**
   - Plorp is designed to be stateless (reads TaskWarrior/Obsidian each time)
   - Perfect for MCP server architecture (each tool call is independent)

3. **Function-Based API**
   - Current design: `daily.start(config)`, `inbox.process(config)`
   - MCP equivalent: `plorp_start(date)`, `plorp_inbox_process()`
   - Almost 1:1 mapping

4. **Direct Integration Approach**
   - Spec already uses subprocess for TaskWarrior (CLI calls)
   - Already uses file operations for Obsidian (markdown files)
   - No dependency on other MCP servers - can work standalone

**Implementation Path:**

1. **Phases 0-5**: Build CLI tool as specified
2. **Phase 6**: Create MCP server wrapper around existing modules

Benefits:
- CLI tool useful for testing/debugging
- Can be used without Claude
- MCP server reuses all logic
- Easy to maintain both

### Best of Both Worlds

```
Reliability when you need it:
  - CLI for automation
  - Slash commands for daily use
  - Structured tool outputs

Flexibility when you want it:
  - Natural language for novel requests
  - Agent analyzes on demand
  - Creative problem-solving
```

---

## Conclusion

This guide has covered:

1. **MCP Server Setup** - How to install and configure MCP servers with Claude Desktop
2. **MCP Servers vs Agents** - Understanding the relationship and distinctions
3. **Stochastic vs Deterministic** - The core design principle for agents vs tools
4. **Technical Definition of Agents** - How agents actually work under the hood
5. **Architectural Patterns** - Three patterns for multi-tool workflows, and when to use each
6. **Reliability and Consistency** - Strategies for making daily workflows reliable
7. **Recommended Architecture** - Three-tier approach for plorp with maximum flexibility and reliability

**Key Takeaways:**

- Agents (stochastic) orchestrate, MCP servers (deterministic) execute
- Use hybrid architecture: workflow servers + atomic servers + agent orchestration
- Provide three interfaces: CLI (max reliability), slash commands (high reliability), natural language (max flexibility)
- Choose the right tool for the job: determinism for routines, intelligence for novel tasks

---

**Document Version:** 1.0
**Last Updated:** October 6, 2025
**Status:** Comprehensive reference guide
