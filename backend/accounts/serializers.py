from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import authenticate
from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import UserDetailsSerializer, LoginSerializer
from allauth.account.models import EmailAddress
from books.serializers import BookSerializer
from allauth.account.adapter import get_adapter
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class CustomUserDetailSerializer(UserDetailsSerializer):
    email = serializers.EmailField(read_only=True)
    # books = BookSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "nickname",
        )


class CustomLoginSerializer(LoginSerializer):
    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        # 1. 이메일과 비밀번호가 모두 입력되었는지 확인
        if not email or not password:
            raise serializers.ValidationError({
                "errors": {
                    "detail": "이메일과 비밀번호를 모두 입력해주세요."
                }
            })

        try:
            # 2. 사용자 인증
            user = authenticate(email=email, password=password)
            if not user:
                raise serializers.ValidationError({
                    "errors": {
                        "detail": "이메일 또는 비밀번호가 올바르지 않습니다."
                    }
                })

            # 3. 이메일 인증 확인
            email_address = EmailAddress.objects.filter(
                user=user, verified=True
            ).exists()
            if not email_address:
                raise serializers.ValidationError({
                    "errors": {
                        "detail": "이메일 인증이 필요합니다. 이메일을 확인해주세요."
                    }
                })

            # 4. 계정 활성화 상태 확인
            if not user.is_active:
                raise serializers.ValidationError({
                    "errors": {
                        "detail": "비활성화된 계정입니다. 관리자에게 문의하세요."
                    }
                })

            attrs["user"] = user
            return attrs

        except User.DoesNotExist:
            raise serializers.ValidationError({
                "errors": {
                    "detail": "등록되지 않은 이메일입니다."
                }
            })

    class Meta:
        fields = (
            "email",
            "password",
        )


class CustomRegisterSerializer(RegisterSerializer):
    nickname = serializers.CharField(required=True)

    def validate_password1(self, password):
        """
        비밀번호 검증:
        다음 조건 중 3가지 이상 충족:
        - 8자 이상
        - 소문자 포함
        - 대문자 포함
        - 숫자 포함
        - 특수문자 포함
        """
        # 모든 조건 체크
        conditions = {
            'length': len(password) >= 8,          # 8자 이상
            'lowercase': any(c.islower() for c in password),  # 소문자 포함
            'uppercase': any(c.isupper() for c in password),  # 대문자 포함
            'number': any(c.isdigit() for c in password),     # 숫자 포함
            # 특수문자 포함
            'special': any(c in '!@#$%^&*(),.?":{}|<>' for c in password)
        }

        # 충족된 조건 수 계산
        satisfied_conditions = sum(conditions.values())

        if satisfied_conditions < 3:
            failed_conditions = []
            if not conditions['length']:
                failed_conditions.append('8자 이상')
            if not conditions['lowercase']:
                failed_conditions.append('소문자 포함')
            if not conditions['uppercase']:
                failed_conditions.append('대문자 포함')
            if not conditions['number']:
                failed_conditions.append('숫자 포함')
            if not conditions['special']:
                failed_conditions.append('특수문자 포함')

            raise serializers.ValidationError(
                f'다음 조건 중 3가지 이상을 충족해야 합니다:\n'
                f'현재 충족되지 않은 조건: {", ".join(failed_conditions)}'
            )

        return password

    def validate(self, data):
        # 기존 유효성 검사
        errors = {}

        # 이메일 검증
        try:
            email = get_adapter().clean_email(data.get('email'))
            if email and get_user_model().objects.filter(email=email).exists():
                errors['email'] = '이미 등록된 이메일 주소입니다.'
        except ValidationError as e:
            errors['email'] = str(e)

        # 닉네임 검증
        nickname = data.get('nickname', '')
        if not nickname:
            errors['nickname'] = '닉네임을 입력해주세요.'
        elif len(nickname) < 2:
            errors['nickname'] = '닉네임은 2자 이상이어야 합니다.'
        elif get_user_model().objects.filter(nickname=nickname).exists():
            errors['nickname'] = '이미 사용 중인 닉네임입니다.'

        # 비밀번호 일치 검증
        password1 = data.get('password1', '')
        password2 = data.get('password2', '')

        if password1 != password2:
            errors['password2'] = '비밀번호가 일치하지 않습니다.'

        if errors:
            raise serializers.ValidationError(errors)

        return super().validate(data)

    def save(self, request):
        try:
            user = super().save(request)
            user.nickname = self.validated_data.get('nickname')
            user.save()
            return user
        except Exception as e:
            raise serializers.ValidationError({
                "detail": f"회원가입 처리 중 오류가 발생했습니다: {str(e)}"
            })

    class Meta:
        model = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):
    books = BookSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "nickname",
            "books",
        )
