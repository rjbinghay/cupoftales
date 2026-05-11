# stories/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # Like: routes.MapRoute()
    path('about/', views.about, name='about'),  # ← Add
    path('story/<int:id>/', views.story_detail, name='story_detail'),
    path('category/<str:slug>/', views.category_filter, name='category_filter'),
    path('search/', views.search_stories, name='search'),
    path('categories/', views.category_list, name='category_list'),
    path('category/<str:slug>/', views.category_filter, name='category_filter'),
    path('tag/<str:slug>/', views.tag_detail, name='tag_detail'),

    # Story creation/editing - NEW!
    path('story/new/', views.story_create, name='story_create'),
    path('story/<int:id>/edit/', views.story_edit, name='story_edit'),
    path('story/<int:id>/delete/', views.story_delete, name='story_delete'),

]
