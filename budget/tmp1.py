from dataclasses import dataclass
from datetime import date, timedelta
import calendar

from budget.services.fixed_term_projection import (
    add_months,
    day_of_month,
    nth_weekday_of_month,
    specific_date_yearly,
)

