from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import DonationAppointment

class Command(BaseCommand):
    help = 'Send reminders for upcoming donation appointments within the next 24 hours'

    def handle(self, *args, **options):
        now = timezone.now()
        window_end = now + timedelta(hours=24)
        appts = DonationAppointment.objects.filter(scheduled_at__gte=now, scheduled_at__lte=window_end, reminder_sent=False, status='scheduled')
        count = 0
        for a in appts:
            # Placeholder: integrate Twilio or email here if configured
            try:
                # mark as reminder sent
                a.reminder_sent = True
                a.save()
                self.stdout.write(self.style.SUCCESS(f"Reminder marked for appointment {a.id} (donor={a.donor.user.username}) scheduled at {a.scheduled_at}"))
                count += 1
            except Exception as e:
                self.stderr.write(f"Failed for appointment {a.id}: {e}")
        self.stdout.write(self.style.NOTICE(f"Processed {count} reminders"))
