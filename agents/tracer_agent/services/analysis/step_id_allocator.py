class StepIdAllocator:
    def __init__(self) -> None:
        self._next = 0

    def next(self) -> str:
        step_id = f"s{self._next}"
        self._next += 1
        return step_id
