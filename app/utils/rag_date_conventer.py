from datetime import date


def quarter_to_date_range(
    year: int,
    quarter: int,
) -> tuple[date, date]:
    """
    Returns [start, end), where end is exclusive.

    Q1 2025:
        2025-01-01 <= published_at < 2025-04-01
    """
    if quarter not in {1, 2, 3, 4}:
        raise ValueError("Quarter must be between 1 and 4")

    start_month = (quarter - 1) * 3 + 1
    start = date(year, start_month, 1)

    if quarter == 4:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, start_month + 3, 1)

    return start, end
