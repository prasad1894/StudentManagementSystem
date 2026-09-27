import os

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from employees.models import UserProfile


class Command(BaseCommand):
    help = "Create or update the production admin user"

    def handle(self, *args, **options):
        username = os.getenv("PROD_ADMIN_USERNAME")
        password = os.getenv("PROD_ADMIN_PASSWORD")
        email = os.getenv("PROD_ADMIN_EMAIL", "")

        if not username or not password:
            self.stdout.write(
                self.style.ERROR(
                    "PROD_ADMIN_USERNAME and PROD_ADMIN_PASSWORD must be set."
                )
            )
            return

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "is_staff": True,
                "is_superuser": True,
            },
        )

        user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        profile, _ = UserProfile.objects.get_or_create(
            user=user
        )

        profile.role = "ADMIN"
        profile.must_change_password = False
        profile.save()

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Production admin '{username}' created successfully."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Production admin '{username}' updated successfully."
                )
            )