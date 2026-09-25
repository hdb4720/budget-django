from budget.models import Budget, Category

class PhantomBudgetRow:
    def __init__(self, category):
        self.category = category
        self.category_id = category.id

