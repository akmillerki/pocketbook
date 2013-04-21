from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext as _
from userena.models import UserenaBaseProfile

# Create your models here.
class LoginProfile(UserenaBaseProfile):
    user = models.OneToOneField(User,
        unique=True,
        verbose_name=_('User'),
        related_name='user_login')
    mothers_maiden_name = models.CharField(_('Mother''s Maiden Name'),
        max_length=30)