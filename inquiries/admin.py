from django.contrib import admin

from .models import ServiceInquiry


@admin.register(ServiceInquiry)
class ServiceInquiryAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "organization", "service", "contacted", "created_at")
    list_filter = ("contacted", "service", "created_at")
    search_fields = ("name", "email", "organization", "message")
    readonly_fields = ("name", "email", "organization", "service", "message", "created_at")

    def has_add_permission(self, request):
        return False


admin.site.site_header = "LumaReach administration"
admin.site.site_title = "LumaReach"
