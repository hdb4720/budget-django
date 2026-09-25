# Budget Manager Status Design Report

## Purpose

This report defines how a consolidated Budget Manager row receives:

- an effective due date;
- a financial-progress classification;
- a final display status;
- a color for presentation.

The rules apply after individual budget and phantom detail rows have been consolidated into a manager row.

## Manager-row assumptions

By the time status is calculated, a manager row contains:

- `type`: normally `Planned` or `Transient`;
- `amount`: the sum of its detail budget amounts;
- `actual`: the applicable transaction total;
- `due_date`: assigned by `assign_due_date()`;
- `details`: the underlying real-budget or phantom detail rows;
- the selected `period`;
- `as_of_date`, normally today.

The manager row is the unit displayed, sorted, filtered, totaled, and color-coded. Detail rows remain available for later selection and CRUD operations.

## Budget and phantom definitions

### Real budget detail

A real detail represents a persisted `Budget` record. A real budget shown for the selected period has a qualifying due date between `period.start` and `period.end`.

### Phantom detail

A phantom represents a category with historical transaction activity but no qualifying budget. It begins with:

- no persisted budget record;
- no entered budget amount;
- no entered due date;
- type `Transient`.

At the manager level, a phantom assumes `period.end` as its due date. Because its amount is zero, its initial status is `incomplete`.

The exact scope of “no qualifying budget” must match the intended phantom definition. If phantoms mean “no budget for the selected period,” `build_phantoms()` must receive or test period-qualified budgets. If they mean “no budget ever,” it must test all `Budget` records.

## Meaning of incomplete

`incomplete` has one meaning in this manager:

> The row has an assigned due date but has no assigned budget amount.

Therefore:

```python
row.amount == ZERO
```

Both of the following can be incomplete:

- a phantom whose manager due date is the assumed `period.end`;
- a real zero-amount budget with a qualifying due date.

An undated planned budget is not a normal manager-row condition because a record without a qualifying due date is not selected into the period's budget set. Such records could later be exposed in a separate data-quality or unscheduled-budget report.

## Signed financial direction

Budget and actual signs carry accounting meaning and must not be discarded with `abs()`.

- Expenses are normally negative.
- Income is normally positive.
- Contra-expenses and contra-income can reverse the expected sign.

Using `abs()` can incorrectly classify rebates, refunds, reversals, garnishments, and recoveries. Instead, normalize the direction while preserving the original sign:

```python
direction = -1 if row.amount < ZERO else 1

budget_progress = row.amount * direction
actual_progress = row.actual * direction
```

This makes ordinary comparisons work for both income and expenses:

```python
met = actual_progress == budget_progress
overfilled = actual_progress > budget_progress
underfilled = actual_progress < budget_progress
```

### Examples

| Budget | Actual | Direction | Normalized budget | Normalized actual | Result |
|---:|---:|---:|---:|---:|---|
| -400 | 0 | -1 | 400 | 0 | Underfilled |
| -400 | -200 | -1 | 400 | 200 | Underfilled |
| -400 | -400 | -1 | 400 | 400 | Met |
| -400 | -500 | -1 | 400 | 500 | Overfilled |
| -500 | 100 | -1 | 500 | -100 | Underfilled contra-expense |
| 400 | 0 | 1 | 400 | 0 | Underfilled |
| 400 | 200 | 1 | 400 | 200 | Underfilled |
| 400 | 400 | 1 | 400 | 400 | Met |
| 400 | 500 | 1 | 400 | 500 | Overfilled |
| 500 | -100 | 1 | 500 | -100 | Underfilled contra-income |

## Assigning the manager due date

### Purpose

For a single-detail manager row, the manager due date is simply the detail due date.

For a multidetail manager row, the manager due date should represent:

> The due date of the next detail whose cumulative budget has not yet been fulfilled.

It must not merely be the next date on or after `as_of_date`. Skipping an earlier unpaid date would hide an overdue obligation.

### Cumulative allocation rule

1. Sort dated details by due date and then by sequence.
2. Normalize the manager actual and each detail amount using the manager's financial direction.
3. Accumulate detail amounts in due-date order.
4. Select the first detail whose cumulative threshold is greater than normalized actual.
5. If all thresholds have been met, retain the final detail due date.
6. If no detail has a real due date, use `period.end`.

No separate `actual == ZERO` branch is required. Zero actual naturally fails the first positive cumulative threshold, selecting the first due date.

