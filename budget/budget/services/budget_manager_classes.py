from budget.budget.services.budget_constants import ZERO

class BudgetManagerDetailRow:
    def __init__(self):
        self.period_id = None
        self.category_id = None
        self.budget_id = None
        self.account_id = None

        self.type = "T"
        self.due_date = None
        self.amount = ZERO

        self.seq = 0
        self.notes = None

        self.category = None
        self.account = None

    @property
    def key(self):
        return self.period_id, self.category_id

    @property
    def is_phantom(self):
        return self.budget_id is None


class BudgetManagerRow:
    def __init__(self):
        self.period_id = None
        self.category_id = None
        self.account_id = None
        self.type = "T"
        self.due_date = None
        self.amount = ZERO

        self.min_amount = None
        self.max_amount = None
        self.avg_amount = None
        self.last_amount = None
        self.last_date = None
        self.actual = None
        self.difference = None
        
        self.status = None

        self.category = None
        self.account = None

        self.details = []

    @property
    def key(self):
        return self.period_id, self.category_id
    
    @property
    def is_phantom(self):
        assert self.details, "BudgetManagerRow must contain at least one detail"
        return self.details[0].budget_id is None

    @property
    def budget_ids(self):
        return [
            detail.budget_id
            for detail in self.details
            if detail.budget_id is not None
        ]

    @property
    def budget_count(self):
        return len(self.budget_ids)

    @property
    def action(self):
        return "Edit" if self.budget_ids else "Add"
    
    @property
    def direction(self):
        return 1 if self.amount >= ZERO else -1