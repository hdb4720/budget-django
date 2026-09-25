# budget/budget/services/manager_sort.py

SORT_KEYS = {
    "category": lambda row: row.category.casefold(),
}


def get_sorted_context(request, manager_context):
    sort_field = request.GET.get("sort_field")
    sort_direction = request.GET.get(
        "sort_direction",
        "asc",
    )

    if sort_field not in SORT_KEYS:
        sort_field = None

    if sort_direction not in ("asc", "desc"):
        sort_direction = "asc"

    return {
        **manager_context,
        "manager": sort_manager(
            manager_context["manager"],
            sort_field,
            sort_direction,
        ),
        "sort_field": sort_field,
        "sort_direction": sort_direction,
    }


def sort_manager(
    manager,
    sort_field,
    sort_direction,
):
    if sort_field is None:
        return manager

    return sorted(
        manager,
        key=SORT_KEYS[sort_field],
        reverse=(sort_direction == "desc"),
    )