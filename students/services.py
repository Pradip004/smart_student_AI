from dataclasses import dataclass, field
from decimal import Decimal

import pandas as pd
from django.forms.models import model_to_dict

from .forms import StudentForm
from .models import Student

REQUIRED_COLUMNS = ["roll_number", "full_name", "department"]
OPTIONAL_COLUMNS = ["email", "phone", "class_name", "marks", "attendance", "fees_paid"]
ALL_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS
MAX_IMPORT_ROWS = 5000
TRUE_WORDS = {"true", "yes", "y", "1", "paid"}
FALSE_WORDS = {"false", "no", "n", "0", "pending", "unpaid"}


def apply_filters(filters):
    qs = Student.objects.all()
    if "department" in filters:
        qs = qs.filter(department__icontains=filters["department"])
    if "class_name" in filters:
        qs = qs.filter(class_name__icontains=filters["class_name"])
    if "roll_number" in filters:
        qs = qs.filter(roll_number__icontains=filters["roll_number"])
    if "name" in filters:
        qs = qs.filter(full_name__icontains=filters["name"])
    if "marks_gt" in filters:
        qs = qs.filter(marks__gt=Decimal(str(filters["marks_gt"])))
    if "marks_lt" in filters:
        qs = qs.filter(marks__lt=Decimal(str(filters["marks_lt"])))
    if "attendance_gt" in filters:
        qs = qs.filter(attendance__gt=Decimal(str(filters["attendance_gt"])))
    if "attendance_lt" in filters:
        qs = qs.filter(attendance__lt=Decimal(str(filters["attendance_lt"])))
    if "fees_paid" in filters:
        qs = qs.filter(fees_paid=filters["fees_paid"])
    return list(qs.order_by("roll_number")[: filters.get("limit", 50)])


class ImportFileError(Exception):
    pass


@dataclass
class ImportResult:
    created: int = 0
    updated: int = 0
    errors: list = field(default_factory=list)


def _clean_cell(column, value):
    text = str(value).strip()
    if column in ("roll_number", "phone") and text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]
    return text


def import_students_from_excel(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file, dtype=str, keep_default_na=False)
    except Exception:
        raise ImportFileError("Could not read the file. Upload a valid .xlsx workbook.")

    df.columns = [str(c).strip().lower() for c in df.columns]
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ImportFileError("Missing required column(s): " + ", ".join(missing))
    if len(df) > MAX_IMPORT_ROWS:
        raise ImportFileError(f"Too many rows (maximum {MAX_IMPORT_ROWS}).")

    result = ImportResult()
    for index, row in df.iterrows():
        excel_row = index + 2
        cells = {c: _clean_cell(c, row[c]) for c in ALL_COLUMNS if c in df.columns}
        roll = cells.get("roll_number", "")
        if not roll:
            result.errors.append(f"Row {excel_row}: roll_number is blank.")
            continue

        instance = Student.objects.filter(roll_number=roll).first()
        if instance:
            data = model_to_dict(instance, fields=ALL_COLUMNS)
        else:
            data = {"marks": "0", "attendance": "0", "fees_paid": False}

        fees_error = False
        for column, value in cells.items():
            if value == "":
                continue
            if column == "fees_paid":
                word = value.lower()
                if word in TRUE_WORDS:
                    data[column] = True
                elif word in FALSE_WORDS:
                    data[column] = False
                else:
                    fees_error = True
            else:
                data[column] = value

        if fees_error:
            result.errors.append(f"Row {excel_row}: fees_paid must be Yes/No/Paid/Pending.")
            continue
        form = StudentForm(data, instance=instance)
        if form.is_valid():
            form.save()
            if instance:
                result.updated += 1
            else:
                result.created += 1
        else:
            problems = "; ".join(f"{n}: {' '.join(e)}" for n, e in form.errors.items())
            result.errors.append(f"Row {excel_row}: {problems}")
    return result