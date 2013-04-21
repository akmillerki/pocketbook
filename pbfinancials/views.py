# Create your views here.
from django.forms.models import modelformset_factory, inlineformset_factory, modelform_factory
from django.http import HttpResponseRedirect
from django.shortcuts import render, render_to_response
from django.utils import timezone
from datetime import datetime
from datetime import timedelta
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, BaseDetailView
from django.core.urlresolvers import reverse_lazy, reverse
from models import Resident, BaseOrganization, OrganizationYear, Block, Rotation, OfficeHours, Holiday, Faculty, \
    UnavailableType, ClinicAvailability, DTO, TeamType, ResidentType, ClinicScheduleType, BlockResidentTypeCount, \
    ResidentElective, RotationSchedule, StaffUnavailable, FacultyUnavailable, BaseRotations, RotationResidentType, \
    BlockWeek, ClinicAvailabilityCount, BlockResidentType, ClinicSchedule, ClinicAvailabilityBlockWeek, \
    AvailableAssignmentWork, FacultyClinicHours, Account, Transaction
from forms import ResidentForm, OrgYearForm, BlockForm, OrgYearRotationForm, RotationForm, OfficeHoursForm, HolidayForm, FacultyForm, UnavailableTypeForm, \
    ClinicAvailabilityForm, PartialBlockForm, BaseBlockFormSet, TeamTypeForm, ResidentTypeForm, ClinicScheduleTypeForm,\
    BlockResidentTypeCountForm, RotationScheduleForm, ResidentDisplayForm, ResidentElectiveForm, RotationScheduleRotationForm,\
    RotationScheduleResidentForm, ClinicAvailabilityCalendarForm, ResidentLeaveForm, FacultyLeaveForm, ClinicCountForm, \
    RotationResidentTypeForm, BlockWeekForm, ClinicAvailabilityCountCalendarForm, BlockResidentTypeForm, \
    ClinicAvailabilityBlockWeekForm, FacultyClinicHoursCalendarForm, AccountForm
from django.core.context_processors import csrf
from django.shortcuts import render_to_response
from utils import ClinicScheduleBuilder
from services import UserOrganization, UserOrganizationYear, dtoFactory, updateFactory
from django.forms import CheckboxInput, HiddenInput, TextInput
from django.template import RequestContext
from django.db.models import Max
from django.views.generic.detail import SingleObjectMixin
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator



@login_required()
def home(request):
    """

    """
    #su = ScheduleUtility()
    test = "test"
    context = {'test': test}
    return render(request, 'pbfinancials/home.html', context)

@login_required()
def profile(request):
    """

    """
    return render(request, 'pbfinancials/home.html', context)

@login_required()
def rotationbyblock(request, pk):
    #BlockFormSet = modelformset_factory(Block, extra=0, form=ResidentDisplayForm)
    rbId = pk
    RotationFormSet = inlineformset_factory(Block, RotationSchedule, extra=1, form=RotationScheduleForm)
    RotationBlock = Block.objects.get(pk=rbId)
    dispContext = RotationBlock.code
    if request.method == "POST":
        if 'add_line' in request.POST:
            formset = RotationFormSet(request.POST, request.FILES, instance=RotationBlock, prefix='rotations', initial=[{'blockRef':rbId}])
            count = formset.total_form_count()
            if formset.is_valid:
                formset.save()
                return render_to_response("pbfinancials/rotation_schedule_block.html", {
                    "formset": formset, "dispContext": dispContext, "count": count}, context_instance=RequestContext(request))

            else:
                # change to error response
                dispSaveError = 'One or more required fields are missing, please re-enter your data or select cancel.'
                return render_to_response("pbfinancials/rotation_schedule_block.html", {
                    "formset": formset, "dispContext": dispContext, "dispSaveError": dispSaveError}, context_instance=RequestContext(request)
                )

        elif 'cancel' in request.POST:
            #resformset = ResidentFormSet(request.POST, request.FILES, prefix='resident', queryset=Resident.objects.filter(id=1))
            uo = UserOrganization()
            userOrg = UserOrganization.get(uo)
            uoy = UserOrganizationYear()
            userOrgYear = UserOrganizationYear.get(uoy)
            blockset = Block.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear)
            return render_to_response("pbfinancials/rotationschedule_list.html", {
                "blockset": blockset}, context_instance=RequestContext(request)
            )

        elif 'submit' in request.POST:
            formset = RotationFormSet(request.POST, request.FILES, instance=RotationBlock, prefix='rotations', initial=[{'blockRef':rbId}])
            if formset.is_valid():
                formset.save()
                uo = UserOrganization()
                userOrg = UserOrganization.get(uo)
                uoy = UserOrganizationYear()
                userOrgYear = UserOrganizationYear.get(uoy)
                blockset = Block.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear)
                return render_to_response("pbfinancials/rotationschedule_list.html", {
                    "blockset": blockset}, context_instance=RequestContext(request)
                )
            else:
                # change to error response
                dispSaveError = 'One or more required fields are missing, please re-enter your data or select cancel.'
                return render_to_response("pbfinancials/rotation_schedule_block.html", {
                    "formset": formset, "dispContext": dispContext, "dispSaveError": dispSaveError}, context_instance=RequestContext(request)
                )


    else:
        formset = RotationFormSet(instance=RotationBlock, prefix='rotations', initial=[{'blockRef':rbId}])
        #resformset = ResidentFormSet(prefix='resident', queryset=Resident.objects.filter(id=1))
        count = formset.total_form_count()
        return render_to_response("pbfinancials/rotation_schedule_block.html", {
            "formset": formset, "dispContext": dispContext, "count": count}, context_instance=RequestContext(request)
        )

@login_required()
def rotationlistmain(request):
    uo = UserOrganization()
    userOrg = UserOrganization.get(uo)
    uoy = UserOrganizationYear()
    userOrgYear = UserOrganizationYear.get(uoy)
    blockset = Block.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear)
    return render_to_response("pbfinancials/rotationschedule_list.html", {
        "blockset": blockset}, context_instance=RequestContext(request)
    )

@login_required()
def rotationlistrotation(request):
    uo = UserOrganization()
    userOrg = UserOrganization.get(uo)
    uoy = UserOrganizationYear()
    userOrgYear = UserOrganizationYear.get(uoy)
    rotationset = Rotation.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear)
    return render_to_response("pbfinancials/rotationschedule_rotation_list.html", {
        "rotationset": rotationset}, context_instance=RequestContext(request)
    )

@login_required()
def clinicavailabilitylistrotation(request):
    uo = UserOrganization()
    userOrg = UserOrganization.get(uo)
    uoy = UserOrganizationYear()
    userOrgYear = UserOrganizationYear.get(uoy)
    rotationset = Rotation.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear)
    return render_to_response("pbfinancials/clinicavailability_rotation_list.html", {
        "rotationset": rotationset}, context_instance=RequestContext(request)
    )

@login_required()
def cliniccountlist(request):
    uo = UserOrganization()
    userOrg = UserOrganization.get(uo)
    uoy = UserOrganizationYear()
    userOrgYear = UserOrganizationYear.get(uoy)
    blockset = Block.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear)
    return render_to_response("pbfinancials/clinic_count_list.html", {
        "blockset": blockset}, context_instance=RequestContext(request)
    )

@login_required()
def rotationlistresident(request):
    uo = UserOrganization()
    userOrg = UserOrganization.get(uo)
    uoy = UserOrganizationYear()
    userOrgYear = UserOrganizationYear.get(uoy)
    residentset = Resident.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear)
    return render_to_response("pbfinancials/rotationschedule_resident_list.html", {
        "residentset": residentset}, context_instance=RequestContext(request)
    )

