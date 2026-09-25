from decimal import Decimal

def compute_status_map(budgets):
    """
    Minimal working status map for Manager.
    Uses:
    - planned = budget.amount
    - actual = 0 (placeholder until transaction aggregation is added)
    """

    status_map = {}

    for b in budgets:
        planned = b.amount or Decimal("0")
        actual = Decimal("0")  # placeholder

        if planned == 0:
            color = "secondary"
            label = "None"
        elif actual == 0:
            color = "success"
            label = "OK"
        elif actual < planned:
            color = "warning"
            label = "At Risk"
        else:
            color = "danger"
            label = "Over"

        status_map[b.category_id] = {
            "color": color,
            "label": label,
        }

    return status_map
