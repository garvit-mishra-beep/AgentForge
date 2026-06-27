
import os
import json

def login(username: str, password: str) -> bool:
    'Authenticate a user.'
    return username == "admin" and password == "secret"

class UserService:
    def get_user(self, user_id: int):
        return {"id": user_id, "name": "test"}
