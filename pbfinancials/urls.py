__author__ = 'mattmccaskey'

from django.conf.urls import patterns, url
from django.views.generic import ListView, UpdateView
from django.contrib import admin
from pbfinancials.models import Resident, OrganizationYear, Block, Rotation, OfficeHours, Holiday, Faculty, \
    UnavailableType, ClinicAvailability, TeamType, ResidentType, ClinicScheduleType, BlockResidentTypeCount, \
    RotationSchedule, FacultyClinicHours, Account, Transaction
from pocketbook import settings
from services import UserOrganization, UserOrganizationYear
from pbfinancials.views import ResidentCreate, ResidentUpdate, ResidentDelete, OrganizationYearCreate, OrganizationYearUpdate, OrganizationYearDelete, \
    BlockDelete, BlockUpdate, BlockCreate, RotationCreate, RotationUpdate, RotationDelete, OfficeHoursCreate, OfficeHoursUpdate, OfficeHoursDelete, HolidayCreate, \
    HolidayUpdate, HolidayDelete, FacultyCreate, FacultyUpdate, FacultyDelete, UnavailableTypeCreate, UnavailableTypeUpdate, UnavailableTypeDelete, ClinicAvailabilityCreate, \
    ClinicAvailabilityUpdate, ClinicAvailabilityDelete, TeamTypeCreate, TeamTypeDelete, TeamTypeUpdate, ResidentTypeCreate, ResidentTypeUpdate, \
    ClinicScheduleTypeUpdate, ClinicScheduleTypeDelete, ClinicScheduleTypeCreate, BlockResidentTypeCountCreate, BlockResidentTypeCountUpdate, \
    RotationScheduleCreate, RotationScheduleUpdate, RotationScheduleDelete, AccountCreate, AccountDelete, AccountUpdate


admin.autodiscover()
uo = UserOrganization()
userOrg = UserOrganization.get(uo)
uoy = UserOrganizationYear()
userOrgYear = UserOrganizationYear.get(uoy)

