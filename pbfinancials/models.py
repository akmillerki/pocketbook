
from django.db import models
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django_localflavor_us.models import USStateField, PhoneNumberField

#################################################################################
# @author:
# @modified by:
#
#	Name			Date			Descr
#	-------			---------		----------------
#	Matt McCaskey	01/05/13		Modified to convert to Django model syntax
#
#
#
#################################################################################

class DTO(object):
    pass

class DTOList(object):
    pass

class BaseOrganization(models.Model):
    organizationName = models.CharField("Organization", max_length=100)
    organizationAddressOne = models.CharField("Address One", max_length=50)
    organizationAddressTwo = models.CharField("Address Two", max_length=50, null=True, default= "")
    organizationCity = models.CharField("City", max_length=50)
    organizationState = USStateField("State")
    organizationZip = models.CharField("Zip Code",max_length=5)
    organizationPlusFour = models.CharField("Zip Plus",max_length=4, null=True, default="")
    organizationMainPhone = PhoneNumberField("Main Phone Number", null=True, default = "")
    organizationFax = PhoneNumberField("Fax Number", null=True, default = "")
    def __unicode__(self):
        return unicode(self.organizationName)

class BaseRotations(models.Model):
    rotationCode = models.CharField("Rotation Code", max_length=10)
    rotationDescr = models.CharField("Rotation Description", max_length=30)


ACCT_TYPE_CHOICES= (
    ('A', 'Asset Account'),
    ('C', 'Credit Account')
)
class AccountType(models.Model):
    accountType = models.CharField("Account Type", choices=ACCT_TYPE_CHOICES, max_length=1)
    def __unicode__(self):
        return unicode(self.accountType)



YESNO_CHOICES = (
    ('Y', 'Yes'),
    ('N', 'No')
)
class Account(models.Model):
    # todo link this to whichever User model we choose
    accountName = models.CharField("Account Name", max_length=30)
    accountNumber = models.BigIntegerField("Account Number", max_length=16)
    accountTypeRef = models.ForeignKey('AccountType')
    accountIsBudgetary = models.CharField("Budgetary Account", choices=YESNO_CHOICES, max_length=1)
    def __unicode__(self):
        return unicode(self.accountName)

class Transaction(models.Model):
    transAccount = models.ForeignKey('Account', verbose_name = "Account")
    transAmount = models.DecimalField("Transaction Amount", max_digits=10, decimal_places=2)



GRANULARITY_CHOICES = (
    ('WKY', 'Weekly'),
    ('BWK', 'Two Week'),
    ('4WK', 'Four Week Rolling'),
    ('MNY', 'Monthly'),
)
CONVENTION_CHOICES = (
    ('ALP', 'Alphabetical'),
    ('NUM', 'Numeric'),
    ('ROM', 'Roman Numeral'),
)
ONOFF_CHOICES = (
    ('True', 'True'),
    ('False', 'False')
    )
TIME_DISPLAY_CHOICES = (
    ('M', 'Military'),
    ('S', 'Standard')
)
class OrganizationYear(models.Model):
    organization = models.ForeignKey('BaseOrganization', verbose_name= "Organization")
    yearStartDate = models.DateField("Start Date")
    yearEndDate = models.DateField("End Date", null=True)
    yearDescr = models.CharField("Academic Year", max_length=30)
    yearGranularity = models.CharField("Yearly Block Schedule Granularity", max_length=3, choices=GRANULARITY_CHOICES)
    yearlyConvention = models.CharField("Yearly Block Naming Convention", max_length=3, choices=CONVENTION_CHOICES)
    yearlySmallestUnit = models.CharField("Yearly Smallest Time Unit", max_length=3, choices=GRANULARITY_CHOICES)
    yearBuiltFlag = models.CharField("Year Setup Generated", max_length=5, choices=ONOFF_CHOICES)
    yearClinicScheduleFlag = models.CharField("Clinic Schedules Generated", max_length=5, choices=ONOFF_CHOICES)
    yearRotationScheduleFlag = models.CharField("Rotation Schedules Generated", max_length=5, choices=ONOFF_CHOICES)
    yearTimeDisplayFlag = models.CharField("Time Display", max_length=1, choices=TIME_DISPLAY_CHOICES)
    def __unicode__(self):
        return unicode(self.yearDescr)

    class Meta:
        verbose_name =  "Academic Year"
        verbose_name_plural = "Academic Years"