@login_required()
def facultyroundinglist(request):
    uo = UserOrganization()
    userOrg = UserOrganization.get(uo)
    uoy = UserOrganizationYear()
    userOrgYear = UserOrganizationYear.get(uoy)
    facultyrounding_list = Faculty.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear)
    return render_to_response("pbfinancials/facultyrounding_list.html", {
        "facultyrounding_list": facultyrounding_list}, context_instance=RequestContext(request)
    )

@login_required()
def residentcustom(request):
    """

    """
    ResidentFormSet = modelformset_factory(Resident, extra=0, form=ResidentDisplayForm)
    ElectiveFormSet = inlineformset_factory(Resident, ResidentElective, extra=0, form=ResidentElectiveForm)
    ElectiveResident = Resident.objects.get(pk=1)
    if request.method == "POST":
        resformset = ResidentFormSet(request.POST, request.FILES, prefix='resident', queryset=Resident.objects.filter(id=1))
        formset = ElectiveFormSet(request.POST, request.FILES, instance=ElectiveResident, prefix='electives')
        if formset.is_valid():
            formset.save()
            # Do something. Should generally end with a redirect. For example:
            #return HttpResponseRedirect(Resident.get_absolute_url())
            return render_to_response("pbfinancials/resident_custom.html", {
                "formset": formset, "resformset": resformset}, context_instance=RequestContext(request))
        else:
            return render_to_response("pbfinancials/resident_custom.html", {
                "formset": formset, "resformset": resformset}, context_instance=RequestContext(request))
    else:
        formset = ElectiveFormSet(instance=ElectiveResident, prefix='electives')
        resformset = ResidentFormSet(prefix='resident', queryset=Resident.objects.filter(id=1))
        return render_to_response("pbfinancials/resident_custom.html", {
        "formset": formset, "resformset": resformset}, context_instance=RequestContext(request)
        )

@login_required()
def facultyleavelist(request):
    uo = UserOrganization()
    userOrg = UserOrganization.get(uo)
    uoy = UserOrganizationYear()
    userOrgYear = UserOrganizationYear.get(uoy)
    facultyset = Faculty.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear)
    return render_to_response("pbfinancials/faculty_leave_list.html", {
        "facultyset": facultyset}, context_instance=RequestContext(request)
    )

@login_required()
def residentleavelist(request):
    uo = UserOrganization()
    userOrg = UserOrganization.get(uo)
    uoy = UserOrganizationYear()
    userOrgYear = UserOrganizationYear.get(uoy)
    residentset = Resident.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear)
    return render_to_response("pbfinancials/resident_leave_list.html", {
        "residentset": residentset}, context_instance=RequestContext(request)
    )

@login_required()
def facultyleave(request, pk):
    fId = pk
    LeaveFormset = inlineformset_factory(Faculty, FacultyUnavailable, extra=1, form=FacultyLeaveForm)
    LeaveFaculty = Faculty.objects.get(pk=fId)
    uo = UserOrganization()
    userOrg = UserOrganization.get(uo)
    uoy = UserOrganizationYear()
    userOrgYear = UserOrganizationYear.get(uoy)
    facultyset = Faculty.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear)
    dispContext = LeaveFaculty.__unicode__()
    if request.method == "POST":
        if 'cancel' in request.POST:
            return render_to_response("pbfinancials/faculty_leave_list.html", {
                "facultyset": facultyset}, context_instance=RequestContext(request)
            )

        elif 'submit' in request.POST:
            formset = LeaveFormset(request.POST, request.FILES, instance=LeaveFaculty, prefix='facultyleave', initial=[{'facultyRef':fId}])
            if formset.is_valid():
                formset.save()
                return render_to_response("pbfinancials/faculty_leave_list.html", {
                    "facultyset": facultyset}, context_instance=RequestContext(request)
                )
            else:
                # change to error response
                dispSaveError = 'One or more required fields are missing, please re-enter your data or select cancel.'
                return render_to_response("pbfinancials/faculty_leave.html", {
                    "formset": formset, "dispContext": dispContext, "dispSaveError": dispSaveError}, context_instance=RequestContext(request)
                )


    else:
        formset = LeaveFormset(instance=LeaveFaculty, prefix='facultyleave', initial=[{'facultyRef':fId}])
        #resformset = ResidentFormSet(prefix='resident', queryset=Resident.objects.filter(id=1))
        count = formset.total_form_count()
        return render_to_response("pbfinancials/faculty_leave.html", {
            "formset": formset, "dispContext": dispContext}, context_instance=RequestContext(request)
        )

@login_required()
def residentleave(request, pk):
    rId = pk
    LeaveFormset = inlineformset_factory(Resident, StaffUnavailable, extra=1, form=ResidentLeaveForm)
    LeaveResident = Resident.objects.get(pk=rId)
    uo = UserOrganization()
    userOrg = UserOrganization.get(uo)
    uoy = UserOrganizationYear()
    userOrgYear = UserOrganizationYear.get(uoy)
    residentset = Resident.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear)
    dispContext = LeaveResident.__unicode__()
    if request.method == "POST":
        if 'cancel' in request.POST:
            return render_to_response("pbfinancials/resident_leave_list.html", {
                "residentset": residentset}, context_instance=RequestContext(request)
            )

        elif 'submit' in request.POST:
            formset = LeaveFormset(request.POST, request.FILES, instance=LeaveResident, prefix='residentleave', initial=[{'residentRef':rId}])
            if formset.is_valid():
                formset.save()
                return render_to_response("pbfinancials/resident_leave_list.html", {
                    "residentset": residentset}, context_instance=RequestContext(request)
                )
            else:
                # change to error response
                dispSaveError = 'One or more required fields are missing, please re-enter your data or select cancel.'
                return render_to_response("pbfinancials/resident_leave.html", {
                    "formset": formset, "dispContext": dispContext, "dispSaveError": dispSaveError}, context_instance=RequestContext(request)
                )


    else:
        formset = LeaveFormset(instance=LeaveResident, prefix='residentleave', initial=[{'residentRef':rId}])
        #resformset = ResidentFormSet(prefix='resident', queryset=Resident.objects.filter(id=1))
        return render_to_response("pbfinancials/resident_leave.html", {
            "formset": formset, "dispContext": dispContext}, context_instance=RequestContext(request)
        )

@login_required()
def cliniccount(request, pk):
    cId = pk
    CountFormset = inlineformset_factory(Block, BlockResidentTypeCount, extra=1, form=ClinicCountForm)
    CountBlock = Block.objects.get(pk=cId)
    uo = UserOrganization()
    userOrg = UserOrganization.get(uo)
    uoy = UserOrganizationYear()
    userOrgYear = UserOrganizationYear.get(uoy)
    blockset = Block.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear)
    dispContext = CountBlock.__unicode__()
    if request.method == "POST":
        if 'cancel' in request.POST:
            return render_to_response("pbfinancials/clinic_count_list.html", {
                "blockset": blockset}, context_instance=RequestContext(request)
            )

        elif 'submit' in request.POST:
            formset = CountFormset(request.POST, request.FILES, instance=CountBlock, prefix='cliniccount', initial=[{'blockRef':cId}])
            if formset.is_valid():
                formset.save()
                return render_to_response("pbfinancials/clinic_count_list.html", {
                    "blockset": blockset}, context_instance=RequestContext(request)
                )
            else:
                # change to error response
                dispSaveError = 'One or more required fields are missing, please re-enter your data or select cancel.'
                return render_to_response("pbfinancials/clinic_count.html", {
                    "formset": formset, "dispContext": dispContext, "dispSaveError": dispSaveError}, context_instance=RequestContext(request)
                )


    else:
        formset = CountFormset(instance=CountBlock, prefix='cliniccount', initial=[{'blockRef':cId}])
        #resformset = ResidentFormSet(prefix='resident', queryset=Resident.objects.filter(id=1))
        count = formset.total_form_count()
        return render_to_response("pbfinancials/clinic_count.html", {
            "formset": formset, "dispContext": dispContext}, context_instance=RequestContext(request)
        )

