
'''
Created on Dec 4, 2012
Modified Jan 31, 2013 mmccaskey
    * converted to Py 2.7/Django 1.4
Modified Apr 08, 2013 mmccaskey
    * removed old unworking code and replaced with new
    * clinicSchedulerBuilder class
@author: mmccaskey
'''

import logging
import datetime
from datetime import timedelta

from models import DTO, Block, ClinicSchedule, Rotation, TeamType, OfficeHours, RotationSchedule, TeamWeekPeriodCountWork
from models import Resident, RotationException, StaffUnavailable, ResidentType, ClinicAvailability, BlockResidentTypeCount, ClinicScheduleType, \
    OrganizationYear, AvailableAssignmentWork, ResidentAvailableSesCountWork, OfficeHoursCountWork, ClinicScheduleWork, \
    BlockResidentType, ClinicAvailabilityCount, ClinicScheduleFinal, ClinicScheduleBlocked, FacultyClinicHours, FacultyClinicSchedule, \
    Faculty, FacultyUnavailable
from services import BlockService, RotationService, HolidayService, OfficeHoursService, ResidentService, UnavailableTimeService, GenFunc, BlockResidentCountService
from services import RotationScheduleService, ClinicAvailabilityService, RotationExceptionService, UserOrganization, UserOrganizationYear
from django.contrib.auth.models import User
from django.db.models import Min
from math import floor, ceil


