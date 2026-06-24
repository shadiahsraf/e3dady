from django.contrib import admin
from .models import Team, Participant, Activity, Scan, TeamBonus, ScanLog, Session


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name_ar', 'name', 'team_code', 'color', 'total_points')
    list_editable = ('total_points',)


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('name', 'team', 'unique_code', 'total_points')
    list_filter = ('team',)
    search_fields = ('name', 'unique_code')


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('label', 'kind', 'number', 'is_entry', 'is_active')
    list_editable = ('is_entry', 'is_active')
    list_filter = ('kind', 'is_entry', 'is_active')


@admin.register(ScanLog)
class ScanLogAdmin(admin.ModelAdmin):
    list_display = ('participant', 'team', 'points_change', 'session_type', 'location', 'scanned_by', 'created_at')
    list_filter = ('session_type', 'location', 'team')
    search_fields = ('participant__name', 'team__name_ar')


@admin.register(Scan)
class ScanAdmin(admin.ModelAdmin):
    list_display = ('participant', 'activity', 'attendance', 'points_awarded', 'created_at')
    list_filter = ('attendance', 'activity')


@admin.register(TeamBonus)
class TeamBonusAdmin(admin.ModelAdmin):
    list_display = ('team', 'reason', 'points', 'created_at')
    list_filter = ('team',)


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('activity', 'is_active', 'is_frozen', 'started_at', 'ended_at')
    list_filter = ('is_active', 'is_frozen')
