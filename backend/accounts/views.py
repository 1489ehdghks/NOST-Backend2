from django.http import HttpResponseRedirect
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from allauth.account.models import EmailConfirmation, EmailConfirmationHMAC
from .serializers import ProfileSerializer
from allauth.account.models import EmailAddress
from allauth.account.utils import send_email_confirmation
from django.contrib.auth import get_user_model

User = get_user_model()


class ConfirmEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, *args, **kwargs):
        self.object = confirmation = self.get_object()
        confirmation.confirm(self.request)
        return HttpResponseRedirect(self.get_main_url())

    def get_object(self, queryset=None):
        key = self.kwargs["key"]
        email_confirmation = EmailConfirmationHMAC.from_key(key)
        if not email_confirmation:
            if queryset is None:
                queryset = self.get_queryset()
            try:
                email_confirmation = queryset.get(key=key.lower())
            except EmailConfirmation.DoesNotExist:
                return HttpResponseRedirect(self.get_main_url())
        return email_confirmation

    def get_queryset(self):
        qs = EmailConfirmation.objects.all_valid()
        qs = qs.select_related("email_address__user")
        return qs

    def get_main_url(self):
        return "https://novel-stella.com/"


class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if not user:
            return Response(
                {"message": "해당 유저는 존재하지 않습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = ProfileSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        user = request.user
        serializer = ProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        user = self.request.user
        password = request.data.get("password")
        refresh_token = request.data.get("refresh_token")

        if not password:
            return Response(
                {"message": "비밀번호가 제공되지 않았습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.check_password(password):
            return Response(
                {"message": "비밀번호가 일치하지 않습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception as e:
            return Response(
                {"message": "토큰 블랙리스트 처리 중 오류 발생"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # 사용자 비활성화
            # user.is_active=False
            # user.save()
            user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class ResendEmailVerificationView(APIView):
    def post(self, request):
        email = request.data.get('email')

        if not email:
            return Response(
                {'error': '이메일 주소를 입력해주세요.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
            email_address = EmailAddress.objects.get(user=user, email=email)

            # 이미 인증된 이메일인지 확인
            if email_address.verified:
                return Response(
                    {'error': '이미 인증된 이메일입니다.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 새로운 인증 이메일 발송
            send_email_confirmation(request, user, signup=False)

            return Response(
                {'message': '인증 이메일이 발송되었습니다. 이메일을 확인해주세요.'},
                status=status.HTTP_200_OK
            )

        except User.DoesNotExist:
            return Response(
                {'error': '등록되지 않은 이메일입니다.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except EmailAddress.DoesNotExist:
            return Response(
                {'error': '이메일 주소를 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'이메일 전송 중 오류가 발생했습니다: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ConfirmEmailView(APIView):
    def get(self, *args, **kwargs):
        key = kwargs['key']
        try:
            confirmation = EmailConfirmationHMAC.from_key(key)
            if not confirmation:
                confirmation = EmailConfirmation.objects.get(key=key.lower())

            confirmation.confirm(self.request)

            # 프론트엔드의 성공 페이지로 리다이렉트
            return redirect(f"{settings.FRONTEND_URL}/email-confirmed")

        except (EmailConfirmation.DoesNotExist, ValueError):
            # 프론트엔드의 에러 페이지로 리다이렉트
            return redirect(f"{settings.FRONTEND_URL}/email-confirmation-error")
