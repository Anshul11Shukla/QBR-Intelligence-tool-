
def calculate_change(
    previous: float | None,
    current: float | None,
) -> tuple[float | None, float | None]:
    if previous is None or current is None:
        return None, None

    absolute = round(current - previous, 4)

    if previous == 0:
        return absolute, None

    percentage = round(
        ((current - previous) / abs(previous)) * 100,
        2,
    )

    return absolute, percentage


def movement_status(
    previous: float | None,
    current: float | None,
    direction: str,
) -> str:
    if previous is None or current is None:
        return "insufficient_data"

    if previous == current:
        return "unchanged"

    improvement = (
        current > previous
        if direction == "higher"
        else current < previous
    )

    return "improved" if improvement else "declined"
