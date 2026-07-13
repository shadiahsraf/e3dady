"""Seed teams, activities and 50 Egyptian participants."""
import random
import secrets
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Team, Participant, Activity, Session, ScanLog


TEAMS_DATA = [
    {
        'name': 'France', 'name_ar': 'فرنسا', 'color': 'blue',
        'primary_hex': '#1d4ed8', 'secondary_hex': '#0b1d50',
        'flag_emoji': '🇫🇷',
    },
    {
        'name': 'Argentina', 'name_ar': 'الأرجنتين', 'color': 'sky',
        'primary_hex': '#38bdf8', 'secondary_hex': '#075985',
        'flag_emoji': '🇦🇷',
    },
    {
        'name': 'Brazil', 'name_ar': 'البرازيل', 'color': 'yellow',
        'primary_hex': '#f5c518', 'secondary_hex': '#1a5e1f',
        'flag_emoji': '🇧🇷',
    },
    {
        'name': 'Portugal', 'name_ar': 'البرتغال', 'color': 'green',
        'primary_hex': '#15803d', 'secondary_hex': '#581c0c',
        'flag_emoji': '🇵🇹',
    },
]

# Realistic Egyptian first + last names — keep these as separate pools and mix
FIRST_NAMES = [
    'مينا', 'كيرلس', 'مارك', 'بيشوي', 'جرجس', 'مايكل', 'أنطون', 'فادي',
    'بطرس', 'صموئيل', 'يوسف', 'بولا', 'ديفيد', 'إيهاب', 'رامي', 'هاني',
    'بافلي', 'ميشيل', 'أندرو', 'كريم', 'عماد', 'ناصر', 'وائل', 'شريف',
    'ماريو', 'بيتر', 'باسم', 'عادل',
    'ماريانا', 'مريم', 'مارينا', 'فيرونيكا', 'مونيكا', 'كريستينا', 'مارثا',
    'إيريني', 'سارة', 'يوستينا', 'إنجي', 'دميانة', 'رنا', 'ديانا',
    'كاترين', 'فيبي', 'ميرنا', 'باسيليا', 'هيلين', 'نانسي', 'ساندي',
    'أمنية', 'ميرا',
]

LAST_NAMES = [
    'عزيز', 'صبري', 'منير', 'كامل', 'فهيم', 'سامي', 'فؤاد', 'إسحاق',
    'حنا', 'يعقوب', 'إبراهيم', 'جرجس', 'فرج', 'بشير', 'رزق', 'نظير',
    'وهبة', 'بسطا', 'لويس', 'سعد', 'رياض', 'لمعي', 'ميلاد', 'موريس',
    'ثروت', 'عياد', 'الفي', 'مكرم', 'رمزي', 'حلمي',
]


def _make_code() -> str:
    """8-char URL-safe code, easy to encode in a QR."""
    return secrets.token_urlsafe(6)[:8].upper().replace('_', 'A').replace('-', 'B')


class Command(BaseCommand):
    help = 'Seed teams, activities, and 50 sample participants.'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true',
                            help='Wipe existing participants/scans before seeding.')

    @transaction.atomic
    def handle(self, *args, **opts):
        if opts['reset']:
            from core.models import Scan, TeamBonus
            ScanLog.objects.all().delete()
            Scan.objects.all().delete()
            TeamBonus.objects.all().delete()
            Session.objects.all().delete()
            Participant.objects.all().delete()
            Team.objects.update(entry_rank=None, total_points=0)
            self.stdout.write(self.style.WARNING('All data cleared.'))

        # Teams (with team_code for QR)
        teams = []
        for t in TEAMS_DATA:
            team_code = 'TEAM_' + t['name'][:3].upper()
            t_data = {**t, 'team_code': team_code}
            team, _ = Team.objects.update_or_create(name=t['name'], defaults=t_data)
            teams.append(team)
        self.stdout.write(self.style.SUCCESS(f'✔ {len(teams)} teams ready (with team QR codes).'))

        # Activities
        activity_specs = (
            [('service', i, f'خدمة {i}') for i in range(1, 6)] +
            [('play', i, f'لعب {i}') for i in range(1, 5)] +
            [('retreat', i, f'خلوة {i}') for i in range(1, 4)]
        )
        for kind, num, label in activity_specs:
            Activity.objects.update_or_create(
                kind=kind, number=num,
                defaults={'label': label},
            )

        # Mark "خدمة 1" as the entry activity + active by default
        entry = Activity.objects.get(kind='service', number=1)
        Activity.objects.all().update(is_entry=False, is_active=False)
        entry.is_entry = True
        entry.is_active = True
        entry.save()
        self.stdout.write(self.style.SUCCESS(
            f'✔ {Activity.objects.count()} activities ready (entry = {entry.label}).'
        ))

        # Participants — 50 total, ~12-13 per team
        rng = random.Random(42)
        names_pool = [f"{f} {l}" for f in FIRST_NAMES for l in LAST_NAMES]
        rng.shuffle(names_pool)
        chosen_names = names_pool[:50]

        used_codes = set(Participant.objects.values_list('unique_code', flat=True))
        per_team = [13, 13, 12, 12]
        rng.shuffle(per_team)

        idx = 0
        for team, count in zip(teams, per_team):
            for _ in range(count):
                if idx >= len(chosen_names):
                    break
                name = chosen_names[idx]
                idx += 1
                # Generate a unique code
                while True:
                    code = _make_code()
                    if code not in used_codes:
                        used_codes.add(code)
                        break
                Participant.objects.create(name=name, unique_code=code, team=team)
        self.stdout.write(self.style.SUCCESS(
            f'✔ {Participant.objects.count()} participants created.'
        ))

        # Shared leader user
        User.objects.filter(username=settings.LEADER_USERNAME).delete()
        user = User.objects.create_user(
            username=settings.LEADER_USERNAME,
            password=settings.LEADER_PASSWORD,
        )
        user.is_staff = True
        user.save()

        # Admin superuser
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin')
            self.stdout.write(self.style.SUCCESS('✔ Admin user: admin / admin'))

        # Default active session
        Session.objects.filter(is_active=True).update(is_active=False)
        Session.objects.create(activity=entry, is_active=True)
        self.stdout.write(self.style.SUCCESS(f'✔ Active session: {entry.label}'))

        self.stdout.write(self.style.SUCCESS(
            f'\n🎉 Seed complete!\n'
            f'   Leader login → username: {settings.LEADER_USERNAME}  '
            f'password: {settings.LEADER_PASSWORD}\n'
            f'   Admin login  → username: admin  password: admin\n'
        ))
