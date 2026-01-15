# Agents module
Contains the Langgraph module used for all of the agent-related business logics in the app. This supports Langgraph CLI and Langgraph Studio, making it easier to manage all of the agents separately from the rest of the app.

## Folder Structure
The structure will be service-based where each folder, apart from the reserved folder names such as `/utils`, represents a flow or an agent. Each service folder will contain an agent with its own resources such as nodes, tools, prompts, and states. In case of orchestration between agents, each agents can call each other within the `/app/agent` module, making it possible to create supervisor / orchestrator agent that calls other agent.

## To Do List:
- [ ] Graph object 
- [ ] Default nodes
- [ ] Default edges 
- [ ] Config / Context
- [ ] Default Prompt
- [ ] Default agent state
- [ ] ReAct Agent service
  - [ ] Nodes
    - [ ] LLM Call (env configs passed through agent config)
  - [ ] Tools
- [ ] Expose only the `main.py` through the `__init__.py`