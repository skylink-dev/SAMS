from datetime import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import ZonalManager, ZMDailyTarget
from django.contrib import messages
from django import forms
from account.models import CustomUser as User
from account.models import CustomUser
from django.utils import timezone
from django.template.defaultfilters import slugify
from decimal import Decimal, InvalidOperation
from master.models import TaskCategory
from activity.models import Task, TaskNote
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib.auth import get_user_model
from datetime import date
from django.db.models import Sum

from partner.models import SDCollection
from partner.forms import SDCollectionForm
from asm.models import ASM

from partner.models import SDCollection
from zonal_manager.models import ZonalManager
from django.http import JsonResponse

User = get_user_model()
@login_required
def daily_target(request):
    """📊 View: Zonal Manager Daily Target Dashboard"""
    try:
        zm = ZonalManager.objects.get(user=request.user)
    except ZonalManager.DoesNotExist:
        zm = None

    # --- Filters from GET request ---
    asm_query = request.GET.get("asm", "").strip()
    from_date = request.GET.get("from_date", "")
    to_date = request.GET.get("to_date", "")
    search_query = request.GET.get("search", "").strip()

    # --- Base queryset ---
    targets = ZMDailyTarget.objects.filter(zonal_manager=zm).select_related("asm", "zonal_manager")

    # --- Apply filters ---
    if asm_query:
        targets = targets.filter(asm__id=asm_query)

    if from_date:
        try:
            start_date = datetime.strptime(from_date, "%Y-%m-%d").date()
            targets = targets.filter(date__gte=start_date)
        except ValueError:
            pass

    if to_date:
        try:
            end_date = datetime.strptime(to_date, "%Y-%m-%d").date()
            targets = targets.filter(date__lte=end_date)
        except ValueError:
            pass

    if search_query:
        targets = targets.filter(
            Q(asm__first_name__icontains=search_query)
            | Q(asm__last_name__icontains=search_query)
            | Q(asm__username__icontains=search_query)
            | Q(asm__email__icontains=search_query)
            | Q(date__icontains=search_query)
        )

    targets = targets.order_by("-date")

    # --- Prepare summarized data ---
    target_data = []
    total_target = total_achieve = 0

    for t in targets:
        t_target = (
            t.application_target
            + t.pop_target
            + t.esign_target
            + t.new_taluk_target
            + t.new_live_partners_target
            + t.activations_target
            + t.calls_target
            + t.sd_collection_target
        )

        t_achieve = (
            t.application_achieve
            + t.pop_achieve
            + t.esign_achieve
            + t.new_taluk_achieve
            + t.new_live_partners_achieve
            + t.activations_achieve
            + t.calls_achieve
            + t.sd_collection_achieve
        )

        percent = round((t_achieve / t_target * 100), 1) if t_target > 0 else 0

        target_data.append({
            "id": t.id,
            "date": t.date,
            "asm": t.asm,
            "total_target": t_target,
            "total_achieve": t_achieve,
            "percent": percent,
        })

        total_target += t_target
        total_achieve += t_achieve

    overall_percent = round((total_achieve / total_target * 100), 1) if total_target > 0 else 0

    # --- Fetch ASMs under this ZM ---
    all_asms = zm.asms.all() if zm and hasattr(zm, "asms") else []

    context = {
        "zm": zm,
        "targets": target_data,
        "total_target": total_target,
        "total_achieve": total_achieve,
        "overall_percent": overall_percent,
        "all_asms": all_asms,
        "asm_query": asm_query,
        "from_date": from_date,
        "to_date": to_date,
        "search_query": search_query,
    }

    return render(request, "zonal_manager/zm_daily_target.html", context)



