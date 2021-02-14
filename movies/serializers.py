from rest_framework import serializers
from .models import *


class ReviewCreateSerializer(serializers.ModelSerializer):
    '''Добавление отзыва'''

    class Meta:
        model = Reviews
        fields = '__all__'


class ActorDetailSerializer(serializers.ModelSerializer):
    '''Вывод полного описания актера или режиссера'''

    class Meta:
        model = Actor
        fields = '__all__'


class FilterReviewListSerializer(serializers.ListSerializer):
    '''Фильтр комментариев, только parents'''

    def to_representation(self, data):
        data = data.filter(parent=None)
        return super().to_representation((data))


class ActorSerializer(serializers.ModelSerializer):
    '''Вывод списка актеров и режиссеров'''

    class Meta:
        model = Actor
        fields = ('id', 'name', 'image')


class RecursiveSerializer(serializers.Serializer):
    def to_representation(self, instance):
        serializer = self.parent.parent.__class__(instance, context=self.context)
        return serializer.data


class ReviewSerializer(serializers.ModelSerializer):
    '''Вывод отзыва'''

    children = RecursiveSerializer(many=True)

    class Meta:
        list_serializer_class = FilterReviewListSerializer
        model = Reviews
        fields = ('name', 'text', 'parent', 'children')


class MovieDetailSerializer(serializers.ModelSerializer):
    '''Полный фильм'''
    category = serializers.SlugRelatedField(slug_field='name', read_only=True)
    directors = ActorSerializer(read_only=True, many=True)
    actors = ActorSerializer(read_only=True, many=True)
    genres = serializers.SlugRelatedField(slug_field='name', read_only=True, many=True)
    reviews = ReviewSerializer(many=True)

    class Meta:
        model = Movie
        exclude = ("draft",)


class MovieListSerializer(serializers.ModelSerializer):
    '''Список фильмов'''
    rating_user = serializers.BooleanField()
    middle_star = serializers.IntegerField()

    class Meta:
        model = Movie
        fields = ('id', 'title', 'tagline', 'category', 'rating_user', 'middle_star')


class CreateRatingSerializer(serializers.ModelSerializer):
    '''Добавление рейтинга пользователем'''

    class Meta:
        model = Rating
        fields = ('star', 'movie')

    def create(self, validated_data):
        rating, _ = Rating.objects.update_or_create(ip=validated_data.get('ip', None),
                                                 movie=validated_data.get('movie', None),
                                                 defaults={'star': validated_data.get('star')}
                                                 )
        return rating
