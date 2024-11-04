import logging
from django.shortcuts import get_object_or_404, render
from openai import OpenAI
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework import status
from .models import Book, Comment, Rating, Chapter, Tag
from .serializers import (
    BookSerializer,
    BookLikeSerializer,
    RatingSerializer,
    CommentSerializer,
    ChapterSerializer,
    ElementsSerializer,
)
from django.core import serializers
from django.core.files.base import ContentFile
from .generators.summary_generator import generate_summary
from .generators.prologue_generator import generate_prologue
from .generators.elements_generator import generate_elements
from .generators.ai_translation import translate_text
from config import secret
from .serializers import BookSerializer, TagSerializer
from django.db.models import Count
import datetime
from django.utils import timezone


def translate_text_with_retries(content, language, max_retries=3):
    attempt = 0
    while attempt < max_retries:
        try:
            return translate_text(content, language)
        except Exception as e:
            logging.error(f"Translation attempt {attempt + 1} failed: {e}")
            attempt += 1
    logging.error(f"Failed to translate after {
                  max_retries} attempts: {content}")
    return content  # 번역 실패 시 원본 텍스트 반환


class BookListAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        try:
            books = Book.objects.prefetch_related(
                'tags').order_by("-created_at")
            serializer = BookSerializer(
                books, many=True, context={"request": request})
            return Response(serializer.data)
        except Exception as e:
            logging.error(f"Error fetching books: {e}")
            return Response({"error": "Failed to retrieve books."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        user_prompt = request.data.get("prompt")
        language = request.data.get("language")
        tags = request.data.get("tags", [])

        if not user_prompt:
            return Response({"error": "Missing prompt"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 콘텐츠 생성
            content = generate_elements(
                user_prompt, language)  # AI로 elements 생성
            translated_content = translate_text(content, language)
            content["user_id"] = request.user.pk
            content["tags"] = tags  # 태그 데이터를 content에 추가

            serializer = BookSerializer(data=content)
            if serializer.is_valid(raise_exception=True):
                book = serializer.save()

            return Response(
                data={
                    "book_id": book.id,
                    "content": translated_content,
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            logging.error(f"Error creating synopsis: {e}")
            return Response({"error": "Failed to create synopsis."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChapterImageGenerationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, chapter_id):
        chapter = get_object_or_404(Chapter, id=chapter_id)
        title = request.data.get("title", chapter.book_id.title)
        tone = request.data.get("tone", chapter.book_id.tone)
        setting = request.data.get("setting", chapter.book_id.setting)

        if not title or not tone or not setting:
            return Response(
                {"error": "Missing parameters"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 이미지 생성
            client = OpenAI(api_key=secret.OPENAI_API_KEY)
            response = client.images.generate(
                model="dall-e-3",
                prompt=f"{title}, {tone}, {setting}",
                size="1024x1024",
                quality="standard",
                n=1,
            )
            res = requests.get(response.data[0].url)
            image_content = ContentFile(res.content, name=f"{title}_chapter_{
                                        chapter.chapter_num}.png")

            # 챕터에 이미지 저장
            chapter.image.save(image_content.name, image_content)
            chapter.save()

            return Response(
                {"image_url": request.build_absolute_uri(
                    chapter.image.url) if request else chapter.image.url},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logging.error(f"Error generating chapter image: {e}")
            return Response({"error": "Failed to generate image."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BookDetailAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)
        ratings = Rating.objects.filter(book=book)

        chapters = Chapter.objects.filter(
            book_id=book_id).order_by('chapter_num')
        chapter_serializer = ChapterSerializer(chapters, many=True)

        book_serializer = BookSerializer(book)

        response_data = book_serializer.data
        response_data["chapters"] = chapter_serializer.data
        return Response(response_data, status=200)

    def post(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)
        if book.user_id != request.user:
            return Response(
                {"error": "You don't have permission."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        language = request.data.get("language", "EN-US")
        selected_recommendation = request.data.get(
            "selected_recommendation", None)

        chapter = Chapter.objects.filter(book_id=book_id).last()
        elements = ElementsSerializer(book).data

        if not chapter:
            chapter_num = 0
            result = generate_prologue(elements)
            content = result["prologue"]
            content = translate_text(content, language)

        else:
            if selected_recommendation:
                summary = f"{selected_recommendation['Title']}: {
                    selected_recommendation['Description']}"
            else:
                summary = request.data.get("summary")
                if not summary:
                    return Response(
                        {"error": "Missing summary prompt"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            chapter_num = chapter.chapter_num + 1
            prologue = Chapter.objects.filter(
                book_id=book_id, chapter_num=0).first()
            result = generate_summary(
                chapter_num,
                summary,
                elements,
                prologue.content if prologue else "",
                language,
            )
            content = result["final_summary"]

        serializer = ChapterSerializer(
            data={"content": content, "book_id": book_id,
                  "chapter_num": chapter_num}
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            response_data = {
                "book_id": book_id,
                "translated_content": content,
                "chapter_num": chapter_num,
                "recommendations": result.get("recommendations", []),
            }
            return Response(data=response_data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # 글 수정

    def put(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)
        if book.user_id != request.user:
            return Response(
                {"error": "You don't have permission."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = BookSerializer(book, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(status=401)

    # 글 삭제
    def delete(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)
        if book.user_id != request.user:
            return Response(
                {"error": "You don't have permission."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        book.delete()
        return Response("No Content", status=204)


class DeletePrologueAPIView(APIView):
    def delete(self, request, book_id):
        prologue = Chapter.objects.filter(chapter_num=0, book_id=book_id)
        prologue.delete()
        return Response("Prologue deleted successfully", status=204)


class BookLikeAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)
        serializer = BookLikeSerializer(book)
        is_liked = book.is_liked.filter(id=request.user.id).exists()
        return Response(
            {
                "total_likes": book.total_likes(),
                "book": serializer.data,
                "like_bool": is_liked,
            },
            status=200,
        )

    def post(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)
        if book.is_liked.filter(id=request.user.id).exists():
            book.is_liked.remove(request.user)
            like_bool = False
        else:
            book.is_liked.add(request.user)
            like_bool = True
        serializer = BookLikeSerializer(book)
        return Response(
            {
                "total_likes": book.total_likes(),
                "book": serializer.data,
                "like_bool": like_bool,
            },
            status=200,
        )


class UserLikedBooksAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        user = request.user
        book_likes = (
            user.book_likes.all()
        )  # 역참조를 이용해 사용자가 좋아요한 책 리스트를 가져옴
        serializer = BookSerializer(book_likes, many=True)
        return Response(serializer.data, status=200)


class UserBooksAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        user = request.user
        user_books = (
            user.books.all()
        )  # 역참조를 이용해 사용자가 작성한 책 리스트를 가져옴
        serializer = BookSerializer(user_books, many=True)
        return Response(serializer.data, status=200)


class RatingAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)
        user_rating = Rating.objects.filter(
            book=book, user_id=request.user.id).first()
        if user_rating:
            serializer = RatingSerializer(user_rating)
            return Response(serializer.data, status=200)
        return Response("User has not rated this book yet.", status=404)

    def post(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)
        rating = request.data.get("rating")

        if rating not in [1, 2, 3, 4, 5]:
            return Response("Rating must be between 1 and 5", status=400)

        existing_rating = Rating.objects.filter(
            book=book, user_id=request.user
        ).exists()
        if existing_rating:
            return Response("You have already rated this book.", status=400)

        serializer = RatingSerializer(data={"rating": rating})
        if serializer.is_valid(raise_exception=True):
            serializer.save(user_id=request.user, book=book)
            return Response(serializer.data, status=200)
        return Response(status=400)


class CommentListAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)
        comments = book.comments.all()
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

    def post(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save(user_id=request.user, book=book)
            return Response(serializer.data, status=201)


class CommentDetailAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def put(self, request, book_id, comment_id):
        comment = get_object_or_404(Comment, id=comment_id)
        if comment.user_id != request.user:
            return Response(
                {"error": "You don't have permission."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        serializer = CommentSerializer(
            comment, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data)

    def delete(self, request, book_id, comment_id):
        comment = get_object_or_404(Comment, id=comment_id)
        if comment.user_id != request.user:
            return Response(
                {"error": "You don't have permission."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        comment.delete()
        return Response("NO comment", status=204)


class TagSearchAPIView(APIView):
    def get(self, request):
        tag = request.query_params.get("tag", None)
        if tag:
            books = Book.objects.filter(tags__name__icontains=tag)
            serializer = BookSerializer(books, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"error": "Tag not provided"}, status=status.HTTP_400_BAD_REQUEST)


class PopularTagsAPIView(APIView):
    def get(self, request):
        tags = Tag.objects.annotate(num_books=Count(
            'books')).order_by('-num_books')[:10]
        serializer = TagSerializer(tags, many=True)
        return Response(serializer.data)


class PopularBooksAPIView(APIView):
    def get(self, request):
        one_week_ago = timezone.now() - datetime.timedelta(days=7)
        books = Book.objects.filter(created_at__gte=one_week_ago).annotate(
            num_likes=Count('is_liked')).order_by('-num_likes')[:10]
        serializer = BookSerializer(books, many=True)
        return Response(serializer.data)


class RecentSearchesAPIView(APIView):
    def get(self, request):
        user = request.user
        # Assuming you have a model to store recent searches
        recent_books = user.recentsearches.order_by('-searched_at')[:10]
        serializer = BookSerializer(recent_books, many=True)
        return Response(serializer.data)
