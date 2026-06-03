from django.db import models


class ImportLog(models.Model):
    task_id = models.CharField(max_length=255, unique=True)
    file_path = models.CharField(max_length=500)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=[
            ("STARTED", "Started"),
            ("SUCCESS", "Success"),
            ("FAILURE", "Failure"),
        ],
    )

    inserted = models.IntegerField(default=0)
    deleted = models.IntegerField(default=0)
    kept = models.IntegerField(default=0)
    total_imported = models.IntegerField(default=0)
    total_db = models.IntegerField(default=0)

    error_message = models.TextField(blank=True, null=True)

    def duration_seconds(self):
        if self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return None

    def __str__(self):
        return f"Import {self.task_id} — {self.status}"