urlpatterns = patterns('',
    #...
    url(r'^$', 'pbfinancials.views.home', name='home'),
    #(r'^static/(?P<path>.*)$', 'django.views.static.serve',
     #{'document_root': settings.STATIC_ROOT, 'show_indexes': True}),
    # residents
    #url(r'^login/$')
    url(r'^account/$',
        ListView.as_view(
            queryset=Account.objects.filter().order_by('accountName')[:20],
            context_object_name='account_list'),
        name='account-list'),
    url(r'^account/add/$', AccountCreate.as_view(), name='account-add'),
    url(r'^account/(?P<pk>\d+)/$', AccountUpdate.as_view(), name = 'account-update'),
    url(r'^account/(?P<pk>\d+)/delete/$', AccountDelete.as_view(), name = 'account-delete'),

    url(r'^resident/$',
        ListView.as_view(
            queryset=Resident.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear).order_by('lastName')[:20],
            context_object_name='resident_list'),
        name='resident-list'),
    url(r'^resident/add/$', ResidentCreate.as_view(), name='resident-add'),
    url(r'^resident/(?P<pk>\d+)/$', ResidentUpdate.as_view(), name = 'resident-update'),
    url(r'^resident/(?P<pk>\d+)/delete/$', ResidentDelete.as_view(), name = 'resident-delete'),
    url(r'^resident/custom/$','pbfinancials.views.residentcustom', name='residentcustom'),
    url(r'^resident/type/$',
        ListView.as_view(
            queryset=ResidentType.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear).order_by('shortDesc')[:20],
            context_object_name='residenttype_list'),
        name='residenttype_list'),
    url(r'^resident/type/add/$', ResidentTypeCreate.as_view(), name='residenttype-add'),
    url(r'^resident/type/(?P<pk>\d+)/$', ResidentTypeUpdate.as_view(), name = 'residenttype-update'),
    url(r'^resident/leave/$', 'pbfinancials.views.residentleavelist', name='residentleavelist'),
    url(r'^resident/leave/(?P<pk>\d+)/$', 'pbfinancials.views.residentleave', name='residentleave'),
    # org years
    url(r'^orgyear/$',
        ListView.as_view(
            queryset=OrganizationYear.objects.filter(organization__exact=userOrg).order_by('yearStartDate')[:20],
            context_object_name='organizationyear_list'),
        name='organizationyear-list'),
    url(r'^orgyear/add/$', OrganizationYearCreate.as_view(), name='organizationyear-add'),
    url(r'^orgyear/(?P<pk>\d+)/$', OrganizationYearUpdate.as_view(), name = 'organizationyear-update'),
    url(r'^orgyear/(?P<pk>\d+)/delete/$', OrganizationYearDelete.as_view(), name = 'organizationyear-delete'),
    #url(r'^orgyear/rotation/(?P<pk>\d+)/$', 'pbfinancials.views.orgyear_rotation', name="orgyear_rotation"),
    #url(r'^orgyear/schedule/$', 'pbfinancials.views.orgyearschedulesetup', name='orgyearschedulesetup'),
    #url(r'^orgyear/schedule/$',
    #    ListView.as_view(
    #        queryset=Block.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear).order_by('code')[:30],
    #        context_object_name='orgyearschedulesetup_list'),
    #        name='orgyearschedulesetup_list'),
    url(r'^orgyear/schedule/$', 'pbfinancials.views.blocktypelist', name='blocktypelist'),
    url(r'^orgyear/schedule/(?P<pk>\d+)/$', 'pbfinancials.views.blockandtype', name = 'blockandtype'),
    url(r'^orgyear/schedule/add', BlockCreate.as_view(), name='block-add'),
    #url(r'^orgyear/redirect/', 'pbfinancials.views.blocktyperedirect', name='blocktyperedirect'),
    url(r'^orgyear/schedule/save/', 'pbfinancials.views.orgyearschedsave', name='orgyearschedsave'),
    url(r'^orgyear/rotation/$', 'pbfinancials.views.rotationtypelist', name='rotationtypelist'),
    #url(r'^orgyear/rotation/$',
    #    ListView.as_view(
    #        queryset=Rotation.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear).order_by('code')[:55],
    #        context_object_name='orgyearrotationsetup_list'),
    #    name='orgyearrotationsetup_list'),
    #url(r'^orgyear/rotation/(?P<pk>\d+)/$', ReqUpdateView.as_view(), name = 'rotation-update'),
    url(r'^orgyear/rotation/(?P<pk>\d+)/$', 'pbfinancials.views.rotationandtype', name = 'rotationandtype'),
    url(r'^orgyear/rotation/add', RotationCreate.as_view(), name='rotation-add'),
    #url(r'^orgyear/session/', 'pbfinancials.views.orgyearsessionsetup', name='orgyearsessionsetup'),
    #url(r'^orgyear/team/', 'pbfinancials.views.orgyearteamsetup', name='orgyearteamsetup'),
    url(r'^orgyear/team/$',
        ListView.as_view(
            queryset=TeamType.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear).order_by('shortDesc')[:25],
            context_object_name='orgyearteamsetup_list'),
        name='orgyearteamsetup_list'),
    url(r'^orgyear/team/(?P<pk>\d+)/$', TeamTypeUpdate.as_view(), name = 'teamtype-update'),
    url(r'^orgyear/team/add', TeamTypeCreate.as_view(), name='teamtype-add'),
    url(r'^orgyear/session/$',
        ListView.as_view(
            queryset=OfficeHours.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear).order_by('sequenceNbr')[:20],
            context_object_name='orgyearsessionsetup_list'),
        name='orgyearsessionsetup_list'),
    url(r'^orgyear/session/(?P<pk>\d+)/$', OfficeHoursUpdate.as_view(), name = 'officehours-update'),
    url(r'^orgyear/session/add', OfficeHoursCreate.as_view(), name='officehours-add'),
    url(r'^orgyear/leave/$',
        ListView.as_view(
            queryset=UnavailableType.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear).order_by('shortDesc')[:20],
            context_object_name='orgyearleavesetup_list'),
        name='orgyearleavesetup_list'),
    url(r'^orgyear/leave/(?P<pk>\d+)/$', UnavailableTypeUpdate.as_view(), name = 'unavailabletype-update'),
    url(r'^orgyear/leave/add', UnavailableTypeCreate.as_view(), name='unavailabletype-add'),

    #url(r'^orgyear/leave/', 'pbfinancials.views.orgyearleavesetup', name='orgyearleavesetup'),
    # blocks
    url(r'^block/$',
        ListView.as_view(
            queryset=Block.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear).order_by('code')[:15],
            context_object_name='block_list'),
        name='block-list'),
    url(r'^block/add/$', BlockCreate.as_view(), name='block-add'),
    #url(r'^block/(?P<pk>\d+)/$', BlockUpdate.as_view(), name = 'block-update'),
    url(r'^block/(?P<pk>\d+)/delete/$', BlockDelete.as_view(), name = 'block-delete'),
    url(r'^block/custom/$','pbfinancials.views.blockcustom', name='blockcustom'),
    # rotations
    #url(r'^rotation/schedule/$',
    #    ListView.as_view(
    #        queryset=Block.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear).order_by('code')[:30],
    #        context_object_name='rotationschedule_list'),
    #    name='rotationschedule-list'),
    url(r'^rotation/schedule/$', 'pbfinancials.views.rotationlistmain', name='rotationlistmain'),
    url(r'^rotation/schedule/block/(?P<pk>\d+)/$', 'pbfinancials.views.rotationbyblock', name='rotationbyblock'),
    #url(r'^rotation/schedule/rotation/$', 'pbfinancials.views.rotationlistrotation', name='rotationlistrotation'),
    #url(r'^rotation/schedule/rotation/(?P<pk>\d+)/$', 'pbfinancials.views.rotationbyrotation', name='rotationbyrotation'),
    url(r'^rotation/schedule/resident/$', 'pbfinancials.views.rotationlistresident', name='rotationlistresident'),
    url(r'^rotation/schedule/resident/(?P<pk>\d+)/$', 'pbfinancials.views.rotationbyresident', name='rotationbyresident'),
    url(r'^rotation/schedule/add/$', RotationScheduleCreate.as_view(), name='rotationschedule-add'),
    url(r'^rotation/schedule/(?P<pk>\d+)/$', RotationScheduleUpdate.as_view(), name = 'rotationschedule-update'),
    url(r'^rotation/schedule/(?P<pk>\d+)/delete/$', RotationScheduleDelete.as_view(), name = 'rotationschedule-delete'),
    url(r'^rotation/custom/$','pbfinancials.views.rotationcustom', name='rotationcustom'),
    # office hours
    url(r'^officehours/$',
        ListView.as_view(
            queryset=OfficeHours.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear).order_by('weekday')[:25],
            context_object_name='officehours_list'),
        name='officehours-list'),
    url(r'^officehours/add/$', OfficeHoursCreate.as_view(), name='officehours-add'),
    url(r'^officehours/(?P<pk>\d+)/$', OfficeHoursUpdate.as_view(), name = 'officehours-update'),
    url(r'^officehours/(?P<pk>\d+)/delete/$', OfficeHoursDelete.as_view(), name = 'officehours-delete'),
    url(r'^officehours/custom/$','pbfinancials.views.officehourscustom', name='officehourscustom'),
    # holidays
    url(r'^holiday/$',
        ListView.as_view(
            queryset=Holiday.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear).order_by('description')[:20],
            context_object_name='holiday_list'),
        name='holiday-list'),
    url(r'^holiday/add/$', HolidayCreate.as_view(), name='holiday-add'),
    url(r'^holiday/(?P<pk>\d+)/$', HolidayUpdate.as_view(), name = 'holiday-update'),
    url(r'^holiday/(?P<pk>\d+)/delete/$', HolidayDelete.as_view(), name = 'holiday-delete'),
    url(r'^holiday/custom/$','pbfinancials.views.holidaycustom', name='holidaycustom'),
    # unavailable types
    url(r'^unavailabletype/$',
        ListView.as_view(
            queryset=UnavailableType.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear).order_by('description')[:20],
            context_object_name='unavailabletype_list'),
        name='leave-list'),
    url(r'^unavailabletype/add/$', UnavailableTypeCreate.as_view(), name='unavailabletype-add'),
    url(r'^unavailabletype/(?P<pk>\d+)/$', UnavailableTypeUpdate.as_view(), name = 'unavailabletype-update'),
    url(r'^unavailabletype/(?P<pk>\d+)/delete/$', UnavailableTypeDelete.as_view(), name = 'unavailabletype-delete'),
    url(r'^unavailabletype/custom/$','pbfinancials.views.unavailabletypecustom', name='unavailabletypecustom'),
    # faculty
    url(r'^faculty/$',
        ListView.as_view(
            queryset=Faculty.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear).order_by('lastName')[:30],
            context_object_name='faculty_list'),
        name='faculty-list'),
    url(r'^faculty/add/$', FacultyCreate.as_view(), name='faculty-add'),
    url(r'^faculty/(?P<pk>\d+)/$', FacultyUpdate.as_view(), name = 'faculty-update'),
    url(r'^faculty/(?P<pk>\d+)/delete/$', FacultyDelete.as_view(), name = 'faculty-delete'),
    url(r'^faculty/custom/$','pbfinancials.views.facultyroundinglist', name='facultyroundinglist'),
    url(r'^faculty/leave/$', 'pbfinancials.views.facultyleavelist', name='facultyleavelist'),
    url(r'^faculty/leave/(?P<pk>\d+)/$', 'pbfinancials.views.facultyleave', name='facultyleave'),
    url(r'^faculty/hours/$', 'pbfinancials.views.facultyclinichourslist', name='facultyclinichourslist'),
    url(r'^faculty/hours/(?P<pk>\d+)/$', 'pbfinancials.views.facultyclinichours', name='facultyclinichours'),

    # clinic availability
    #url(r'^clinicavailability/$',
    #    ListView.as_view(
    #        queryset=ClinicAvailability.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear).order_by('id')[:300],
    #        context_object_name='clinicavailability_list'),
    #    name='clinicavailability-list'),
    url(r'^clinicavailability/$', 'pbfinancials.views.clinicavailabilitylistrotation', name='clinicavailabilitylistrotation'),
    url(r'^clinicavailability/add/$', ClinicAvailabilityCreate.as_view(), name='clinicavailability-add'),
    #url(r'^clinicavailability/(?P<pk>\d+)/$', ClinicAvailabilityUpdate.as_view(), name = 'clinicavailability-update'),
    url(r'^clinicavailability/(?P<pk>\d+)/$', 'pbfinancials.views.clinicavailabilityrotation', name = 'clinicavailabilityrotation'),
    #url(r'^clinicavailability/(?P<pk>\d+)/delete/$', ClinicAvailabilityDelete.as_view(), name = 'clinicavailability-delete'),
    url(r'^clinicavailability/custom/$','pbfinancials.views.clinicavailabilitycustom', name='clinicavailabilitycustom'),
    # clinic
    url(r'^clinic/$',
        ListView.as_view(
            queryset=ClinicScheduleType.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear).order_by('scheduleType')[:10],
            context_object_name='clinicscheduletype_list'),
        name='clinicscheduletype_list'),
    url(r'^clinic/type/(?P<pk>\d+)/$', ClinicScheduleTypeUpdate.as_view(), name = 'clinicscheduletype-update'),
    url(r'^clinic/type/add/$', ClinicScheduleTypeCreate.as_view(), name = 'clinicscheduletype-add'),
    url(r'^clinic/type/(?P<pk>\d+)/delete/$', ClinicScheduleTypeDelete.as_view(), name='clinicscheduletype-delete'),
    #url(r'^clinic/counts/$',
    #    ListView.as_view(
    #        queryset=BlockResidentTypeCount.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear).order_by('blockRef')[:60],
    #        context_object_name='blockresidenttypecount_list'),
    #    name='blockresidenttypecount_list'),
    url(r'^clinic/counts/$', 'pbfinancials.views.cliniccountlist', name='cliniccountlist'),
    url(r'^clinic/counts/(?P<pk>\d+)/$', 'pbfinancials.views.cliniccount', name = 'cliniccount'),
    #url(r'^clinic/counts/(?P<pk>\d+)/$', BlockResidentTypeCountUpdate.as_view(), name = 'blockresidenttypecount-update'),
    url(r'^clinic/counts/add/$', BlockResidentTypeCountCreate.as_view(), name = 'blockresidenttypecount-add'),
    url(r'^clinic/holiday/$',
        ListView.as_view(
            queryset=Holiday.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear).order_by('sHolidayDate')[:15],
            context_object_name='holiday_list'),
        name='holiday_list'),
    url(r'^clinic/holiday/(?P<pk>\d+)/$', HolidayUpdate.as_view(), name = 'holiday-update'),
    url(r'^clinic/holiday/add/$', HolidayCreate.as_view(), name = 'holiday-add'),

    # process
    url(r'^generateschedule/$','pbfinancials.views.schedulebyblockweek', name='schedulebyblockweek'),
    url(r'^reviewschedule/$', 'pbfinancials.views.reviewschedulebyblockweek', name='reviewschedulebyblockweek'),
    # others/helpers
    (r'^my_admin/jsi18n', 'django.views.i18n.javascript_catalog'),
)
