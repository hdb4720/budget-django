from datetime import date
from budget.models import Period, PeriodScheme


class PeriodResolver:
    """
    PeriodResolver is a service class responsible for determining the appropriate 
    period to display based on the provided criteria. It resolves the period 
    using the following logic:
    1. Explicit Period Selection:
        If a `period_id` is provided, it directly retrieves and returns the 
        corresponding period from the given scheme.
    2. Current Date Matching:
        If no `period_id` is provided, it attempts to find the period that 
        contains today's date. This is the normal usage scenario.
    3. Fallback to Scheme Boundaries:
        If today's date does not fall within any period in the scheme, it falls 
        back to the scheme boundaries:
        - Returns the first period if today's date is before the scheme's start.
        - Returns the last period if today's date is after the scheme's end.
    In the unlikely event that none of the above conditions are met, it defaults 
    to returning the first period as a safe fallback.
    Attributes:
         None
    Methods:
         resolve(scheme: PeriodScheme, period_id=None) -> Period:
              Resolves and returns the appropriate period based on the provided 
              scheme and optional `period_id`.
    """
    
    """
    Resolves the correct period to display based on:
    - explicit period_id (user navigation)
    - today's date (normal usage)
    - scheme boundaries (fallback)
    """

    def resolve(self, scheme: PeriodScheme, period_id=None) -> Period:
        # 1. User explicitly selected a period
        if period_id:
            return scheme.periods.get(id=period_id)

        today = date.today()

        # 2. Normal case: find the period containing today
        current = (
            scheme.periods
            .filter(start__lte=today, end__gte=today)
            .first()
        )
        if current:
            return current

        # 3. Fallback: today is outside the scheme range
        first = scheme.periods.order_by("sequence").first()
        last = scheme.periods.order_by("-sequence").first()

        if today < first.start:
            return first

        if today > last.end:
            return last

        # Should never happen, but safe fallback
        return first


class PeriodNavigator:
    """
    PeriodNavigator is a utility class designed to navigate through periods within a given PeriodScheme. 
    It provides functionality to retrieve the previous, current, and next periods relative to a specified current period.
    Attributes:
        scheme (PeriodScheme): The period scheme containing the list of periods to navigate.
    Methods:
        __init__(scheme: PeriodScheme):
            Initializes the PeriodNavigator with a given PeriodScheme.
        get_period(sequence: int) -> Period:
            Retrieves a period from the scheme based on its sequence number. 
            Returns the first matching period or None if no match is found.
        navigate(current_period: Period) -> dict:
            Given a current period, returns a dictionary containing:
                - "previous": The period preceding the current period, or None if it does not exist.
                - "current": The current period.
                - "next": The period following the current period, or None if it does not exist.
    """
                
    """
    Given a PeriodScheme and a current Period,
    returns previous, current, and next periods.
    """

    def __init__(self, scheme: PeriodScheme):
        self.scheme = scheme

    def get_period(self, sequence: int):
        return (
            self.scheme.periods
            .filter(sequence=sequence)
            .first()
        )

    def navigate(self, current_period: Period):
        seq = current_period.sequence

        return {
            "previous": self.get_period(seq - 1),
            "current": current_period,
            "next": self.get_period(seq + 1),
        }


class PeriodNavigationService:
    """
    PeriodNavigationService is a high-level API designed for use by the dashboard.
    It combines the functionality of a resolver and a navigator to provide period navigation.
    Attributes:
        scheme (PeriodScheme): The period scheme used for navigation.
        resolver (PeriodResolver): Resolves the current period based on the scheme and optional period ID.
        navigator (PeriodNavigator): Handles navigation logic for the resolved period.
    Methods:
        __init__(scheme: PeriodScheme):
            Initializes the service with a given period scheme, and sets up the resolver and navigator.
        get_navigation(period_id=None):
            Resolves the current period based on the scheme and optional period ID, and returns navigation data.
            Args:
                period_id (optional): The ID of the period to resolve. Defaults to None.
            Returns:
                Navigation data for the resolved period.
    """
    
    """
    High-level API used by the dashboard.
    Combines resolver + navigator.
    """

    def __init__(self, scheme: PeriodScheme):
        self.scheme = scheme
        self.resolver = PeriodResolver()
        self.navigator = PeriodNavigator(scheme)

    def get_navigation(self, period_id=None):
        current = self.resolver.resolve(self.scheme, period_id)
        return self.navigator.navigate(current)
