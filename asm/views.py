from dal import autocomplete
from account.models import CustomUser
from datetime import date
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from zonal_manager.models import ZMDailyTarget, ZonalManager
from account.models import CustomUser
from django.shortcuts import render, get_object_or_404, redirect
from decimal import Decimal, InvalidOperation


class PartnerAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = CustomUser.objects.filter(role="Partner")
        if self.q:
            qs = qs.filter(full_name__icontains=self.q)
        return qs

@login_required
def asm_daily_target(request):
    if request.user.role != "Area Sales Manager":
        messages.error(request, "Access Denied.")
        return redirect(get_dashboard_url(request.user))

    targets = ZMDailyTarget.objects.filter(asm=request.user).order_by('-date')

    for t in targets:

        # ---------------------------
        # ZM total target (given by ZM)
        # ---------------------------
        t.zm_total_target = (
            t.application_target +
            t.pop_target +
            t.esign_target +
            t.new_taluk_target +
            t.new_live_partners_target +
            t.activations_target +
            t.calls_target +
            t.sd_collection_target
        )

        # ---------------------------
        # ASM total target
        # (if you have separate ASM_target fields, replace here)
        # else ASM target = ZM target
        # ---------------------------
        t.asm_total_target = t.zm_total_target   # temporary (unless ASM target fields exist)

        # ---------------------------
        # ASM total achieve
        # ---------------------------
        t.asm_total_achieve = (
            t.application_achieve +
            t.pop_achieve +
            t.esign_achieve +
            t.new_taluk_achieve +
            t.new_live_partners_achieve +
            t.activations_achieve +
            t.calls_achieve +
            t.sd_collection_achieve
        )

        # ---------------------------
        # 1️⃣ ZM Target vs ASM Achieve %
        # ---------------------------
        if t.zm_total_target > 0:
            t.zm_vs_achieve_percent = round((t.asm_total_achieve / t.zm_total_target) * 100, 1)
        else:
            t.zm_vs_achieve_percent = 0

        # ---------------------------
        # 2️⃣ ASM Target vs ASM Achieve %
        # ---------------------------
        if t.asm_total_target > 0:
            t.asm_vs_achieve_percent = round((t.asm_total_achieve / t.asm_total_target) * 100, 1)
        else:
            t.asm_vs_achieve_percent = 0

    context = {"targets": targets}
    return render(request, "asm/asm_daily_target.html", context)


@login_required
def asm_daily_target_detail(request, pk):
    """📄 View: Detail page for a specific ZM daily target (ASM Editable)"""
    target = get_object_or_404(ZMDailyTarget, pk=pk)
    asm = target.asm

    # Get ASM’s assigned regions if available
    asm_states = getattr(asm, "states", []).all() if asm and hasattr(asm, "states") else []
    asm_districts = getattr(asm, "districts", []).all() if asm and hasattr(asm, "districts") else []
    asm_offices = getattr(asm, "offices", []).all() if asm and hasattr(asm, "offices") else []

    metrics = [
        {"name": "Applications", "zm_target": target.application_target, "asm_target": target.asm_application_target, "achieve": target.application_achieve},
        {"name": "POP", "zm_target": target.pop_target, "asm_target": target.asm_pop_target, "achieve": target.pop_achieve},
        {"name": "E-Sign", "zm_target": target.esign_target, "asm_target": target.asm_esign_target, "achieve": target.esign_achieve},
        {"name": "New Taluk", "zm_target": target.new_taluk_target, "asm_target": target.asm_new_taluk_target, "achieve": target.new_taluk_achieve},
        {"name": "New Live Partners", "zm_target": target.new_live_partners_target, "asm_target": target.asm_new_live_partners_target, "achieve": target.new_live_partners_achieve},
        {"name": "Activations", "zm_target": target.activations_target, "asm_target": target.asm_activations_target, "achieve": target.activations_achieve},
        {"name": "Calls", "zm_target": target.calls_target, "asm_target": target.asm_calls_target, "achieve": target.calls_achieve},
        {"name": "SD Collection", "zm_target": target.sd_collection_target, "asm_target": target.asm_sd_collection_target, "achieve": target.sd_collection_achieve},
    ]

    # -------------------------
    # Correct percent calculation:
    # Achieved ÷ ZM Target × 100
    # -------------------------
    for m in metrics:
        if m["zm_target"] and m["zm_target"] > 0:
            m["percent"] = round((m["achieve"] / m["zm_target"]) * 100, 1)
        else:
            m["percent"] = 0

    context = {
        "target": target,
        "metrics": metrics,
        "asm": asm,
        "asm_states": asm_states,
        "asm_districts": asm_districts,
        "asm_offices": asm_offices,
    }

    return render(request, "asm/asm_daily_target_detail.html", context)



