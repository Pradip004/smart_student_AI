from django import forms

from .models import Student


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ["roll_number", "full_name", "email", "phone", "department",
                  "class_name", "marks", "attendance", "fees_paid"]
        labels = {"class_name": "Class", "fees_paid": "Fees paid"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs["class"] = "form-check-input" if name == "fees_paid" else "form-control"
        self.fields["roll_number"].error_messages["unique"] = (
            "A student with this roll number already exists.")


class ExcelImportForm(forms.Form):
    file = forms.FileField(label="Excel workbook (.xlsx)")

    def clean_file(self):
        f = self.cleaned_data["file"]
        if not f.name.lower().endswith(".xlsx"):
            raise forms.ValidationError("Only .xlsx files are supported.")
        if f.size > 5 * 1024 * 1024:
            raise forms.ValidationError("File is larger than 5 MB.")
        return f


class AskAIForm(forms.Form):
    question = forms.CharField(max_length=300, widget=forms.Textarea(attrs={
        "rows": 2, "class": "form-control",
        "placeholder": "e.g. Find CSE students with marks above 80"}))