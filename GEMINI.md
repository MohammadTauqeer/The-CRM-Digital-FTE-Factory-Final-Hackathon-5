# CRM FTE Factory - Project Progress

This file tracks the exercises and progress of the TechCorp customer support agent prototype.

## Exercises

### Phase 1: Prototype Development
- [x] **Exercise 1.1: Basic Agent Setup** - Initial prototype with system instructions and knowledge base.
- [x] **Exercise 1.2: Structured Output & Channels** - Added JSON output schema and channel-specific tone/formatting.
- [x] **Exercise 1.3: Add Memory and State** - Implemented Gemini Chat Sessions to maintain conversation history.
- [x] **Exercise 1.4: MCP Tools Integration** - Implemented and verified Model Context Protocol tools.
- [x] **Exercise 1.5: Define Agent Skills** - Formalized agent capabilities into a skills manifest.

### Phase 2: Specialization
- [x] **Exercise 2.1: Tool-Enabled Custom Agent** - Transitioned prototype to a specialized agent with function calling and enforced workflow.
- [x] **Exercise 2.2: Database & API Foundation** - Implementing PostgreSQL schema and FastAPI layer for CRM data.

## Architecture Notes
- **Model:** `gemini-flash-latest`
- **Output Format:** JSON (structured via `typing.TypedDict`)
- **State Management:** Gemini Chat Sessions (`model.start_chat`)
- **Tooling:** MCP Server (`mcp_server.py`)
- **Skills Manifest:** `specs/agent-skills.json`
