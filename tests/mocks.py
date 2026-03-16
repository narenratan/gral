class mock_open_output:
    def __init__(self, name):
        self._name = name

    def __enter__(self):
        print(f"Opening {self._name}")
        return MockMidoOutput()

    def __exit__(self, exc_type, exc_val, exc_tb):
        print(f"Closing {self._name}")


class MockMidoOutput:
    def send(self, x):
        print(x)


def printer(name):
    return lambda *args: print(name + "(" + ", ".join(map(str, args)) + ")")
