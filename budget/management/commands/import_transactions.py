from django.core.management.base import BaseCommand, CommandError

from Budget.Django.budget.budget_import.transform.superseded_excel import parse_quicken_excel
from budget.budget_import.importer import run_import


class Command(BaseCommand):
    help = "Import transactions from a Quicken Excel/CSV file"

    def add_arguments(self, parser):
        parser.add_argument(
            "file",
            type=str,
            help="Path to the Quicken Excel/CSV file",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simulate the import without writing to the database",
        )
        parser.add_argument(
            "--display-results",
            action="store_true",
            help="Show inserted/deleted rows in the output",
        )

    def handle(self, *args, **options):
        file_path = options["file"]
        dry_run = options["dry_run"]
        display_results = options["display_results"]

        # -----------------------------------------------------
        # 1. Load file
        # -----------------------------------------------------
        try:
            with open(file_path, "rb") as f:
                quicken_rows, start_date, end_date = parse_quicken_excel(f)
        except FileNotFoundError:
            raise CommandError(f"File not found: {file_path}")
        except Exception as e:
            raise CommandError(f"Error parsing file: {e}")

        # -----------------------------------------------------
        # 2. Run importer
        # -----------------------------------------------------
        result = run_import(
            quicken_rows=quicken_rows,
            start_date=start_date,
            end_date=end_date,
            dry_run=dry_run,
            display_results=display_results,
        )

        # -----------------------------------------------------
        # 3. Print summary
        # -----------------------------------------------------
        self.stdout.write(self.style.SUCCESS("Import Summary"))
        self.stdout.write(f"Inserted: {result['inserted']}")
        self.stdout.write(f"Deleted: {result['deleted']}")
        self.stdout.write(f"Kept: {result['kept']}")
        self.stdout.write(f"Total Imported: {result['total_imported']}")
        self.stdout.write(f"Total in DB: {result['total_db']}")

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry Run: No changes were written."))

        # -----------------------------------------------------
        # 4. Optional: show row details
        # -----------------------------------------------------
        if display_results:
            if result.get("inserted_rows"):
                self.stdout.write("\nRows to Insert:")
                for tx in result["inserted_rows"]:
                    self.stdout.write(f"  {tx}")

            if result.get("deleted_rows"):
                self.stdout.write("\nRows to Delete:")
                for tx in result["deleted_rows"]:
                    self.stdout.write(f"  {tx}")