@login_required
def asm_daily_target_edit(request, pk):
    """✏️ ASM updates only ASM Target + ASM Achievement"""
    target = get_object_or_404(ZMDailyTarget, pk=pk)

    # metric_slug : (asm_target_field, asm_achieve_field)
    metric_fields = {
        "applications": ("asm_application_target", "application_achieve"),
        "pop": ("asm_pop_target", "pop_achieve"),
        "e-sign": ("asm_esign_target", "esign_achieve"),
        "new-taluk": ("asm_new_taluk_target", "new_taluk_achieve"),
        "new-live-partners": ("asm_new_live_partners_target", "new_live_partners_achieve"),
        "activations": ("asm_activations_target", "activations_achieve"),
        "calls": ("asm_calls_target", "calls_achieve"),
        "sd-collection": ("asm_sd_collection_target", "sd_collection_achieve"),
    }

    if request.method == "POST":
        errors = []

        for metric, (asm_target_field, achieve_field) in metric_fields.items():
            try:
                asm_t_value = Decimal(request.POST.get(f"{metric}_asm_target", "0") or "0")
                asm_a_value = Decimal(request.POST.get(f"{metric}_achieve", "0") or "0")

                # Validation: no negative numbers
                if asm_t_value < 0 or asm_a_value < 0:
                    errors.append(f"⚠️ {metric.replace('-', ' ').title()} values cannot be negative.")
                    continue

                setattr(target, asm_target_field, asm_t_value)
                setattr(target, achieve_field, asm_a_value)

            except InvalidOperation:
                errors.append(f"⚠️ Invalid number entered for {metric.replace('-', ' ').title()}.")

        # Show errors
        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            target.save()
            messages.success(request, "✅ ASM Target updated successfully!")
            return redirect("asm_daily_target_detail", pk=pk)

    context = {"target": target}
    return render(request, "asm/asm_daily_target_edit.html", context)


# SD collect 
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from django.utils import timezone

from asm.models import ASM  
from account.models import CustomUser
from partner.models import SDCollection
from zonal_manager.models import ZonalManager
from zonal_manager.models import ZonalManager  # you already have this
# optionally import Decimal for amounts validation

@login_required
def asm_sd_list(request):
    if request.user.role != "Area Sales Manager":
        messages.error(request, "Access Denied.")
        return redirect('home')

    # All collections where this user is the asm
    qs = SDCollection.objects.filter(asm=request.user, is_deleted=False).order_by('-date')

    # basic filters
    start = request.GET.get('start_date')
    end = request.GET.get('end_date')
    status = request.GET.get('status')

    if start:
        qs = qs.filter(date__gte=start)
    if end:
        qs = qs.filter(date__lte=end)
    if status:
        qs = qs.filter(status=status)

    context = {
        'collections': qs,
        'start_date': start or '',
        'end_date': end or '',
        'status': status or '',
    }
    return render(request, 'asm/asm_sd_list.html', context)
@login_required
@login_required
def asm_sd_add(request):
    if request.user.role != "Area Sales Manager":
        messages.error(request, "Access Denied.")
        return redirect("home")

    # Get ASM profile for logged-in user
    asm_obj = ASM.objects.filter(user=request.user).first()

    if not asm_obj:
        messages.error(request, "ASM profile not found.")
        return redirect("home")

    # FIXED: show only partners assigned to this ASM
    partners = CustomUser.objects.filter(
        role="Partner",
        assigned_asms=asm_obj,
        is_active=True
    )

    if request.method == "POST":
        partner_id = request.POST.get("partner")
        amount = request.POST.get("amount")
        note = request.POST.get("note")

        # Security: ensure partner belongs to this ASM
        partner = CustomUser.objects.filter(
            id=partner_id,
            role="Partner",
            assigned_asms=asm_obj
        ).first()

        if not partner:
            messages.error(request, "Invalid Partner selected.")
            return redirect("asm_sd_add")

        # Determine ZM of this ASM
        zm_obj = asm_obj.zone_manager if hasattr(asm_obj, "zone_manager") else None

        # 🔥 FIXED: SDCollection.asm MUST be CustomUser → use asm_obj.user
        SDCollection.objects.create(
            partner=partner,
            asm=asm_obj.user,       # FIXED ✔✔✔
            zone_manager=zm_obj,
            amount=amount,
            note=note,
        )

        messages.success(request, "SD Collection Added Successfully ✅")
        return redirect("asm_sd_list")

    return render(request, "asm/sd_collection_add.html", {
        "partners": partners,
        "asm": asm_obj,
    })



