from django.contrib import messages

from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from . import ai_helper, reports, services
from .forms import AskAIForm, ExcelImportForm, StudentForm
from .models import Student



def dashboard(request):
    q = request.GET.get("q", "").strip()
    students = Student.objects.all()
    if q:
        students = students.filter(
            Q(full_name__icontains=q) | Q(roll_number__icontains=q)
            | Q(department__icontains=q) | Q(class_name__icontains=q))
    paginator = Paginator(students, 15)
    match_count = paginator.count
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "dashboard.html",
                  {"page": page, "q": q, "total": Student.objects.count(),
                   "match_count": match_count})



def student_add(request):
    form = StudentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        student = form.save()
        messages.success(request, f"Student {student.full_name} added.")
        return redirect("dashboard")
    return render(request, "student_form.html", {"form": form, "title": "Add Student"})



def student_edit(request, pk):
    student = get_object_or_404(Student, pk=pk)
    form = StudentForm(request.POST or None, instance=student)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Student updated.")
        return redirect("dashboard")
    return render(request, "student_form.html", {"form": form, "title": "Edit Student"})



def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == "POST":
        student.delete()
        messages.success(request, "Student deleted.")
        return redirect("dashboard")
    return render(request, "student_confirm_delete.html", {"student": student})



def import_excel(request):
    form = ExcelImportForm(request.POST or None, request.FILES or None)
    result = None
    if request.method == "POST" and form.is_valid():
        try:
            result = services.import_students_from_excel(form.cleaned_data["file"])
        except services.ImportFileError as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, f"Import finished: {result.created} created, "
                                      f"{result.updated} updated, {len(result.errors)} skipped.")
    return render(request, "import.html", {
        "form": form, "result": result,
        "required": services.REQUIRED_COLUMNS, "optional": services.OPTIONAL_COLUMNS})



def ask_ai(request):
    form = AskAIForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            raw = ai_helper.ask_gemma(form.cleaned_data["question"])
        except ai_helper.AIServiceError as exc:
            messages.error(request, str(exc))
        else:
            filters, warnings = ai_helper.validate_filters(raw)
            request.session["last_filters"] = filters
            request.session["last_question"] = form.cleaned_data["question"]
            request.session["last_warnings"] = warnings
            return redirect("ai_results")
    return render(request, "ask_ai.html", {"form": form})



def ai_results(request):
    filters = request.session.get("last_filters")
    if filters is None:
        messages.info(request, "Ask AI a question to see matching student details.")
        return redirect("ask_ai")
    return render(request, "ai_results.html", {
        "results": services.apply_filters(filters),
        "filters": filters,
        "warnings": request.session.get("last_warnings", []),
        "question": request.session.get("last_question", ""),
    })



def export_report(request, fmt):
    builders = {
        "xlsx": (reports.build_xlsx,
                 "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        "docx": (reports.build_docx,
                 "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        "pdf": (reports.build_pdf, "application/pdf"),
    }
    if fmt not in builders:
        messages.error(request, "Unsupported report format.")
        return redirect("ask_ai")
    filters = request.session.get("last_filters")
    if filters is None:
        messages.error(request, "Run an AI search first, then export its results.")
        return redirect("ask_ai")
    builder, content_type = builders[fmt]
    response = HttpResponse(builder(services.apply_filters(filters)), content_type=content_type)
    response["Content-Disposition"] = f'attachment; filename="student_report.{fmt}"'
    return response
