# Skill: Add a New Agent

Use this every time a new agent is added to LifeOS.

## Steps

### 1. Create the agent file
Create `/backend/agents/<name>.py` using this template:

```python
"""
<AgentName> — <one line description of role>
"""

import logging
from backend.memory.db import get_db
from backend.tools.<relevant_tool> import <ToolClass>  # if needed

logger = logging.getLogger(__name__)


class <AgentName>Agent:
    def __init__(self):
        self.db = get_db()
        # initialise any tools here

    def run(self, task: str) -> str:
        """
        Main entry point. Receives a task string, returns a response string.
        All agent logic lives here or in private methods below.
        """
        logger.info(f"<AgentName> received task: {task}")
        try:
            result = self._handle(task)
            logger.info(f"<AgentName> completed task: {result}")
            return result
        except Exception as e:
            logger.error(f"<AgentName> error: {e}")
            return f"Error: {str(e)}"

    def _handle(self, task: str) -> str:
        # implement logic here
        raise NotImplementedError
```

### 2. Register in Albus
Open `/backend/agents/albus.py` and add the new agent to the routing map:

```python
from backend.agents.<name> import <AgentName>Agent

AGENT_MAP = {
    ...
    "<trigger_keyword>": <AgentName>Agent,
}
```

### 3. Add DB tables if needed
Follow /skills/add-db-table.md before writing any new DB logic.

### 4. Add a log file reference
Logs automatically go to `/logs/<agentname>.log` via the logger name. No extra setup needed.

### 5. Add to scheduler if needed
If the agent runs on a schedule (not just on demand), add it to `/backend/scheduler/jobs.py`:

```python
from backend.agents.<name> import <AgentName>Agent

scheduler.add_job(
    func=<AgentName>Agent().run,
    trigger="cron",
    hour=8,  # adjust as needed
    id="<agentname>_daily",
)
```

### 6. Update CLAUDE.md
Add the new agent to the agents table in CLAUDE.md with its status.

### 7. Write a quick test
Create `/backend/agents/test_<name>.py` with at least one happy path test.

## Checklist
- [ ] Agent file created from template
- [ ] Registered in Albus routing map
- [ ] DB tables added if needed
- [ ] Scheduler job added if needed
- [ ] CLAUDE.md agents table updated
- [ ] Basic test written
