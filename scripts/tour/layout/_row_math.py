def row_positions(widths: list[int], gap: int) -> list[int]:
    positions: list[int] = []
    cursor = 0
    for width in widths:
        positions.append(cursor)
        cursor += width + gap
    return positions


def total_row_width(widths: list[int], gap: int) -> int:
    if not widths:
        return 0
    return sum(widths) + gap * (len(widths) - 1)
