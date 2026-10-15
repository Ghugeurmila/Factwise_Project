import json
from datetime import datetime
from user_base import UserBase
from storage import FileStorage


class User(UserBase):
    def _validate_request(self, request: str) -> dict:
        if not request:
            raise ValueError("Request body cannot be empty.")
        try:
            return json.loads(request)
        except Exception as e:
            raise ValueError(f"Invalid JSON: {str(e)}")

    def create_user(self, request: str) -> str:
        data = self._validate_request(request)
        name = data.get("name")
        display_name = data.get("display_name")

        if not name or not isinstance(name, str) or len(name) > 64:
            raise ValueError("Name is required and must not exceed 64 characters.")
        if not display_name or not isinstance(display_name, str) or len(display_name) > 64:
            raise ValueError("Display name is required and must not exceed 64 characters.")

        users = FileStorage.load("users")
        for user_id, user_data in users.items():
            if user_data["name"] == name:
                raise ValueError(f"User with name '{name}' already exists.")

        new_id = FileStorage.next_id("users")
        users[new_id] = {
            "id": new_id,
            "name": name,
            "display_name": display_name,
            "creation_time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }
        FileStorage.save("users", users)
        return json.dumps({"id": new_id})

    def list_users(self) -> str:
        users = FileStorage.load("users")
        result = [
            {
                "name": u["name"],
                "display_name": u["display_name"],
                "creation_time": u["creation_time"]
            }
            for u in users.values()
        ]
        return json.dumps(result)

    def describe_user(self, request: str) -> str:
        data = self._validate_request(request)
        user_id = str(data.get("id"))

        users = FileStorage.load("users")
        if user_id not in users:
            raise ValueError(f"User with id '{user_id}' does not exist.")

        u = users[user_id]
        return json.dumps({
            "name": u["name"],
            "description": u.get("display_name", ""),
            "creation_time": u["creation_time"]
        })

    def update_user(self, request: str) -> str:
        data = self._validate_request(request)
        user_id = str(data.get("id"))
        user_updates = data.get("user", {})

        users = FileStorage.load("users")
        if user_id not in users:
            raise ValueError(f"User with id '{user_id}' does not exist.")

        existing = users[user_id]
        if "name" in user_updates and user_updates["name"] != existing["name"]:
            raise ValueError("User name cannot be updated.")

        display_name = user_updates.get("display_name")
        if display_name:
            if not isinstance(display_name, str) or len(display_name) > 128:
                raise ValueError("Display name can be max 128 characters.")
            existing["display_name"] = display_name

        users[user_id] = existing
        FileStorage.save("users", users)
        return json.dumps({"status": "SUCCESS"})

    def get_user_teams(self, request: str) -> str:
        data = self._validate_request(request)
        user_id = str(data.get("id"))

        users = FileStorage.load("users")
        if user_id not in users:
            raise ValueError(f"User with id '{user_id}' does not exist.")

        teams = FileStorage.load("teams")
        user_teams = []
        for team in teams.values():
            if user_id in team.get("members", []):
                user_teams.append({
                    "name": team["name"],
                    "description": team["description"],
                    "creation_time": team["creation_time"]
                })

        return json.dumps(user_teams)