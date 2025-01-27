from django.urls import path, re_path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("signup/", views.signup_view, name="signup"),
    path("login/", auth_views.LoginView.as_view(template_name='registration/login.html'), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path('', views.board_view, name='home'),
    re_path(r'^board/(?P<center_x>-?\d+)/(?P<center_y>-?\d+)/$', views.board_view, name='board_view'),
    path('place_tile', views.place_tile, name='place_tile'),
    path('undo/', views.undo_tile, name='undo_tile'),
    path('clear/', views.clear_placed_tiles, name='clear_placed_tiles'),
    path('submit/', views.submit_tiles, name='submit_tiles'),
    re_path(r'^zoom/(?P<level>-?\d+)/$', views.zoom_view, name='zoom_view'),
    path("swap/", views.swap_tiles_view, name="swap_tiles_view"),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('update_tile/', views.update_tile, name='update_tile'),
]
