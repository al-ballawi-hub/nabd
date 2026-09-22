import os
import tempfile
from pathlib import Path

# Isolated temp database for tests — must be set before importing the app.
_tmp_dir = Path(tempfile.mkdtemp(prefix="nabd_test_"))
os.environ["DATABASE_URL"] = f"sqlite:///{(_tmp_dir / 'test.db').as_posix()}"
# Force the mock AI path in tests (no external DeepSeek calls).
os.environ["DEEPSEEK_API_KEY"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import init_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    init_db()
    with TestClient(app) as c:
        yield c