@login_required
def daily_target_detail(request, pk):
    """📄 Detail page for ZM: Show ZM target + ASM target + ASM achieve + percentages"""
    target = get_object_or_404(ZMDailyTarget, pk=pk)
    asm = target.asm

    # Assigned locations
    asm_states = getattr(asm, "states", []).all() if asm and hasattr(asm, "states") else []
    asm_districts = getattr(asm, "districts", []).all() if asm and hasattr(asm, "districts") else []
    asm_offices = getattr(asm, "offices", []).all() if asm and hasattr(asm, "offices") else []

    # Metrics structure
    metrics = [
        {
            "name": "Applications",
            "zm_target": target.application_target,
            "asm_target": target.asm_application_target,
            "asm_achieve": target.application_achieve,
        },
        {
            "name": "POP",
            "zm_target": target.pop_target,
            "asm_target": target.asm_pop_target,
            "asm_achieve": target.pop_achieve,
        },
        {
            "name": "E-Sign",
            "zm_target": target.esign_target,
            "asm_target": target.asm_esign_target,
            "asm_achieve": target.esign_achieve,
        },
        {
            "name": "New Taluk",
            "zm_target": target.new_taluk_target,
            "asm_target": target.asm_new_taluk_target,
            "asm_achieve": target.new_taluk_achieve,
        },
        {
            "name": "New Live Partners",
            "zm_target": target.new_live_partners_target,
            "asm_target": target.asm_new_live_partners_target,
            "asm_achieve": target.new_live_partners_achieve,
        },
        {
            "name": "Activations",
            "zm_target": target.activations_target,
            "asm_target": target.asm_activations_target,
            "asm_achieve": target.activations_achieve,
        },
        {
            "name": "Calls",
            "zm_target": target.calls_target,
            "asm_target": target.asm_calls_target,
            "asm_achieve": target.calls_achieve,
        },
        {
            "name": "SD Collection",
            "zm_target": target.sd_collection_target,
            "asm_target": target.asm_sd_collection_target,
            "asm_achieve": target.sd_collection_achieve,
        },
    ]

    # Add Percentages
    for m in metrics:
        m["zm_percent"] = round((m["asm_achieve"] / m["zm_target"] * 100), 1) if m["zm_target"] else 0
        m["asm_percent"] = round((m["asm_achieve"] / m["asm_target"] * 100), 1) if m["asm_target"] else 0

    context = {
        "target": target,
        "asm": asm,
        "metrics": metrics,
        "asm_states": asm_states,
        "asm_districts": asm_districts,
        "asm_offices": asm_offices,
    }

    return render(request, "zonal_manager/zm_daily_target_detail.html", context)



@login_required
def daily_target_edit(request, pk):
    target = get_object_or_404(ZMDailyTarget, pk=pk)

    metric_fields = {
        "applications": ("application_target", "application_achieve"),
        "pop": ("pop_target", "pop_achieve"),
        "e-sign": ("esign_target", "esign_achieve"),
        "new-taluk": ("new_taluk_target", "new_taluk_achieve"),
        "new-live-partners": ("new_live_partners_target", "new_live_partners_achieve"),
        "activations": ("activations_target", "activations_achieve"),
        "calls": ("calls_target", "calls_achieve"),
        "sd-collection": ("sd_collection_target", "sd_collection_achieve"),
    }

    if request.method == "POST":
        errors = []
        for metric, (target_field, achieve_field) in metric_fields.items():
            try:
                t_value = Decimal(request.POST.get(f"{metric}_target", "0") or "0")
                a_value = Decimal(request.POST.get(f"{metric}_achieve", "0") or "0")

                # Validation: disallow negatives
                if t_value < 0 or a_value < 0:
                    errors.append(f"⚠️ {metric.replace('-', ' ').title()} values cannot be negative.")
                    continue

                setattr(target, target_field, t_value)
                setattr(target, achieve_field, a_value)

            except InvalidOperation:
                errors.append(f"⚠️ Invalid number entered for {metric.replace('-', ' ').title()}.")

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            target.save()
            messages.success(request, "✅ Daily Target updated successfully!")
            return redirect("daily_target_detail", pk=pk)

    context = {"target": target}
    return render(request, "zonal_manager/zm_daily_target_edit.html", context)

# ✅ Form for multiple ASM selection

