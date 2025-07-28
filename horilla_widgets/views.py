from django.shortcuts import render

from horilla.decorators import login_required
from horilla_widgets.widgets.select_widgets import (
    ALL_INSTANCES,
    HorillaMultiSelectWidget,
)

# Create your views here.

# urls.py
# path("employee-widget-filter",views.widget_filter,name="employee-widget-filter")

# views.py
# @login_required
# def widget_filter(request):
#     """
#     This method is used to return all the ids of the employees
#     """
#     ids = EmployeeFilter(request.GET).qs.values_list("id", flat=True)
#     return JsonResponse({'ids':list(ids)})


@login_required
def get_filter_form(request):
    """
    This method will return filtering from
    """
    widget_instance = ALL_INSTANCES[str(request.user.id)]
    template_path = request.GET.get("template_path")
    
    # If template_path is None, use a default template for widgets without filters
    if template_path is None or template_path == "None":
        template_path = "horilla_widgets/no_filter_template.html"
    
    # Check if filter_class exists and is callable
    if widget_instance.filter_class is not None:
        filter_instance = widget_instance.filter_class()
    else:
        filter_instance = None
    
    return render(request, template_path, {"f": filter_instance})
