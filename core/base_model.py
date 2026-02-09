from django.db import models
import uuid


class BaseModel(models.Model):
    """
    Abstract base model that includes:
    - UUID as primary key
    - Auto-managed `created_at` timestamp
    - Auto-managed `updated_at` timestamp (tracks modification)

    This model should be used when you want to track both creation and update timestamps.
    """
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f"id--{self.id}--created_at-{self.created_at}--updated_at--{self.updated_at}"


class BaseImmutableModel(models.Model):
    """
    Abstract base model that includes:
    - UUID as primary key
    - Auto-managed `created_at` timestamp only (no updates)

    Use this when the record should not track updates (i.e., immutable data).
    """
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f"id--{self.id}--created_at-{self.created_at}"
