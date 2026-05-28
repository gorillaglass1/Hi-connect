import os

from app.core.config import _load_dotenv_fallback


def test_load_dotenv_fallback_reads_env_file_without_overriding_existing_env(
    monkeypatch,
    tmp_path,
):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "# comment",
                "EXISTING=value_from_file",
                "NEW_VALUE=loaded",
                'QUOTED_VALUE="quoted loaded"',
                "export EXPORTED_VALUE=from_export",
                "INVALID-NAME=ignored",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("EXISTING", "already_set")

    _load_dotenv_fallback(env_path)

    assert "INVALID-NAME" not in os.environ
    assert os.environ["EXISTING"] == "already_set"
    assert os.environ["NEW_VALUE"] == "loaded"
    assert os.environ["QUOTED_VALUE"] == "quoted loaded"
    assert os.environ["EXPORTED_VALUE"] == "from_export"
