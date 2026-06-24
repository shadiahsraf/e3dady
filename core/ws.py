from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def broadcast(event_type, data):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'live',
        {
            'type': event_type,
            'data': data,
        }
    )


def broadcast_scan(participant, scan_log):
    broadcast('scan_event', {
        'event': 'scan',
        'scan_type': 'individual',
        'participant': {
            'id': participant.id,
            'name': participant.name,
            'total_points': participant.total_points,
        },
        'team': {
            'id': participant.team.id,
            'name_ar': participant.team.name_ar,
            'primary': participant.team.primary_hex,
            'total_points': participant.team.total_points,
        },
        'points_change': scan_log.points_change,
        'location': scan_log.location,
    })


def broadcast_team_scan(team, points_change, location):
    broadcast('scan_event', {
        'event': 'scan',
        'scan_type': 'team',
        'team': {
            'id': team.id,
            'name_ar': team.name_ar,
            'primary': team.primary_hex,
            'total_points': team.total_points,
        },
        'points_change': points_change,
        'location': location,
    })


def broadcast_session(action, data=None):
    broadcast('session_event', {
        'event': 'session',
        'action': action,
        **(data or {}),
    })


def broadcast_leaderboard(teams_data):
    broadcast('leaderboard_update', {
        'event': 'leaderboard',
        'teams': teams_data,
    })
