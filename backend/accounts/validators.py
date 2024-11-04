from django.core.exceptions import ValidationError


class CustomPasswordValidator:
    def validate(self, password, user=None):
        """
        비밀번호 검증:
        1. 8자 이상 (필수)
        2. 소문자, 대문자, 숫자, 특수문자 중 3가지 이상 포함
        """

        conditions = {
            'length': len(password) >= 8,  # 길이 조건
            'lowercase': any(c.islower() for c in password),  # 소문자 포함
            'uppercase': any(c.isupper() for c in password),  # 대문자 포함
            'number': any(c.isdigit() for c in password),     # 숫자 포함
            # 특수문자 포함
            'special': any(c in '!@#$%^&*(),.?":{}|<>' for c in password)
        }

        # 8자 이상 필수 조건
        if not conditions['length']:
            raise ValidationError(
                '비밀번호는 최소 8자 이상이어야 합니다.',
                code='password_too_short',
            )

        # 나머지 조건 중 3가지 이상 충족해야 함
        satisfied_conditions = sum([
            conditions['lowercase'],
            conditions['uppercase'],
            conditions['number'],
            conditions['special']
        ])

        if satisfied_conditions < 3:
            raise ValidationError(
                '비밀번호는 소문자, 대문자, 숫자, 특수문자(!@#$%^&*(),.?":{}|<>) 중 '
                '3가지 이상을 포함해야 합니다.',
                code='password_too_simple',
            )

    def get_help_text(self):
        return (
            '비밀번호는 8자 이상이어야 하며, '
            '소문자, 대문자, 숫자, 특수문자(!@#$%^&*(),.?":{}|<>) 중 '
            '3가지 이상을 포함해야 합니다.'
        )
