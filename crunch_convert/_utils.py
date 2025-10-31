class MockedWriteTextIO:

    def write(self, *args, **kwargs):  # type: ignore
        pass  # pragma: no cover

    def __enter__(self):  # type: ignore
        return self  # pragma: no cover

    def __exit__(self, exc_type, exc_value, traceback):  # type: ignore
        pass  # pragma: no cover
