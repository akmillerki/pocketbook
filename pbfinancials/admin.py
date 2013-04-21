__author__ = 'mattmccaskey'

from pbfinancials.models import BaseOrganization
from pbfinancials.models import Resident
from pbfinancials.models import Rotation
from pbfinancials.models import TeamType
from pbfinancials.models import ResidentType

from django.contrib import admin

class BaseOrganizationAdmin(admin.ModelAdmin):
    save_as = True

class TeamTypeAdmin(admin.ModelAdmin):
    save_as = True

class FacResTypeAdmin(admin.ModelAdmin):
    save_as = True

class ResidentAdmin(admin.ModelAdmin):
    save_as = True

class RotationAdmin(admin.ModelAdmin):
    save_as = True

admin.site.register(BaseOrganization, BaseOrganizationAdmin)
admin.site.register(TeamType, TeamTypeAdmin)
admin.site.register(ResidentType, FacResTypeAdmin)
admin.site.register(Rotation, RotationAdmin)
admin.site.register(Resident, ResidentAdmin)