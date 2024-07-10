from pytest import MonkeyPatch, warns

from epidatpy._auth import _get_api_key


def test_get_api_key(monkeypatch: MonkeyPatch) -> None:
    with monkeypatch.context() as m:
        m.setenv("DELPHI_EPIDATA_KEY", "test")
        assert _get_api_key() == "test"
        m.delenv("DELPHI_EPIDATA_KEY")
        with warns(UserWarning):
            assert _get_api_key() == ""