######################## old code deprecated to utils_backup.py, MMcCaskey, April 2013 #################################
########################################################################################################################
################################# begin new code, MMcCaskey, March/April 2013 ##########################################
class ClinicScheduleBuilder():
    # global variables, built in to avoid hard coding for future releases and unnecessary variable passing

    def setOrganizationAndYear(self, inOrg, inOrgYear):
        ################################################################################################################
        # inOrg = Organization passed from calling view, inOrgYear = organizationYear passed from calling view
        # PURPOSE: set global class variables of Org and OrgYear which are stored in session variables in calling view
        # FIRST:  Set Org
        # NEXT:  Set Org Year
        # FINAL: Calculate Number of Office Hours for this org and org year, added to prevent hard coding for future releases
        ################################################################################################################
        self.globalOrg = inOrg
        self.globalOrgYear = inOrgYear
        self.officeHoursCount = OfficeHours.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear).count()
        self.unavailableTypeId = ClinicScheduleType.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, scheduleType__exact='U').id
        self.establishedTypeId = ClinicScheduleType.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, scheduleType__exact='E').id
        self.potentialTypeId = ClinicScheduleType.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, scheduleType__exact='P').id
        self.outOfOfficeTypeId = ClinicScheduleType.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, scheduleType__exact='O').id
        self.filledTypeId = ClinicScheduleType.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, scheduleType__exact='F').id
        self.loopBreaker = 0
        self.assignmentScoringConstant = 100
        self.facultyPatientsPerSession = 10


    def setTargetValuesAndTolerances(self, maxWeekSessions):
        ################################################################################################################
        # inOrg = Organization passed from calling view, inOrgYear = organizationYear passed from calling view
        # PURPOSE: set global class variables of Org and OrgYear which are stored in session variables in calling view
        # FIRST:  Set Org
        # NEXT:  Set Org Year
        # FINAL: Calculate Number of Office Hours for this org and org year, added to prevent hard coding for future releases
        ################################################################################################################
        teamCount = TeamType.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear).count()
        self.periodPatientTarget = floor(maxWeekSessions/self.officeHoursCount)
        self.periodTeamTarget = floor(self.periodPatientTarget/teamCount)
        self.remainingWeekSessions = maxWeekSessions
        # todo set these as variable per organization
        periodPatientTolerance = 0.50
        periodTeamTolerance = 100.00
        self.periodPatientFloor = self.periodPatientTarget - floor(self.periodPatientTarget * periodPatientTolerance)
        if self.periodPatientFloor < 0:
            self.periodPatientFloor = 0
        self.periodPatientCeiling = self.periodPatientTarget + ceil(self.periodPatientTarget * periodPatientTolerance)
        self.teamPatientFloor = self.periodTeamTarget - floor(self.periodTeamTarget * periodTeamTolerance)
        if self.teamPatientFloor < 0:
            self.teamPatientFloor = 0
        self.teamPatientCeiling = self.periodTeamTarget + ceil(self.periodTeamTarget * periodTeamTolerance)

    def checkAndDeleteFromRecord(self, b, w):
        # b = block, w = week
        # PURPOSE: create initial work record of ALL possible sessions without logic for established, unavailable, etc
        # FIRST:  Delete any existing work record values by Org and OrgYear
        # NEXT:  Loop through all residents
        # FINAL: Loop through all office hours and create a record for each resident in each office hour spot
        # No return value; data is saved to database
        intW = int(w)
        lockedRecordCount = ClinicScheduleFinal.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=b, weekID__exact=intW).count()
        if lockedRecordCount == 0:
            # then the clinic schedule is not locked, delete.
            dClinicSchedule = ClinicSchedule.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=b, weekID__exact=intW).delete()
            dFacultyClinicSchedule = FacultyClinicSchedule.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=b, weekID__exact=intW).delete()
            return True
        else:
            # todo add message that clinic schedule is locked and cannot be processed
            return False


    def determineAvailableSessions(self, b, w):
        ################################################################################################################
        # b = block, w = week
        # PURPOSE: create initial work record of ALL possible sessions without logic for established, unavailable, etc
        # FIRST:  Delete any existing work record values by Org and OrgYear
        # NEXT:  Loop through all residents
        # FINAL: Loop through all office hours and create a record for each resident in each office hour spot
        # No return value; data is saved to database
        ################################################################################################################
        blockInfo = Block.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, id__exact=b)
        setBlockId = blockInfo.id
        blockStartDate = blockInfo.sDateBeg
        intW = int(w)
        weekMuliplier = (intW - 1) * 7
        weekStartDate = blockStartDate + timedelta(days=weekMuliplier)
        weekEndDate = weekStartDate + timedelta(days=7)
        dAvailableAssignmentWork = AvailableAssignmentWork.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=setBlockId, weekID__exact=intW).delete()
        residentSet = Resident.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear)
        # todo migrate to block of code to set for self
        for resident in residentSet:
            officeHoursSet = OfficeHours.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear)
            for officeHour in officeHoursSet:
                aa = AvailableAssignmentWork()
                aa.organization_id = self.globalOrg
                aa.organizationYear_id = self.globalOrgYear
                aa.residentRef_id = resident.id
                aa.officeHoursRef_id = officeHour.id
                aa.blockRef_id = setBlockId
                aa.weekID = intW
                aa.patientCount = BlockResidentType.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=setBlockId, residentTypeRef__exact=resident.residentYear_id).patientSessions
                aa.scoringValue = 0
                aa.available = 'N'
                aa.save()
            rRotations = RotationSchedule.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=setBlockId, residentRef__exact = resident.id)
            for rRotation in rRotations:
                if rRotation.weekNum == 7:
                    currRot = rRotation.rotationRef_id
                    break
                elif rRotation.weekNum == 6 and intW in (3,4):
                    currRot = rRotation.rotationRef_id
                    break
                elif rRotation.weekNum == 5 and intW in (1,2):
                    currRot = rRotation.rotationRef_id
                    break
                elif rRotation.weekNum == intW:
                    currRot = rRotation.rotationRef_id
                    break
                else:
                    # todo write error message
                    currRot = 0
                    # end check current rotation

            if currRot != 0:
                rPossibleSessions = ClinicAvailability.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear,residentTypeRef__exact=resident.residentYear.id, rotationRef__exact=currRot, clinicScheduleTypeRef__in=[self.establishedTypeId, self.potentialTypeId])
                for rPossibleSession in rPossibleSessions:
                    rPossibleAssignment = AvailableAssignmentWork.objects.get(organization__exact=self.globalOrg, organizationYear__exact=self.globalOrgYear,residentRef__exact = resident.id, officeHoursRef__exact = rPossibleSession.officeHrsRef, blockRef__exact = b, weekID__exact = intW)
                    rPossibleAssignment.available = 'Y'
                    rPossibleAssignment.scoringValue = 0
                    rPossibleAssignment.patientCount = BlockResidentType.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=setBlockId, residentTypeRef__exact=resident.residentYear_id).patientSessions
                    rPossibleAssignment.save()

                rUnavailableSessions = ClinicAvailability.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear,rotationRef_id__exact=currRot, residentTypeRef_id__exact=resident.residentYear.id, clinicScheduleTypeRef_id__exact=self.unavailableTypeId)
                for rUnavailableSession in rUnavailableSessions:
                    rUnavailableAssignment = AvailableAssignmentWork.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear,residentRef__exact = resident.id, officeHoursRef__exact = rUnavailableSession.officeHrsRef, blockRef__exact = setBlockId, weekID__exact = intW)
                    rUnavailableAssignment.available = 'N'
                    rUnavailableAssignment.scoringValue = 0
                    rUnavailableAssignment.patientCount = 0
                    rUnavailableAssignment.save()

                d = weekStartDate
                dDelta = datetime.timedelta(days=1)
                while d <= weekEndDate:
                    rPtoSessions = StaffUnavailable.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear,residentRef__exact=resident.id, dateBeg__lte=d, dateEnd__gte=d)
                    for rPtoSession in rPtoSessions:
                        rUnavailableAssignment = AvailableAssignmentWork.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear,residentRef__exact = resident.id, officeHoursRef__exact = rPtoSession.officeHoursRef, blockRef__exact = setBlockId, weekID__exact = intW)
                        rUnavailableAssignment.available = 'N'
                        rUnavailableAssignment.scoringValue = 0
                        rUnavailableAssignment.patientCount = 0
                        rUnavailableAssignment.save()
                        csw = ClinicScheduleWork()
                        csw.organization_id = self.globalOrg
                        csw.organizationYear_id = self.globalOrgYear
                        csw.blockRef_id = setBlockId
                        csw.residentRef_id = resident.id
                        csw.teamRef_id = resTeam
                        csw.residentTypeRef_id = resYear
                        csw.rotationRef_id = currRot
                        csw.weekID = intW
                        csw.officeHoursRef = rPtoSession.officeHoursRef
                        csw.assignment_id = self.outOfOfficeTypeId
                        csw.blocked = 'N'
                        csw.save()
                    d += dDelta

        # todo add Holiday logic for both Residents and Faculty
        d = weekStartDate
        dDelta = datetime.timedelta(days=1)
        while d <= weekEndDate:
            rHolidayDates = Holiday.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, sHolidayDate__exact=d)
            for rHolidayDate in rHolidayDates:
                rUnavailableAssignment = AvailableAssignmentWork.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact = setBlockId, weekID__exact = intW)
                rUnavailableAssignment.available = 'N'
                rUnavailableAssignment.scoringValue = 0
                rUnavailableAssignment.patientCount = 0
                rUnavailableAssignment.save()
                dayOfWeek = d.strftime("%a")
                if dayOfWeek == "Mon":
                    ohsCriteria = "M"
                elif dayOfWeek == "Tue":
                    ohsCriteria = "T"
                elif dayOfWeek == "Wed":
                    ohsCriteria = "W"
                elif dayOfWeek == "Thu":
                    ohsCriteria = "H"
                elif dayOfWeek == "Fri":
                    ohsCriteria = "F"
                elif dayOfWeek == "Sat":
                    ohsCriteria = "S"
                else:
                    ohsCriteria = "U"

                officeHoursSet = OfficeHours.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, weekday__exact=ohsCriteria)
                for officeHour in officeHoursSet:
                    residentSet = Resident.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear)
                    # todo migrate to block of code to set for self
                    for resident in residentSet:
                        csw = ClinicScheduleWork()
                        csw.organization_id = self.globalOrg
                        csw.organizationYear_id = self.globalOrgYear
                        csw.blockRef_id = setBlockId
                        csw.residentRef_id = resident.id
                        csw.teamRef_id = resTeam
                        csw.residentTypeRef_id = resYear
                        csw.rotationRef_id = currRot
                        csw.weekID = intW
                        csw.officeHoursRef = rPtoSession.officeHoursRef
                        csw.assignment_id = self.outOfOfficeTypeId
                        csw.blocked = 'N'
                        csw.save()
            d += dDelta

    def determineMaxThroughput(self, b, w):
        ################################################################################################################
        # b = block, w = week
        # PURPOSE: determine max number of patients possible for week
        # FIRST: find the lessor of available sessions (not U or PTO) or max number of sessions for each resident for this week
        # NEXT:  multiply that number by the total number of patient sessions that each resident can perform based on PGY
        # FINAL: the sum of this value is the maximum number of possible patient throughput, return this value to main
        ################################################################################################################
        blockInfo = Block.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, id__exact=b)
        blockStartDate = blockInfo.sDateBeg
        intW = int(w)
        weekMuliplier = (intW - 1) * 7
        weekStartDate = blockStartDate + timedelta(days=weekMuliplier)
        weekEndDate = weekStartDate + timedelta(days=7)
        maxThroughput = 0
        residentSet = Resident.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear)
        for resident in residentSet:
            rPtoSessionCount = 0
            rPatientPerSession = BlockResidentType.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=b, residentTypeRef = resident.residentYear_id).patientSessions
            rRotations = RotationSchedule.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=b, residentRef__exact = resident.id)
            for rRotation in rRotations:
                if rRotation.weekNum == 7:
                    currRot = rRotation.rotationRef_id
                    break
                elif rRotation.weekNum == 6 and intW in (3,4):
                    currRot = rRotation.rotationRef_id
                    break
                elif rRotation.weekNum == 5 and intW in (1,2):
                    currRot = rRotation.rotationRef_id
                    break
                elif rRotation.weekNum == intW:
                    currRot = rRotation.rotationRef_id
                    break
                else:
                    # todo write error message
                    currRot = rRotation.rotationRef_id
                # end check current rotation
            rMaxSessions = ClinicAvailabilityCount.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, rotationRef__exact=currRot, residentTypeRef = resident.residentYear_id).weeklySessions
            rUnavailableSessions = ClinicAvailability.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear,rotationRef__exact=currRot, residentTypeRef__exact=resident.residentYear, clinicScheduleTypeRef__exact=self.unavailableTypeId).count()
            d = weekStartDate
            dDelta = datetime.timedelta(days=1)
            while d <= weekEndDate:
                rPtoSessionCountInc = StaffUnavailable.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear,residentRef__exact=resident.id, dateBeg__lte=d, dateEnd__gte=d).count()
                rPtoSessionCount = rPtoSessionCount + rPtoSessionCountInc
                d += dDelta
            totalAvailable = self.officeHoursCount - (rPtoSessionCount + rUnavailableSessions)
            if totalAvailable < 0:
                totalAvailable = 0
            if totalAvailable < rMaxSessions:
                rThroughPut = totalAvailable * rPatientPerSession
            else:
                rThroughPut = rMaxSessions * rPatientPerSession
            maxThroughput = maxThroughput + rThroughPut
            # end resident looping to get MaxThroughput value
        facultySet = Faculty.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear)
        for faculty in facultySet:
            fPtoSessionCount = 0
            fPatientPerSession = self.facultyPatientsPerSession
            fMaxSessions = FacultyClinicHours.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, facultyRef__exact=faculty.id, clinicScheduleTypeRef__exact=self.establishedTypeId).count()
            fUnavailableSessions = FacultyClinicHours.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, clinicScheduleTypeRef__exact=self.unavailableTypeId).count()
            d = weekStartDate
            dDelta = datetime.timedelta(days=1)
            while d <= weekEndDate:
                fPtoSessionCountInc = FacultyUnavailable.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear,facultyRef__exact=faculty.id, dateBeg__lte=d, dateEnd__gte=d).count()
                fPtoSessionCount = fPtoSessionCount + fPtoSessionCountInc
                if fPtoSessionCountInc > 0:
                    fPtoSessionSet = FacultyUnavailable.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear,facultyRef__exact=faculty.id, dateBeg__lte=d, dateEnd__gte=d)
                    for fPtoSession in fPtoSessionSet:
                        fcs = FacultyClinicSchedule()
                        fcs.organization_id = self.globalOrg
                        fcs.organizationYear_id = self.globalOrgYear
                        fcs.blockRef_id = setBlockId
                        fcs.facultyRef_id = fPtoSession.facultyRef.id
                        fcs.teamRef_id = fFacultySession.facultyRef.facultyTeam.id
                        fcs.weekID = intW
                        fcs.officeHoursRef = fPtoSession.officeHrsRef
                        fcs.assignment_id = self.outOfOfficeTypeId
                        fcs.save()
                d += dDelta
            totalAvailable = self.officeHoursCount - (fPtoSessionCount + fUnavailableSessions)
            if totalAvailable < 0:
                totalAvailable = 0
            if totalAvailable < fMaxSessions:
                fThroughPut = totalAvailable * fPatientPerSession
            else:
                fThroughPut = fMaxSessions * fPatientPerSession
            maxThroughput = maxThroughput + fThroughPut
            # end faculty looping to get MaxThroughput value
        return maxThroughput

    def processEstablishedUpdateCounts(self, b, w):
        ################################################################################################################
        # b = block, w = week
        # PURPOSE: Established clinic sessions are immutable, we must set them first and update our counts after
        # FIRST:
        # NEXT:
        # FINAL:
        ################################################################################################################
        blockInfo = Block.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, id__exact=b)
        setBlockId = blockInfo.id
        intW = int(w)
        rRotations = RotationSchedule.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=b)
        for rRotation in rRotations:
            if rRotation.weekNum == 7:
                currRot = rRotation.rotationRef_id
            elif rRotation.weekNum == 6 and intW in (3,4):
                currRot = rRotation.rotationRef_id
            elif rRotation.weekNum == 5 and intW in (1,2):
                currRot = rRotation.rotationRef_id
            elif rRotation.weekNum == intW:
                currRot = rRotation.rotationRef_id
            else:
                # todo write error message
                continue
                # end check current rotation
            rEstablishedSessions = ClinicAvailability.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear,residentTypeRef__exact=rRotation.residentRef.residentYear, rotationRef__exact=currRot, clinicScheduleTypeRef__exact=self.establishedTypeId)
            # todo ask docs about Established for Inpatient Chief Resident can this override the max number of sessions per week?
            # todo what if resident or doctor is on PTO for established session...
            for rEstablishedSession in rEstablishedSessions:
                # get resident team and PGY
                resTeam = Resident.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, id__exact=rRotation.residentRef_id).residentTeam.id
                resYear = Resident.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, id__exact=rRotation.residentRef_id).residentYear.id
                # create Clinic Schedule Work Record
                cswInitCount = ClinicScheduleWork.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=setBlockId, weekID__exact=intW, residentRef__exact=rRotation.residentRef_id, officeHoursRef__exact=rEstablishedSession.officeHrsRef).count()
                if cswInitCount == 0:
                    csw = ClinicScheduleWork()
                    csw.organization_id = self.globalOrg
                    csw.organizationYear_id = self.globalOrgYear
                    csw.blockRef_id = setBlockId
                    csw.residentRef_id = rRotation.residentRef_id
                    csw.teamRef_id = resTeam
                    csw.residentTypeRef_id = resYear
                    csw.rotationRef_id = currRot
                    csw.weekID = intW
                    csw.officeHoursRef = rEstablishedSession.officeHrsRef
                    csw.assignment_id = self.establishedTypeId
                    csw.blocked = 'N'
                    csw.save()
                    # update counts
                    self.UpdateTeamWorkingCounts(b, w, rEstablishedSession.officeHrsRef, resTeam, resYear)
                    self.UpdatePeriodWorkingCounts(b, w, rEstablishedSession.officeHrsRef, resYear)
                    self.UpdateResidentWorkingCounts(b, w, rRotation.residentRef_id)
                    self.UpdateRemainingSessionCount(b, resYear)
                    # update available work record
                    rEstablishedAssignment = AvailableAssignmentWork.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear,residentRef__exact = rRotation.residentRef_id, officeHoursRef__exact = rEstablishedSession.officeHrsRef, blockRef__exact = setBlockId, weekID__exact = intW)
                    rEstablishedAssignment.available = 'N'
                    rEstablishedAssignment.scoringValue = 0
                    rEstablishedAssignment.save()
        fFacultySessions = FacultyClinicHours.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, clinicScheduleTypeRef__exact=self.establishedTypeId)
        for fFacultySession in fFacultySessions:
            fcsInitCount = FacultyClinicSchedule.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=b, weekID__exact=w, facultyRef__exact=fFacultySession.facultyRef.id, officeHoursRef__exact=fFacultySession.officeHrsRef).count()
            if fcsInitCount == 0:
                fcs = FacultyClinicSchedule()
                fcs.organization_id = self.globalOrg
                fcs.organizationYear_id = self.globalOrgYear
                fcs.blockRef_id = setBlockId
                fcs.facultyRef_id = fFacultySession.facultyRef.id
                fcs.teamRef_id = fFacultySession.facultyRef.facultyTeam.id
                fcs.weekID = intW
                fcs.officeHoursRef = fFacultySession.officeHrsRef
                fcs.assignment_id = self.establishedTypeId
                fcs.save()
                # update counts
                self.UpdateFacultyTeamWorkingCounts(b, w, rEstablishedSession.officeHrsRef, fFacultySession.facultyRef.facultyTeam)
                self.UpdateFacultyPeriodWorkingCounts(b, w, rEstablishedSession.officeHrsRef)
                self.UpdateFacultyRemainingSessionCount(b)


    def UpdateTeamWorkingCounts(self, b, w, o, t, y):
        ################################################################################################################
        # b = block, w = week, o = office hours, t = team, y = PGY
        # PURPOSE: Established clinic sessions are immutable, we must set them first and update our counts after
        # FIRST:
        # NEXT:
        # FINAL:
        ################################################################################################################
        twpcw = TeamWeekPeriodCountWork.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, teamTypeRef__exact= t, officeHoursRef__exact = o, blockRef__exact = b, weekID__exact = w)
        origCount = twpcw.teamTypeRunningCount
        updateValue = BlockResidentType.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=b, residentTypeRef_id__exact = y).patientSessions
        twpcw.teamTypeRunningCount = origCount + updateValue
        twpcw.save()

    def UpdateFacultyTeamWorkingCounts(self, b, w, o, t):
        ################################################################################################################
        # b = block, w = week, o = office hours, t = team, y = PGY
        # PURPOSE: Established clinic sessions are immutable, we must set them first and update our counts after
        # FIRST:
        # NEXT:
        # FINAL:
        ################################################################################################################
        twpcw = TeamWeekPeriodCountWork.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, teamTypeRef__exact= t, officeHoursRef__exact = o, blockRef__exact = b, weekID__exact = w)
        origCount = twpcw.teamTypeRunningCount
        updateValue = self.facultyPatientsPerSession
        twpcw.teamTypeRunningCount = origCount + updateValue
        twpcw.save()

    def UpdatePeriodWorkingCounts(self, b, w, o, y):
        ################################################################################################################
        # b = block, w = week, o = office hours,  y = PGY
        # PURPOSE: Established clinic sessions are immutable, we must set them first and update our counts after
        # FIRST:
        # NEXT:
        # FINAL:
        ################################################################################################################
        ohcw = OfficeHoursCountWork.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, officeHoursRef__exact = o, blockRef__exact = b, weekID__exact = w)
        origCount = ohcw.officeHoursRunningCount
        updateValue = BlockResidentType.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=b, residentTypeRef_id__exact = y).patientSessions
        ohcw.officeHoursRunningCount = origCount + updateValue
        ohcw.officeHoursAssignmentCount = ohcw.officeHoursAssignmentCount + 1
        ohcw.save()

    def UpdateFacultyPeriodWorkingCounts(self, b, w, o):
        ################################################################################################################
        # b = block, w = week, o = office hours,  y = PGY
        # PURPOSE: Established clinic sessions are immutable, we must set them first and update our counts after
        # FIRST:
        # NEXT:
        # FINAL:
        ################################################################################################################
        ohcw = OfficeHoursCountWork.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, officeHoursRef__exact = o, blockRef__exact = b, weekID__exact = w)
        origCount = ohcw.officeHoursRunningCount
        updateValue = self.facultyPatientsPerSession
        ohcw.officeHoursRunningCount = origCount + updateValue
        ohcw.officeHoursAssignmentCount = ohcw.officeHoursAssignmentCount + 1
        ohcw.save()

    def UpdateResidentWorkingCounts(self, b, w, r):
        ################################################################################################################
        # b = block, w = week, r = resident
        # PURPOSE: Established clinic sessions are immutable, we must set them first and update our counts after
        # FIRST:
        # NEXT:
        # FINAL:
        ################################################################################################################
        rascw = ResidentAvailableSesCountWork.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, residentRef__exact = r,  blockRef__exact = b, weekID__exact = w)
        blockInfo = Block.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, id__exact=b)
        setBlockId = blockInfo.id
        intW = int(w)
        origCount = rascw.availableSesCount
        if origCount == 0:
            availableAssignmentWorkSet = AvailableAssignmentWork.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, residentRef__exact=r, blockRef__exact=setBlockId, weekID__exact=intW, available__exact='Y')
            for availableAssignmentWork in availableAssignmentWorkSet:
                availableAssignmentWork.available = 'N'
                availableAssignmentWork.save()
        if rascw.availableSesCount > 0:
            rascw.availableSesCount = origCount - 1
        else:
            rascw.availableSesCount = 0
        rascw.save()

    def UpdateRemainingSessionCount(self, b, y):
        ################################################################################################################
        # b = block,  o = office Hours, y = PGY
        # PURPOSE: Established clinic sessions are immutable, we must set them first and update our counts after
        # FIRST:
        # NEXT:
        # FINAL:
        ################################################################################################################
        updateValue = BlockResidentType.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=b, residentTypeRef_id = y).patientSessions
        self.remainingWeekSessions = self.remainingWeekSessions - updateValue

    def UpdateFacultyRemainingSessionCount(self, b):
        ################################################################################################################
        # b = block,  o = office Hours, y = PGY
        # PURPOSE: Established clinic sessions are immutable, we must set them first and update our counts after
        # FIRST:
        # NEXT:
        # FINAL:
        ################################################################################################################
        updateValue = self.facultyPatientsPerSession
        self.remainingWeekSessions = self.remainingWeekSessions - updateValue


    def InitializeWorkCounts(self, b, w):
        ################################################################################################################
        # b = block, w = week
        # PURPOSE: Established clinic sessions are immutable, we must set them first and update our counts after
        # FIRST:
        # NEXT:
        # FINAL:
        ################################################################################################################
        blockInfo = Block.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, id__exact=b)
        setBlockId = blockInfo.id
        intW = int(w)
        dOfficeHoursCountWork = OfficeHoursCountWork.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=setBlockId, weekID__exact=intW).delete()
        dTeamWeekPeriodCountWork = TeamWeekPeriodCountWork.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=setBlockId, weekID__exact=intW).delete()
        dResidentAvailableSesCountWork = ResidentAvailableSesCountWork.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=setBlockId, weekID__exact=intW).delete()
        dClinicScheduleWork = ClinicScheduleWork.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=setBlockId, weekID__exact=intW).delete()
        dClinicScheduleBlocked = ClinicScheduleBlocked.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=setBlockId, weekID__exact=intW).delete()
        officeHoursSet = OfficeHours.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear)
        for officeHour in officeHoursSet:
            ohcw = OfficeHoursCountWork()
            ohcw.organization_id = self.globalOrg
            ohcw.organizationYear_id = self.globalOrgYear
            ohcw.officeHoursRef_id = officeHour.id
            ohcw.blockRef_id = setBlockId
            ohcw.weekID = intW
            ohcw.officeHoursRunningCount = 0
            ohcw.officeHoursAssignmentCount = 0
            ohcw.save()
            #  for each office hour session set a running counter for team patients for balancing
            teamTypes = TeamType.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear)
            for teamType in teamTypes:
                twpcw = TeamWeekPeriodCountWork()
                twpcw.organization_id = self.globalOrg
                twpcw.organizationYear_id = self.globalOrgYear
                twpcw.teamTypeRef_id = teamType.id
                twpcw.officeHoursRef_id = officeHour.id
                twpcw.blockRef_id = setBlockId
                twpcw.weekID = intW
                twpcw.teamTypeRunningCount = 0
                twpcw.save()
        residentSet = Resident.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear)
        for resident in residentSet:
            resRot = 0
            rascw = ResidentAvailableSesCountWork()
            rascw.organization_id = self.globalOrg
            rascw.organizationYear_id = self.globalOrgYear
            rascw.residentRef_id = resident.id
            rascw.blockRef_id = setBlockId
            rascw.weekID = intW
            rRotations = RotationSchedule.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=setBlockId, residentRef__exact= resident.id)
            for rRotation in rRotations:
                if rRotation.weekNum == 7:
                    resRot = rRotation.rotationRef_id
                    break
                elif rRotation.weekNum == 6 and intW in (3,4):
                    resRot = rRotation.rotationRef_id
                    break
                elif rRotation.weekNum == 5 and intW in (1,2):
                    resRot = rRotation.rotationRef_id
                    break
                elif rRotation.weekNum == intW:
                    resRot = rRotation.rotationRef_id
                    break
                else:
                    # todo write error message
                    continue
                    # end check current rotation
            if resRot != 0:
                rascw.availableSesCount = ClinicAvailabilityCount.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, rotationRef__exact=resRot, residentTypeRef = resident.residentYear_id).weeklySessions
            else:
                rascw.availableSesCount = 0
            rascw.save()

    def calculateScoringRoutine(self, b, w):
        ################################################################################################################
        # Main programming section
        # FIRST: call method to setup initial available sessions
        # SECOND:  call method to determine our maximum Patients Per week possible
        # THIRD:
        # FINAL:
        ################################################################################################################
        blockInfo = Block.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, id__exact=b)
        setBlockId = blockInfo.id
        intW = int(w)
        self.maxScoringValue = 0
        availableAssignmentWorkSet = AvailableAssignmentWork.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=setBlockId, weekID__exact=intW, available__exact='Y')
        for availableAssignmentWork in availableAssignmentWorkSet:
            ras = ResidentAvailableSesCountWork.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, residentRef__exact = availableAssignmentWork.residentRef,  blockRef__exact = b, weekID__exact = intW).availableSesCount
            tas = self.periodTeamTarget - TeamWeekPeriodCountWork.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear,teamTypeRef__exact=availableAssignmentWork.residentRef.residentTeam, blockRef__exact=setBlockId, weekID__exact=intW, officeHoursRef__exact=availableAssignmentWork.officeHoursRef).teamTypeRunningCount
            oas = self.periodPatientTarget - OfficeHoursCountWork.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=setBlockId, weekID__exact=intW, officeHoursRef__exact=availableAssignmentWork.officeHoursRef).officeHoursRunningCount
            oas2 = self.assignmentScoringConstant - OfficeHoursCountWork.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=setBlockId, weekID__exact=intW, officeHoursRef__exact=availableAssignmentWork.officeHoursRef).officeHoursAssignmentCount
            score = ras + tas + oas + oas2
            availableAssignmentWork.scoringValue = score
            availableAssignmentWork.save()
            if availableAssignmentWork.scoringValue > self.maxScoringValue:
                self.maxScoringValue = availableAssignmentWork.scoringValue
        return self.maxScoringValue

    def checkTolerances(self, assignment, b, w):
        ################################################################################################################
        # Main programming section
        # FIRST: call method to setup initial available sessions
        # SECOND:  call method to determine our maximum Patients Per week possible
        # THIRD:
        # FINAL:
        ################################################################################################################
        setCount = assignment.patientCount
        blockInfo = Block.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, id__exact=b)
        setBlockId = blockInfo.id
        intW = int(w)
        ras = ResidentAvailableSesCountWork.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, residentRef__exact = assignment.residentRef,  blockRef__exact = setBlockId, weekID__exact = intW).availableSesCount
        tas = TeamWeekPeriodCountWork.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear,teamTypeRef__exact=assignment.residentRef.residentTeam, blockRef__exact=setBlockId, weekID__exact=intW, officeHoursRef__exact=assignment.officeHoursRef).teamTypeRunningCount
        oas = OfficeHoursCountWork.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=setBlockId, weekID__exact=intW, officeHoursRef__exact=assignment.officeHoursRef).officeHoursRunningCount
        newtas = tas + setCount
        newoas = oas + setCount
        if newtas > self.teamPatientCeiling or newoas > self.periodPatientCeiling or ras == 0:
            return False
        else:
            return True

    def buildFilledClinicScheduleWork(self, assignment, b, w):
        ################################################################################################################
        # Main programming section
        # FIRST: call method to setup initial available sessions
        # SECOND:  call method to determine our maximum Patients Per week possible
        # THIRD:
        # FINAL:
        ################################################################################################################
        blockInfo = Block.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, id__exact=b)
        setBlockId = blockInfo.id
        intW = int(w)
        currRot = 0
        # get resident team and PGY
        resTeam = Resident.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, id__exact=assignment.residentRef_id).residentTeam.id
        resYear = Resident.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, id__exact=assignment.residentRef_id).residentYear.id
        rRotations = RotationSchedule.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=b, residentRef_id = assignment.residentRef_id)
        for rRotation in rRotations:
            if rRotation.weekNum == 7:
                currRot = rRotation.rotationRef_id
                break
            elif rRotation.weekNum == 6 and intW in (3,4):
                currRot = rRotation.rotationRef_id
                break
            elif rRotation.weekNum == 5 and intW in (1,2):
                currRot = rRotation.rotationRef_id
                break
            elif rRotation.weekNum == intW:
                currRot = rRotation.rotationRef_id
                break
            else:
                # todo write error message
                currRot = 0
                continue
                # end check current rotation
        # create Clinic Schedule Work Record
        if currRot != 0:
            csw = ClinicScheduleWork()
            csw.organization_id = self.globalOrg
            csw.organizationYear_id = self.globalOrgYear
            csw.blockRef_id = setBlockId
            csw.residentRef_id = assignment.residentRef_id
            csw.teamRef_id = resTeam
            csw.residentTypeRef_id = resYear
            csw.rotationRef_id = currRot
            csw.weekID = intW
            csw.officeHoursRef = assignment.officeHoursRef
            csw.assignment_id = self.filledTypeId
            #csw.blocked = 'N'
            csw.save()
            # update counts
            self.UpdateTeamWorkingCounts(b, w, assignment.officeHoursRef, resTeam, resYear)
            self.UpdatePeriodWorkingCounts(b, w, assignment.officeHoursRef, resYear)
            self.UpdateResidentWorkingCounts(b, w, assignment.residentRef_id)
            self.UpdateRemainingSessionCount(b, resYear)
            # update available work record
            rFilledAssignment = AvailableAssignmentWork.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear,residentRef__exact = assignment.residentRef_id, officeHoursRef__exact = assignment.officeHoursRef, blockRef__exact = setBlockId, weekID__exact = intW)
            rFilledAssignment.available = 'N'
            rFilledAssignment.scoringValue = 0
            rFilledAssignment.save()

    def buildBlockedClinicSchedule(self, assignment, b, w):
        ################################################################################################################
        # Main programming section
        # FIRST: call method to setup initial available sessions
        # SECOND:  call method to determine our maximum Patients Per week possible
        # THIRD:
        # FINAL:
        ################################################################################################################
        blockInfo = Block.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, id__exact=b)
        setBlockId = blockInfo.id
        intW = int(w)
        currRot = 0
        # get resident team and PGY
        resTeam = Resident.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, id__exact=assignment.residentRef_id).residentTeam.id
        resYear = Resident.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, id__exact=assignment.residentRef_id).residentYear.id
        rRotations = RotationSchedule.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=b, residentRef_id = assignment.residentRef_id)
        for rRotation in rRotations:
            if rRotation.weekNum == 7:
                currRot = rRotation.rotationRef_id
                break
            elif rRotation.weekNum == 6 and intW in (3,4):
                currRot = rRotation.rotationRef_id
                break
            elif rRotation.weekNum == 5 and intW in (1,2):
                currRot = rRotation.rotationRef_id
                break
            elif rRotation.weekNum == intW:
                currRot = rRotation.rotationRef_id
                break
            else:
                # todo write error message
                continue
                # end check current rotation
        # create Clinic Schedule Blocked Record
        if currRot != 0:
            csb = ClinicScheduleBlocked()
            csb.organization_id = self.globalOrg
            csb.organizationYear_id = self.globalOrgYear
            csb.blockRef_id = setBlockId
            csb.residentRef_id = assignment.residentRef_id
            csb.teamRef_id = resTeam
            csb.residentTypeRef_id = resYear
            csb.rotationRef_id = currRot
            csb.weekID = intW
            csb.officeHoursRef = assignment.officeHoursRef
            csb.blocked = 'Y'
            csb.save()
        rBlockedAssignment = AvailableAssignmentWork.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear,residentRef__exact = assignment.residentRef_id, officeHoursRef__exact = assignment.officeHoursRef, blockRef__exact = setBlockId, weekID__exact = intW)
        rBlockedAssignment.available = 'N'
        rBlockedAssignment.scoringValue = 0
        rBlockedAssignment.save()

    def writeToClinicSchedule(self, b, w):
        ################################################################################################################
        # Main programming section
        # FIRST: call method to setup initial available sessions
        # SECOND:  call method to determine our maximum Patients Per week possible
        # THIRD:
        # FINAL:
        ################################################################################################################
        blockInfo = Block.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, id__exact=b)
        setBlockId = blockInfo.id
        intW = int(w)
        clinicScheduleWorkSet = ClinicScheduleWork.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=setBlockId, weekID__exact=intW)
        for clinicScheduleWork in clinicScheduleWorkSet:
            cs = ClinicSchedule()
            cs.organization_id = clinicScheduleWork.organization_id
            cs.organizationYear_id = clinicScheduleWork.organizationYear_id
            cs.blockRef_id = clinicScheduleWork.blockRef_id
            cs.residentRef_id = clinicScheduleWork.residentRef_id
            cs.teamRef_id = clinicScheduleWork.teamRef_id
            cs.residentTypeRef_id = clinicScheduleWork.residentTypeRef_id
            cs.rotationRef_id = clinicScheduleWork.rotationRef_id
            cs.weekID = clinicScheduleWork.weekID
            cs.officeHoursRef = clinicScheduleWork.officeHoursRef
            cs.assignment_id = clinicScheduleWork.assignment_id
            cs.save()


    def DeleteWorkCounts(self, b, w):
        ################################################################################################################
        # b = block, w = week
        # PURPOSE: Established clinic sessions are immutable, we must set them first and update our counts after
        # FIRST:
        # NEXT:
        # FINAL:
        ################################################################################################################
        blockInfo = Block.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, id__exact=b)
        setBlockId = blockInfo.id
        intW = int(w)
        dOfficeHoursCountWork = OfficeHoursCountWork.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=setBlockId, weekID__exact=intW).delete()
        dTeamWeekPeriodCountWork = TeamWeekPeriodCountWork.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=setBlockId, weekID__exact=intW).delete()
        dResidentAvailableSesCountWork = ResidentAvailableSesCountWork.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=setBlockId, weekID__exact=intW).delete()
        dClinicScheduleWork = ClinicScheduleWork.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=setBlockId, weekID__exact=intW).delete()
        dClinicScheduleBlocked = ClinicScheduleBlocked.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=setBlockId, weekID__exact=intW).delete()
        dAvailableAssignmentWork = AvailableAssignmentWork.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=setBlockId, weekID__exact=intW).delete()

    def generateScheduleForWeek(self, inBlock, inWeek):
        ################################################################################################################
        # Main programming section
        # FIRST: call method to setup initial available sessions
        # SECOND:  call method to determine our maximum Patients Per week possible
        # THIRD:
        # FINAL:
        ################################################################################################################
        bDelete = self.checkAndDeleteFromRecord(inBlock, inWeek)
        if bDelete:
            try:
                blockInfo = Block.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, id__exact=inBlock)
                setBlockId = blockInfo.id
                intW = int(inWeek)
                self.determineAvailableSessions(inBlock, inWeek)
                maximumPatientsPerWeek = self.determineMaxThroughput(inBlock, inWeek)
                self.setTargetValuesAndTolerances(maximumPatientsPerWeek)
                self.InitializeWorkCounts(inBlock, inWeek)
                self.processEstablishedUpdateCounts(inBlock, inWeek)
                returnMaxValue = self.calculateScoringRoutine(inBlock, inWeek)
                availableSessionCount = AvailableAssignmentWork.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=setBlockId, weekID__exact=intW, available__exact='Y').count()
                # loop Break should end the loop after all open Assignments have had the opportunity to be evaluated at least once
                loopBreakVal = availableSessionCount + 1
                while self.remainingWeekSessions > 0 and availableSessionCount > 0 and self.loopBreaker < loopBreakVal:
                    availableWithMaxValueSet = AvailableAssignmentWork.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=setBlockId, weekID__exact=intW, available__exact='Y', scoringValue__exact=returnMaxValue).order_by('?')
                    for availableWithMaxValue in availableWithMaxValueSet:
                        validToSet = self.checkTolerances(availableWithMaxValue, inBlock, inWeek)
                        if validToSet:
                            # set and update counts
                            self.buildFilledClinicScheduleWork(availableWithMaxValue, inBlock, inWeek)
                            break
                        else:
                            # set to blocked and update counts
                            self.buildBlockedClinicSchedule(availableWithMaxValue, inBlock, inWeek)
                    returnMaxValue = self.calculateScoringRoutine(inBlock, inWeek)
                    availableSessionCount = AvailableAssignmentWork.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=setBlockId, weekID__exact=intW, available__exact='Y').count()
                    self.loopBreaker += 1
               # once loop breaks write all values to clinic schedule
                self.writeToClinicSchedule(inBlock, inWeek)
                self.DeleteWorkCounts(inBlock, inWeek)
                return True
            except Exception as e:
                # todo set up error messages on why the program failed
                # missing setup data, etc.
                self.DeleteWorkCounts(inBlock, inWeek)
                return False
        else:
            # todo add error message displaying that clinic schedule is locked
            return False

