from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import LoginForm


# 🔹 Login View
def login_view(request):
    if request.user.is_authenticated:
        return redirect(get_dashboard_url(request.user))

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome {user.username}!")
            return redirect(get_dashboard_url(user))
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()

    return render(request, 'account/login.html', {'form': form})


# 🔹 Logout View
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('/login/')


# 🔹 Role-based Dashboard Helper
def get_dashboard_url(user):
    if user.role == 'Admin':
        return '/admin-dashboard/'
    elif user.role == 'Zone Manager':
        return '/zone-manager-dashboard/'
    
    elif user.role == 'Technical Manager':
        return '/technical-manager-dashboard/'
    elif user.role == 'Area Sales Manager':
        return '/area-sales-dashboard/'
    elif user.role == 'Customer Support':
        return '/customer-support-dashboard/'
    elif user.role == 'Field Sales':
        return '/field-sales-dashboard/'
    elif user.role == 'Partner':  # 🆕 New Role
        return '/partner-dashboard/'
    else:
        return '/'


# ===========================
# 🎯 Role-Based Dashboards
# ===========================

@login_required
def admin_dashboard(request):
    if request.user.role != 'Admin':
        messages.error(request, "Access Denied.")
        return redirect(get_dashboard_url(request.user))
    return render(request, 'dashboards/admin.html')


from datetime import date
from account.models import CustomUser 
from zonal_manager.models import ZonalManager, ZMDailyTarget
@login_required
def zone_manager_dashboard(request):
    if request.user.role != 'Zone Manager':
        messages.error(request, "Access Denied.")
        return redirect(get_dashboard_url(request.user))

    try:
        zm_profile = request.user.zm_profile
    except ZonalManager.DoesNotExist:
        messages.error(request, "Zonal Manager profile not found.")
        return redirect(get_dashboard_url(request.user))

    # Get today's target data for all ASMs under this ZM
    today = date.today()
    targets = ZMDailyTarget.objects.filter(
        zonal_manager=zm_profile,
        date=today
    )

    # Aggregate KPI values
    total_application_target = sum(t.application_target for t in targets)
    total_application_achieve = sum(t.application_achieve for t in targets)

    total_pop_target = sum(t.pop_target for t in targets)
    total_pop_achieve = sum(t.pop_achieve for t in targets)

    total_revenue = sum(t.sd_collection_achieve for t in targets)

    total_asms = zm_profile.asms.count()

    district_coverage = "7/8"  # If you have a real calculation, replace this

    # For charts: Monthly performance & revenue trends
    # Example: past 6 months
    import datetime
    from django.db.models import Sum

    months = []
    performance_data = []
    revenue_data = []

    for i in range(5, -1, -1):
        month_start = datetime.date(today.year, today.month, 1) - datetime.timedelta(days=i*30)
        month_end = month_start.replace(day=28) + datetime.timedelta(days=4)
        month_end = month_end - datetime.timedelta(days=month_end.day)

        monthly_targets = ZMDailyTarget.objects.filter(
            zonal_manager=zm_profile,
            date__range=[month_start, month_end]
        )

        if monthly_targets.exists():
            performance = sum(t.application_achieve for t in monthly_targets) / sum(t.application_target for t in monthly_targets) * 100 if sum(t.application_target for t in monthly_targets) > 0 else 0
            revenue = sum(t.sd_collection_achieve for t in monthly_targets)
        else:
            performance = 0
            revenue = 0

        months.append(month_start.strftime("%b"))
        performance_data.append(round(performance, 2))
        revenue_data.append(round(revenue, 2))
        if total_application_target > 0:
            zone_performance = round((total_application_achieve / total_application_target) * 100, 0)
        else:
            zone_performance = 0
    context = {
        "total_application_target": total_application_target,
        "total_application_achieve": total_application_achieve,
        "total_pop_target": total_pop_target,
        "total_pop_achieve": total_pop_achieve,
        "total_revenue": total_revenue,
        "total_asms": total_asms,
        "district_coverage": district_coverage,
        "chart_months": months,
        "chart_performance": performance_data,
        "chart_revenue": revenue_data,
        "zone_performance": zone_performance,
    }

    return render(request, 'dashboards/zone_manager.html', context)



@login_required
def technical_manager_dashboard(request):
    if request.user.role != 'Zone Manager':
        messages.error(request, "Access Denied.")
        return redirect(get_dashboard_url(request.user))
    return render(request, 'dashboards/tech_manager.html')


