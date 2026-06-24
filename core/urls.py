from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('scanner/', views.scanner, name='scanner'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('teams/', views.team_view, name='team_view'),
    path('live/', views.live_screen, name='live_screen'),
    path('qr-codes/', views.qr_codes_page, name='qr_codes'),
    path('qr-codes/download/', views.qr_download_all, name='qr_download_all'),
    path('qr/<str:code>.png', views.qr_image, name='qr_image'),
    path('qr/team/<str:team_code>.png', views.qr_team_image, name='qr_team_image'),
    path('dashboard/', views.dashboard, name='dashboard'),

    path('api/lookup/', views.api_lookup, name='api_lookup'),
    path('api/scan/', views.api_record_scan, name='api_scan'),
    path('api/leaderboard/', views.api_leaderboard, name='api_leaderboard'),
    path('api/team-view/', views.api_team_view, name='api_team_view'),
    path('api/live/', views.api_live_data, name='api_live'),

    path('api/session/start/', views.api_session_start, name='api_session_start'),
    path('api/session/end/', views.api_session_end, name='api_session_end'),
    path('api/session/reset/', views.api_session_reset, name='api_session_reset'),

    path('api/participant/add/', views.api_add_participant, name='api_add_participant'),
    path('api/participant/delete/', views.api_delete_participant, name='api_delete_participant'),
    path('api/logs/', views.api_scan_logs, name='api_scan_logs'),
    path('export/points/', views.export_points_excel, name='export_points'),
]