class ZMDailyTargetForm(forms.ModelForm):
    asm = forms.ModelChoiceField(
        queryset=User.objects.filter(role="Area Sales Manager"),
        widget=forms.Select(attrs={
            'class': 'border border-gray-300 rounded-lg px-3 py-2 w-full focus:ring-2 focus:ring-yellow-400',
        }),
        label="Select ASM"
    )

    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'text',  # 'text' enables Flatpickr, while still usable as date input fallback
            'class': 'datepicker border border-gray-300 rounded-lg px-3 py-2 w-full focus:ring-2 focus:ring-yellow-400',
            'placeholder': 'Select date'
        }),
        label="Select Date"
    )

    class Meta:
        model = ZMDailyTarget
        fields = [
            'asm',
            'date',
            'application_target',
            'pop_target',
            'esign_target',
            'new_taluk_target',
            'new_live_partners_target',
            'activations_target',
            'calls_target',
            'sd_collection_target',
        ]
@login_required
def daily_target_add(request):
    # ✅ Get the ZM instance
    zonal_manager = get_object_or_404(ZonalManager, user=request.user)

    # ✅ Get only ASMs under this ZM
    asms = zonal_manager.asms.filter(is_active=True).order_by('username')

    if request.method == "POST":
        form = ZMDailyTargetForm(request.POST)

        # ✅ Restrict ASM dropdown dynamically
        form.fields['asm'].queryset = asms

        if form.is_valid():
            asm = form.cleaned_data['asm']
            date = form.cleaned_data['date']

            # 🚫 Prevent duplicate ASM + Date entry
            if ZMDailyTarget.objects.filter(asm=asm, date=date).exists():
                form.add_error('asm', f"⚠️ Target for {asm.username} on {date} already exists.")
            else:
                targets = {
                    'application_target': form.cleaned_data['application_target'],
                    'pop_target': form.cleaned_data['pop_target'],
                    'esign_target': form.cleaned_data['esign_target'],
                    'new_taluk_target': form.cleaned_data['new_taluk_target'],
                    'new_live_partners_target': form.cleaned_data['new_live_partners_target'],
                    'activations_target': form.cleaned_data['activations_target'],
                    'calls_target': form.cleaned_data['calls_target'],
                    'sd_collection_target': form.cleaned_data['sd_collection_target'],
                }

                # ✅ Create the daily target record
                ZMDailyTarget.objects.create(
                    zonal_manager=zonal_manager,
                    asm=asm,
                    date=date,
                    **targets
                )

                messages.success(request, "✅ Daily target added successfully.")
                return redirect('daily_target')
    else:
        form = ZMDailyTargetForm(initial={'date': timezone.now().date()})
        # ✅ Restrict ASM dropdown for GET as well
        form.fields['asm'].queryset = asms

    return render(request, 'zonal_manager/daily_target_add.html', {'form': form})

@login_required
def assign_task_to_asm(request):
    """🎯 Zone Manager: Assign Task to ASM"""
    if request.user.role != "Zone Manager":
        messages.error(request, "🚫 You are not authorized to assign tasks.")
        return redirect("daily_target")

    # ✅ Find current ZM and related ASMs
    zm = ZonalManager.objects.filter(user=request.user).first()
    if not zm:
        messages.error(request, "⚠️ You are not mapped as a Zone Manager.")
        return redirect("daily_target")

    # ✅ Get ASMs under this ZM only
    asms = zm.asms.all().filter(is_active=True).order_by("username")

    categories = TaskCategory.objects.all().order_by("name")

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        details = request.POST.get("details", "").strip()
        category_id = request.POST.get("category")
        assigned_to_id = request.POST.get("assigned_to")
        start_date = request.POST.get("start_date") or timezone.now().date()
        end_date = request.POST.get("end_date") or timezone.now().date()

        # ✅ Validate ASM belongs to this ZM
        if not title or not assigned_to_id:
            messages.error(request, "⚠️ Please fill all required fields.")
        elif not asms.filter(id=assigned_to_id).exists():
            messages.error(request, "⚠️ You can assign tasks only to your ASMs.")
        else:
            Task.objects.create(
                category_id=category_id or None,
                title=title,
                details=details,
                assigned_by=request.user,
                assigned_to_id=assigned_to_id,
                start_date=start_date,
                end_date=end_date,
            )
            messages.success(request, "✅ Task assigned successfully.")
            return redirect("zm_task_list")

    return render(request, "zonal_manager/assign_task.html", {
        "categories": categories,
        "asms": asms,
    })


