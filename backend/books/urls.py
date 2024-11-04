from django.urls import path
from . import views

urlpatterns = [
    path("", views.BookListAPIView.as_view()),
    path("<int:book_id>/", views.BookDetailAPIView.as_view()),
    path("<int:book_id>/del_prol/", views.DeletePrologueAPIView.as_view()),
    path("<int:book_id>/rating/", views.RatingAPIView.as_view()),
    path("<int:book_id>/comments/", views.CommentListAPIView.as_view()),
    path(
        "<int:book_id>/comments/<int:comment_id>/", views.CommentDetailAPIView.as_view()
    ),
    path("<int:book_id>/like/", views.BookLikeAPIView.as_view()),
    path("userlikedbooks/", views.UserLikedBooksAPIView.as_view()),
    path("userbooks/", views.UserBooksAPIView.as_view()),
    # 새로운 이미지 생성 엔드포인트 추가
    path("chapters/<int:chapter_id>/generate-image/",
         views.ChapterImageGenerationAPIView.as_view()),
    # 태그 검색
    path("search_by_tags/", views.TagSearchAPIView.as_view(), name="search_by_tags"),
    path("popular_tags/", views.PopularTagsAPIView.as_view(), name="popular-tags"),
    path("popular_books/", views.PopularBooksAPIView.as_view(), name="popular-books"),
    path("recent_searches/", views.RecentSearchesAPIView.as_view(),
         name="recent-searches"),
]
