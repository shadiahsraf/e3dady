from django.db import models
from django.utils import timezone


class Team(models.Model):
    name = models.CharField(max_length=50, unique=True)
    name_ar = models.CharField(max_length=50)
    color = models.CharField(max_length=20)
    primary_hex = models.CharField(max_length=7, default='#1d4ed8')
    secondary_hex = models.CharField(max_length=7, default='#0b1d50')
    flag_emoji = models.CharField(max_length=8, default='🏳️')
    team_code = models.CharField(max_length=32, unique=True, blank=True, null=True)
    total_points = models.IntegerField(default=0)
    entry_rank = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name_ar

    def recalculate_total(self):
        from django.db.models import Sum
        player_total = self.participants.aggregate(s=Sum('total_points'))['s'] or 0
        team_only_total = self.scan_logs.filter(participant__isnull=True).aggregate(s=Sum('points_change'))['s'] or 0
        self.total_points = player_total + team_only_total
        self.save(update_fields=['total_points'])
        return self.total_points


class Activity(models.Model):
    SERVICE = 'service'
    PLAY = 'play'
    RETREAT = 'retreat'
    KIND_CHOICES = [
        (SERVICE, 'خدمة'),
        (PLAY, 'لعب'),
        (RETREAT, 'خلوة'),
    ]

    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    number = models.IntegerField()
    label = models.CharField(max_length=50)
    is_entry = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)

    class Meta:
        unique_together = ('kind', 'number')
        ordering = ['kind', 'number']

    def __str__(self):
        return self.label


class Participant(models.Model):
    name = models.CharField(max_length=120)
    unique_code = models.CharField(max_length=32, unique=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='participants')
    total_points = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['team', 'name']

    def __str__(self):
        return f"{self.name} ({self.team.name_ar})"

    def recalculate_total(self):
        from django.db.models import Sum
        agg = self.scan_logs.aggregate(s=Sum('points_change'))
        self.total_points = agg['s'] or 0
        self.save(update_fields=['total_points'])
        return self.total_points


class Scan(models.Model):
    """Legacy scan model — kept for migration compatibility. New logic uses ScanLog."""
    ON_TIME = 'on_time'
    LATE = 'late'
    ABSENT = 'absent'
    ATTENDANCE_CHOICES = [
        (ON_TIME, 'حضر في المعاد'),
        (LATE, 'اتأخر'),
        (ABSENT, 'غاب'),
    ]
    ATTENDANCE_POINTS = {ON_TIME: 15, LATE: 5, ABSENT: 0}

    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='scans')
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='scans')
    attendance = models.CharField(max_length=12, choices=ATTENDANCE_CHOICES)
    bonus_points = models.IntegerField(default=0)
    points_awarded = models.IntegerField(default=0)
    scanned_by = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('participant', 'activity')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.participant.name} → {self.activity.label}"

    def save(self, *args, **kwargs):
        base = self.ATTENDANCE_POINTS.get(self.attendance, 0)
        self.points_awarded = base + (self.bonus_points or 0)
        super().save(*args, **kwargs)


class TeamBonus(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='bonuses')
    reason = models.CharField(max_length=200)
    points = models.IntegerField()
    activity = models.ForeignKey(Activity, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.team.name_ar}: {self.reason} ({self.points:+d})"


class ScanLog(models.Model):
    """Every point change is logged here. This is the single source of truth for points."""
    INDIVIDUAL = 'individual'
    TEAM_SCAN = 'team'
    SESSION_TYPES = [
        (INDIVIDUAL, 'فردي'),
        (TEAM_SCAN, 'فريق'),
    ]

    LOCATION_CHOICES = [
        ('qa3a_1', 'قاعة 1'),
        ('qa3a_2', 'قاعة 2'),
        ('qa3a_3', 'قاعة 3'),
        ('qa3a_4', 'قاعة 4'),
        ('qa3a_5', 'قاعة 5'),
        ('qa3a_6', 'قاعة 6'),
        ('mal3ab_1', 'ملعب 1'),
        ('mal3ab_2', 'ملعب 2'),
        ('mal3ab_3', 'ملعب 3'),
        ('mal3ab_4', 'ملعب 4'),
        ('mal3ab_5', 'ملعب 5'),
    ]

    participant = models.ForeignKey(
        Participant, on_delete=models.CASCADE,
        related_name='scan_logs', null=True, blank=True
    )
    team = models.ForeignKey(
        Team, on_delete=models.CASCADE,
        related_name='scan_logs', null=True, blank=True
    )
    points_change = models.IntegerField(default=1)  # +1 or -1
    session_type = models.CharField(max_length=12, choices=SESSION_TYPES, default=INDIVIDUAL)
    location = models.CharField(max_length=20, choices=LOCATION_CHOICES, blank=True)
    scanned_by = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        target = self.participant.name if self.participant else (self.team.name_ar if self.team else '?')
        return f"{target}: {self.points_change:+d} ({self.get_location_display()})"


class Session(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='sessions')
    is_active = models.BooleanField(default=True)
    is_frozen = models.BooleanField(default=False)
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    completion_order = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        status = 'نشطة' if self.is_active else 'منتهية'
        return f"{self.activity.label} ({status})"
