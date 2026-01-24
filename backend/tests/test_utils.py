from app.utils import get_request_id


def test_get_request_id():
    assert isinstance(get_request_id(), str)