@login_required()
def clinicavailabilityrotation(request, pk):
    rId = pk
    uo = UserOrganization()
    userOrg = UserOrganization.get(uo)
    uoy = UserOrganizationYear()
    userOrgYear = UserOrganizationYear.get(uoy)
    residentTypeSet = ResidentType.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear)
    officeHoursSet = OfficeHours.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear)
    caInitialSet = ClinicAvailability.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear, rotationRef__exact=rId)
    residentTypeCount = ResidentType.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear)
    officeHoursCount = OfficeHours.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear)
    expectedTotal = residentTypeCount.count() * officeHoursCount.count()
    if caInitialSet.count() < expectedTotal:
        for resType in residentTypeSet:
            for officeHour in officeHoursSet:
                caCheck = ClinicAvailability.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear, residentTypeRef__exact=resType.id, officeHrsRef__exact=officeHour.id, rotationRef__exact=rId)
                if caCheck.count() == 0:
                    ca = ClinicAvailability()
                    ca.organization_id = userOrg
                    ca.organizationYear_id = userOrgYear
                    ca.residentTypeRef_id = resType.id
                    ca.officeHrsRef_id = officeHour.id
                    ca.rotationRef_id = rId
                    ca.save()
    cacCheckSet = ClinicAvailabilityCount.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear, rotationRef__exact=rId)
    if cacCheckSet.count() == 0:
        pgySet = ResidentType.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear)
        for pgy in pgySet:
            cacInit = ClinicAvailabilityCount()
            cacInit.organization_id = userOrg
            cacInit.organizationYear_id = userOrgYear
            cacInit.rotationRef_id = rId
            cacInit.residentTypeRef_id = pgy.id
            cacInit.weeklySessions = 0
            cacInit.save()
    cacDataSet = ClinicAvailabilityCount.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear, rotationRef__exact=rId)
    RotationFormSet = inlineformset_factory(Rotation, ClinicAvailability, extra=0, form=ClinicAvailabilityCalendarForm)
    CacFormSet = modelformset_factory(ClinicAvailabilityCount, extra=0, form=ClinicAvailabilityCountCalendarForm)
    RotationRotation = Rotation.objects.get(pk=rId)
    dispContext = RotationRotation.code
    if request.method == "POST":
        if 'cancel' in request.POST:
            uo = UserOrganization()
            userOrg = UserOrganization.get(uo)
            uoy = UserOrganizationYear()
            userOrgYear = UserOrganizationYear.get(uoy)
            rotationset = Rotation.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear)
            return render_to_response("pbfinancials/clinicavailability_rotation_list.html", {
                "rotationset": rotationset}, context_instance=RequestContext(request)
            )

        elif 'submit' in request.POST:
            formset = RotationFormSet(request.POST, request.FILES, instance=RotationRotation, prefix='clinicavailability', initial=[{'rotationRef':rId}])
            cacFormSet = CacFormSet(request.POST, request.FILES, queryset=ClinicAvailabilityCount.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear, rotationRef__exact=rId), prefix='clinicavailabilitycount')
            if formset.is_valid() and cacFormSet.is_valid():
                formset.save()
                cacFormSet.save()
                uo = UserOrganization()
                userOrg = UserOrganization.get(uo)
                uoy = UserOrganizationYear()
                userOrgYear = UserOrganizationYear.get(uoy)
                rotationset = Rotation.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear)
                return render_to_response("pbfinancials/clinicavailability_rotation_list.html", {
                    "rotationset": rotationset}, context_instance=RequestContext(request)
                )
            else:
                # change to error response
                dispSaveError = 'One or more required fields are missing, please re-enter your data or select cancel.'
                return render_to_response("pbfinancials/clinicavailability_rotation.html", {
                    "formset": formset, "dispContext": dispContext, "dispSaveError": dispSaveError, "residentTypeSet": residentTypeSet, "officeHoursSet": officeHoursSet, "cacDataSet": cacDataSet, "cacFormSet": cacFormSet}, context_instance=RequestContext(request)
                )


    else:
        formset = RotationFormSet(instance=RotationRotation, prefix='clinicavailability', initial=[{'rotationRef':rId}])
        cacFormSet = CacFormSet(queryset=ClinicAvailabilityCount.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear, rotationRef__exact=rId), prefix='clinicavailabilitycount')
        #resformset = ResidentFormSet(prefix='resident', queryset=Resident.objects.filter(id=1))
        count = formset.total_form_count()
        return render_to_response("pbfinancials/clinicavailability_rotation.html", {
            "formset": formset, "dispContext": dispContext, "residentTypeSet": residentTypeSet, "officeHoursSet": officeHoursSet, "cacDataSet": cacDataSet, "cacFormSet": cacFormSet}, context_instance=RequestContext(request)
        )


class ResidentCreate(CreateView):
    form_class = ResidentForm
    model = Resident
    success_url = reverse_lazy('resident-list')

    def form_valid(self, form):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        uoy = UserOrganizationYear()
        userOrgYear = UserOrganizationYear.get(uoy)
        form.instance.lastUpdUser = self.request.user.id
        form.instance.organization_id = userOrg
        form.instance.organizationYear_id = userOrgYear
        return super(ResidentCreate, self).form_valid(form)

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(ResidentCreate, self).dispatch(request, *args, **kwargs)


class ResidentUpdate(UpdateView):
    form_class = ResidentForm
    model = Resident
    success_url = reverse_lazy('resident-list')

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(ResidentUpdate, self).dispatch(request, *args, **kwargs)



class ResidentDelete(DeleteView):
    model = Resident
    success_url = reverse_lazy('resident-list')

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(ResidentDelete, self).dispatch(request, *args, **kwargs)



class OrganizationYearCreate(CreateView):
    # set session variable for new Org Year
    uo = UserOrganization()
    userOrg = UserOrganization.get(uo)
    uoy = UserOrganizationYear()
    userOrgYear = UserOrganizationYear.get(uoy)
    RotationSet = Rotation.objects.filter(organization_id__exact=userOrg, organizationYear_id__exact=userOrgYear)
    if RotationSet.count() == 0:
        BaseRotationSet = BaseRotations.objects.all()
        for BaseRotation in BaseRotationSet:
            r = Rotation()
            r.organization_id = userOrg
            r.organizationYear_id = userOrgYear
            r.rotationName = BaseRotation.rotationDescr
            r.description = BaseRotation.rotationDescr
            r.code = BaseRotation.rotationCode
            r.rotationActive = 'True'
            r.splitAllowed = 'False'
            r.save()
    form_class = OrgYearForm
    model = OrganizationYear
    success_url = reverse_lazy('organizationyear-list')

    def form_valid(self, form):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        uoy = UserOrganizationYear()
        userOrgYear = UserOrganizationYear.get(uoy)
        form.instance.lastUpdUser = self.request.user.id
        form.instance.organization_id = userOrg
        form.instance.organizationYear_id = userOrgYear
        return super(OrganizationYearCreate, self).form_valid(form)

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(OrganizationYearCreate, self).dispatch(request, *args, **kwargs)



class OrganizationYearUpdate(UpdateView):
    form_class = OrgYearForm
    model = OrganizationYear
    success_url = reverse_lazy('organizationyear-list')

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(OrganizationYearUpdate, self).dispatch(request, *args, **kwargs)



class OrganizationYearDelete(DeleteView):
    form_class = OrgYearForm
    model = OrganizationYear
    success_url = reverse_lazy('organizationyear-list')

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(OrganizationYearDelete, self).dispatch(request, *args, **kwargs)


class ResidentListView(ListView):
    model = Resident

    def get_context_data(self, **kwargs):
        context = super(ResidentListView, self).get_context_data(**kwargs)
        context['now'] = timezone.now()
        return context

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(ResidentListView, self).dispatch(request, *args, **kwargs)