################################## end new code, MMcCaskey, March/April 2013 ###########################################

    def getFiltered(self, dto, inBlock, inWeek):
        #logging.info("getFiltered:%s" % (dto,))
        cSchedCount = ClinicSchedule.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=inBlock, weekID__exact=inWeek).count()
        if cSchedCount > 0:
            self.monAMcount = 0
            self.monPMcount = 0
            self.tueAMcount = 0
            self.tuePMcount = 0
            self.wedAMcount = 0
            self.wedPMcount = 0
            self.thuAMcount = 0
            self.thuPMcount = 0
            self.friAMcount = 0
            self.friPMcount = 0
            self.monAMpatcount = 0
            self.monPMpatcount = 0
            self.tueAMpatcount = 0
            self.tuePMpatcount = 0
            self.wedAMpatcount = 0
            self.wedPMpatcount = 0
            self.thuAMpatcount = 0
            self.thuPMpatcount = 0
            self.friAMpatcount = 0
            self.friPMpatcount = 0
            self.patientTotal = 0
            self.sessionAll = 0
            items_dto = []
            Residents = Resident.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear).order_by('lastName')
            for resident in Residents:
                #for item in cItem.weekID:
                item = DTO()
                item2Add = self.to_dto(item, inBlock, inWeek, resident)
                if item2Add:
                    items_dto.append(item2Add)
            FacultySet = Faculty.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear).order_by('lastName')
            for faculty in FacultySet:
                #for item in cItem.weekID:
                item = DTO()
                item2Add = self.to_dto_fac(item, inBlock, inWeek, faculty)
                if item2Add:
                    items_dto.append(item2Add)

            #logging.info("getFiltered done:")
            dto = DTO()
            dto.id = 0
            dto.name = 'Totals: ' + str(self.sessionAll)
            #dto.totals = self.sessionAll
            dto.monAM = self.monAMcount
            dto.monPM = self.monPMcount
            dto.tueAM = self.tueAMcount
            dto.tuePM = self.tuePMcount
            dto.wedAM = self.wedAMcount
            dto.wedPM = self.wedPMcount
            dto.thuAM = self.thuAMcount
            dto.thuPM = self.thuPMcount
            dto.friAM = self.friAMcount
            dto.friPM = self.friPMcount
            items_dto.append(dto)

            dto = DTO()
            dto.id = -1
            dto.name = 'Patient Totals: ' + str(self.patientTotal)
            #dto.totals = self.sessionAll
            dto.monAM = self.monAMpatcount
            dto.monPM = self.monPMpatcount
            dto.tueAM = self.tueAMpatcount
            dto.tuePM = self.tuePMpatcount
            dto.wedAM = self.wedAMpatcount
            dto.wedPM = self.wedPMpatcount
            dto.thuAM = self.thuAMpatcount
            dto.thuPM = self.thuPMpatcount
            dto.friAM = self.friAMpatcount
            dto.friPM = self.friPMpatcount
            items_dto.append(dto)

            return items_dto
        else:
            return None

    def to_dto(self, item, b, w, r):
        if item is None: return None

        dto = DTO()
        dto.id = r.id
        intW = int(w)
        dto.name = r.lastName + "," + r.firstName

        # todo refactor to be generated dynamically
        #   on organizational yearly schedule

        cSchedSet = ClinicSchedule.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=b, weekID__exact=w, residentRef__exact=r.id)

        patCount = BlockResidentType.objects.get(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=b, residentTypeRef_id = r.residentYear.id).patientSessions

        if cSchedSet.count() == 0:
            currRot = None
            rRotations = RotationSchedule.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=b, residentRef__exact = r.id)
            for rRotation in rRotations:
                if rRotation.weekNum == 7:
                    currRot = rRotation
                    break
                elif rRotation.weekNum == 6 and intW in (3,4):
                    currRot = rRotation
                    break
                elif rRotation.weekNum == 5 and intW in (1,2):
                    currRot = rRotation
                    break
                elif rRotation.weekNum == intW:
                    currRot = rRotation
                    break
                else:
                    # todo write error message
                    continue
                    # end check current rotation
            # create Clinic Schedule Blocked Record
            if currRot is not None:
                dto.rotation = currRot.rotationRef.rotationName
            else:
                dto.rotation = 'None Assigned'
            dto.team = r.residentTeam.shortDesc
        else:
            for item in cSchedSet:
                self.sessionAll += 1
                self.patientTotal += patCount
                dto.rotation = item.rotationRef.rotationName
                dto.team = item.teamRef.shortDesc

                if item.officeHoursRef.weekday == 'M':
                    if item.officeHoursRef.period == 'AM':
                        dto.monAM  = item.assignment.scheduleType
                        self.monAMcount += 1
                        self.monAMpatcount += patCount
                    else:
                        dto.monPM  = item.assignment.scheduleType
                        self.monPMcount += 1
                        self.monPMpatcount += patCount
                if item.officeHoursRef.weekday == 'T':
                    if item.officeHoursRef.period == 'AM':
                        dto.tueAM = item.assignment.scheduleType
                        self.tueAMcount += 1
                        self.tueAMpatcount += patCount
                    else:
                        dto.tuePM = item.assignment.scheduleType
                        self.tuePMcount += 1
                        self.tuePMpatcount += patCount
                if item.officeHoursRef.weekday == 'W':
                    if item.officeHoursRef.period== 'AM':
                        dto.wedAM = item.assignment.scheduleType
                        self.wedAMcount += 1
                        self.wedAMpatcount += patCount
                    else:
                        dto.wedPM = item.assignment.scheduleType
                        self.wedPMcount += 1
                        self.wedPMpatcount += patCount
                if item.officeHoursRef.weekday == 'H':
                    if item.officeHoursRef.period == 'AM':
                        dto.thuAM = item.assignment.scheduleType
                        self.thuAMcount += 1
                        self.thuAMpatcount += patCount
                    else:
                        dto.thuPM = item.assignment.scheduleType
                        self.thuPMcount += 1
                        self.thuPMpatcount += patCount
                if item.officeHoursRef.weekday == 'F':
                    if item.officeHoursRef.period == 'AM':
                        dto.friAM = item.assignment.scheduleType
                        self.friAMcount += 1
                        self.friAMpatcount += patCount
                    else:
                        dto.friPM = item.assignment.scheduleType
                        self.friPMcount += 1
                        self.friPMpatcount += patCount
        return dto

    def to_dto_fac(self, item, b, w, f):
        if item is None: return None

        dto = DTO()
        dto.id = f.id
        intW = int(w)
        dto.name = f.lastName + "," + f.firstName

        # todo refactor to be generated dynamically
        #   on organizational yearly schedule

        fchSet = FacultyClinicSchedule.objects.filter(organization__exact=self.globalOrg,organizationYear__exact=self.globalOrgYear, blockRef__exact=b, weekID__exact=w, facultyRef__exact=f.id)

        patCount = self.facultyPatientsPerSession

        if fchSet.count() == 0:
            dto.rotation = 'Faculty Session'
            dto.team = f.facultyTeam.shortDesc
        else:
            for item in fchSet:
                self.sessionAll += 1
                self.patientTotal += patCount
                dto.rotation = 'Faculty Session'
                dto.team = item.teamRef.shortDesc

                if item.officeHoursRef.weekday == 'M':
                    if item.officeHoursRef.period == 'AM':
                        dto.monAM  = item.assignment.scheduleType
                        self.monAMcount += 1
                        self.monAMpatcount += patCount
                    else:
                        dto.monPM  = item.assignment.scheduleType
                        self.monPMcount += 1
                        self.monPMpatcount += patCount
                if item.officeHoursRef.weekday == 'T':
                    if item.officeHoursRef.period == 'AM':
                        dto.tueAM = item.assignment.scheduleType
                        self.tueAMcount += 1
                        self.tueAMpatcount += patCount
                    else:
                        dto.tuePM = item.assignment.scheduleType
                        self.tuePMcount += 1
                        self.tuePMpatcount += patCount
                if item.officeHoursRef.weekday == 'W':
                    if item.officeHoursRef.period== 'AM':
                        dto.wedAM = item.assignment.scheduleType
                        self.wedAMcount += 1
                        self.wedAMpatcount += patCount
                    else:
                        dto.wedPM = item.assignment.scheduleType
                        self.wedPMcount += 1
                        self.wedPMpatcount += patCount
                if item.officeHoursRef.weekday == 'H':
                    if item.officeHoursRef.period == 'AM':
                        dto.thuAM = item.assignment.scheduleType
                        self.thuAMcount += 1
                        self.thuAMpatcount += patCount
                    else:
                        dto.thuPM = item.assignment.scheduleType
                        self.thuPMcount += 1
                        self.thuPMpatcount += patCount
                if item.officeHoursRef.weekday == 'F':
                    if item.officeHoursRef.period == 'AM':
                        dto.friAM = item.assignment.scheduleType
                        self.friAMcount += 1
                        self.friAMpatcount += patCount
                    else:
                        dto.friPM = item.assignment.scheduleType
                        self.friPMcount += 1
                        self.friPMpatcount += patCount
        return dto
