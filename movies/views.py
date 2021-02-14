from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView
from django.views.generic.base import View
from rest_framework import generics, permissions
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Movie, Category, Actor, Genre, Rating
from .forms import ReviewForm, RatingForm

# Create your views here.
from .serializers import *
from .service import get_client_ip, MovieFilter


class GenreYear:
    '''Жанры и года выхода фильма'''

    def get_genres(self):
        return Genre.objects.all()

    def get_years(self):
        return Movie.objects.filter(draft=False)


class MoviesView(GenreYear, ListView):
    '''Список фильмов'''

    model = Movie
    queryset = Movie.objects.filter(draft=False)
    paginate_by = 2


# class MovieListViewAPI(APIView):
#     '''Вывод списка фильмов'''
#
#     def get(self, request):
#         movies = Movie.objects.filter(draft=False).annotate(
#             rating_user=models.Count('ratings', filter=models.Q(ratings__ip=get_client_ip(request)))
#         ).annotate(
#             middle_star=models.Sum(models.F('ratings__star')) / models.Count(models.F('ratings'))
#         )
#         serializer = MovieListSerializer(movies, many=True)
#         return Response(serializer.data)

class MovieListViewAPI(ListAPIView):
    '''Вывод списка фильмов'''

    serializer_class = MovieListSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = MovieFilter
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        movies = Movie.objects.filter(draft=False).annotate(
            rating_user=models.Count('ratings', filter=models.Q(ratings__ip=get_client_ip(self.request)))
        ).annotate(
            middle_star=models.Sum(models.F('ratings__star')) / models.Count(models.F('ratings'))
        )
        return movies


class MovieDetailView(GenreYear, DetailView):
    '''Полное описание фильма'''

    model = Movie
    slug_field = 'url'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['star_form'] = RatingForm()
        context['form'] = ReviewForm()
        return context


# class MovieDetailViewAPI(APIView):
#     '''Полная информация по фильму'''
#
#     def get(self, request, pk):
#         queryset = Movie.objects.get(id=pk)
#         serializer = MovieDetailSerializer(queryset)
#         return Response(serializer.data)


class MovieDetailViewAPI(generics.RetrieveAPIView):
    '''Полная информация по фильму'''
    queryset = Movie.objects.filter(draft=False)
    serializer_class = MovieDetailSerializer


class AddReview(GenreYear, View):
    '''Отзывы'''

    def post(self, request, pk):
        form = ReviewForm(request.POST)
        movie = Movie.objects.get(id=pk)
        if form.is_valid():
            form = form.save(commit=False)
            if request.POST.get('parent', None):
                form.parent_id = int(request.POST.get('parent'))
            form.movie_id = pk
            form.save()
        return redirect(movie.get_absolute_url())


# class ReviewCreateViewAPI(APIView):
#     '''Добавление отзыва к фильму'''
#
#     def post(self, request):
#         review = ReviewCreateSerializer(data=request.data)
#         if review.is_valid():
#             review.save()
#         return Response(status=201)


class ReviewCreateViewAPI(generics.CreateAPIView):
    '''Добавление отзыва к фильму'''

    serializer_class = ReviewCreateSerializer


class ActorView(DetailView):
    '''Вывод информации об актере'''
    model = Actor
    template_name = 'movies/actor.html'
    slug_field = 'name'


class ActorListViewAPI(generics.ListAPIView):
    '''Вывод списка актеров'''
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer


class ActorDetailViewAPI(generics.RetrieveAPIView):
    '''Вывод актера или режиссера'''
    queryset = Actor.objects.all()
    serializer_class = ActorDetailSerializer


class FilterMoviesView(GenreYear, ListView):
    '''Филтр фильмов'''
    paginate_by = 2

    def get_queryset(self):
        queryset = Movie.objects.filter(Q(year__in=self.request.GET.getlist('year')) |
                                        Q(genres__in=self.request.GET.getlist('genre'))).distinct()
        return queryset

    def get_context_data(self, *args, object_list=None, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['year'] = ''.join([f'year={x}&' for x in self.request.GET.getlist('year')])
        context['genre'] = ''.join([f'genre={x}&' for x in self.request.GET.getlist('genre')])
        return context


class JsonFilterMoviesView(ListView):
    """Фильтр фильмов в json"""

    def get_queryset(self):
        queryset = Movie.objects.filter(
            Q(year__in=self.request.GET.getlist("year")) |
            Q(genres__in=self.request.GET.getlist("genre"))
        ).distinct().values("title", "tagline", "url", "poster")
        return queryset

    def get(self, request, *args, **kwargs):
        queryset = list(self.get_queryset())
        return JsonResponse({"movies": queryset}, safe=False)


class AddStarRating(View):
    '''Добавление рейтинга фильму'''

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def post(self, request):
        form = RatingForm(request.POST)
        if form.is_valid():
            Rating.objects.update_or_create(
                ip=self.get_client_ip(request),
                movie_id=int(request.POST.get('movie')),
                defaults={'star_id': int(request.POST.get('star'))}
            )
            return HttpResponse(status=201)
        else:
            return HttpResponse(status=400)


# class AddStarRatingViewAPI(APIView):
#     '''Добавление рейтинга к фильму'''
#
#     def post(self, request):
#         serializer = CreateRatingSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save(ip=get_client_ip(request))
#             return Response(status=201)
#         else:
#             return Response(status=400)


class AddStarRatingViewAPI(generics.CreateAPIView):
    '''Добавление рейтинга к фильму'''

    serializer_class = CreateRatingSerializer

    def perform_create(self, serializer):
        serializer.save(ip=get_client_ip(self.request))


class Search(ListView):
    '''Поиск фильмов'''
    paginate_by = 2

    def get_queryset(self):
        return Movie.objects.filter(title__icontains=self.request.GET.get('q'))

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['q'] = f'q={self.request.GET.get("q")}&'
        return context
