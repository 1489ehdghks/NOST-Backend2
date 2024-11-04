from django.db.models import Avg
from rest_framework import serializers
from .models import Book, Chapter, Comment, Rating, Tag


class ChapterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapter
        fields = "__all__"


class BookSerializer(serializers.ModelSerializer):
    average_rating = serializers.SerializerMethodField()
    user_nickname = serializers.SerializerMethodField()
    chapters = ChapterSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()
    tags = serializers.StringRelatedField(many=True)

    class Meta:
        model = Book
        fields = [
            "id", "title", "genre", "theme", "tone", "setting", "characters",
            "created_at", "updated_at", "user_id", "image", "average_rating",
            "user_nickname", "chapters", "image_url", "tags"
        ]

    def create(self, validated_data):
        tags_data = validated_data.pop('tags', [])
        book = Book.objects.create(**validated_data)
        for tag_name in tags_data:
            tag, created = Tag.objects.get_or_create(name=tag_name)
            book.tags.add(tag)
        return book

    def get_average_rating(self, book):
        avg_rating = Rating.objects.filter(book=book).aggregate(
            avg_rating=Avg("rating"))["avg_rating"]
        return round(avg_rating, 1) if avg_rating is not None else None

    def get_user_nickname(self, book):
        return book.user_id.nickname

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None


class BookLikeSerializer(BookSerializer):
    total_likes = serializers.IntegerField(read_only=True)


class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = "__all__"
        read_only_fields = ("book", "user_id")


class ElementsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = (
            "title",
            "genre",
            "theme",
            "tone",
            "setting",
            "characters",
        )


class CommentSerializer(serializers.ModelSerializer):
    user_nickname = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = "__all__"
        read_only_fields = ("book", "user_id")

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret.pop("article", None)  # 'article' 필드가 없다면 None을 반환
        return ret

    def get_user_nickname(self, comment):
        return comment.user_id.nickname


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']