@login_required
def asm_sd_edit(request, pk):
    if request.user.role != "Area Sales Manager":
        messages.error(request, "Access Denied.")
        return redirect('home')

    collection = get_object_or_404(SDCollection, pk=pk, is_deleted=False)

    # Security: ASM can only edit their own records (asm is CustomUser)
    if collection.asm_id != request.user.id:
        return HttpResponseForbidden("You cannot edit this record.")

    if request.method == "POST":
        amount = request.POST.get("amount") or 0
        note = request.POST.get("note", "")
        status = request.POST.get("status", "pending")

        collection.amount = amount
        collection.note = note
        collection.status = status
        collection.save()

        messages.success(request, "SD Collection Updated Successfully ✅")
        return redirect("asm_sd_list")

    return render(request, "asm/sd_collection_edit.html", {
        "collection": collection
    })



@login_required
def asm_sd_delete(request, pk):
    if request.user.role != "Area Sales Manager":
        messages.error(request, "Access Denied.")
        return redirect('home')

    collection = get_object_or_404(SDCollection, pk=pk, is_deleted=False)

    # Security: ensure this ASM owns this record
    if collection.asm_id != request.user.id:
        return HttpResponseForbidden("You cannot delete this record.")

    # Soft delete
    collection.is_deleted = True
    collection.save()

    messages.success(request, "SD Collection Deleted Successfully ❌")
    return redirect("asm_sd_list")


@login_required
def asm_get_partner_details(request, partner_id):
    partner = get_object_or_404(CustomUser, pk=partner_id, role='Partner')
    # try find assigned ASM/ZM info (depends on your relations)
    asm_name = ''
    asm_id = ''
    zm_name = ''
    zm_id = ''
    if hasattr(partner, 'assigned_asm') and partner.assigned_asm:
        asm_user = partner.assigned_asm.user if hasattr(partner.assigned_asm, 'user') else partner.assigned_asm
        asm_name = asm_user.get_full_name() if asm_user else ''
        asm_id = asm_user.id if asm_user else ''
        zm = partner.assigned_asm.zone_manager if hasattr(partner.assigned_asm, 'zone_manager') else None
        if zm:
            zm_name = zm.user.get_full_name()
            zm_id = zm.id

    return JsonResponse({
        'asm_name': asm_name,
        'asm_id': asm_id,
        'zm_name': zm_name,
        'zm_id': zm_id,
    })


## Task


from master.models import TaskCategory
from activity.models import Task, TaskNote
from django.contrib.auth import get_user_model
User = get_user_model()

@login_required
def asm_task_list(request):
    """📋 Show all tasks assigned to the logged-in ASM WITH FILTERS + UI"""
    if request.user.role != "Area Sales Manager":
        messages.error(request, "Access Denied.")
        return redirect("daily_target")

    tasks = Task.objects.filter(
        assigned_to=request.user,
        is_deleted=False
    ).select_related("category", "assigned_by")

    # ---------- FILTERS ----------
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    selected_status = request.GET.get("status", "")
    selected_user = request.GET.get("assigned_to", "")

    # date filter
    if start_date:
        tasks = tasks.filter(start_date__gte=start_date)
    if end_date:
        tasks = tasks.filter(end_date__lte=end_date)

    # status filter
    if selected_status:
        tasks = tasks.filter(status=selected_status)

    # keep this for UI (ASM will still see only own tasks)
    if selected_user:
        tasks = tasks.filter(assigned_to_id=selected_user)

    # ---------- SUMMARY ----------
    total_tasks = tasks.count()
    pending_tasks = tasks.filter(status="pending").count()
    completed_tasks = tasks.filter(status="completed").count()

    # ---------- DROPDOWNS ----------
    users = User.objects.filter(role="Area Sales Manager")
    status_choices = Task.STATUS_CHOICES

    context = {
        "tasks": tasks,
        "total_tasks": total_tasks,
        "pending_tasks": pending_tasks,
        "completed_tasks": completed_tasks,
        "start_date": start_date,
        "end_date": end_date,
        "selected_user": selected_user,
        "selected_status": selected_status,
        "status_choices": status_choices,
        "users": users,
    }

    return render(request, "asm/task_list.html", context)



@login_required
def asm_task_detail(request, task_id):
    """📄 ASM View / Update Task"""
    task = get_object_or_404(Task, id=task_id, assigned_to=request.user)
    notes = task.notes.all()

    if request.method == "POST":
        # Change status
        new_status = request.POST.get("status")
        if new_status:
            task.status = new_status
            task.save()
            messages.success(request, "✅ Task status updated.")
            return redirect("asm_task_detail", task_id=task.id)

        # Add note
        note_text = request.POST.get("note")
        if note_text:
            TaskNote.objects.create(task=task, user=request.user, note=note_text)
            messages.success(request, "📝 Note added.")
            return redirect("asm_task_detail", task_id=task.id)

    return render(request, "asm/task_detail.html", {
        "task": task,
        "notes": notes
    })

def asm_update_task_status(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if request.method == "POST":
        task.status = request.POST.get("status")
        task.save()

        messages.success(request, "Task status updated successfully!")
        return redirect("asm_task_detail", task_id=task.id)
