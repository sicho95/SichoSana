import importlib
import os
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient

def test_sync_and_auth():
    with tempfile.TemporaryDirectory() as directory:
        os.environ["SICHOSANA_DB_PATH"] = str(Path(directory) / "sichosana.sqlite3")
        os.environ["SICHOSANA_REGISTRATION_ENABLED"] = "1"
        module = importlib.import_module("server.app")
        module = importlib.reload(module)
        with TestClient(module.app) as client:
            assert client.get("/api/v1/health").json()["ok"] is True
            creds = {"username":"testperson","password":"treslonguedemo123!"}
            register=client.post("/api/v1/auth/register",json=creds)
            assert register.status_code==200,register.text
            token=register.json()["token"]
            headers={"Authorization":"Bearer "+token}
            assert client.get("/api/v1/state",headers=headers).json()=={"revision":0,"state":None}
            state={"version":1,"activeProfileId":"p1","profiles":[{"id":"p1","name":"Démo"}],"logs":[],"settings":{}}
            result=client.put("/api/v1/state",headers=headers,json={"revision":0,"state":state})
            assert result.status_code==200 and result.json()["revision"]==1
            conflict=client.put("/api/v1/state",headers=headers,json={"revision":0,"state":state})
            assert conflict.status_code==409
            assert client.get("/api/v1/state",headers=headers).json()["state"]["profiles"][0]["name"]=="Démo"
            assert client.post("/api/v1/auth/login",json=creds).status_code==200
            assert client.post("/api/v1/auth/login",json={**creds,"password":"incorrect123456"}).status_code==401
            assert client.get("/api/v1/state").status_code==401
            assert client.get("/").status_code==200
