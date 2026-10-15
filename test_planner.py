import os
import shutil
import unittest
import json
from storage import DB_DIR, OUT_DIR
from user import User
from team import Team
from project_board import ProjectBoard


class TestTeamPlanner(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(DB_DIR, ignore_errors=True)
        shutil.rmtree(OUT_DIR, ignore_errors=True)
        os.makedirs(DB_DIR, exist_ok=True)
        os.makedirs(OUT_DIR, exist_ok=True)
        self.user_api = User()
        self.team_api = Team()
        self.board_api = ProjectBoard()

    def test_complete_flow(self):
        # 1. Create User
        u1 = json.loads(self.user_api.create_user(json.dumps({
            "name": "alice_dev",
            "display_name": "Alice Developer"
        })))
        u1_id = u1["id"]

        # 2. Duplicate User Name should raise ValueError
        with self.assertRaises(ValueError):
            self.user_api.create_user(json.dumps({
                "name": "alice_dev",
                "display_name": "Alice Duplicate"
            }))

        # 3. Create Team
        t1 = json.loads(self.team_api.create_team(json.dumps({
            "name": "Platform Team",
            "description": "Core Infrastructure",
            "admin": u1_id
        })))
        t1_id = t1["id"]

        # 4. Create Board
        b1 = json.loads(self.board_api.create_board(json.dumps({
            "name": "Sprint 1",
            "description": "Sprint 1 deliverables",
            "team_id": t1_id
        })))
        b1_id = b1["id"]

        # 5. Add Task
        task1 = json.loads(self.board_api.add_task(json.dumps({
            "title": "Setup Django routing",
            "description": "Configure urls and views",
            "user_id": u1_id,
            "board_id": b1_id
        })))
        task1_id = task1["id"]

        # 6. Cannot close board while task is OPEN
        with self.assertRaises(ValueError):
            self.board_api.close_board(json.dumps({"id": b1_id}))

        # 7. Update Task to COMPLETE and close board
        self.board_api.update_task_status(json.dumps({
            "id": task1_id,
            "status": "COMPLETE"
        }))
        self.board_api.close_board(json.dumps({"id": b1_id}))

        # 8. Export Board
        export_res = json.loads(self.board_api.export_board(json.dumps({"id": b1_id})))
        self.assertTrue(os.path.exists(os.path.join(OUT_DIR, export_res["out_file"])))


if __name__ == "__main__":
    unittest.main()
