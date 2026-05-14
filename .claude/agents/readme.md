# Agents

Sub-agents are specialized Claude instances spawned via the `Task` tool to work in parallel or handle specific responsibilities within a larger workflow.

## What Belongs Here

Each file defines a named agent with:
- A specific **role** and area of responsibility
- The **tools** it is allowed to use
- Any **constraints** or behavioral guidelines
- Expected **inputs and outputs**

## File Naming

Name files descriptively: `<role>.md`
Examples: `researcher.md`, `coder.md`, `reviewer.md`, `tester.md`

## Agent File Template

```
# Agent: <Name>

## Role
<What this agent does>

## Tools
- Bash
- Read
- Write

## Instructions
<Detailed instructions for this agent>

## Output Format
<What the agent should return to the orchestrator>
```

## How Agents Are Invoked

Agents are launched by Claude (the orchestrator) using the `Task` tool:

```
Task(description="...", prompt="...")
```

The orchestrator delegates subtasks, collects results, and synthesizes the final output.