class ResidentTypeListView(ListView):
    model = ResidentType

    def get_context_data(self, **kwargs):
        context = super(ResidentTypeListView, self).get_context_data(**kwargs)
        context['now'] = timezone.now()
        return context

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(ResidentTypeListView, self).dispatch(request, *args, **kwargs)


class ResidentTypeCreate(CreateView):
    form_class = ResidentTypeForm
    model = ResidentType
    success_url = reverse_lazy('residenttype_list')

    def form_valid(self, form):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        uoy = UserOrganizationYear()
        userOrgYear = UserOrganizationYear.get(uoy)
        form.instance.lastUpdUser = self.request.user.id
        form.instance.organization_id = userOrg
        form.instance.organizationYear_id = userOrgYear
        return super(ResidentTypeCreate, self).form_valid(form)


class ResidentTypeUpdate(UpdateView):
    form_class = ResidentTypeForm
    model = ResidentType
    success_url = reverse_lazy('residenttype_list')

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(ResidentTypeUpdate, self).dispatch(request, *args, **kwargs)


class ResidentTypeDelete(DeleteView):
    model = ResidentType
    success_url = reverse_lazy('residenttype_list')

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(ResidentTypeDelete, self).dispatch(request, *args, **kwargs)



class BlockListView(ListView):
    model = Block
    form = BlockForm

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(BlockListView, self).dispatch(request, *args, **kwargs)


class BlockCreate(CreateView):
    form_class = BlockForm
    model = Block
    #success_url = reverse_lazy('blockandtype', args=(self.object.id))

    def form_valid(self, form):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        uoy = UserOrganizationYear()
        userOrgYear = UserOrganizationYear.get(uoy)
        form.instance.lastUpdUser = self.request.user.id
        form.instance.organization_id = userOrg
        form.instance.organizationYear_id = userOrgYear
        return super(BlockCreate, self).form_valid(form)

    def get_success_url(self): return reverse_lazy('blockandtype',args=(self.object.id,))

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(BlockCreate, self).dispatch(request, *args, **kwargs)

@login_required()
def blocktyperedirect(request):
    uo = UserOrganization()
    userOrg = UserOrganization.get(uo)
    uoy = UserOrganizationYear()
    userOrgYear = UserOrganizationYear.get(uoy)
    req = request.FILES
    foo = 1
    formset = RotationFormSet(queryset=Rotation.objects.filter(organization_id__exact=userOrg, organizationYear_id__exact=userOrgYear))
    #formset = RotationFormSet(request.POST, request.FILES, instance=organizationyear)
    return render_to_response("pbfinancials/orgyear_rotation.html", {
        "formset": formset,
        })

class BlockUpdate(UpdateView):
    form_class = BlockForm
    model = Block
    success_url = reverse_lazy('orgyearschedulesetup_list')

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(BlockUpdate, self).dispatch(request, *args, **kwargs)


class BlockDelete(DeleteView):
    model = Block
    success_url = reverse_lazy('orgyearschedulesetup_list')

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(BlockDelete, self).dispatch(request, *args, **kwargs)


@login_required()
def orgyear_rotation(request, pk):
    y = pk
    RotationFormSet = modelformset_factory(Rotation, form=OrgYearRotationForm)
    if request.method == "POST":
        formset = RotationFormSet(request.POST, request.FILES,
                                  queryset=Rotation.objects.filter(organization_id__exact=s,
                                                                   organizationYear_id__exact=y))
        if formset.is_valid():
            formset.save()
            # Do something.
    else:
        formset = RotationFormSet(
            queryset=Rotation.objects.filter(organization_id__exact=s, organizationYear_id__exact=y))
        #formset = RotationFormSet(request.POST, request.FILES, instance=organizationyear)
    return render_to_response("pbfinancials/orgyear_rotation.html", {
        "formset": formset,
    })

@login_required()
def blockcustom(request):
    context = {'blockcustom': blockcustom}
    return render(request, 'pbfinancials/block_custom.html', context)


class RotationListView(ListView):
    model = Rotation

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(RotationListView, self).dispatch(request, *args, **kwargs)



class RotationCreate(CreateView):
    form_class = RotationForm
    model = Rotation
    #success_url = reverse_lazy('orgyearrotationsetup_list')

    def form_valid(self, form):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        uoy = UserOrganizationYear()
        userOrgYear = UserOrganizationYear.get(uoy)
        form.instance.lastUpdUser = self.request.user.id
        form.instance.organization_id = userOrg
        form.instance.organizationYear_id = userOrgYear
        return super(RotationCreate, self).form_valid(form)

    def get_success_url(self): return reverse_lazy('rotationandtype',args=(self.object.id,))

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(RotationCreate, self).dispatch(request, *args, **kwargs)



@login_required()
def rotationtypelist(request):
    uo = UserOrganization()
    userOrg = UserOrganization.get(uo)
    uoy = UserOrganizationYear()
    userOrgYear = UserOrganizationYear.get(uoy)
    rotationset = Rotation.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear)
    return render_to_response("pbfinancials/rotation_type_list.html", {
        "rotationset": rotationset}, context_instance=RequestContext(request)
    )

@login_required()
def rotationandtype(request, pk):
    rId = pk
    uo = UserOrganization()
    userOrg = UserOrganization.get(uo)
    uoy = UserOrganizationYear()
    userOrgYear = UserOrganizationYear.get(uoy)
    RotationFormset = modelformset_factory(Rotation, form=RotationForm, extra=0)
    RotationResidentTypeSet = RotationResidentType.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear, rotationRef__exact=rId)
    if RotationResidentTypeSet.count() == 0:
        ResidentTypeSet = ResidentType.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear)
        for rts in ResidentTypeSet:
            rrt = RotationResidentType()
            rrt.organization_id = userOrg
            rrt.organizationYear_id = userOrgYear
            rrt.rotationRef_id = rId
            rrt.residentTypeRef_id = rts.id
            rrt.pgyRotation = 'N'
            rrt.pgyElective = 'N'
            rrt.save()
    ResidentTypeFormset = inlineformset_factory(Rotation, RotationResidentType, extra=0, form=RotationResidentTypeForm)
    RotationInstance = Rotation.objects.get(pk=rId)
    rotationset = Rotation.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear)
    dispContext = RotationInstance.rotationName
    if request.method == "POST":
        if 'cancel' in request.POST:
            return render_to_response("pbfinancials/rotation_type_list.html", {
                "rotationset": rotationset}, context_instance=RequestContext(request)
            )

        elif 'submit' in request.POST:
            rotFormset = RotationFormset(request.POST, request.FILES, prefix='rotation', queryset=Rotation.objects.filter(id=rId))
            formset = ResidentTypeFormset(request.POST, request.FILES, instance=RotationInstance, prefix='residenttype', initial=[{'rotationRef':rId}])
            if formset.is_valid() and rotFormset.is_valid():
                formset.save()
                rotFormset.save()
                return render_to_response("pbfinancials/rotation_type_list.html", {
                    "rotationset": rotationset}, context_instance=RequestContext(request)
                )
            else:
                # change to error response
                dispSaveError = 'One or more required fields are missing, please re-enter your data or select cancel.'
                return render_to_response("pbfinancials/rotation_type.html", {
                    "formset": formset, "rotFormset": rotFormset, "dispContext": dispContext, "dispSaveError": dispSaveError}, context_instance=RequestContext(request)
                )


    else:
        rotFormset = RotationFormset(prefix='rotation', queryset=Rotation.objects.filter(id=rId))
        formset = ResidentTypeFormset(instance=RotationInstance, prefix='residenttype', initial=[{'rotationRef':rId}])
        return render_to_response("pbfinancials/rotation_type.html", {
            "formset": formset, "rotFormset": rotFormset, "dispContext": dispContext}, context_instance=RequestContext(request)
        )

