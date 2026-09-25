# budget/services/manager_requests.py

def get_manager_requests(request):
    return {
        "respond_to": request.GET.get("respond_to", "full"),
        "selected": get_selected(request),
        "sorting": get_sorting(request),
        "filtering": get_filtering(request),
        "manager_modal": get_manager_modal(request),
        "other": get_manager_other(request),
}

def get_selected(request):
    return {
        "selected_scheme": request.GET.get("scheme"),
        "selected_period": request.GET.get("period"),
        "selected_date": request.GET.get("selected_date"),
    }

def get_sorting(request):
    return {
        "sort_field": request.GET.get("sort_field"),
        "sort_direction": request.GET.get(
            "sort_direction", 
            "asc",
        ),
    }
    
def get_filtering(request):    
    return {
    }

def get_manager_modal(request):
    return {
        "manager_period_id": request.GET.get("manager_period_id"),
        "manager_category_id": request.GET.get("manager_category_id"),
        "manager_budget_id": request.GET.get("manager_budget_id"),
    }

def get_manager_other(request):
    other = {}
    expected_keys = {
        "respond_to",
        "scheme",
        "period",
        "selected_scheme",
        "selected_period",
        "selected_date",
        "sort_field",
        "sort_direction",
        "manager_period_id",
        "manager_category_id",
        "manager_budget_id",
    }
    
    for key, value in request.GET.items():
        if key not in expected_keys:
            other[key] = value
            
    return other