class AppUser(models.Model):
    organization = models.ForeignKey('BaseOrganization')
    user = models.ForeignKey(User, null=True, blank=True)
    sessionID = models.CharField(max_length=255)
    lmDateTime = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Application User"
        verbose_name_plural = "Application Users"

class AppUserHistory(models.Model):
    organization = models.ForeignKey('BaseOrganization')
    user = models.ForeignKey(User, null=True, blank=True)
    sessionID = models.CharField(max_length=255)
    logonDT = models.DateTimeField()
    logoffDT = models.DateTimeField()
    lmDateTime = models.DateTimeField(auto_now=True)
    created_dt = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name =  "User History"
        verbose_name_plural = "User Histories"


class ToleranceVariables(models.Model):
    organization = models.ForeignKey('BaseOrganization', verbose_name="Associated Organization")
    organizationYear = models.ForeignKey('OrganizationYear', verbose_name= "Academic Year")
    patientSessionTolerance = models.DecimalField(decimal_places=2, max_digits=2)
    teamSessionTolerance = models.DecimalField(decimal_places=2, max_digits=2)

ONOFF_CHOICES = (
    ('True', 'True'),
    ('False', 'False')
)
class Block(models.Model):
    organization = models.ForeignKey('BaseOrganization', db_index=True, verbose_name="Associated Organization")
    organizationYear = models.ForeignKey('OrganizationYear', db_index=True, verbose_name= "Academic Year")
    description = models.CharField('Block Description',max_length=50)
    code = models.CharField('Block ID', db_index=True, max_length=5)
    blockActive = models.CharField('Active for Year', max_length=5, choices=ONOFF_CHOICES)
    sDateBeg = models.DateField("Block Start Date",auto_now=False)
    sDateEnd = models.DateField("Block End Date",auto_now=False)
    def __unicode__(self):
        return unicode(self.description)

    class Meta:
        verbose_name =  "Block"
        verbose_name_plural = "Blocks"

ONOFF_CHOICES = (
    ('True', 'True'),
    ('False', 'False')
)
class Rotation(models.Model):
    organization = models.ForeignKey('BaseOrganization', db_index=True, verbose_name="Associated Organization")
    organizationYear = models.ForeignKey('OrganizationYear', db_index=True, verbose_name= "Academic Year")
    rotationName = models.CharField('Rotation Name', db_index=True, max_length=30)
    code = models.CharField('Rotation Abbreviation', db_index=True, max_length=10)
    rotationActive = models.CharField('Active for Year', max_length=5, choices=ONOFF_CHOICES)
    description = models.CharField('Unique Description', max_length=100, null=True, blank=True)
    splitAllowed = models.CharField('Split Rotation', max_length=5, choices=ONOFF_CHOICES)

    def __unicode__(self):
        return unicode(self.rotationName)

    class Meta:
        verbose_name =  "Rotation"
        verbose_name_plural = "Rotations"

#    weekday : 3 char
WEEKDAY_CHOICES = (
    ('M', 'Monday'),
    ('T', 'Tuesday'),
    ('W', 'Wednesday'),
    ('H', 'Thursday'),
    ('F', 'Friday'),
    ('S', 'Saturday'),
    ('U', 'Sunday'),
    )
ONOFF_CHOICES = (
    ('True', 'True'),
    ('False', 'False'),
)
PERIOD_CHOICES = (
    ('AM', 'AM'),
    ('PM', 'PM'),
)
class OfficeHours(models.Model):
    organization = models.ForeignKey('BaseOrganization', db_index=True, verbose_name="Associated Organization")
    organizationYear = models.ForeignKey('OrganizationYear', db_index=True, verbose_name= "Academic Year")
    weekday = models.CharField(max_length=1, choices=WEEKDAY_CHOICES)
    sequenceNbr = models.IntegerField()
    period = models.CharField(max_length=2, verbose_name="Period Description", choices=PERIOD_CHOICES)
    sessionActive = models.CharField('Active For Year', max_length=5, choices=ONOFF_CHOICES)
    sTimeBeg = models.TimeField(auto_now=False, verbose_name="Start Time")
    sTimeEnd = models.TimeField(auto_now=False, verbose_name="End Time")
    def __unicode__(self):
        return u'%s %s %s' % (self.weekday,'-', self.period)

    class Meta:
        verbose_name =  "Office Hours"
        verbose_name_plural = "Office Hours"