@login_required()
def blocktypelist(request):
    uo = UserOrganization()
    userOrg = UserOrganization.get(uo)
    uoy = UserOrganizationYear()
    userOrgYear = UserOrganizationYear.get(uoy)
    blockset = Block.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear)
    return render_to_response("pbfinancials/block_type_list.html", {
        "blockset": blockset}, context_instance=RequestContext(request)
    )

@login_required()
def blockandtype(request, pk):
    bId = pk
    uo = UserOrganization()
    userOrg = UserOrganization.get(uo)
    uoy = UserOrganizationYear()
    userOrgYear = UserOrganizationYear.get(uoy)
    BlockFormSet = modelformset_factory(Block, form=BlockForm, extra=0)
    BlockResidentTypeSet = BlockResidentType.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear, blockRef__exact=bId)
    if BlockResidentTypeSet.count() == 0:
        ResidentTypeSet = ResidentType.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear)
        for rts in ResidentTypeSet:
            brt = BlockResidentType()
            brt.organization_id = userOrg
            brt.organizationYear_id = userOrgYear
            brt.blockRef_id = bId
            brt.residentTypeRef_id = rts.id
            brt.residentExcluded = 'N'
            brt.patientSessions = 0
            brt.save()
    ResidentTypeFormset = inlineformset_factory(Block, BlockResidentType, extra=0, form=BlockResidentTypeForm)
    BlockInstance = Block.objects.get(pk=bId)
    blockset = Block.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear)
    dispContext = BlockInstance.description
    if request.method == "POST":
        if 'cancel' in request.POST:
            return render_to_response("pbfinancials/block_type_list.html", {
                "blockset": blockset}, context_instance=RequestContext(request)
            )

        elif 'submit' in request.POST:
            blkFormset = BlockFormSet(request.POST, request.FILES, prefix='block', queryset=Block.objects.filter(id=bId))
            formset = ResidentTypeFormset(request.POST, request.FILES, instance=BlockInstance, prefix='blocktype', initial=[{'blockRef':bId}])
            if formset.is_valid() and blkFormset.is_valid():
                formset.save()
                blkFormset.save()
                return render_to_response("pbfinancials/block_type_list.html", {
                    "blockset": blockset}, context_instance=RequestContext(request)
                )
            else:
                # change to error response
                dispSaveError = 'One or more required fields are missing, please re-enter your data or select cancel.'
                return render_to_response("pbfinancials/block_type.html", {
                    "formset": formset, "blkFormset": blkFormset, "dispContext": dispContext, "dispSaveError": dispSaveError}, context_instance=RequestContext(request)
                )


    else:
        blkFormset = BlockFormSet(prefix='block', queryset=Block.objects.filter(id=bId))
        formset = ResidentTypeFormset(instance=BlockInstance, prefix='blocktype', initial=[{'blockRef':bId}])
        return render_to_response("pbfinancials/block_type.html", {
            "formset": formset, "blkFormset": blkFormset, "dispContext": dispContext}, context_instance=RequestContext(request)
        )

class RotationUpdate(UpdateView):
    form_class = RotationForm
    model = Rotation
    success_url = reverse_lazy('orgyearrotationsetup_list')

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(RotationUpdate, self).dispatch(request, *args, **kwargs)



class RotationDelete(DeleteView):
    model = Rotation
    success_url = reverse_lazy('orgyearrotationsetup_list')

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(RotationDelete, self).dispatch(request, *args, **kwargs)


class TeamTypeListView(ListView):
    model = TeamType

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(TeamTypeListView, self).dispatch(request, *args, **kwargs)


class TeamTypeCreate(CreateView):
    form_class = TeamTypeForm
    model = TeamType
    success_url = reverse_lazy('orgyearteamsetup_list')

    def form_valid(self, form):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        uoy = UserOrganizationYear()
        userOrgYear = UserOrganizationYear.get(uoy)
        form.instance.lastUpdUser = self.request.user.id
        form.instance.organization_id = userOrg
        form.instance.organizationYear_id = userOrgYear
        return super(TeamTypeCreate, self).form_valid(form)

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(TeamTypeCreate, self).dispatch(request, *args, **kwargs)


class TeamTypeUpdate(UpdateView):
    form_class = TeamTypeForm
    model = TeamType
    success_url = reverse_lazy('orgyearteamsetup_list')

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(TeamTypeUpdate, self).dispatch(request, *args, **kwargs)


class TeamTypeDelete(DeleteView):
    model = TeamType
    success_url = reverse_lazy('orgyearteamsetup_list')

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(TeamTypeDelete, self).dispatch(request, *args, **kwargs)


@login_required()
def rotationcustom(request):
    context = {'rotationcustom': rotationcustom}
    return render(request, 'pbfinancials/rotation_custom.html', context)


class OfficeHoursListView(ListView):
    model = OfficeHours

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(OfficeHoursListView, self).dispatch(request, *args, **kwargs)



class OfficeHoursCreate(CreateView):
    form_class = OfficeHoursForm
    model = OfficeHours
    success_url = reverse_lazy('orgyearsessionsetup_list')

    def form_valid(self, form):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        uoy = UserOrganizationYear()
        userOrgYear = UserOrganizationYear.get(uoy)
        form.instance.lastUpdUser = self.request.user.id
        form.instance.organization_id = userOrg
        form.instance.organizationYear_id = userOrgYear
        return super(OfficeHoursCreate, self).form_valid(form)

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(OfficeHoursCreate, self).dispatch(request, *args, **kwargs)


class OfficeHoursUpdate(UpdateView):
    form_class = OfficeHoursForm
    model = OfficeHours
    success_url = reverse_lazy('orgyearsessionsetup_list')

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(OfficeHoursUpdate, self).dispatch(request, *args, **kwargs)


class OfficeHoursDelete(DeleteView):
    model = OfficeHoursForm
    success_url = reverse_lazy('orgyearsessionsetup_list')

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(OfficeHoursDelete, self).dispatch(request, *args, **kwargs)


@login_required()
def officehourscustom(request):
    context = {'officehourscustom': officehourscustom}
    return render(request, 'pbfinancials/officehours_custom.html', context)


class HolidayCreate(CreateView):
    form_class = HolidayForm
    model = Holiday
    success_url = reverse_lazy('holiday_list')

    def form_valid(self, form):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        uoy = UserOrganizationYear()
        userOrgYear = UserOrganizationYear.get(uoy)
        form.instance.lastUpdUser = self.request.user.id
        form.instance.organization_id = userOrg
        form.instance.organizationYear_id = userOrgYear
        return super(HolidayCreate, self).form_valid(form)

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(HolidayCreate, self).dispatch(request, *args, **kwargs)



class HolidayUpdate(UpdateView):
    form_class = HolidayForm
    model = Holiday
    success_url = reverse_lazy('holiday_list')

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(HolidayUpdate, self).dispatch(request, *args, **kwargs)



class HolidayDelete(DeleteView):
    model = Holiday
    success_url = reverse_lazy('holiday_list')

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(HolidayDelete, self).dispatch(request, *args, **kwargs)


@login_required()
def holidaycustom(request):
    context = {'holidaycustom': holidaycustom}
    return render(request, 'pbfinancials/holiday_custom.html', context)


class FacultyCreate(CreateView):
    form_class = FacultyForm
    model = Faculty
    success_url = reverse_lazy('faculty-list')

    def form_valid(self, form):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        uoy = UserOrganizationYear()
        userOrgYear = UserOrganizationYear.get(uoy)
        form.instance.lastUpdUser = self.request.user.id
        form.instance.organization_id = userOrg
        form.instance.organizationYear_id = userOrgYear
        return super(FacultyCreate, self).form_valid(form)

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(FacultyCreate, self).dispatch(request, *args, **kwargs)



class FacultyUpdate(UpdateView):
    form_class = FacultyForm
    model = Faculty
    success_url = reverse_lazy('faculty-list')

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(FacultyUpdate, self).dispatch(request, *args, **kwargs)


