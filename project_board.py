import json
import os
from datetime import datetime
from project_board_base import ProjectBoardBase
from storage import FileStorage, OUT_DIR


class ProjectBoard(ProjectBoardBase):
    VALID_STATUSES = {"OPEN", "IN_PROGRESS", "COMPLETE"}

    def _validate_request(self, request: str) -> dict:
        if not request:
            raise ValueError("Request body cannot be empty.")
        try:
            return json.loads(request)
        except Exception as e:
            raise ValueError(f"Invalid JSON: {str(e)}")

    def create_board(self, request: str):
        data = self._validate_request(request)
        name = data.get("name")
        description = data.get("description")
        team_id = str(data.get("team_id"))

        if not name or not isinstance(name, str) or len(name) > 64:
            raise ValueError("Board name is required and can be max 64 characters.")
        if not description or not isinstance(description, str) or len(description) > 128:
            raise ValueError("Description is required and can be max 128 characters.")

        teams = FileStorage.load("teams")
        if team_id not in teams:
            raise ValueError(f"Team with id '{team_id}' does not exist.")

        boards = FileStorage.load("boards")
        for b in boards.values():
            if b["team_id"] == team_id and b["name"] == name:
                raise ValueError(f"Board '{name}' already exists in this team.")

        new_id = FileStorage.next_id("boards")
        boards[new_id] = {
            "id": new_id,
            "name": name,
            "description": description,
            "team_id": team_id,
            "creation_time": data.get("creation_time") or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "OPEN",
            "end_time": None
        }
        FileStorage.save("boards", boards)
        return json.dumps({"id": new_id})

    def close_board(self, request: str) -> str:
        data = self._validate_request(request)
        board_id = str(data.get("id"))

        boards = FileStorage.load("boards")
        if board_id not in boards:
            raise ValueError(f"Board with id '{board_id}' does not exist.")

        tasks = FileStorage.load("tasks")
        board_tasks = [t for t in tasks.values() if t.get("board_id") == board_id]

        for task in board_tasks:
            if task.get("status") != "COMPLETE":
                raise ValueError("Cannot close board: not all tasks are marked as COMPLETE.")

        boards[board_id]["status"] = "CLOSED"
        boards[board_id]["end_time"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        FileStorage.save("boards", boards)
        return json.dumps({"status": "SUCCESS"})

    def add_task(self, request: str) -> str:
        data = self._validate_request(request)
        title = data.get("title")
        description = data.get("description")
        user_id = str(data.get("user_id"))
        board_id = str(data.get("board_id"))

        if not title or not isinstance(title, str) or len(title) > 64:
            raise ValueError("Task title is required and can be max 64 characters.")
        if not description or not isinstance(description, str) or len(description) > 128:
            raise ValueError("Description can be max 128 characters.")

        boards = FileStorage.load("boards")
        if board_id not in boards:
            raise ValueError(f"Board with id '{board_id}' does not exist.")

        if boards[board_id]["status"] != "OPEN":
            raise ValueError("Can only add tasks to an OPEN board.")

        users = FileStorage.load("users")
        if user_id not in users:
            raise ValueError(f"User with id '{user_id}' does not exist.")

        tasks = FileStorage.load("tasks")
        for t in tasks.values():
            if t.get("board_id") == board_id and t.get("title") == title:
                raise ValueError(f"Task title '{title}' must be unique for this board.")

        new_id = FileStorage.next_id("tasks")
        tasks[new_id] = {
            "id": new_id,
            "title": title,
            "description": description,
            "user_id": user_id,
            "board_id": board_id,
            "creation_time": data.get("creation_time") or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "OPEN"
        }
        FileStorage.save("tasks", tasks)
        return json.dumps({"id": new_id})

    def update_task_status(self, request: str):
        data = self._validate_request(request)
        task_id = str(data.get("id"))
        status = data.get("status")

        if status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status '{status}'. Must be one of {self.VALID_STATUSES}.")

        tasks = FileStorage.load("tasks")
        if task_id not in tasks:
            raise ValueError(f"Task with id '{task_id}' does not exist.")

        tasks[task_id]["status"] = status
        FileStorage.save("tasks", tasks)
        return json.dumps({"status": "SUCCESS"})

    def list_boards(self, request: str) -> str:
        data = self._validate_request(request)
        team_id = str(data.get("id"))

        boards = FileStorage.load("boards")
        open_boards = [
            {"id": b["id"], "name": b["name"]}
            for b in boards.values()
            if b.get("team_id") == team_id and b.get("status") == "OPEN"
        ]
        return json.dumps(open_boards)

    def export_board(self, request: str) -> str:
        data = self._validate_request(request)
        board_id = str(data.get("id"))

        boards = FileStorage.load("boards")
        if board_id not in boards:
            raise ValueError(f"Board with id '{board_id}' does not exist.")

        board = boards[board_id]
        tasks = FileStorage.load("tasks")
        users = FileStorage.load("users")
        teams = FileStorage.load("teams")

        team_name = teams.get(board["team_id"], {}).get("name", "Unknown Team")
        board_tasks = [t for t in tasks.values() if t.get("board_id") == board_id]

        divider = "=" * 70
        subdivider = "-" * 70

        content = [
            divider,
            f"PROJECT BOARD: {board['name'].upper()} (ID: {board_id})",
            divider,
            f"Team        : {team_name} (Team ID: {board['team_id']})",
            f"Status      : {board.get('status', 'OPEN')}",
            f"Description : {board.get('description', '')}",
            f"Created At  : {board.get('creation_time', '')}",
            f"Closed At   : {board.get('end_time', 'N/A')}",
            subdivider,
            f"TASKS LIST ({len(board_tasks)} total):",
            subdivider,
        ]

        if not board_tasks:
            content.append("  (No tasks found on this board)")
        else:
            for idx, task in enumerate(board_tasks, 1):
                assigned_user = users.get(task["user_id"], {}).get("display_name", f"User {task['user_id']}")
                content.extend([
                    f"[{idx}] {task['title']} [Status: {task['status']}]",
                    f"    ID          : {task['id']}",
                    f"    Assigned To : {assigned_user} (ID: {task['user_id']})",
                    f"    Created At  : {task['creation_time']}",
                    f"    Description : {task['description']}",
                    ""
                ])

        content.append(divider)
        filename = f"board_{board_id}_export.txt"
        out_filepath = os.path.join(OUT_DIR, filename)

        with open(out_filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(content))

        return json.dumps({"out_file": filename})