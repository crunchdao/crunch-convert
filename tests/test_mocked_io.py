from crunch_convert._utils import MockedWriteTextIO


def test_context_manager():
    with MockedWriteTextIO() as mocked_io:
        assert mocked_io is not None
        mocked_io.write(b"hello")  # type: ignore