class Holiday(models.Model):
    organization = models.ForeignKey('BaseOrganization', verbose_name="Associated Organization")
    organizationYear = models.ForeignKey('OrganizationYear', verbose_name= "Academic Year")
    description = models.CharField(max_length=255, verbose_name="Holiday Title")
    sHolidayDate = models.DateField(auto_now=False, verbose_name="Holiday Date")
    def __unicode__(self):
        return self.description

    class Meta:
        verbose_name =  "Holiday"
        verbose_name_plural = "Holidays"

ONOFF_CHOICES = (
    ('True', 'True'),
    ('False', 'False')
)
class UnavailableType(models.Model):
    organization = models.ForeignKey('BaseOrganization', verbose_name="Associated Organization")
    organizationYear = models.ForeignKey('OrganizationYear', verbose_name= "Academic Year")
    shortDesc = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    leaveActive = models.CharField('Active For Year', max_length=5, choices=ONOFF_CHOICES)
    def __unicode__(self):
        return self.description

    class Meta:
        verbose_name =  "Type of Unavailability"
        verbose_name_plural = "Types of Unavailability"

ONOFF_CHOICES = (
    ('True', 'True'),
    ('False', 'False')
)
class TeamType(models.Model):
    organization = models.ForeignKey('BaseOrganization', db_index=True, verbose_name="Associated Organization")
    organizationYear = models.ForeignKey('OrganizationYear', db_index=True, verbose_name= "Academic Year")
    shortDesc = models.CharField(max_length=255, db_index=True, verbose_name="Abbreviation")
    description = models.CharField(max_length=255, verbose_name="Description")
    teamActive = models.CharField('Active For Year', max_length=5, choices= ONOFF_CHOICES)
    def __unicode__(self):
        return self.description

    class Meta:
        verbose_name =  "Team Type"
        verbose_name_plural = "Team Types"

class ResidentType(models.Model):
    organization = models.ForeignKey('BaseOrganization', db_index=True, verbose_name="Associated Organization")
    organizationYear = models.ForeignKey('OrganizationYear', db_index=True, verbose_name= "Academic Year")
    shortDesc = models.CharField(max_length=255, db_index=True)
    description = models.CharField(max_length=255)
    def __unicode__(self):
        return unicode(self.shortDesc)

    class Meta:
        verbose_name =  "Resident Type"
        verbose_name_plural = "Resident Types"

class ResidentElective(models.Model):
    organization = models.ForeignKey('BaseOrganization', verbose_name="Associated Organization")
    organizationYear = models.ForeignKey('OrganizationYear', verbose_name= "Academic Year")
    residentRef = models.ForeignKey('Resident', verbose_name='Resident')
    blockRef = models.ForeignKey('Block', verbose_name='Schedule Block')
    rotationRef = models.ForeignKey('Rotation', verbose_name = 'Rotation')
    def __unicode__(self):
        return u'%s %s' % (self.residentRef.lastName, self.rotationRef.description)

    class Meta:
        verbose_name = "Resident Elective"
        verbose_name_plural = "Resident Electives"


ONOFF_CHOICES = (
    ('Y', 'Yes'),
    ('N', 'No')
)
class RotationResidentType(models.Model):
    organization = models.ForeignKey('BaseOrganization', verbose_name="Associated Organization")
    organizationYear = models.ForeignKey('OrganizationYear', verbose_name= "Academic Year")
    residentTypeRef = models.ForeignKey('ResidentType')
    rotationRef = models.ForeignKey('Rotation')
    pgyRotation = models.CharField("Available to PGY", max_length=1, choices=ONOFF_CHOICES, null=True, blank=True, default=False)
    pgyElective = models.CharField("PGY Elective", max_length=1, choices=ONOFF_CHOICES, null=True, blank=True, default=False)

ONOFF_CHOICES = (
    ('Y', 'Yes'),
    ('N', 'No')
)
class BlockResidentType(models.Model):
    organization = models.ForeignKey('BaseOrganization', db_index=True, verbose_name="Associated Organization")
    organizationYear = models.ForeignKey('OrganizationYear', db_index=True, verbose_name= "Academic Year")
    residentTypeRef = models.ForeignKey('ResidentType', db_index=True)
    blockRef = models.ForeignKey('Block',  db_index=True)
    residentExcluded = models.CharField("Resident Excluded", max_length=1, choices=ONOFF_CHOICES, default='N', null=True, blank=True)
    patientSessions = models.IntegerField("Patients Seen per Session", null=False, blank=False, default=0)


