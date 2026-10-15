import json
from datetime import datetime
from team_base import TeamBase
from storage import FileStorage


class Team(TeamBase):
    def _validate_request(self, request: str) -> dict:
        if not request:
            raise ValueError("Request body cannot be empty.")
        try:
            return json.loads(request)
        except Exception as e:
            raise ValueError(f"Invalid JSON: {str(e)}")

    def create_team(self, request: str) -> str:
        data = self._validate_request(request)
        name = data.get("name")
        description = data.get("description")
        admin_id = str(data.get("admin"))

        if not name or not isinstance(name, str) or len(name) > 64:
            raise ValueError("Team name is required and can be max 64 characters.")
        if not description or not isinstance(description, str) or len(description) > 128:
            raise ValueError("Description is required and can be max 128 characters.")

        users = FileStorage.load("users")
        if admin_id not in users:
            raise ValueError(f"Admin user id '{admin_id}' does not exist.")

        teams = FileStorage.load("teams")
        for t in teams.values():
            if t["name"] == name:
                raise ValueError(f"Team name '{name}' already exists.")

        new_id = FileStorage.next_id("teams")
        teams[new_id] = {
            "id": new_id,
            "name": name,
            "description": description,
            "admin": admin_id,
            "creation_time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "members": [admin_id]
        }
        FileStorage.save("teams", teams)
        return json.dumps({"id": new_id})

    def list_teams(self) -> str:
        teams = FileStorage.load("teams")
        result = [
            {
                "name": t["name"],
                "description": t["description"],
                "creation_time": t["creation_time"],
                "admin": t["admin"]
            }
            for t in teams.values()
        ]
        return json.dumps(result)

    def describe_team(self, request: str) -> str:
        data = self._validate_request(request)
        team_id = str(data.get("id"))

        teams = FileStorage.load("teams")
        if team_id not in teams:
            raise ValueError(f"Team with id '{team_id}' does not exist.")

        t = teams[team_id]
        return json.dumps({
            "name": t["name"],
            "description": t["description"],
            "creation_time": t["creation_time"],
            "admin": t["admin"]
        })

    def update_team(self, request: str) -> str:
        data = self._validate_request(request)
        team_id = str(data.get("id"))
        team_updates = data.get("team", {})

        teams = FileStorage.load("teams")
        if team_id not in teams:
            raise ValueError(f"Team with id '{team_id}' does not exist.")

        name = team_updates.get("name")
        description = team_updates.get("description")
        admin_id = str(team_updates.get("admin")) if team_updates.get("admin") else None

        if name:
            if not isinstance(name, str) or len(name) > 64:
                raise ValueError("Name can be max 64 characters.")
            for tid, t in teams.items():
                if tid != team_id and t["name"] == name:
                    raise ValueError(f"Team name '{name}' already in use.")
            teams[team_id]["name"] = name

        if description:
            if not isinstance(description, str) or len(description) > 128:
                raise ValueError("Description can be max 128 characters.")
            teams[team_id]["description"] = description

        if admin_id:
            users = FileStorage.load("users")
            if admin_id not in users:
                raise ValueError(f"User '{admin_id}' does not exist.")
            teams[team_id]["admin"] = admin_id
            if admin_id not in teams[team_id]["members"]:
                teams[team_id]["members"].append(admin_id)

        FileStorage.save("teams", teams)
        return json.dumps({"status": "SUCCESS"})

    def add_users_to_team(self, request: str):
        data = self._validate_request(request)
        team_id = str(data.get("id"))
        user_ids = [str(uid) for uid in data.get("users", [])]

        teams = FileStorage.load("teams")
        if team_id not in teams:
            raise ValueError(f"Team with id '{team_id}' does not exist.")

        users = FileStorage.load("users")
        for uid in user_ids:
            if uid not in users:
                raise ValueError(f"User with id '{uid}' does not exist.")

        current_members = set(teams[team_id].get("members", []))
        new_members = current_members.union(set(user_ids))

        if len(new_members) > 50:
            raise ValueError("Cannot exceed maximum cap of 50 users per team.")

        teams[team_id]["members"] = list(new_members)
        FileStorage.save("teams", teams)
        return json.dumps({"status": "SUCCESS"})

    def remove_users_from_team(self, request: str):
        data = self._validate_request(request)
        team_id = str(data.get("id"))
        user_ids = [str(uid) for uid in data.get("users", [])]

        teams = FileStorage.load("teams")
        if team_id not in teams:
            raise ValueError(f"Team with id '{team_id}' does not exist.")

        current_members = set(teams[team_id].get("members", []))
        for uid in user_ids:
            current_members.discard(uid)

        teams[team_id]["members"] = list(current_members)
        FileStorage.save("teams", teams)
        return json.dumps({"status": "SUCCESS"})

    def list_team_users(self, request: str):
        data = self._validate_request(request)
        team_id = str(data.get("id"))

        teams = FileStorage.load("teams")
        if team_id not in teams:
            raise ValueError(f"Team with id '{team_id}' does not exist.")

        users = FileStorage.load("users")
        members = teams[team_id].get("members", [])
        result = []
        for uid in members:
            if uid in users:
                u = users[uid]
                result.append({
                    "id": u["id"],
                    "name": u["name"],
                    "display_name": u["display_name"]
                })
        return json.dumps(result)