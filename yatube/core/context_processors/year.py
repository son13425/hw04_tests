import datetime as dt


def year(request):
    """Добавляет переменную с текущим годом."""
    today = dt.date.today()
    y = today.year
    return {
        'year': int(y)
    }