@login_required
def zm_task_list(request):
    """📋 Show only tasks assigned by the logged-in ZM"""
    if request.user.role != "Zone Manager":
        messages.error(request, "🚫 Access restricted.")
        return redirect("daily_target")

    zm = ZonalManager.objects.filter(user=request.user).first()
    if not zm:
        messages.error(request, "⚠️ You are not mapped as a Zone Manager.")
        return redirect("daily_target")

    today = timezone.now().date()
    tasks = Task.objects.filter(assigned_by=request.user).select_related("category", "assigned_to")

    # ✅ Filters
    start_date = request.GET.get("start_date", today)
    end_date = request.GET.get("end_date", today)
    category = request.GET.get("category")
    asm_id = request.GET.get("asm")
    status = request.GET.get("status")

    if start_date and end_date:
        tasks = tasks.filter(start_date__gte=start_date, end_date__lte=end_date)
    if category:
        tasks = tasks.filter(category_id=category)
    if asm_id:
        tasks = tasks.filter(assigned_to_id=asm_id)
    if status:
        tasks = tasks.filter(status=status)

    # ✅ Summary
    total_tasks = tasks.count()
    pending_tasks = tasks.filter(status="pending").count()
    completed_tasks = tasks.filter(status="completed").count()

    # ✅ Filter data
    categories = TaskCategory.objects.all().order_by("name")
    asms = zm.asms.all().order_by("username")

    return render(request, "zonal_manager/task_list.html", {
        "tasks": tasks,
        "categories": categories,
        "asms": asms,
        "total_tasks": total_tasks,
        "pending_tasks": pending_tasks,
        "completed_tasks": completed_tasks,
        "today": today,
    })

@login_required
def zm_task_detail(request, task_id):
    """📄 Task Detail with Notes (ZM can view only their tasks)"""
    task = get_object_or_404(Task, id=task_id, assigned_by=request.user)
    notes = task.notes.all().order_by("-created_at")

    if request.method == "POST":
        note_text = request.POST.get("note")
        if note_text:
            TaskNote.objects.create(task=task, user=request.user, note=note_text)
            messages.success(request, "✅ Note added successfully.")
            return redirect("zm_task_detail", task_id=task.id)

    return render(request, "zonal_manager/task_detail.html", {"task": task, "notes": notes})


