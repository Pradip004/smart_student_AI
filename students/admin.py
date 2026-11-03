from django.contrib import admin

from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("roll_number", "full_name", "department", "class_name",
                    "marks", "attendance", "fees_paid")
    search_fields = ("roll_number", "full_name", "department", "class_name")
    list_filter = ("department", "fees_paid")