class BaseStaff(models.Model):
    organization = models.ForeignKey('BaseOrganization', db_index=True, verbose_name="Associated Organization")
    organizationYear = models.ForeignKey('OrganizationYear', db_index=True, verbose_name= "Academic Year")
    lastName = models.CharField("Last Name", db_index=True, max_length=100)
    firstName = models.CharField("First Name", max_length=100)
    middleInitial = models.CharField("Middle Initial", max_length=1, null=True, default="")
    emailAddress = models.EmailField("Email", max_length=100, null=True, default="")
    staffIdNumber = models.CharField("ID Number", max_length=25, null=True, default="")
    phoneNumber = PhoneNumberField("Phone Number", null=True, default="")
    phoneExtension = models.CharField("Phone Ext.",max_length=5, null=True, default="")
    pagerNumber = PhoneNumberField("Pager Number", null=True, default="")
    def __unicode__(self):
        return u'%s %s' % (self.firstName, self.lastName)

    class Meta:
        abstract = True

class Resident(BaseStaff):
    residentYear = models.ForeignKey('ResidentType', verbose_name="Resident Year")
    residentTeam = models.ForeignKey('TeamType', verbose_name="Assigned Team")
    def __unicode__(self):
        return u'%s %s' % (self.firstName, self.lastName)

    def get_absolute_url(self):
        return reverse('resident-update', kwargs={'pk': self.pk})

    class Meta:
        verbose_name = "Resident"
        verbose_name_plural = "Residents"

class Faculty(BaseStaff):
    facultyTeam = models.ForeignKey('TeamType')

    class Meta:
        verbose_name =  "Faculty"
        verbose_name_plural = "Faculty"


class FacultyRounds(models.Model):
    facultyRef = models.ForeignKey('Faculty')
    officeHoursRef = models.ForeignKey('OfficeHours')
    dateBeg = models.DateField("Begin Date", auto_now=False)
    dateEnd = models.DateField("End Date", auto_now=False)


class StaffUnavailable(models.Model):
    organization = models.ForeignKey('BaseOrganization', db_index=True, verbose_name="Associated Organization")
    organizationYear = models.ForeignKey(OrganizationYear, db_index=True, verbose_name="Academic Year")
    residentRef = models.ForeignKey('Resident', db_index=True, verbose_name= "Resident")
    unavailRef = models.ForeignKey('UnavailableType', verbose_name= "Reason")
    officeHoursRef = models.ForeignKey('OfficeHours', verbose_name='Clinic Session Unavailable')
    dateBeg = models.DateField("Begin Date", db_index=True, auto_now=False)
    dateEnd = models.DateField("End Date", db_index=True, auto_now=False)

class FacultyUnavailable(models.Model):
    organization = models.ForeignKey('BaseOrganization', db_index=True, verbose_name="Associated Organization")
    organizationYear = models.ForeignKey(OrganizationYear, db_index=True, verbose_name="Academic Year")
    facultyRef = models.ForeignKey('Faculty', db_index=True, verbose_name= "Resident")
    unavailRef = models.ForeignKey('UnavailableType', verbose_name= "Reason")
    officeHoursRef = models.ForeignKey('OfficeHours', verbose_name='Clinic Session Unavailable')
    dateBeg = models.DateField("Begin Date", db_index=True, auto_now=False)
    dateEnd = models.DateField("End Date", db_index=True, auto_now=False)

# deprecated 04/08/2013
class BlockResidentTypeCount(models.Model):
    organization = models.ForeignKey('BaseOrganization', verbose_name="Associated Organization")
    organizationYear = models.ForeignKey('OrganizationYear', verbose_name= "Academic Year")
    blockRef = models.ForeignKey('Block', verbose_name="Schedule Block")
    residentTypeRef = models.ForeignKey('ResidentType', verbose_name="PGY")
    minSession = models.IntegerField(verbose_name='Minimum Sessions/Week')
    maxSession = models.IntegerField(verbose_name='Maximum Sessions/Week')
    ptsSession = models.IntegerField(verbose_name='Total Sessions/Week')

