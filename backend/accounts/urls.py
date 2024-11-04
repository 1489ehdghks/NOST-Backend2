from django.urls import path, include, re_path
from dj_rest_auth.registration.views import VerifyEmailView
from .views import ProfileAPIView, ConfirmEmailView, ResendEmailVerificationView

urlpatterns = [
    # 기본 인증 URLs (로그인, 로그아웃 등)
    path("", include("dj_rest_auth.urls")),
    path("registration/", include("dj_rest_auth.registration.urls")),

    # 커스텀 URL 패턴들
    path('profile/', ProfileAPIView.as_view()),
    # 이메일 확인 URLs
    re_path(
        r"^account-confirm-email/$",
        VerifyEmailView.as_view(),
        name="account_email_verification_sent",
    ),
    re_path(
        r"^account-confirm-email/(?P<key>[-:\w]+)/$",
        ConfirmEmailView.as_view(),
        name="account_confirm_email",
    ),
    # 이메일 다시보내기
    path(
        'verify-email/',
        VerifyEmailView.as_view(),
        name='verify-email'
    ),
    path(
        'confirm-email/<str:key>/',
        ConfirmEmailView.as_view(),
        name='account_confirm_email'
    ),

]
