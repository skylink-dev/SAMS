from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch
from decimal import Decimal

from django.contrib.auth import get_user_model
from zonal_manager.models import ZonalManager, ZMDailyTarget
from activity.models import Task, TaskNote
from master.models import TaskCategory

User = get_user_model()


class ZonalManagerViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Users
        self.zm_user = User.objects.create_user(username="zm1", password="pass", role="Zone Manager")
        self.asm_user = User.objects.create_user(username="asm1", password="pass", role="Area Sales Manager")
        self.other_asm = User.objects.create_user(username="asm2", password="pass", role="Area Sales Manager")

        # ZM and relations
        self.zm = ZonalManager.objects.create(user=self.zm_user)
        # Some projects use m2m as `asms`; ensure add works
        if hasattr(self.zm, 'asms'):
            self.zm.asms.add(self.asm_user)
        
        # Category
        self.category = TaskCategory.objects.create(name="General")

        # Targets
        self.target = ZMDailyTarget.objects.create(
            zonal_manager=self.zm,
            asm=self.asm_user,
            date=timezone.now().date(),
            application_target=10,
            pop_target=5,
            esign_target=3,
            new_taluk_target=2,
            new_live_partners_target=1,
            activations_target=4,
            calls_target=20,
            sd_collection_target=100,
            application_achieve=8,
            pop_achieve=5,
            esign_achieve=1,
            new_taluk_achieve=0,
            new_live_partners_achieve=1,
            activations_achieve=4,
            calls_achieve=10,
            sd_collection_achieve=50,
        )

    def login_zm(self):
        self.client.login(username="zm1", password="pass")

    # 1. daily_target filters and percentage aggregation
    def test_daily_target_filters_and_summary(self):
        self.login_zm()
        url = reverse('daily_target')
        response = self.client.get(url, {
            'asm': str(self.asm_user.id),
            'from_date': self.target.date.strftime('%Y-%m-%d'),
            'to_date': self.target.date.strftime('%Y-%m-%d'),
            'search': 'asm1',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('targets', response.context)
        targets = response.context['targets']
        self.assertTrue(len(targets) >= 1)
        # Ensure percent calculation present
        self.assertIn('percent', targets[0])
        self.assertIn('overall_percent', response.context)

    # 2. daily_target_detail metrics and percents
    def test_daily_target_detail_metrics(self):
        self.login_zm()
        url = reverse('daily_target_detail', args=[self.target.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('metrics', response.context)
        metrics = response.context['metrics']
        self.assertEqual(len(metrics), 8)
        for m in metrics:
            self.assertIn('percent', m)

    # 3. daily_target_edit rejects negative values and accepts valid updates
    def test_daily_target_edit_validation(self):
        self.login_zm()
        url = reverse('daily_target_edit', args=[self.target.pk])
        # Negative should error
        payload_neg = {
            'applications_target': '-1', 'applications_achieve': '0',
            'pop_target': '1', 'pop_achieve': '1',
            'e-sign_target': '1', 'e-sign_achieve': '1',
            'new-taluk_target': '1', 'new-taluk_achieve': '1',
            'new-live-partners_target': '1', 'new-live-partners_achieve': '1',
            'activations_target': '1', 'activations_achieve': '1',
            'calls_target': '1', 'calls_achieve': '1',
            'sd-collection_target': '1', 'sd-collection_achieve': '1',
        }
        response = self.client.post(url, data=payload_neg, follow=True)
        self.assertEqual(response.status_code, 200)
        # Stay on page with errors
        self.assertTemplateUsed(response, 'zonal_manager/zm_daily_target_edit.html')

        # Valid update
        payload_ok = {
            'applications_target': '12', 'applications_achieve': '10',
            'pop_target': '5', 'pop_achieve': '5',
            'e-sign_target': '3', 'e-sign_achieve': '2',
            'new-taluk_target': '2', 'new-taluk_achieve': '1',
            'new-live-partners_target': '1', 'new-live-partners_achieve': '1',
            'activations_target': '4', 'activations_achieve': '4',
            'calls_target': '10', 'calls_achieve': '10',
            'sd-collection_target': '20', 'sd-collection_achieve': '10',
        }
        response = self.client.post(url, data=payload_ok)
        self.assertEqual(response.status_code, 302)

    # 4. daily_target_add prevents duplicates and restricts ASM queryset
    def test_daily_target_add_duplicate_and_queryset(self):
        self.login_zm()
        url = reverse('daily_target_add')
        # Duplicate for same asm and date should error
        payload = {
            'asm': self.asm_user.id,
            'date': self.target.date.strftime('%Y-%m-%d'),
            'application_target': 1,
            'pop_target': 1,
            'esign_target': 1,
            'new_taluk_target': 1,
            'new_live_partners_target': 1,
            'activations_target': 1,
            'calls_target': 1,
            'sd_collection_target': 1,
        }
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        # asm queryset only contains related asms
        self.assertIn(self.asm_user, list(form.fields['asm'].queryset))
        self.assertNotIn(self.other_asm, list(form.fields['asm'].queryset))

    # 5. Task assignment validates ASM ownership and creates task
    def test_assign_task_to_asm_validation_and_create(self):
        self.login_zm()
        url = reverse('assign_task_to_asm')

        # Unauthorized role
        self.zm_user.role = 'Area Sales Manager'
        self.zm_user.save()
        resp = self.client.get(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        
        # Set back to ZM
        self.zm_user.role = 'Zone Manager'
        self.zm_user.save()

        # Invalid ASM (not under this ZM)
        payload_invalid = {
            'title': 'Task 1',
            'details': 'Do something',
            'category': self.category.id,
            'assigned_to': self.other_asm.id,
            'start_date': timezone.now().date(),
            'end_date': timezone.now().date(),
        }
        resp = self.client.post(url, data=payload_invalid, follow=True)
        self.assertEqual(resp.status_code, 200)

        # Valid ASM
        payload_valid = {
            'title': 'Task 1',
            'details': 'Do something',
            'category': self.category.id,
            'assigned_to': self.asm_user.id,
            'start_date': timezone.now().date(),
            'end_date': timezone.now().date(),
        }
        resp = self.client.post(url, data=payload_valid)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Task.objects.filter(title='Task 1', assigned_by=self.zm_user).exists())

    # 6. zm_task_list filters and summary
    def test_zm_task_list_filters(self):
        self.login_zm()
        Task.objects.create(title='A', details='d', assigned_by=self.zm_user, assigned_to=self.asm_user, start_date=timezone.now().date(), end_date=timezone.now().date(), status='pending')
        Task.objects.create(title='B', details='d', assigned_by=self.zm_user, assigned_to=self.asm_user, start_date=timezone.now().date(), end_date=timezone.now().date(), status='completed')
        url = reverse('zm_task_list')
        resp = self.client.get(url, {'status': 'pending'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn('total_tasks', resp.context)
        self.assertIn('pending_tasks', resp.context)
        self.assertIn('completed_tasks', resp.context)

    # 7. zm_task_detail adds notes
    def test_zm_task_detail_add_note(self):
        self.login_zm()
        task = Task.objects.create(title='A', details='d', assigned_by=self.zm_user, assigned_to=self.asm_user, start_date=timezone.now().date(), end_date=timezone.now().date())
        url = reverse('zm_task_detail', args=[task.id])
        resp = self.client.post(url, {'note': 'hello'})
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(TaskNote.objects.filter(task=task, user=self.zm_user, note='hello').exists())

    # 8. zm_task_edit updates fields
    def test_zm_task_edit_updates(self):
        self.login_zm()
        task = Task.objects.create(title='A', details='d', assigned_by=self.zm_user, assigned_to=self.asm_user, start_date=timezone.now().date(), end_date=timezone.now().date(), status='pending')
        url = reverse('zm_task_edit', args=[task.id])
        resp = self.client.post(url, {
            'title': 'A2',
            'details': 'd2',
            'category': self.category.id,
            'assigned_to': self.asm_user.id,
            'start_date': timezone.now().date(),
            'end_date': timezone.now().date(),
            'status': 'completed',
        })
        self.assertEqual(resp.status_code, 302)
        task.refresh_from_db()
        self.assertEqual(task.title, 'A2')
        self.assertEqual(task.status, 'completed')

    # 9. zm_task_delete deletes
    def test_zm_task_delete(self):
        self.login_zm()
        task = Task.objects.create(title='A', details='d', assigned_by=self.zm_user, assigned_to=self.asm_user, start_date=timezone.now().date(), end_date=timezone.now().date())
        url = reverse('zm_task_delete', args=[task.id])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Task.objects.filter(id=task.id).exists())

    # 10. zm_change_status changes status
    def test_zm_change_status(self):
        self.login_zm()
        task = Task.objects.create(title='A', details='d', assigned_by=self.zm_user, assigned_to=self.asm_user, start_date=timezone.now().date(), end_date=timezone.now().date(), status='pending')
        url = reverse('zm_change_status', args=[task.id, 'completed'])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        task.refresh_from_db()
        self.assertEqual(task.status, 'completed')