WEEKNUM_CHOICES = (
    (1, 'Week 1'),
    (2, 'Week 2'),
    (3, 'Week 3'),
    (4, 'Week 4'),
    (5, 'Weeks 1 & 2'),
    (6, 'Weeks 3 & 4'),
    (7, 'All Weeks'),
)
class RotationSchedule(models.Model):
    organization = models.ForeignKey('BaseOrganization', db_index=True, verbose_name="Associated Organization")
    organizationYear = models.ForeignKey('OrganizationYear', db_index=True, verbose_name= "Academic Year")
    residentRef = models.ForeignKey('Resident', db_index=True, verbose_name='Resident')
    blockRef = models.ForeignKey('Block', db_index=True, verbose_name='Schedule Block')
    rotationRef = models.ForeignKey('Rotation', verbose_name='Rotation')
 #   weekNum = models.IntegerField(verbose_name='Week Number')
    weekNum = models.IntegerField(verbose_name='Week Number', db_index=True, choices=WEEKNUM_CHOICES)


SCHED_TYPE_CHOICES = (
('E', 'Established'),
('P', 'Potential'),
('F', 'Filled'),
('U', 'Unavailable'),
('O', 'Out of Office')
)
class ClinicScheduleType(models.Model):
    organization = models.ForeignKey('BaseOrganization', verbose_name="Associated Organization")
    organizationYear = models.ForeignKey('OrganizationYear', verbose_name= "Academic Year")
    scheduleType = models.CharField(max_length=1, choices=SCHED_TYPE_CHOICES, verbose_name='Schedule Type')
    scheduleTypeDescr = models.CharField(max_length=30, verbose_name='Schedule Type Description')
    def __unicode__(self):
        return unicode(self.scheduleType)


class ClinicAvailability(models.Model):
    organization = models.ForeignKey('BaseOrganization', db_index=True, verbose_name="Associated Organization")
    organizationYear = models.ForeignKey('OrganizationYear', db_index=True, verbose_name= "Academic Year")
    rotationRef = models.ForeignKey('Rotation', db_index=True, verbose_name='Rotation')
    officeHrsRef = models.ForeignKey('OfficeHours', verbose_name='Office Hour Session')
    residentTypeRef = models.ForeignKey('ResidentType', db_index=True, verbose_name='Resident Type')
    clinicScheduleTypeRef = models.ForeignKey('ClinicScheduleType', db_index=True, verbose_name='Clinic Schedule Type', null=True, blank=True)


class FacultyClinicHours(models.Model):
    organization = models.ForeignKey('BaseOrganization', db_index=True, verbose_name="Associated Organization")
    organizationYear = models.ForeignKey('OrganizationYear', db_index=True, verbose_name= "Academic Year")
    officeHrsRef = models.ForeignKey('OfficeHours', verbose_name='Office Hour Session')
    facultyRef = models.ForeignKey('Faculty')
    clinicScheduleTypeRef = models.ForeignKey('ClinicScheduleType', db_index=True, verbose_name='Clinic Schedule Type', null=True, blank=True)


class ClinicAvailabilityCount(models.Model):
    organization = models.ForeignKey('BaseOrganization', verbose_name="Associated Organization")
    organizationYear = models.ForeignKey('OrganizationYear', verbose_name= "Academic Year")
    rotationRef = models.ForeignKey('Rotation', verbose_name='Rotation')
    residentTypeRef = models.ForeignKey('ResidentType', verbose_name='Resident Type')
    weeklySessions = models.IntegerField('Weekly Sessions')


class RotationException(models.Model):
    organization = models.ForeignKey('BaseOrganization', verbose_name="Associated Organization")
    organizationYear = models.ForeignKey('OrganizationYear', verbose_name= "Academic Year")
    rotationRef = models.ForeignKey('Rotation')
    typeFRRef = models.ForeignKey('ResidentType')
    period = models.CharField(max_length=255)
    maxSession = models.IntegerField()


class RotationRuleType(models.Model):
    organization = models.ForeignKey('BaseOrganization', verbose_name="Associated Organization")
    organizationYear = models.ForeignKey('OrganizationYear', verbose_name= "Academic Year")
    rotationRuleTypeCode = models.CharField(max_length=1)
    rotationRuleTypeDescr = models.CharField(max_length=50)


