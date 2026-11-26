"""LumaReach's public landing page and private service inquiries."""
import logging
from smtplib import SMTPException

from django import forms
from django.conf import settings
from django.core.mail import EmailMessage
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .security import reserve_submission_attempt
from .models import ServiceInquiry

logger = logging.getLogger(__name__)


class InquiryForm(forms.ModelForm):
    service = forms.ChoiceField(choices=ServiceInquiry.SERVICE_CHOICES, initial="other", widget=forms.HiddenInput)
    website = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = ServiceInquiry
        fields = ("name", "email", "organization", "service", "message")
        labels = {"name": "Name", "email": "Email", "organization": "Organization (optional)",
                  "service": "What can we help with?", "message": "What do you have in mind?"}
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "name", "placeholder": "Your name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "you@organization.com"}),
            "organization": forms.HiddenInput(),
            "message": forms.Textarea(attrs={"rows": 3, "placeholder": "A project, a question, an idea…"}),
        }

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Unable to submit this inquiry. Please try again.")
        return ""


def notify_inquiry(inquiry):
    if not (settings.LUMA_INQUIRY_EMAIL and settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD):
        return
    try:
        EmailMessage(
            subject=f"[LumaReach] Service inquiry #{inquiry.pk}",
            body=(f"Name: {inquiry.name}\nEmail: {inquiry.email}\n"
                  f"Organization: {inquiry.organization}\nService: {inquiry.get_service_display()}\n\n"
                  f"{inquiry.message}\n\nSaved in Django admin under Service inquiries."),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.LUMA_INQUIRY_EMAIL],
            reply_to=[inquiry.email],
        ).send(fail_silently=False)
    except (SMTPException, OSError, ValueError):
        logger.error("Inquiry %s saved, but email notification failed.", inquiry.pk)


@require_http_methods(["GET", "POST"])
def luma_home(request):
    form = InquiryForm(request.POST if request.method == "POST" else None)
    status, retry_after = 200, 0
    if request.method == "POST":
        retry_after = reserve_submission_attempt(request, namespace="luma-inquiry-rate")
        if retry_after:
            form.is_valid()
            form.add_error(None, "You've sent several requests. Please try again in an hour.")
            status = 429
        elif form.is_valid():
            with transaction.atomic():
                inquiry = form.save()
                transaction.on_commit(lambda: notify_inquiry(inquiry))
            request.session["luma_inquiry_received"] = True
            return redirect(reverse("luma_home") + "#contact")
        else:
            status = 400
    received = request.session.pop("luma_inquiry_received", False) if request.method == "GET" else False
    response = render(request, "luma_home.html", {"form": form, "inquiry_received": received, "baltimore_url": settings.BALTIMORE_LIFELINE_URL}, status=status)
    if retry_after:
        response["Retry-After"] = str(retry_after)
    return response


@require_http_methods(["GET"])
def luma_about(request):
    return render(request, "luma_about.html", {"baltimore_url": settings.BALTIMORE_LIFELINE_URL, "page": "about"})
