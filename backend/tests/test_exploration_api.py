from importlib import reload
from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient


def test_explore_api_persists_job(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")

    import app.core.config as config
    import app.db.session as session
    import app.db.models as models
    import app.db.init_db as init_db
    import app.main as main

    reload(config)
    reload(session)
    reload(models)
    reload(init_db)
    reload(main)

    init_db.init_db()

    file_path = tmp_path / "sample.csv"
    pd.DataFrame({"name": ["Alice", "Alice", "Bob"], "age": [30, None, 40]}).to_csv(file_path, index=False)

    with TestClient(main.app) as client, file_path.open("rb") as fp:
        response = client.post("/api/explore", files={"file": ("sample.csv", fp, "text/csv")})

    assert response.status_code == 200
    data = response.json()
    assert data["exploration"]["summary"]["rows"] == 3
    assert data["exploration"]["summary"]["columns"] == 2
    assert data["preprocessing"]["required"] is True
    assert len(data["visualization"]["charts"]) >= 1
    assert len(data["insights"]["summary_points"]) >= 1
    assert data["job_id"] > 0
    assert db_path.exists()
