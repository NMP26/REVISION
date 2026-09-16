from django.db import models

class FoundationMarker(models.Model):
    """Technical LOT 0 schema marker; no business data is stored."""
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "foundation_marker"
