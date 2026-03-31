from django.db import models


class IngestLog(models.Model):
    """Audit trail for each ingestion run."""

    source_id = models.CharField(max_length=255)
    source_text = models.TextField()
    concepts_extracted = models.IntegerField(default=0)
    relations_extracted = models.IntegerField(default=0)
    status = models.CharField(max_length=50)  # "success" | "partial" | "error"
    error_message = models.TextField(blank=True, null=True)
    ingested_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"IngestLog {self.source_id} at {self.ingested_at}"
