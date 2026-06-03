from budget.budget_import.extract.source_config import (
    QuickenXLSXConfig
)
from budget.budget_import.importers.importer import (
    TransactionImporter
)

cfg = QuickenXLSXConfig()
filepath = "C:/Users/hdb47/OneDrive/Source/Budget/Excel/full.xlsx"

importer = TransactionImporter(
    cfg,
    filepath,
)

importer.run()
