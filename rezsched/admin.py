__author__ = 'mattmccaskey'

from rezsched.models import BaseOrganization
from rezsched.models import Resident
from rezsched.models import Rotation
from rezsched.models import TeamType
from rezsched.models import ResidentType

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