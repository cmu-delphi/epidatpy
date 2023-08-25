from pytest import warns, MonkeyPatch

from epidatpy import get_api_key


def test_get_api_key(monkeypatch: MonkeyPatch) -> None:
    with monkeypatch.context() as m:
        m.setenv("DELPHI_EPIDATA_KEY", "test")
        assert get_api_key() == "test"
        m.delenv("DELPHI_EPIDATA_KEY")
        with warns(UserWarning):
            assert get_api_key() is None
