def compute_suggested_price_per_second_minor_units(*, quality_score: int) -> int:
    if quality_score < 1:
        quality_score = 1
    if quality_score > 10:
        quality_score = 10

    base = 0
    per_point = 250
    suggested = base + (quality_score - 1) * per_point

    floor = 5
    ceiling = 2000

    if suggested < floor:
        return floor
    if suggested > ceiling:
        return ceiling
    return suggested
