from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Student(models.Model):
    roll_number = models.CharField(max_length=30, unique=True)
    full_name = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=80)
    class_name = models.CharField(max_length=40, blank=True)
    marks = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                validators=[MinValueValidator(0), MaxValueValidator(100)])
    attendance = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                     validators=[MinValueValidator(0), MaxValueValidator(100)])
    fees_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["roll_number"]

    def __str__(self):
        return f"{self.roll_number} - {self.full_name}"