class RotationRule(models.Model):
    organization = models.ForeignKey('BaseOrganization', verbose_name="Associated Organization")
    organizationYear = models.ForeignKey('OrganizationYear', verbose_name= "Academic Year")
    rotationRef = models.ForeignKey('Rotation')
    typeFRRef = models.ForeignKey('ResidentType')
    rotationRuleTypeRef = models.ForeignKey('RotationRuleType')
    # comparator is either another rotation, a set period, etc
    comparator = models.CharField(max_length=50)


class ClinicSchedule(models.Model):
    # Name
    organization = models.ForeignKey('BaseOrganization', db_index=True, verbose_name="Associated Organization")
    organizationYear = models.ForeignKey('OrganizationYear', db_index=True, verbose_name= "Academic Year")
    blockRef = models.ForeignKey('Block', db_index=True, verbose_name='Schedule Block')
    residentRef = models.ForeignKey('Resident', verbose_name='Resident')
    teamRef = models.ForeignKey('TeamType', verbose_name='Team')
    residentTypeRef = models.ForeignKey('ResidentType', verbose_name='Resident Type')
    rotationRef = models.ForeignKey('Rotation', verbose_name='Rotation')
    weekID = models.IntegerField(db_index=True)
    officeHoursRef=models.ForeignKey('OfficeHours', verbose_name='Office Hour Session')
    assignment = models.ForeignKey('ClinicScheduleType', verbose_name='Clinic Schedule Type')

class FacultyClinicSchedule(models.Model):
    # Name
    organization = models.ForeignKey('BaseOrganization', db_index=True, verbose_name="Associated Organization")
    organizationYear = models.ForeignKey('OrganizationYear', db_index=True, verbose_name= "Academic Year")
    blockRef = models.ForeignKey('Block', db_index=True, verbose_name='Schedule Block')
    facultyRef = models.ForeignKey('Faculty', verbose_name='Faculty')
    teamRef = models.ForeignKey('TeamType', verbose_name='Team')
    weekID = models.IntegerField(db_index=True)
    officeHoursRef=models.ForeignKey('OfficeHours', verbose_name='Office Hour Session')
    assignment = models.ForeignKey('ClinicScheduleType', verbose_name='Clinic Schedule Type')


ONOFF_CHOICES = (
    ('Y', 'Yes'),
    ('N', 'No')
)
class ClinicScheduleFinal(models.Model):
    organization = models.ForeignKey('BaseOrganization', verbose_name="Associated Organization")
    organizationYear = models.ForeignKey('OrganizationYear', verbose_name= "Academic Year")
    blockRef = models.ForeignKey('Block', verbose_name='Schedule Block')
    weekID = models.IntegerField()
    locked = models.CharField('Schedule Locked', max_length=1, choices=ONOFF_CHOICES)

WEEK_CHOICES = (
    ('1', 'Week 1'),
    ('2', 'Week 2'),
    ('3', 'Week 3'),
    ('4', 'Week 4'),
    ('5', 'All Weeks')
)
class BlockWeek(models.Model):
    organization = models.ForeignKey('BaseOrganization', verbose_name="Associated Organization")
    organizationYear = models.ForeignKey('OrganizationYear', verbose_name= "Academic Year")
    blockRef = models.ForeignKey('Block', verbose_name='Schedule Block')
    week = models.CharField('Week', max_length=1, choices=WEEK_CHOICES)

WEEK_CHOICES = (
    ('1', 'Week 1'),
    ('2', 'Week 2'),
    ('3', 'Week 3'),
    ('4', 'Week 4')
)
class ClinicAvailabilityBlockWeek(models.Model):
    organization = models.ForeignKey('BaseOrganization', verbose_name="Associated Organization")
    organizationYear = models.ForeignKey('OrganizationYear', verbose_name= "Academic Year")
    blockRef = models.ForeignKey('Block', verbose_name='Schedule Block')
    week = models.CharField('Week', max_length=1, choices=WEEK_CHOICES)


