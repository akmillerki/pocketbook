
__author__ = 'mattmccaskey'
from django import forms
from rezsched.models import Resident, OrganizationYear, Block, Rotation, OfficeHours, Holiday, Faculty, \
    UnavailableType, ClinicAvailability, TeamType, ResidentType, ClinicScheduleType, BlockResidentTypeCount, \
    RotationSchedule, ResidentElective, BaseOrganization, StaffUnavailable, FacultyUnavailable, \
    RotationResidentType, BlockWeek, ClinicAvailabilityCount, BlockResidentType, ClinicAvailabilityBlockWeek, \
    FacultyClinicHours
from django.forms.models import BaseModelFormSet
from datetime import datetime
from services import UserOrganization, UserOrganizationYear
from django.forms import TextInput, CheckboxInput, DateInput, Select, HiddenInput
from django.db.models import Max

class BaseBlockFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        uoy = UserOrganizationYear()
        userOrgYear = UserOrganizationYear.get(uoy)
        super(BaseBlockFormSet, self).__init__(*args, **kwargs)
        self.queryset = Block.objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear)

class ResidentForm(forms.ModelForm):
    lastName=forms.CharField(label='Last Name')
    firstName=forms.CharField(label="First name")

    class Meta:
        model = Resident
        fields = ('lastName', 'firstName','residentYear', 'residentTeam')
        exclude = ('Id','id', 'baseStaff_id')