# Your Models
from django.contrib.auth import get_user_model
User = get_user_model()
from zonal_manager.models import ZMDailyTarget
from partner.models import SDCollection
from django.contrib.auth import get_user_model
from django.db import models  #
User = get_user_model()
@login_required
def area_sales_dashboard(request):
    if request.user.role != "Area Sales Manager":
        messages.error(request, "Access Denied.")
        return redirect('/')

    asm_user = request.user

    # Last 6 target entries
    last_6 = ZMDailyTarget.objects.filter(
        asm=asm_user
    ).order_by("-date")[:6][::-1]

    # ---- KPI CALCULATIONS ----
    total_application_target = sum(t.application_target for t in last_6)
    total_application_achieve = sum(t.application_achieve for t in last_6)

    total_pop_target = sum(t.pop_target for t in last_6)
    total_pop_achieve = sum(t.pop_achieve for t in last_6)

    # Revenue (Lakhs)
    total_revenue = SDCollection.objects.filter(
        asm=asm_user,
        is_deleted=False
    ).aggregate(total=models.Sum("amount"))["total"] or 0

    # ---- PERFORMANCE % ----
    total_zm_target = 0
    total_asm_achieve = 0

    for t in last_6:
        zm_t = (
            t.application_target + t.pop_target + t.esign_target +
            t.new_taluk_target + t.new_live_partners_target +
            t.activations_target + t.calls_target + t.sd_collection_target
        )
        asm_a = (
            t.application_achieve + t.pop_achieve + t.esign_achieve +
            t.new_taluk_achieve + t.new_live_partners_achieve +
            t.activations_achieve + t.calls_achieve + t.sd_collection_achieve
        )

        total_zm_target += zm_t
        total_asm_achieve += asm_a

    asm_performance = round((total_asm_achieve / total_zm_target) * 100, 1) if total_zm_target > 0 else 0

    # ---- CHART DATA ----
    chart_months = [t.date.strftime("%b") for t in last_6]
    chart_performance = []
    chart_revenue = []

    for t in last_6:
        # Performance month-wise
        zm_t = (
            t.application_target + t.pop_target + t.esign_target +
            t.new_taluk_target + t.new_live_partners_target +
            t.activations_target + t.calls_target + t.sd_collection_target
        )
        asm_a = (
            t.application_achieve + t.pop_achieve + t.esign_achieve +
            t.new_taluk_achieve + t.new_live_partners_achieve +
            t.activations_achieve + t.calls_achieve + t.sd_collection_achieve
        )
        perf = round((asm_a / zm_t) * 100, 1) if zm_t > 0 else 0
        chart_performance.append(perf)

        # Revenue month-wise
        month_rev = SDCollection.objects.filter(
            asm=asm_user,
            date__month=t.date.month,
            date__year=t.date.year,
            is_deleted=False
        ).aggregate(total=models.Sum("amount"))["total"] or 0

        chart_revenue.append(float(month_rev / 100000))

    context = {
        "asm_profile": asm_user,
        "asm_performance": asm_performance,
        "total_application_target": total_application_target,
        "total_application_achieve": total_application_achieve,
        "total_pop_target": total_pop_target,
        "total_pop_achieve": total_pop_achieve,
        "total_revenue": round(total_revenue / 100000, 2),
        "chart_months": chart_months,
        "chart_performance": chart_performance,
        "chart_revenue": chart_revenue,
    }

    return render(request, "dashboards/area_sales.html", context)



@login_required
def customer_support_dashboard(request):
    if request.user.role != 'Customer Support':
        messages.error(request, "Access Denied.")
        return redirect(get_dashboard_url(request.user))
    return render(request, 'dashboards/customer_support.html')


@login_required
def field_sales_dashboard(request):
    if request.user.role != 'Field Sales':
        messages.error(request, "Access Denied.")
        return redirect(get_dashboard_url(request.user))
    return render(request, 'dashboards/field_sales.html')
from dal import autocomplete
from master.models import State

class StateAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = State.objects.all().order_by("name")
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs
@login_required
def partner_dashboard(request):
    if request.user.role != 'Partner':
        messages.error(request, "Access Denied.")
        return redirect(get_dashboard_url(request.user))
    return render(request, 'dashboards/partner.html')
