from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site


class CustomUserAccountAdapter(DefaultAccountAdapter):
    def get_email_confirmation_url(self, request, emailconfirmation):
        """
        이메일 확인 페이지 URL을 생성합니다.
        """
        key = emailconfirmation.key
        return f"{settings.FRONTEND_URL}/confirm-email/{key}"
    
    def send_confirmation_mail(self, request, emailconfirmation, signup):
        current_site = get_current_site(request)
        activate_url = self.get_email_confirmation_url(
            request, emailconfirmation)

        ctx = {
            'user': emailconfirmation.email_address.user,
            'activate_url': activate_url,
            'current_site': current_site,
            'key': emailconfirmation.key,
            'email': emailconfirmation.email_address.email,
            'expiration_days': settings.ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS,
        }

        email_template = 'account/email/email_confirmation'

        self.send_mail(
            email_template, emailconfirmation.email_address.email, ctx)

    def get_email_confirmation_url(self, request, emailconfirmation):
        key = emailconfirmation.key
        return f"{settings.EMAIL_CONFIRMATION_REDIRECT_URL}/confirm-email/{key}"