class ClinicScheduleWork(models.Model):
    organization = models.ForeignKey('BaseOrganization', db_index=True, verbose_name="Associated Organization")
    organizationYear = models.ForeignKey('OrganizationYear', db_index=True, verbose_name= "Academic Year")
    blockRef = models.ForeignKey('Block', db_index=True, verbose_name='Schedule Block')
    residentRef = models.ForeignKey('Resident', verbose_name='Resident')
    teamRef = models.ForeignKey('TeamType', verbose_name='Team')
    residentTypeRef = models.ForeignKey('ResidentType', verbose_name='Resident Type')
    rotationRef = models.ForeignKey('Rotation', verbose_name='Rotation')
    weekID = models.IntegerField(db_index=True)
    officeHoursRef=models.ForeignKey('OfficeHours', verbose_name='Office Hour Session')
    assignment = models.ForeignKey('ClinicScheduleType', verbose_name='Clinic Schedule Type')


ONOFF_CHOICES = (
    ('Y', 'Yes'),
    ('N', 'No')
)
class ClinicScheduleBlocked(models.Model):
    organization = models.ForeignKey('BaseOrganization', db_index=True, verbose_name="Associated Organization")
    organizationYear = models.ForeignKey('OrganizationYear', db_index=True, verbose_name= "Academic Year")
    blockRef = models.ForeignKey('Block', db_index=True, verbose_name='Schedule Block')
    residentRef = models.ForeignKey('Resident', verbose_name='Resident')
    teamRef = models.ForeignKey('TeamType', verbose_name='Team')
    residentTypeRef = models.ForeignKey('ResidentType', verbose_name='Resident Type')
    rotationRef = models.ForeignKey('Rotation', verbose_name='Rotation')
    weekID = models.IntegerField(db_index=True)
    officeHoursRef=models.ForeignKey('OfficeHours', verbose_name='Office Hour Session')
    blocked = models.CharField('Blocked for Assignment', max_length=1, choices=ONOFF_CHOICES)


class ResidentAvailableSesCountWork(models.Model):
    organization = models.ForeignKey('BaseOrganization', db_index=True, verbose_name="Associated Organization")
    organizationYear = models.ForeignKey('OrganizationYear', db_index=True, verbose_name= "Academic Year")
    residentRef = models.ForeignKey('Resident', verbose_name='Resident')
    blockRef = models.ForeignKey('Block', db_index=True, verbose_name='Schedule Block')
    weekID = models.IntegerField(db_index=True)
    availableSesCount = models.IntegerField()

class TeamWeekPeriodCountWork(models.Model):
    organization = models.ForeignKey('BaseOrganization', db_index=True, verbose_name="Associated Organization")
    organizationYear = models.ForeignKey('OrganizationYear',  db_index=True,verbose_name= "Academic Year")
    teamTypeRef = models.ForeignKey('TeamType', verbose_name="Assigned Team")
    officeHoursRef = models.ForeignKey('OfficeHours', verbose_name='Clinic Session Unavailable')
    blockRef = models.ForeignKey('Block', db_index=True, verbose_name='Schedule Block')
    weekID = models.IntegerField(db_index=True)
    teamTypeRunningCount = models.IntegerField()

class OfficeHoursCountWork(models.Model):
    organization = models.ForeignKey('BaseOrganization', db_index=True, verbose_name="Associated Organization")
    organizationYear = models.ForeignKey('OrganizationYear', db_index=True, verbose_name= "Academic Year")
    officeHoursRef = models.ForeignKey('OfficeHours', verbose_name='Clinic Session Unavailable')
    blockRef = models.ForeignKey('Block', db_index=True, verbose_name='Schedule Block')
    weekID = models.IntegerField(db_index=True)
    officeHoursRunningCount = models.IntegerField()
    officeHoursAssignmentCount = models.IntegerField()

ONOFF_CHOICES = (
    ('Y', 'Yes'),
    ('N', 'No')
)
class AvailableAssignmentWork(models.Model):
    organization = models.ForeignKey('BaseOrganization', db_index=True, verbose_name="Associated Organization")
    organizationYear = models.ForeignKey('OrganizationYear', db_index=True, verbose_name= "Academic Year")
    residentRef = models.ForeignKey('Resident', verbose_name='Resident')
    officeHoursRef = models.ForeignKey('OfficeHours', verbose_name='Clinic Session Unavailable')
    blockRef = models.ForeignKey('Block', db_index=True, verbose_name='Schedule Block')
    weekID = models.IntegerField(db_index=True)
    patientCount = models.IntegerField()
    scoringValue = models.IntegerField(db_index=True)
    available = models.CharField(max_length=1,db_index=True, choices=ONOFF_CHOICES)