class FacultyDelete(DeleteView):
    model = Faculty
    success_url = reverse_lazy('faculty-list')

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(FacultyDelete, self).dispatch(request, *args, **kwargs)


class UnavailableTypeCreate(CreateView):
    form_class = UnavailableTypeForm
    model = UnavailableType
    success_url = reverse_lazy('orgyearleavesetup_list')

    def form_valid(self, form):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        uoy = UserOrganizationYear()
        userOrgYear = UserOrganizationYear.get(uoy)
        form.instance.lastUpdUser = self.request.user.id
        form.instance.organization_id = userOrg
        form.instance.organizationYear_id = userOrgYear
        return super(UnavailableTypeCreate, self).form_valid(form)

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(UnavailableTypeCreate, self).dispatch(request, *args, **kwargs)


class UnavailableTypeUpdate(UpdateView):
    form_class = UnavailableTypeForm
    model = UnavailableType
    success_url = reverse_lazy('orgyearleavesetup_list')

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(UnavailableTypeUpdate, self).dispatch(request, *args, **kwargs)


class UnavailableTypeDelete(DeleteView):
    model = UnavailableType
    success_url = reverse_lazy('orgyearleavesetup_list')

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(UnavailableTypeDelete, self).dispatch(request, *args, **kwargs)


@login_required()
def unavailabletypecustom(request):
    context = {'unavailabletypecustom': unavailabletypecustom}
    return render(request, 'pbfinancials/unavailabletype_custom.html', context)


class ClinicAvailabilityCreate(CreateView):
    form_class = ClinicAvailabilityForm
    model = ClinicAvailability
    success_url = reverse_lazy('clinicavailability-list')

    def form_valid(self, form):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        uoy = UserOrganizationYear()
        userOrgYear = UserOrganizationYear.get(uoy)
        form.instance.lastUpdUser = self.request.user.id
        form.instance.organization_id = userOrg
        form.instance.organizationYear_id = userOrgYear
        return super(ClinicAvailabilityCreate, self).form_valid(form)

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(ClinicAvailabilityCreate, self).dispatch(request, *args, **kwargs)



class ClinicAvailabilityUpdate(UpdateView):
    form_class = ClinicAvailabilityForm
    model = ClinicAvailability
    success_url = reverse_lazy('clinicavailability-list')

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(ClinicAvailabilityUpdate, self).dispatch(request, *args, **kwargs)



class ClinicAvailabilityDelete(DeleteView):
    model = ClinicAvailability
    success_url = reverse_lazy('clinicavailability-list')

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(ClinicAvailabilityDelete, self).dispatch(request, *args, **kwargs)


@login_required()
def clinicavailabilitycustom(request):
    context = {'clinicavailabilitycustom': clinicavailabilitycustom}
    return render(request, 'pbfinancials/clinicavailability_custom.html', context)


@csrf_exempt
@login_required()
def generateschedule(request):
    uo = UserOrganization()
    userOrg = UserOrganization.get(uo)
    uoy = UserOrganizationYear()
    userOrgYear = UserOrganizationYear.get(uoy)
    #pt = request.POST
    #dto = pt.dto
    #su = ScheduleUtility()
    #dto.toLogging = True
    #dto.toConsole = True
    #dto.debug = True

    #dto.weekID = 0
    #dto.year = 1
    #dto.block = 0
    #cp = request.POST
    #cpBlockRef = cp['form-0-blockRef']
    #cpWeekId = cp['form-0-week']
    dto = DTO()
    #su = ScheduleUtility()
    dto.toLogging = False
    dto.toConsole = True
    dto.debug = True
    dto.weekID = 1
    dto.year = userOrgYear
    dto.block = 10
    #su.genSchedule(dto)
    #su.rebuild(dto)
    #items = su.getFiltered(dto)
    #context = {'items': items}
    #return render(request, 'pbfinancials/generateSchedules.html', context)

@login_required()
def schedulebyblockweek(request):
    uo = UserOrganization()
    userOrg = UserOrganization.get(uo)
    uoy = UserOrganizationYear()
    userOrgYear = UserOrganizationYear.get(uoy)
    BlockWeekFormset = modelformset_factory(BlockWeek, form=BlockWeekForm)
    if request.method == 'POST':
        if 'submit' in request.POST:
            cp = request.POST
            cpBlockRef = cp['form-0-blockRef']
            cpWeekId = cp['form-0-week']
            blockDisp = Block.objects.get(organization__exact=userOrg, organizationYear__exact=userOrgYear, id__exact=cpBlockRef).code
            weekDisp = str(cpWeekId)
            beginDisp = Block.objects.get(organization__exact=userOrg, organizationYear__exact=userOrgYear, id__exact=cpBlockRef).sDateBeg
            endDisp = beginDisp + timedelta(days=7)
            arrayWeeks = []
            if int(cpWeekId) == 5:
                i = 1
                workingSet = AvailableAssignmentWork.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear, blockRef__exact=cpBlockRef).count()
                while i <= 4:
                    arrayWeeks.append(i)
                    i += 1
            else:
                arrayWeeks.append(int(cpWeekId))
                workingSet = AvailableAssignmentWork.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear, blockRef__exact=cpBlockRef, weekID__exact=cpWeekId).count()
            for w in arrayWeeks:
                if workingSet > 0:
                    dispFormMessage = 'The Block and Week Options that you are attempting to generate schedules for is currently being processed, ' \
                                      'the system will not allow the schedule to be generated more than once at the same time.'
                    bwformset = BlockWeekFormset(queryset=Block.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear))
                    return render_to_response('pbfinancials/clinic_schedule_run.html', {
                        "bwformset": bwformset, "dispFormMessage": dispFormMessage}, context_instance=RequestContext(request)
                    )
                else:
                    csb = ClinicScheduleBuilder()
                    csb.setOrganizationAndYear(userOrg, userOrgYear)
                    csb.generateScheduleForWeek(cpBlockRef, w)
                    if int(cpWeekId) != 5:
                        dto = DTO()
                        dto.weekID = int(w)
                        dto.year = userOrgYear
                        dto.block = int(cpBlockRef)
                        items = csb.getFiltered(dto, cpBlockRef, cpWeekId)

                        context = {'items': items, 'blockDisp': blockDisp, 'weekDisp': weekDisp, 'beginDisp': beginDisp, 'endDisp': endDisp}
                        return render(request, 'pbfinancials/reviewSchedules.html', context)
            if workingSet > 0 and int(cpWeekId) == 5:
                dispFormMessage = 'The Block and Week Options that you are attempting to generate schedules for is currently being processed, ' \
                                      'the system will not allow the schedule to be generated more than once at the same time.'
                bwformset = BlockWeekFormset(queryset=Block.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear))
                return render_to_response('pbfinancials/clinic_schedule_run.html', {
                "bwformset": bwformset, "dispFormMessage": dispFormMessage}, context_instance=RequestContext(request)
                )
            else:
                dispFormMessage = 'You have selected an option to run all weeks for a Block, please wait for several minutes and then ' \
                                      'review the generated schedules under the Review Schedules link.'
                bwformset = BlockWeekFormset(queryset=Block.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear))
                return render_to_response('pbfinancials/clinic_schedule_run.html', {
                    "bwformset": bwformset, "dispFormMessage": dispFormMessage}, context_instance=RequestContext(request)
                )
        elif 'submitall' in request.POST:
            workingSet = AvailableAssignmentWork.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear).count()
            if workingSet > 0:
                dispFormMessage = 'The Academic Year that you are attempting to generate schedules for is currently being processed, ' \
                                'the system will not allow the schedule to be generated more than once at the same time.'
                bwformset = BlockWeekFormset(queryset=Block.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear))
                return render_to_response('pbfinancials/clinic_schedule_run.html', {
                    "bwformset": bwformset, "dispFormMessage": dispFormMessage}, context_instance=RequestContext(request)
                )
            else:
                dispFormMessage = 'You have selected to Generate all schedules for the Academic Year, this can take quite a well, please wait between 5 and 10 minutes ' \
                                'and then review the generated schedules under the Review Schedules link.'
                arrayWeeks = []
                i = 1
                while i <= 4:
                    arrayWeeks.append(i)
                blockSet = Block.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear)
                for block in blockSet:
                    for w in arrayWeeks:
                        csb = ClinicScheduleBuilder()
                        csb.setOrganizationAndYear(userOrg, userOrgYear)
                        csb.generateScheduleForWeek(block.id, w)
                bwformset = BlockWeekFormset(queryset=Block.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear))
                return render_to_response('pbfinancials/clinic_schedule_run.html', {
                    "bwformset": bwformset, "dispFormMessage": dispFormMessage}, context_instance=RequestContext(request)
                )
        else:
            dispFormError = 'There was an error with the selected options, please review your choices and attempt schedule generation again.'
            bwformset = BlockWeekFormset(queryset=Block.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear))
            return render_to_response('pbfinancials/clinic_schedule_run.html', {
                "bwformset": bwformset, "dispFormError": dispFormError}, context_instance=RequestContext(request)
            )
    else:
        bwformset = BlockWeekFormset(queryset=Block.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear))
        return render_to_response('pbfinancials/clinic_schedule_run.html', {
            "bwformset": bwformset}, context_instance=RequestContext(request)
        )

