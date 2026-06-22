from django.contrib.admin import AdminSite
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

@staff_member_required
def importer_admin_view(request):
    return render(request, "admin/importer_admin_view.html")