class ResidentDisplayForm(forms.ModelForm):
    lastName=forms.CharField(label='Last Name')
    firstName=forms.CharField(label="First name")
    def __init__(self, *args, **kwargs):
        super(ResidentDisplayForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.fields['lastName'].widget.attrs['readonly'] = True
            self.fields['firstName'].widget.attrs['readonly'] = True
            self.fields['organization'].widget.attrs['readonly'] = True
            self.fields['organizationYear'].widget.attrs['readonly'] = True
            #self.fields['id'].widget.attrs['readonly'] = True


    class Meta:
        model = Resident
        exclude = ( 'baseStaff_id')
        widgets = {
            'organization': TextInput(attrs={'size': 30, 'maxlength': 30}), 'organizationYear': TextInput(attrs={'size': 10, 'maxlength': 10}),
            }

    class Media:
        css = {
            'all': ('http/site/layout.css',)
        }

class BlockForm(forms.ModelForm):
    class Meta:
        model = Block
        #fields= ('code', 'description', 'blockActive', 'sDateBeg', 'sDateEnd')
        fields= ('code', 'description', 'sDateBeg', 'sDateEnd')
        exclude = ('Id','id','organization_id', 'baseStaff_id')
        widgets = {
            'code': TextInput(attrs={'size': 5, 'maxlength': 1}), 'description': TextInput(attrs={'size': 20, 'maxlength': 20}), 'blockActive':CheckboxInput,
                'sDateBeg': DateInput, 'sDateEnd': DateInput, 'organizationYear': Select,
            }

class RotationForm(forms.ModelForm):
    class Meta:
        model = Rotation
        fields = ('code', 'rotationName', 'id')
        exclude = ( 'organization_id', 'baseStaff_id')
        widgets = {
            'id':HiddenInput
            }

class ResidentTypeForm(forms.ModelForm):
    class Meta:
        model = ResidentType
        exclude = ('Id','id','organization_id')


class TeamTypeForm(forms.ModelForm):
    class Meta:
        model = TeamType
        fields=('shortDesc', 'description')
        exclude = ('Id','id','organization_id', 'baseStaff_id')


class ClinicScheduleTypeForm(forms.ModelForm):
    class Meta:
        model = ClinicScheduleType
        exclude = ('Id','id','organization_id')


class ResidentListForm(forms.ModelForm):
    class Meta:
        model = Resident
        fields = ('firstName', 'lastName', 'emailAddress', 'residentYear', 'residentTeam')

class ResidentElectiveForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        uoy = UserOrganizationYear()
        userOrgYear = UserOrganizationYear.get(uoy)
        initial = kwargs.get('initial', {})
        initial['organization'] = userOrg
        initial['organizationYear'] = userOrgYear
        kwargs['initial'] = initial
        super(ResidentElectiveForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            uo = UserOrganization()
            userOrg = UserOrganization.get(uo)
            uoy = UserOrganizationYear()
            userOrgYear = UserOrganizationYear.get(uoy)
            self.fields['organization'].value = userOrg
            self.fields['organizationYear'].value = userOrgYear
            #self.fields['lastUpdUser'].value = 1
            # = forms.IntegerField(widget=forms.HiddenInput())
            self.fields['organizationYear'].widget.attrs['hidden'] = True
            self.fields['organization'].widget.attrs['hidden'] = True
            #self.fields['id'].widget.attrs['readonly'] = True

    class Meta:
        model = ResidentElective
        widgets = {
            'organizationYear': HiddenInput, 'organization': HiddenInput
            }


class OrgYearForm(forms.ModelForm):

    class Meta:
        model = OrganizationYear
        # hiding yearly variables until system can generate all blocks etc
        exclude = ('organization', 'yearGranularity', 'yearlyConvention', 'yearlySmallestUnit', 'yearBuiltFlag', 'yearClinicScheduleFlag', 'yearRotationScheduleFlag')
        widgets = {
            'yearBuiltFlag':CheckboxInput, 'yearClinicScheduleFlag':CheckboxInput, 'yearRotationScheduleFlag':CheckboxInput,
            }


class OrgYearRotationForm(forms.ModelForm):

    class Meta:
        model = Rotation
        fields = ('code', 'rotationName','description', 'id')

class OfficeHoursForm(forms.ModelForm):

    class Meta:
        model = OfficeHours
        fields = ('weekday', 'period', 'sequenceNbr', 'sTimeBeg', 'sTimeEnd')
        exclude = ('Id','id','organization_id', 'baseStaff_id')

class HolidayForm(forms.ModelForm):

    class Meta:
        model = Holiday
        exclude = ('Id','id','organization_id', 'baseStaff_id')

class FacultyForm(forms.ModelForm):

    class Meta:
        model = Faculty
        fields = ('lastName', 'firstName', 'facultyTeam')
        exclude = ('Id','id','organization_id', 'baseStaff_id')

class UnavailableTypeForm(forms.ModelForm):

    class Meta:
        model = UnavailableType
        fields = ('shortDesc','description')
        exclude = ('Id','id','organization_id', 'baseStaff_id')

class ClinicAvailabilityForm(forms.ModelForm):

    class Meta:
        model = ClinicAvailability
        exclude = ('Id','id','organization_id', 'baseStaff_id')


class PartialOrgYearRotationForm(forms.ModelForm):

    class Meta:
        model = Rotation
        fields = ('organization','organizationYear','code', 'rotationName','description','rotationActive', 'splitAllowed')


class PartialBlockForm(forms.ModelForm):

    class Meta:
        model = Block
        include = ('code','description','blockActive')


class BlockResidentTypeCountForm(forms.ModelForm):

    class Meta:
        model = BlockResidentTypeCount
        fields = ('blockRef', 'residentTypeRef', 'minSession', 'maxSession', 'ptsSession')
        exclude = ('Id','id','organization_id')


class RotationDisplayForm(forms.ModelForm):
    lastName=forms.CharField(label='Last Name')
    firstName=forms.CharField(label="First name")
    def __init__(self, *args, **kwargs):
        super(RotationDisplayForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.fields['lastName'].widget.attrs['readonly'] = True
            self.fields['firstName'].widget.attrs['readonly'] = True
            self.fields['organization'].widget.attrs['readonly'] = True
            self.fields['organizationYear'].widget.attrs['readonly'] = True
            #self.fields['id'].widget.attrs['readonly'] = True


    class Meta:
        model = Resident
        exclude = ( 'baseStaff_id')
        widgets = {
            'organization': TextInput(attrs={'size': 30, 'maxlength': 30}), 'organizationYear': TextInput(attrs={'size': 10, 'maxlength': 10}),
            }

    class Media:
        css = {
            'all': ('http/site/layout.css',)
        }

class RotationScheduleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        uoy = UserOrganizationYear()
        userOrgYear = UserOrganizationYear.get(uoy)
        initial = kwargs.get('initial', {})
        initial['organization'] = userOrg
        initial['organizationYear'] = userOrgYear
        kwargs['initial'] = initial
        super(RotationScheduleForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            uo = UserOrganization()
            userOrg = UserOrganization.get(uo)
            uoy = UserOrganizationYear()
            userOrgYear = UserOrganizationYear.get(uoy)
            self.fields['organization'].value = userOrg
            self.fields['organizationYear'].value = userOrgYear
            #self.fields['lastUpdUser'].value = 1
            # = forms.IntegerField(widget=forms.HiddenInput())
            self.fields['organizationYear'].widget.attrs['hidden'] = True
            self.fields['organization'].widget.attrs['hidden'] = True
            self.fields['blockRef'].widget.attrs['hidden'] = True
            #self.fields['id'].widget.attrs['readonly'] = True

    class Meta:
        model = RotationSchedule
        #widgets = {
        #    'organizationYear': HiddenInput, 'organization': HiddenInput, 'blockRef': HiddenInput
        #}

class RotationScheduleRotationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        uoy = UserOrganizationYear()
        userOrgYear = UserOrganizationYear.get(uoy)
        initial = kwargs.get('initial', {})
        initial['organization'] = userOrg
        initial['organizationYear'] = userOrgYear
        kwargs['initial'] = initial
        super(RotationScheduleRotationForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            uo = UserOrganization()
            userOrg = UserOrganization.get(uo)
            uoy = UserOrganizationYear()
            userOrgYear = UserOrganizationYear.get(uoy)
            self.fields['organization'].value = userOrg
            self.fields['organizationYear'].value = userOrgYear
            #self.fields['lastUpdUser'].value = 1
            # = forms.IntegerField(widget=forms.HiddenInput())
            self.fields['organizationYear'].widget.attrs['hidden'] = True
            self.fields['organization'].widget.attrs['hidden'] = True
            self.fields['rotationRef'].widget.attrs['hidden'] = True
            #self.fields['id'].widget.attrs['readonly'] = True

    class Meta:
        model = RotationSchedule
        widgets = {
            'organizationYear': HiddenInput, 'organization': HiddenInput, 'rotationRef': HiddenInput
        }

class RotationScheduleResidentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        uoy = UserOrganizationYear()
        userOrgYear = UserOrganizationYear.get(uoy)
        initial = kwargs.get('initial', {})
        initial['organization'] = userOrg
        initial['organizationYear'] = userOrgYear
        #initial['lastUpdUser'] = 1
        kwargs['initial'] = initial
        super(RotationScheduleResidentForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            uo = UserOrganization()
            userOrg = UserOrganization.get(uo)
            uoy = UserOrganizationYear()
            userOrgYear = UserOrganizationYear.get(uoy)
            self.fields['organization'].value = userOrg
            self.fields['organizationYear'].value = userOrgYear
            #self.fields['lastUpdUser'].value = 1
            # = forms.IntegerField(widget=forms.HiddenInput())
            self.fields['organizationYear'].widget.attrs['readonly'] = True
            self.fields['organization'].widget.attrs['readonly'] = True
            self.fields['residentRef'].widget.attrs['readonly'] = True
            #self.fields['id'].widget.attrs['readonly'] = True

    #def clean(self):
        """apply our custom validation rules"""
    #    data = self.cleaned_data
    #    uo = UserOrganization()
    #    userOrg = UserOrganization.get(uo)
    #    uoy = UserOrganizationYear()
    #    userOrgYear = UserOrganizationYear.get(uoy)
    #    maxRs = RotationSchedule.objects.all().aggregate(Max('id'))
    #    maxId = maxRs['id__max']
    #    newId = maxId + 1
    #    data['id'] = newId
    #    data['organization_id'] = userOrg
    #    data['organizationYear_id'] = userOrgYear
    #    data['residentRef_id'] = 16
    #    return data

    class Meta:
        model = RotationSchedule
        #widgets = {
        #    'organizationYear': HiddenInput,
        #    'organization': HiddenInput,
        #    'residentRef': HiddenInput
        #}


class ClinicAvailabilityCalendarForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        uoy = UserOrganizationYear()
        userOrgYear = UserOrganizationYear.get(uoy)
        initial = kwargs.get('initial', {})
        initial['organization'] = userOrg
        initial['organizationYear'] = userOrgYear
        #initial['residentRef'] = 16
        #initial['lastUpdUser'] = 1
        kwargs['initial'] = initial
        super(ClinicAvailabilityCalendarForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            uo = UserOrganization()
            userOrg = UserOrganization.get(uo)
            uoy = UserOrganizationYear()
            userOrgYear = UserOrganizationYear.get(uoy)
            self.fields['organization'].value = userOrg
            self.fields['organizationYear'].value = userOrgYear
            #self.fields['lastUpdUser'].value = 1
            #self.fields['residentRef'].value = 16
            # = forms.IntegerField(widget=forms.HiddenInput())
            self.fields['organizationYear'].widget.attrs['readonly'] = True
            self.fields['organization'].widget.attrs['readonly'] = True
            #self.fields['id'].widget.attrs['readonly'] = True

    class Meta:
        model = ClinicAvailability
        widgets = {
            'organizationYear': HiddenInput,
            'organization': HiddenInput,
            'rotationRef': HiddenInput,
            'residentTypeRef': HiddenInput,
            'officeHrsRef': HiddenInput
        }

class ClinicAvailabilityCountCalendarForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        uoy = UserOrganizationYear()
        userOrgYear = UserOrganizationYear.get(uoy)
        initial = kwargs.get('initial', {})
        initial['organization'] = userOrg
        initial['organizationYear'] = userOrgYear
        #initial['residentRef'] = 16
        #initial['lastUpdUser'] = 1
        kwargs['initial'] = initial
        super(ClinicAvailabilityCountCalendarForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            uo = UserOrganization()
            userOrg = UserOrganization.get(uo)
            uoy = UserOrganizationYear()
            userOrgYear = UserOrganizationYear.get(uoy)
            self.fields['organization'].value = userOrg
            self.fields['organizationYear'].value = userOrgYear
            #self.fields['lastUpdUser'].value = 1
            #self.fields['residentRef'].value = 16
            # = forms.IntegerField(widget=forms.HiddenInput())
            self.fields['organizationYear'].widget.attrs['readonly'] = True
            self.fields['organization'].widget.attrs['readonly'] = True
            #self.fields['id'].widget.attrs['readonly'] = True

    class Meta:
        model = ClinicAvailabilityCount
        widgets = {
            'organizationYear': HiddenInput,
            'organization': HiddenInput,
            'rotationRef': HiddenInput,
            'residentTypeRef': HiddenInput,
            'weeklySessions': TextInput(attrs={'size': 3, 'maxlength': 2})
        }

class ResidentLeaveForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        uoy = UserOrganizationYear()
        userOrgYear = UserOrganizationYear.get(uoy)
        initial = kwargs.get('initial', {})
        initial['organization'] = userOrg
        initial['organizationYear'] = userOrgYear
        #initial['residentRef'] = 16
        #initial['lastUpdUser'] = 1
        kwargs['initial'] = initial
        super(ResidentLeaveForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            uo = UserOrganization()
            userOrg = UserOrganization.get(uo)
            uoy = UserOrganizationYear()
            userOrgYear = UserOrganizationYear.get(uoy)
            self.fields['organization'].value = userOrg
            self.fields['organizationYear'].value = userOrgYear
            #self.fields['lastUpdUser'].value = 1
            #self.fields['residentRef'].value = 16
            # = forms.IntegerField(widget=forms.HiddenInput())
            self.fields['organizationYear'].widget.attrs['readonly'] = True
            self.fields['organization'].widget.attrs['readonly'] = True
            #self.fields['id'].widget.attrs['readonly'] = True

    class Meta:
        model = StaffUnavailable

class FacultyLeaveForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        uoy = UserOrganizationYear()
        userOrgYear = UserOrganizationYear.get(uoy)
        initial = kwargs.get('initial', {})
        initial['organization'] = userOrg
        initial['organizationYear'] = userOrgYear
        #initial['residentRef'] = 16
        #initial['lastUpdUser'] = 1
        kwargs['initial'] = initial
        super(FacultyLeaveForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            uo = UserOrganization()
            userOrg = UserOrganization.get(uo)
            uoy = UserOrganizationYear()
            userOrgYear = UserOrganizationYear.get(uoy)
            self.fields['organization'].value = userOrg
            self.fields['organizationYear'].value = userOrgYear
            #self.fields['lastUpdUser'].value = 1
            #self.fields['residentRef'].value = 16
            # = forms.IntegerField(widget=forms.HiddenInput())
            self.fields['organizationYear'].widget.attrs['readonly'] = True
            self.fields['organization'].widget.attrs['readonly'] = True
            #self.fields['id'].widget.attrs['readonly'] = True

    class Meta:
        model = FacultyUnavailable

#ClinicCountForm
class ClinicCountForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        uoy = UserOrganizationYear()
        userOrgYear = UserOrganizationYear.get(uoy)
        initial = kwargs.get('initial', {})
        initial['organization'] = userOrg
        initial['organizationYear'] = userOrgYear
        #initial['residentRef'] = 16
        #initial['lastUpdUser'] = 1
        kwargs['initial'] = initial
        super(ClinicCountForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            uo = UserOrganization()
            userOrg = UserOrganization.get(uo)
            uoy = UserOrganizationYear()
            userOrgYear = UserOrganizationYear.get(uoy)
            self.fields['organization'].value = userOrg
            self.fields['organizationYear'].value = userOrgYear
            #self.fields['lastUpdUser'].value = 1
            #self.fields['residentRef'].value = 16
            # = forms.IntegerField(widget=forms.HiddenInput())
            self.fields['organizationYear'].widget.attrs['readonly'] = True
            self.fields['organization'].widget.attrs['readonly'] = True
            #self.fields['id'].widget.attrs['readonly'] = True

    class Meta:
        model = BlockResidentTypeCount

#ClinicCountForm
class RotationResidentTypeForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        uoy = UserOrganizationYear()
        userOrgYear = UserOrganizationYear.get(uoy)
        initial = kwargs.get('initial', {})
        initial['organization'] = userOrg
        initial['organizationYear'] = userOrgYear
        #initial['residentRef'] = 16
        #initial['lastUpdUser'] = 1
        kwargs['initial'] = initial
        super(RotationResidentTypeForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            uo = UserOrganization()
            userOrg = UserOrganization.get(uo)
            uoy = UserOrganizationYear()
            userOrgYear = UserOrganizationYear.get(uoy)
            self.fields['organization'].value = userOrg
            self.fields['organizationYear'].value = userOrgYear
            #self.fields['lastUpdUser'].value = 1
            #self.fields['residentRef'].value = 16
            # = forms.IntegerField(widget=forms.HiddenInput())
            self.fields['organizationYear'].widget.attrs['readonly'] = True
            self.fields['organization'].widget.attrs['readonly'] = True
            #self.fields['id'].widget.attrs['readonly'] = True

    class Meta:
        model = RotationResidentType
        widgets = {
            'pgyRotation': Select, 'pgyElective': Select, 'rotationRef':HiddenInput
            }

class BlockResidentTypeForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        uoy = UserOrganizationYear()
        userOrgYear = UserOrganizationYear.get(uoy)
        initial = kwargs.get('initial', {})
        initial['organization'] = userOrg
        initial['organizationYear'] = userOrgYear
        #initial['residentRef'] = 16
        #initial['lastUpdUser'] = 1
        kwargs['initial'] = initial
        super(BlockResidentTypeForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            uo = UserOrganization()
            userOrg = UserOrganization.get(uo)
            uoy = UserOrganizationYear()
            userOrgYear = UserOrganizationYear.get(uoy)
            self.fields['organization'].value = userOrg
            self.fields['organizationYear'].value = userOrgYear
            #self.fields['lastUpdUser'].value = 1
            #self.fields['residentRef'].value = 16
            # = forms.IntegerField(widget=forms.HiddenInput())
            self.fields['organizationYear'].widget.attrs['readonly'] = True
            self.fields['organization'].widget.attrs['readonly'] = True
            #self.fields['id'].widget.attrs['readonly'] = True

    class Meta:
        model = BlockResidentType
        widgets = {
            'patientSessions': TextInput,  'blockRef':HiddenInput, 'residentExcluded':HiddenInput
        }

class BlockWeekForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        uoy = UserOrganizationYear()
        userOrgYear = UserOrganizationYear.get(uoy)
        initial = kwargs.get('initial', {})
        initial['organization'] = userOrg
        initial['organizationYear'] = userOrgYear
        #initial['residentRef'] = 16
        #initial['lastUpdUser'] = 1
        kwargs['initial'] = initial
        super(BlockWeekForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            uo = UserOrganization()
            userOrg = UserOrganization.get(uo)
            uoy = UserOrganizationYear()
            userOrgYear = UserOrganizationYear.get(uoy)
            self.fields['organization'].value = userOrg
            self.fields['organizationYear'].value = userOrgYear
            #self.fields['lastUpdUser'].value = 1
            #self.fields['residentRef'].value = 16
            # = forms.IntegerField(widget=forms.HiddenInput())
            self.fields['organizationYear'].widget.attrs['readonly'] = True
            self.fields['organization'].widget.attrs['readonly'] = True
            #self.fields['id'].widget.attrs['readonly'] = True

    class Meta:
        model = BlockWeek
        widgets = {
            'blockRef': Select, 'week': Select,
        }

class ClinicAvailabilityBlockWeekForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        uoy = UserOrganizationYear()
        userOrgYear = UserOrganizationYear.get(uoy)
        initial = kwargs.get('initial', {})
        initial['organization'] = userOrg
        initial['organizationYear'] = userOrgYear
        kwargs['initial'] = initial
        super(ClinicAvailabilityBlockWeekForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            uo = UserOrganization()
            userOrg = UserOrganization.get(uo)
            uoy = UserOrganizationYear()
            userOrgYear = UserOrganizationYear.get(uoy)
            self.fields['organization'].value = userOrg
            self.fields['organizationYear'].value = userOrgYear
            self.fields['organizationYear'].widget.attrs['readonly'] = True
            self.fields['organization'].widget.attrs['readonly'] = True

    class Meta:
        model = ClinicAvailabilityBlockWeek
        widgets = {
            'blockRef': Select, 'week': Select,
            }

class FacultyClinicHoursCalendarForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        uoy = UserOrganizationYear()
        userOrgYear = UserOrganizationYear.get(uoy)
        initial = kwargs.get('initial', {})
        initial['organization'] = userOrg
        initial['organizationYear'] = userOrgYear
        #initial['residentRef'] = 16
        #initial['lastUpdUser'] = 1
        kwargs['initial'] = initial
        super(FacultyClinicHoursCalendarForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            uo = UserOrganization()
            userOrg = UserOrganization.get(uo)
            uoy = UserOrganizationYear()
            userOrgYear = UserOrganizationYear.get(uoy)
            self.fields['organization'].value = userOrg
            self.fields['organizationYear'].value = userOrgYear
            #self.fields['lastUpdUser'].value = 1
            #self.fields['residentRef'].value = 16
            # = forms.IntegerField(widget=forms.HiddenInput())
            self.fields['organizationYear'].widget.attrs['readonly'] = True
            self.fields['organization'].widget.attrs['readonly'] = True
            #self.fields['id'].widget.attrs['readonly'] = True

    class Meta:
        model = FacultyClinicHours
        widgets = {
            'organizationYear': HiddenInput,
            'organization': HiddenInput,
            'facultyRef': HiddenInput,
            'officeHrsRef': HiddenInput,
        }