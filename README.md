# Team Project Planner Tool

## Overview
A backend implementation for managing users, teams, project boards, and tasks. The service adheres strictly to the provided abstract base interfaces (`UserBase`, `TeamBase`, and `ProjectBoardBase`) while persisting all domain state into local JSON files in the `db/` directory.

## Architecture & Design Decisions
1. **Interface Compliance**: Concrete implementations (`User`, `Team`, `ProjectBoard`) extend the corresponding base interfaces, accepting and returning standardized JSON strings.
2. **Persistence Strategy (`storage.py`)**:
   - Persisted as isolated, flat-file JSON collections (`users.json`, `teams.json`, `boards.json`, `tasks.json`) under the `db/` folder.
   - Atomic writes via temporary file replacement (`os.replace`) to ensure crash consistency and guard against corruption.
   - Abstracted behind `FileStorage` to keep callers decoupled from disk storage mechanics.
3. **Identifier Generation**: Sequential numeric IDs represented as strings for predictable lookup, foreign key references, and clean JSON payloads.
4. **Validation & Integrity Constraints**:
   - String length restrictions enforced across user names (<=64), display names (<=64, or <=128 on update), team names (<=64), descriptions (<=128), and task titles (<=64).
   - Uniqueness enforced for user names globally, team names globally, and task titles per board.
   - Membership cap enforced at 50 users per team.
   - Project boards cannot be marked as closed until all associated tasks reach `COMPLETE` status.
5. **Board Export**: Formats board metadata, lifecycle timestamps, and task distributions into a formatted text file in the `out/` directory.

## Directory Structure
```text
factwise-python/
├── db/                     # Flat-file database storage
├── out/                    # Board export outputs
├── project_board_base.py   # Base abstract class for boards
├── project_board.py        # Concrete board & task logic
├── storage.py              # Atomic file storage manager
├── team_base.py            # Base abstract class for teams
├── team.py                 # Concrete team logic
├── user_base.py            # Base abstract class for users
├── user.py                 # Concrete user logic
├── test_planner.py         # Unit tests covering end-to-end flows
├── requirements.txt        # Dependencies
└── README.md