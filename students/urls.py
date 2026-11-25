from django.urls import path


from . import views

urlpatterns = [
    
    
    path("ask-ai/", views.ask_ai, name="ask_ai"),
    path("students/results/", views.ai_results, name="ai_results"),
    path("export/<str:fmt>/", views.export_report, name="export_report"),
    path("", views.ask_ai, name="home"),
    path("students/", views.dashboard, name="dashboard"),
    path("students/add/", views.student_add, name="student_add"),
    path("students/<int:pk>/edit/", views.student_edit, name="student_edit"),
    path("students/<int:pk>/delete/", views.student_delete, name="student_delete"),
    path("import/", views.import_excel, name="import_excel"),

]
