from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_download():
    response = client.post("/download", json={"url": "https://youtu.be/AzION-X5cEU?si=J7tpWv-LthDaDz6-"})
    assert response.status_code == 200