from django.urls import path, include
from . import views

urlpatterns = [
    path('movies/', views.MovieListViewAPI.as_view(), name='movie_list_API'),
    path('movie/<int:pk>/', views.MovieDetailViewAPI.as_view(), name='movie_detail_API'),
    path('review/', views.ReviewCreateViewAPI.as_view()),
    path('rating/', views.AddStarRatingViewAPI.as_view()),
    path('actors/', views.ActorListViewAPI.as_view()),
    path('actors/<int:pk>/', views.ActorDetailViewAPI.as_view()),

]