### Example

| Detail due date | Expense amount | Normalized cumulative threshold |
|---|---:|---:|
| September 5 | -100 | 100 |
| September 20 | -150 | 250 |
| September 25 | -50 | 300 |

The resulting manager due date is:

| Actual | Normalized actual | Assigned due date |
|---:|---:|---|
| 0 | 0 | September 5 |
| -75 | 75 | September 5 |
| -100 | 100 | September 20 |
| -200 | 200 | September 20 |
| -250 | 250 | September 25 |
| -350 | 350 | September 25; all details are complete |

### Proposed implementation

```python
def assign_due_date(row, details, period):
    dated_details = sorted(
        (
            detail
            for detail in details
            if detail.due_date is not None
        ),
        key=lambda detail: (
            detail.due_date,
            detail.seq,
        ),
    )

    if not dated_details:
        row.due_date = period.end
        return

    if row.amount == ZERO:
        row.due_date = dated_details[0].due_date
        return

    direction = -1 if row.amount < ZERO else 1
    actual_progress = row.actual * direction
    cumulative_progress = ZERO

    for detail in dated_details:
        cumulative_progress += detail.amount * direction

        if actual_progress < cumulative_progress:
            row.due_date = detail.due_date
            return

    row.due_date = dated_details[-1].due_date
```

`as_of_date` is unnecessary in this calculation. Date comparison belongs in status calculation after the next unfulfilled due date has been selected.

### Mixed-sign detail limitation

The cumulative allocation assumes that every nonzero detail in a consolidated row has the same financial direction as the manager total.

If positive and negative budget details can coexist in one manager row, cumulative thresholds can decrease and transaction totals cannot reliably identify which detail was fulfilled. During development, validate this assumption:

```python
for detail in dated_details:
    if detail.amount != ZERO and detail.amount * direction < ZERO:
        raise ValueError(
            "Mixed-sign budget details cannot be allocated "
            "using cumulative due-date logic."
        )
```

The eventual production response could be a diagnostic status rather than an exception.

## Status definitions

| Status | Definition |
|---|---|
| `incomplete` | The row has an assigned due date but its budget amount is zero. |
| `met` | Actual equals the nonzero consolidated budget. |
| `overfilled` | Actual has exceeded the consolidated budget in its signed financial direction. |
| `overdue` | The row remains underfilled and its assigned due date is before `as_of_date`. |
| `pending` | The row remains underfilled, is not overdue, and has no payment or receipt activity. |
| `partial` | The row remains underfilled, is not overdue, and has some payment or receipt activity. |
| `other` | An unexpected condition not covered by the defined rules; retained as a diagnostic fallback. |

`met` and `overfilled` are both complete conditions:

```python
row.is_complete = row.status in {"met", "overfilled"}
```

Keeping them as distinct statuses supports separate filtering, coloring, analysis, and totals while retaining the broader concept of completion.

## Status precedence

Rule order is significant:

1. A zero amount is `incomplete` even when actual is also zero.
2. Exact fulfillment is `met`, regardless of due date.
3. Exceeding the amount is `overfilled`, regardless of due date.
4. Only an underfilled row can be `overdue`.
5. A current underfilled row with no activity is `pending`.
6. A current underfilled row with activity is `partial`.

The due date is therefore ignored after a row becomes met or overfilled unless the project later adds analytical labels such as paid early, paid on time, or paid late.

## Proposed status implementation

```python
def assign_status(row, as_of_date):
    if row.amount == ZERO:
        row.status = "incomplete"
        row.is_complete = False
        return

    direction = -1 if row.amount < ZERO else 1
    budget_progress = row.amount * direction
    actual_progress = row.actual * direction

    if actual_progress == budget_progress:
        row.status = "met"

    elif actual_progress > budget_progress:
        row.status = "overfilled"

    elif row.due_date < as_of_date:
        row.status = "overdue"

    elif row.actual == ZERO:
        row.status = "pending"

    else:
        row.status = "partial"

    row.is_complete = row.status in {"met", "overfilled"}
```

The recommended due-date boundary is:

```python
row.due_date < as_of_date
```

A budget due today remains pending or partial throughout today and becomes overdue the following day.

## Activity-count refinement

Using `actual == ZERO` as shorthand for “nothing paid or received” has one known weakness. Transactions can net to zero:

```text
Expense        -50
Reimbursement  +50
Net actual       0
```