@login_required()
def orgyearschedulesetup(request):
    DictList = {'Block': Block}
    df = dtoFactory()
    dto = df.getFactory(DictList, 1)
    BlockFormSet = modelformset_factory(Block, form=BlockForm, formset=BaseBlockFormSet, extra=0, fields=('code', 'description', 'blockActive'))
    if request.method == 'POST':
        formset = BlockFormSet(request.POST, request.FILES)
        if formset.is_valid():
            formset.save()
            return render_to_response(request, 'pbfinancials/sched_setup.html', {
                "formset": formset
                }, RequestContext(request))
    else:
        formset = BlockFormSet()
        return render_to_response('pbfinancials/sched_setup.html', {
        })
    #context = {'schedBlocks': dto}
    #return render(request, 'pbfinancials/sched_setup.html', context)

@login_required()
def orgyearschedsave(request):
    # ... view code here
    return render_to_response('pbfinancials/sched_setup.html')

@login_required()
def orgyearrotationsetup(request):
    DictList = {'Rotation': Rotation}
    df = dtoFactory()
    dto = df.getFactory(DictList, 1)
    context = {'schedRotations': dto}
    return render(request, 'pbfinancials/rotation_setup.html', context)

@login_required()
def orgyearsessionsetup(request):
    DictList = {'OfficeHours': OfficeHours}
    df = dtoFactory()
    dto = df.getFactory(DictList, 1)
    context = {'schedSessions': dto}
    return render(request, 'pbfinancials/session_setup.html', context)

@login_required()
def orgyearteamsetup(request):
    DictList = {'TeamType': TeamType}
    df = dtoFactory()
    dto = df.getFactory(DictList, 1)
    context = {'schedTeams': dto}
    return render(request, 'pbfinancials/team_setup.html', context)

@login_required()
def orgyearleavesetup(request):
    DictList = {'UnavailableType': UnavailableType}
    df = dtoFactory()
    dto = df.getFactory(DictList, 1)
    context = {'schedLeaveType': dto}
    return render(request, 'pbfinancials/leave_setup.html', context)

@login_required()
def orgyearschedulechange(request):
    postItems = RequestContext
    DictList = {'Block': Block}
    fieldList = []
    fieldList.append('code')
    fieldList.append('description')
    uf = updateFactory()
    dto = uf.setFactory(postItems, DictList, fieldList, 1)
    context = {'schedBlocks': dto}
    return render(request, 'pbfinancials/sched_setup.html', context)


class ClinicScheduleTypeListView(ListView):
    model = ClinicScheduleType

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(ClinicScheduleTypeListView, self).dispatch(request, *args, **kwargs)



class ClinicScheduleTypeCreate(CreateView):
    form_class = ClinicScheduleTypeForm
    model = ClinicScheduleType
    success_url = reverse_lazy('clinicscheduletype_list')

    def form_valid(self, form):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        uoy = UserOrganizationYear()
        userOrgYear = UserOrganizationYear.get(uoy)
        form.instance.lastUpdUser = self.request.user.id
        form.instance.organization_id = userOrg
        form.instance.organizationYear_id = userOrgYear
        return super(ClinicScheduleTypeCreate, self).form_valid(form)

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(ClinicScheduleTypeCreate, self).dispatch(request, *args, **kwargs)


class ClinicScheduleTypeUpdate(UpdateView):
    form_class = ClinicScheduleTypeForm
    model = ClinicScheduleType
    success_url = reverse_lazy('clinicscheduletype_list')

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(ClinicScheduleTypeUpdate, self).dispatch(request, *args, **kwargs)


class ClinicScheduleTypeDelete(DeleteView):
    model = ClinicScheduleType
    success_url = reverse_lazy('clinicscheduletype_list')

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(ClinicScheduleTypeDelete, self).dispatch(request, *args, **kwargs)


#blockresidenttypecount_list
class BlockResidentTypeCountListView(ListView):
    model = BlockResidentTypeCount

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(BlockResidentTypeCountListView, self).dispatch(request, *args, **kwargs)


class BlockResidentTypeCountCreate(CreateView):
    form_class = BlockResidentTypeCountForm
    model = BlockResidentTypeCount
    success_url = reverse_lazy('blockresidenttypecount_list')

    def form_valid(self, form):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        uoy = UserOrganizationYear()
        userOrgYear = UserOrganizationYear.get(uoy)
        form.instance.lastUpdUser = self.request.user.id
        form.instance.organization_id = userOrg
        form.instance.organizationYear_id = userOrgYear
        return super(BlockResidentTypeCountCreate, self).form_valid(form)

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(BlockResidentTypeCountCreate, self).dispatch(request, *args, **kwargs)


class BlockResidentTypeCountUpdate(UpdateView):
    form_class = BlockResidentTypeCountForm
    model = BlockResidentTypeCount
    success_url = reverse_lazy('blockresidenttypecount_list')

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(BlockResidentTypeCountUpdate, self).dispatch(request, *args, **kwargs)


class BlockResidentTypeCountDelete(DeleteView):
    model = BlockResidentTypeCount
    success_url = reverse_lazy('blockresidenttypecount_list')

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(BlockResidentTypeCountDelete, self).dispatch(request, *args, **kwargs)


class RotationScheduleCreate(CreateView):
    form_class = RotationScheduleForm
    model = RotationSchedule
    success_url = reverse_lazy('rotationschedule_list')

    def form_valid(self, form):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        uoy = UserOrganizationYear()
        userOrgYear = UserOrganizationYear.get(uoy)
        form.instance.lastUpdUser = self.request.user.id
        form.instance.organization_id = userOrg
        form.instance.organizationYear_id = userOrgYear
        return super(RotationScheduleCreate, self).form_valid(form)

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(RotationScheduleCreate, self).dispatch(request, *args, **kwargs)


class RotationScheduleUpdate(UpdateView):
    form_class = RotationScheduleForm
    model = RotationSchedule
    success_url = reverse_lazy('rotationschedule_list')

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(RotationScheduleUpdate, self).dispatch(request, *args, **kwargs)


class RotationScheduleDelete(DeleteView):
    model = RotationSchedule
    success_url = reverse_lazy('rotationschedule_list')

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(RotationScheduleDelete, self).dispatch(request, *args, **kwargs)


