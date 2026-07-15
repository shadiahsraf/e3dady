from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from .models import Team, Participant, Activity, ScanLog, Session
from . import ws


@transaction.atomic
def record_individual_scan(participant, points_change, location, scanned_by=''):
    """Record a ±1 point scan for a single participant."""
    log = ScanLog.objects.create(
        participant=participant,
        team=participant.team,
        points_change=points_change,
        session_type=ScanLog.INDIVIDUAL,
        location=location,
        scanned_by=scanned_by,
    )
    participant.recalculate_total()
    participant.team.recalculate_total()

    try:
        ws.broadcast_scan(participant, log)
    except Exception:
        pass
    try:
        ws.broadcast_leaderboard(_build_leaderboard_data())
    except Exception:
        pass

    return log


@transaction.atomic
def record_team_scan(team, points_change, location, scanned_by=''):
    """Record a ±1 point scan for ALL members of a team."""
    logs = []
    for p in team.participants.all():
        log = ScanLog.objects.create(
            participant=p,
            team=team,
            points_change=points_change,
            session_type=ScanLog.TEAM_SCAN,
            location=location,
            scanned_by=scanned_by,
        )
        logs.append(log)
        p.recalculate_total()

    team.recalculate_total()

    try:
        ws.broadcast_team_scan(team, points_change, location)
    except Exception:
        pass
    try:
        ws.broadcast_leaderboard(_build_leaderboard_data())
    except Exception:
        pass

    return logs


@transaction.atomic
def record_team_only_scan(team, points_change, location, scanned_by=''):
    """Record points for the TEAM only (not distributed to individual players)."""
    log = ScanLog.objects.create(
        participant=None,
        team=team,
        points_change=points_change,
        session_type=ScanLog.TEAM_SCAN,
        location=location,
        scanned_by=scanned_by,
    )
    team.recalculate_total()

    try:
        ws.broadcast_team_scan(team, points_change, location)
    except Exception:
        pass
    try:
        ws.broadcast_leaderboard(_build_leaderboard_data())
    except Exception:
        pass

    return log


def lookup_code(code):
    """Look up a code — could be a participant or a team."""
    try:
        p = Participant.objects.select_related('team').get(unique_code=code)
        return {'type': 'individual', 'participant': p}
    except Participant.DoesNotExist:
        pass
    try:
        t = Team.objects.get(team_code=code)
        return {'type': 'team', 'team': t}
    except Team.DoesNotExist:
        pass
    return None


def get_team_scoreboard():
    """Returns teams sorted by total points."""
    teams = list(Team.objects.all())
    for t in teams:
        total = t.participants.aggregate(s=Sum('total_points'))['s'] or 0
        t.computed_total = total
        if t.total_points != total:
            t.total_points = total
            t.save(update_fields=['total_points'])
    teams.sort(key=lambda t: (-t.computed_total, t.name))
    return teams


def get_team_view_data():
    """Data for the team view display — names + checkmarks for current session."""
    session = get_active_session()
    teams_data = []
    for team in Team.objects.all().order_by('name'):
        members = []
        for p in team.participants.all().order_by('name'):
            # A participant is "checked" if they have any ScanLog in the current session's timeframe
            checked = False
            if session:
                checked = ScanLog.objects.filter(
                    participant=p,
                    created_at__gte=session.started_at,
                ).exists()
            members.append({
                'id': p.id,
                'name': p.name,
                'checked': checked,
            })
        teams_data.append({
            'id': team.id,
            'name': team.name,
            'name_ar': team.name_ar,
            'flag': team.flag_emoji,
            'primary': team.primary_hex,
            'secondary': team.secondary_hex,
            'total_points': team.total_points,
            'members': members,
        })
    return {'teams': teams_data}


def get_active_session():
    return Session.objects.filter(is_active=True).select_related('activity').first()


def start_session(activity):
    Session.objects.filter(is_active=True).update(is_active=False, ended_at=timezone.now())
    Activity.objects.all().update(is_active=False)
    activity.is_active = True
    activity.save(update_fields=['is_active'])

    session = Session.objects.create(activity=activity, is_active=True)

    try:
        ws.broadcast_session('start', {
            'activity': {'id': activity.id, 'label': activity.label},
            'session_id': session.id,
        })
    except Exception:
        pass
    return session


def end_session():
    session = Session.objects.filter(is_active=True).first()
    if not session:
        return None
    session.is_active = False
    session.is_frozen = True
    session.ended_at = timezone.now()
    session.save()
    try:
        ws.broadcast_session('end', {'session_id': session.id})
    except Exception:
        pass
    return session


def reset_session_checkmarks():
    """Reset the current session (new timestamps) without affecting total points."""
    session = get_active_session()
    if session:
        session.is_active = False
        session.ended_at = timezone.now()
        session.save()
        new_session = Session.objects.create(activity=session.activity, is_active=True)
        try:
            ws.broadcast_session('reset', {
                'activity': {'id': session.activity.id, 'label': session.activity.label},
            })
        except Exception:
            pass
        return new_session
    return None


def get_scan_logs(participant_id=None, team_id=None, location=None, limit=100):
    """Filter scan logs for admin dashboard."""
    qs = ScanLog.objects.select_related('participant', 'team').all()
    if participant_id:
        qs = qs.filter(participant_id=participant_id)
    if team_id:
        qs = qs.filter(team_id=team_id)
    if location:
        qs = qs.filter(location=location)
    return qs[:limit]


def _build_leaderboard_data():
    teams = get_team_scoreboard()
    return [
        {
            'id': t.id,
            'name_ar': t.name_ar,
            'flag': t.flag_emoji,
            'primary': t.primary_hex,
            'total': t.computed_total,
        } for t in teams
    ]
