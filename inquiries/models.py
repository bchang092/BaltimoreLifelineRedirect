from django.db import models


class ServiceInquiry(models.Model):
    SERVICE_CHOICES = [
        ("scraping", "Web scraping & collection"),
        ("cleanup", "Data cleanup & organization"),
        ("updates", "Ongoing data updates"),
        ("other", "Let's figure it out"),
    ]
    name = models.CharField(max_length=120)
    email = models.EmailField()
    organization = models.CharField(max_length=160, blank=True)
    service = models.CharField(max_length=20, choices=SERVICE_CHOICES)
    message = models.TextField(max_length=5000)
    contacted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} — {self.get_service_display()}"


class InquiryRateLimit(models.Model):
    key = models.CharField(max_length=64, primary_key=True)
    attempts = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(db_index=True)