@login_required()
def rotationbyresident(request, pk):
    rbId = pk
    RotationFormSet = inlineformset_factory(Resident, RotationSchedule, extra=0, form=RotationScheduleResidentForm, can_delete=True, can_order=True)
    RotationResident = Resident.objects.get(pk=rbId)
    dispContext = RotationResident.__unicode__()
    uo = UserOrganization()
    userOrg = UserOrganization.get(uo)
    uoy = UserOrganizationYear()
    userOrgYear = UserOrganizationYear.get(uoy)
    maxRs = RotationSchedule.objects.all().aggregate(Max('id'))
    maxId = maxRs['id__max']
    newId = maxId + 1
    if request.method == "POST":
        if 'cancel' in request.POST:
            residentset = Resident.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear)
            return render_to_response("pbfinancials/rotationschedule_resident_list.html", {
                "residentset": residentset}, context_instance=RequestContext(request)
            )

        elif 'submit' in request.POST:
            formset = RotationFormSet(request.POST, request.FILES, instance=RotationResident, prefix='rotations', initial=[{'residentRef':rbId, 'organization': userOrg, 'organizationYear': userOrgYear}])

            if formset.is_valid():
                formset.save()
                residentset = Resident.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear)
                return render_to_response("pbfinancials/rotationschedule_resident_list.html", {
                    "residentset": residentset}, context_instance=RequestContext(request)
                )
            else:
                dispSaveError = 'One or more required fields are missing, please re-enter your data or select cancel.'
                return render_to_response("pbfinancials/rotation_schedule_resident.html", {
                    "formset": formset, "dispContext": dispContext, "dispSaveError": dispSaveError}, context_instance=RequestContext(request)
                )
    else:
        formset = RotationFormSet(instance=RotationResident, prefix='rotations', initial=[{'residentRef':rbId, 'organization': userOrg, 'organizationYear': userOrgYear}])
        #resformset = ResidentFormSet(prefix='resident', queryset=Resident.objects.filter(id=1))
        count = formset.total_form_count()
        return render_to_response("pbfinancials/rotation_schedule_resident.html", {
            "formset": formset, "dispContext": dispContext, "count": count, "rbId":rbId, "userOrgYear": userOrgYear,
            "userOrg": userOrg, "newId": newId}
            , context_instance=RequestContext(request)
        )


@login_required()
def reviewschedulebyblockweek(request):
    uo = UserOrganization()
    userOrg = UserOrganization.get(uo)
    uoy = UserOrganizationYear()
    userOrgYear = UserOrganizationYear.get(uoy)
    ClinicAvailabilityBlockWeekFormset = modelformset_factory(ClinicAvailabilityBlockWeek, form=ClinicAvailabilityBlockWeekForm)
    if request.method == 'POST':
        cp = request.POST
        cpBlockRef = cp['form-0-blockRef']
        cpWeekId = cp['form-0-week']
        blockDisp = Block.objects.get(organization__exact=userOrg, organizationYear__exact=userOrgYear, id__exact=cpBlockRef).code
        weekDisp = str(cpWeekId)
        beginDisp = Block.objects.get(organization__exact=userOrg, organizationYear__exact=userOrgYear, id__exact=cpBlockRef).sDateBeg
        endDisp = beginDisp + timedelta(days=7)
        csb = ClinicScheduleBuilder()
        csb.setOrganizationAndYear(userOrg, userOrgYear)
        dto = DTO()
        dto.weekID = int(cpWeekId)
        dto.year = userOrgYear
        dto.block = int(cpBlockRef)
        items = csb.getFiltered(dto, cpBlockRef, cpWeekId)
        context = {'items': items, 'blockDisp': blockDisp, 'weekDisp': weekDisp, 'beginDisp': beginDisp, 'endDisp': endDisp}
        return render(request, 'pbfinancials/reviewSchedules.html', context)
    else:
        cabwformset = ClinicAvailabilityBlockWeekFormset(queryset=Block.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear))
        return render_to_response('pbfinancials/review_schedule_run.html', {
            "cabwformset": cabwformset}, context_instance=RequestContext(request)
        )

@login_required()
def facultyclinichours(request, pk):
    fId = pk
    uo = UserOrganization()
    userOrg = UserOrganization.get(uo)
    uoy = UserOrganizationYear()
    userOrgYear = UserOrganizationYear.get(uoy)
    officeHoursSet = OfficeHours.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear)
    fchInitialSet = FacultyClinicHours.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear, facultyRef__exact=fId)
    if fchInitialSet.count() == 0:
        for officeHour in officeHoursSet:
            fchCheck = FacultyClinicHours.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear, officeHrsRef__exact=officeHour.id, facultyRef__exact=fId)
            if fchCheck.count() == 0:
                fch = FacultyClinicHours()
                fch.organization_id = userOrg
                fch.organizationYear_id = userOrgYear
                fch.officeHrsRef_id = officeHour.id
                fch.facultyRef_id = fId
                fch.save()
    FacultyFormSet = inlineformset_factory(Faculty, FacultyClinicHours, extra=0, form=FacultyClinicHoursCalendarForm)
    facultyObj = Faculty.objects.get(pk=fId)
    dispContext = facultyObj.__unicode__()
    if request.method == "POST":
        if 'cancel' in request.POST:
            uo = UserOrganization()
            userOrg = UserOrganization.get(uo)
            uoy = UserOrganizationYear()
            userOrgYear = UserOrganizationYear.get(uoy)
            facultyset = Faculty.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear)
            return render_to_response("pbfinancials/facultyclinichours_list.html", {
                "facultyset": facultyset}, context_instance=RequestContext(request)
            )

        elif 'submit' in request.POST:
            formset = FacultyFormSet(request.POST, request.FILES, instance=facultyObj, prefix='facultyclinichours', initial=[{'facultyRef':fId}])
            if formset.is_valid():
                formset.save()
                uo = UserOrganization()
                userOrg = UserOrganization.get(uo)
                uoy = UserOrganizationYear()
                userOrgYear = UserOrganizationYear.get(uoy)
                facultyset = Faculty.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear)
                return render_to_response("pbfinancials/facultyclinichours_list.html", {
                    "facultyset": facultyset}, context_instance=RequestContext(request)
                )
            else:
                # change to error response
                dispSaveError = 'One or more required fields are missing, please re-enter your data or select cancel.'
                return render_to_response("pbfinancials/facultyclinichours.html", {
                    "formset": formset, "dispContext": dispContext, "dispSaveError": dispSaveError, "officeHoursSet": officeHoursSet}, context_instance=RequestContext(request)
                )


    else:
        formset = FacultyFormSet(instance=facultyObj, prefix='facultyclinichours', initial=[{'facultyRef':fId}])
        return render_to_response("pbfinancials/facultyclinichours.html", {
            "formset": formset, "dispContext": dispContext, "officeHoursSet": officeHoursSet}, context_instance=RequestContext(request)
        )

@login_required()
def facultyclinichourslist(request):
    uo = UserOrganization()
    userOrg = UserOrganization.get(uo)
    uoy = UserOrganizationYear()
    userOrgYear = UserOrganizationYear.get(uoy)
    facultyset = Faculty.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear)
    return render_to_response("pbfinancials/facultyclinichours_list.html", {
        "facultyset": facultyset}, context_instance=RequestContext(request)
    )


class AccountCreate(CreateView):
    form_class = AccountForm
    model = Account
    success_url = reverse_lazy('account-list')

    def form_valid(self, form):
        return super(AccountCreate, self).form_valid(form)

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(AccountCreate, self).dispatch(request, *args, **kwargs)


class AccountUpdate(UpdateView):
    form_class = AccountForm
    model = Account
    success_url = reverse_lazy('account-list')

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(AccountUpdate, self).dispatch(request, *args, **kwargs)



class AccountDelete(DeleteView):
    model = Account
    success_url = reverse_lazy('account-list')

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(AccountDelete, self).dispatch(request, *args, **kwargs)