@login_required
def zm_task_edit(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    categories = TaskCategory.objects.all()
    asms = CustomUser.objects.filter(role="Area Sales Manager")

    if request.method == "POST":
        task.title = request.POST.get("title")
        task.details = request.POST.get("details")
        task.category_id = request.POST.get("category") or None
        task.assigned_to_id = request.POST.get("assigned_to")
        task.start_date = request.POST.get("start_date")
        task.end_date = request.POST.get("end_date")
        task.status = request.POST.get("status")
        task.save()
        messages.success(request, "✅ Task updated successfully.")
        return redirect("zm_task_list")

    return render(request, "zonal_manager/task_edit.html", {"task": task, "categories": categories, "asms": asms})


@login_required
def zm_task_delete(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.delete()
    messages.success(request, "🗑️ Task deleted successfully.")
    return redirect("zm_task_list")


@login_required
def zm_change_status(request, task_id, new_status):
    task = get_object_or_404(Task, id=task_id)
    task.status = new_status
    task.save()
    messages.success(request, f"✅ Task status changed to {new_status}.")
    return redirect("zm_task_list")


def zm_sd_collections_view(request):
    # 🔹 Get ZM object for logged-in user
    zm = ZonalManager.objects.filter(user=request.user).first()
    if not zm:
        return render(request, "errors/403.html", {"message": "You are not a Zonal Manager."})

    # 🔹 Filter by Zone Manager
    collections = SDCollection.objects.filter(zone_manager=zm)

    # 🔹 Optional Filters
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    status = request.GET.get("status")
    asm_id = request.GET.get("asm")

    if start_date:
        collections = collections.filter(date__gte=start_date)
    if end_date:
        collections = collections.filter(date__lte=end_date)
    if status:
        collections = collections.filter(status=status)
    if asm_id:
        collections = collections.filter(asm__id=asm_id)

    # 🔹 Summary
    total_amount = collections.aggregate(total=Sum("amount"))["total"] or 0
    pending_amount = collections.filter(status="pending").aggregate(total=Sum("amount"))["total"] or 0
    completed_amount = collections.filter(status="completed").aggregate(total=Sum("amount"))["total"] or 0

    # 🔹 ASMs under this ZM
    asms = zm.asms.all()


    return render(request, "zonal_manager/sd_collections_list.html", {
        "zm": zm,
        "collections": collections,
        "asms": asms,
        "start_date": start_date or "",
        "end_date": end_date or "",
        "status": status or "",
        "asm_id": asm_id or "",
        "total_amount": total_amount,
        "pending_amount": pending_amount,
        "completed_amount": completed_amount,
    })
@login_required
def sd_collection_add(request):
    if request.method == "POST":
        partner_id = request.POST.get("partner")
        asm_id = request.POST.get("asm")
        zm_id = request.POST.get("zone_manager")
        amount = request.POST.get("amount")
        note = request.POST.get("note")

        partner = CustomUser.objects.filter(id=partner_id).first()
        asm = CustomUser.objects.filter(id=asm_id).first()
        zm = ZonalManager.objects.filter(id=zm_id).first()

        SDCollection.objects.create(
            partner=partner,
            asm=asm,
            zone_manager=zm,
            amount=amount,
            note=note,
        )
        messages.success(request, "SD Collection Added Successfully ✅")
        return redirect("sd_collection_list_zm")

    partners = CustomUser.objects.filter(role="Partner")
    asms = CustomUser.objects.filter(role="Area Sales Manager")
    zms = ZonalManager.objects.all()

    return render(request, "zonal_manager/sd_collection_add.html", {"partners": partners, "asms": asms, "zms": zms})


@login_required
def get_partner_details(request, partner_id):
    try:
        partner = CustomUser.objects.get(id=partner_id)

        # Find ASM linked to this partner
        asm_obj = ASM.objects.filter(partners=partner).first()

        # Find ZM linked to that ASM
        zm_obj = None
        if asm_obj:
            zm_obj = ZonalManager.objects.filter(asms=asm_obj.user).first()

        data = {
            "asm": asm_obj.user.username if asm_obj and asm_obj.user else "N/A",
            "zm": zm_obj.user.username if zm_obj and zm_obj.user else "N/A",
            "asm_id": asm_obj.user.id if asm_obj and asm_obj.user else "",
            "zm_id": zm_obj.id if zm_obj else "",
        }

        return JsonResponse(data)

    except CustomUser.DoesNotExist:
        return JsonResponse({"asm": "N/A", "zm": "N/A", "asm_id": "", "zm_id": ""})




def sd_collection_edit(request, pk):
    collection = get_object_or_404(SDCollection, pk=pk)

    # ✅ Allow only Zonal Manager or Admin
    if request.user.role not in ["Zone Manager", "Admin"]:
        messages.error(request, "🚫 Access restricted.")
        return redirect("sd_collection_list_zm")

    if request.method == "POST":
        amount = request.POST.get("amount")
        note = request.POST.get("note", "")

        collection.amount = amount
        collection.note = note
        collection.save()

        messages.success(request, "✅ SD Collection updated successfully.")
        return redirect("sd_collection_list_zm")

    return render(request, "zonal_manager/sd_collection_edit.html", {"collection": collection})



@login_required
def sd_collection_delete(request, pk):
    collection = get_object_or_404(SDCollection, pk=pk)
    collection.delete()
    messages.success(request, "SD Collection deleted successfully ❌")
    return redirect("sd_collection_list_zm")



