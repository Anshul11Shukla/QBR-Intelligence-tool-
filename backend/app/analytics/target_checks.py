
def check_target(
    value: float | None,
    target: float | None,
    direction: str,
) -> bool | None:
    if value is None or target is None:
        return None

    if direction == "higher":
        return value >= target

    if direction == "lower":
        return value <= target

    raise ValueError("Unknown KPI direction")
