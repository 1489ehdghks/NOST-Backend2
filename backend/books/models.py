from django.conf import settings
from django.db import models


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Book(models.Model):
    """소설 책의 설정을 저장"""

    title = models.CharField(max_length=255)
    genre = models.CharField(max_length=255)
    theme = models.CharField(max_length=255)
    tone = models.CharField(max_length=255)
    setting = models.CharField(max_length=1000)
    characters = models.TextField()
    image = models.ImageField(upload_to='books', null=True, blank=True)

    full_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Foriegn Key
    user_id = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="books"
    )
    is_liked = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="book_likes",
        blank=True,
    )
    tags = models.ManyToManyField(Tag, related_name="books", blank=True)

    def total_likes(self):
        return self.is_liked.count()


class Rating(models.Model):
    RATING_CHOICES = [
        (1, "1"),
        (2, "2"),
        (3, "3"),
        (4, "4"),
        (5, "5"),
    ]
    book = models.ForeignKey(
        Book, related_name="ratings", on_delete=models.CASCADE)
    user_id = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="rating_user", on_delete=models.CASCADE
    )
    rating = models.PositiveIntegerField(choices=RATING_CHOICES, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["book", "user_id"], name="unique_book_user_rating"
            )
        ]


class Comment(models.Model):
    book = models.ForeignKey(
        Book, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField()
    user_id = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Chapter(models.Model):
    """각 소설의 내용(Chapter)을 저장"""

    chapter_num = models.PositiveIntegerField(editable=False)
    content = models.TextField()
    image = models.ImageField(upload_to='chapters',
                              null=True, blank=True)  # 이미지 필드 추가
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    book_id = models.ForeignKey(
        Book, on_delete=models.CASCADE, related_name="chapters")

    # 각 소설책마다 챕터는 1,2,3의 순서대로 저장하기 위해 save를 override
    def save(self, *args, **kwargs):
        if not self.id:
            last_index = (
                Chapter.objects.filter(book_id=self.book_id)
                .order_by("chapter_num")
                .last()
            )
            if last_index:
                self.chapter_num = last_index.chapter_num + 1
            else:
                self.chapter_num = 0
        super(Chapter, self).save(*args, **kwargs)

    def update_full_text(self):
        book = self.book_id
        chapters = Chapter.objects.filter(book_id=book).order_by('chapter_num')
        book.full_text = "\n\n".join(chapter.content for chapter in chapters)
        book.save()


class RecentSearch(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recentsearches")
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    searched_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} searched {self.book.title}"
