# HITL Sample Size Planner

Offline Windows tool under construction. Python 3.11; Flask is the only runtime dependency.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe hitl_planner.py
```

Open http://127.0.0.1:5062/ after launch. Stop with Ctrl-C. The first launch atomically creates `config.json` beside the script and the workspace at `%USERPROFILE%\Documents\HITL Planner`. Config and user records are excluded from Git. Invalid config is preserved and exits 2. Port 5062 is provisional until both existing tool launchers are checked. Current stage: config, placeholder page and health endpoint; statistical functionality is not yet implemented.

See `todo.md` for actual progress, `AGENTS.md` for project rules and `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the authoritative contract. GitHub publication is pending repository access.