If `pending` must mean literally no activity, `build_actuals()` should return a transaction count as well as the sum:

```python
.annotate(
    actual=Sum("amount"),
    actual_count=Count("id"),
)
```

Status can then use:

```python
no_activity = row.actual_count == 0
```

instead of:

```python
row.actual == ZERO
```

This refinement is recommended because rebates, reversals, corrections, and contra transactions are valid accounting events. Until it is implemented, zero-net activity will be displayed as pending.

## Period-position considerations

The selected period can be classified independently:

```python
if period.end < as_of_date:
    period_position = "past"
elif period.start > as_of_date:
    period_position = "future"
else:
    period_position = "current"
```

The initial status algorithm can use the same rules for every period. However, a past-period underfilled row will appear overdue when evaluated against today's date. That may be factually correct but visually distracting during historical review.

Possible later refinements include:

- use `unfulfilled` instead of `overdue` when viewing a past period;
- reserve urgent overdue coloring for the current period;
- distinguish future-period pending rows from current pending rows;
- preserve status as of the selected period end rather than recalculating all history against today.

These are presentation and historical-analysis decisions and do not need to block the first implementation.

## Color mapping

Status and color should remain separate. Python assigns a meaningful status; presentation maps that status to a CSS class or fill color.

The Excel colors documented so far are:

| Status group | Excel color | Hex |
|---|---|---|
| Overdue | Red | `#FF6666` |
| Incomplete | Orange/gold | `#FFC000` |
| Pending or partial | Light peach | `#FBE2D5` |
| Met or overfilled | Light green | `#C6E0B4` |
| Future | Light purple | `#C8B4E3` |
| Active without budget | Blue | `#00B0F0` |
| No budget/no due date | Yellow | `#E7F20F` |
| Other | No fill | — |

The revised status model removes some of the old combined Excel conditions. Final CSS mappings should be chosen after the statuses are verified against real rows. `met` and `overfilled` may share the complete color initially while remaining logically distinct.

## Required tests

### Single-detail rows

- Zero amount produces `incomplete`.
- Zero actual with a future or current due date produces `pending`.
- Partial actual before the due date produces `partial`.
- Partial actual after the due date produces `overdue`.
- Exact actual produces `met` before, on, or after the due date.
- Actual beyond the budget produces `overfilled` before, on, or after the due date.
- Expense, income, contra-expense, and contra-income examples preserve their signs.

### Multidetail rows

- Zero actual selects the first detail due date.
- Partial fulfillment below the first threshold retains the first due date.
- Exact fulfillment of the first detail rolls to the second due date.
- Fulfillment between cumulative thresholds selects the correct next detail.
- Exact fulfillment of a cumulative threshold rolls to the following detail.
- Fulfillment or overfilling of the total retains the last due date.
- An earlier unpaid date is not skipped merely because it is before `as_of_date`.
- Equal due dates are resolved consistently using `seq`.
- Mixed-sign detail amounts are detected.

### Phantom rows

- A phantom with no dated detail receives `period.end`.
- A phantom begins with amount zero.
- A phantom therefore begins as `incomplete`.
- Creating a real budget causes the row to leave phantom/incomplete status after the manager is rebuilt.

### Boundary conditions

- A row due today is not overdue.
- It becomes overdue on the following date if still underfilled.
- Past, current, and future selected periods are inspected for acceptable presentation.
- Zero-net transaction activity is tested before deciding whether `actual_count` is required immediately.

## Recommended implementation sequence

1. Replace calendar-based `assign_due_date()` selection with cumulative fulfillment logic.
2. Add mixed-sign validation for multidetail rows.
3. Decide whether `build_actuals()` should supply `actual_count` now.
4. Implement `assign_status()` using the defined precedence.
5. Test single-detail, multidetail, phantom, contra, and date-boundary scenarios.
6. Map verified statuses to CSS classes and colors.
7. Add status to later sorting, filtering, totals, and analytical tools.

## Decisions still open

1. Does phantom mean no budget ever, or no qualifying budget in the selected period?
2. Should pending mean net actual is zero, or strictly that no transactions exist?
3. Should past-period underfilled rows display `overdue` or a historical `unfulfilled` status?
4. Should `met` and `overfilled` share a color even though they remain separate statuses?
5. Can a consolidated manager row contain mixed-sign budget details, and if so, what business rule replaces cumulative allocation?

