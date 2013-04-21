
'''
Created on Dec 4, 2012
Modified Jan 31, 2013 mmccaskey
    * converted to Py 2.7/Django 1.4
@author: rmaduri
'''

import logging
import datetime

from models import DTO, Block, ClinicSchedule, Rotation, TeamType, OfficeHours, RotationSchedule, ClinicScheduleAssignment
from models import Resident, RotationException, StaffUnavailable, ResidentType, ClinicAvailability, BlockResidentTypeCount, ClinicScheduleType, \
    OrganizationYear
from services import BlockService, RotationService, HolidayService, OfficeHoursService, ResidentService, UnavailableTimeService, GenFunc, BlockResidentCountService
from services import RotationScheduleService, ClinicAvailabilityService, RotationExceptionService, UserOrganization, UserOrganizationYear
from django.contrib.auth.models import User
from django.db.models import Min

# RotationException

class ScheduleUtility:

    # refactor after is working, mm/rm
    C_FMC_WEEKDAY = ("M-AM", "M-PM", "T-AM", "T-PM", "W-AM", "W-PM", "H-AM", "H-PM", "F-AM", "F-PM")
    C_WEEKDAY = ("M", "T", "W", "H", "F", "S", "U")
    # change to dynamic based on organization
    C_BLOCK_LETTERS = [x for x in 'ABCDEFGHIJKLM']
    iMinResPerSession = 4

    # Key : Class, execute the class in loadData()
    # potential refactor review djangos model_to_dict
    CTabs = {'Block': BlockService, 'Rotation': RotationService, 'Holiday': HolidayService,
             'OfficeHours': OfficeHoursService, 'Resident': ResidentService, 'StaffUnavailable': UnavailableTimeService,
             'RotationSchedule': RotationScheduleService, 'BlockResidentCount': BlockResidentCountService,
             'ClinicAvailability': ClinicAvailabilityService, 'RotationException': RotationExceptionService}

    def printToLog(self, dto, item):
        """

        """
        if dto.toConsole:
            print(item)
        if dto.toLogging:
            logging.info(item)

    def returnHw(self):
        return "testing call to utility"

    def printCollection(self, colToPrint):
        logging.info("%s" % colToPrint)
        return None


    def printAllItemsDict(self, key):
        logging.info('Printing...:' + key)
        self.printCollection(self.allItems[key])
        return None


    def resetSesCount(self, val):
        for frItem in self.allItems['Resident'].values():
            frItem['SesCount'] = val
        return None

    def loadData(self):
        #self.allItems['Block'] = ScheduleUtility.CTabs['Block']().getAsDict(self.dto)
        for key in ScheduleUtility.CTabs:
            self.allItems[key] = ScheduleUtility.CTabs[key]().getAsDict(self.dto)
        return None

    def printAllItems(self):
        for key in ScheduleUtility.CTabs:
            self.printAllItemsDict(key)
        return None

    def getWeekNum(self, dtCur):
        if dtCur >= self.dtBeg and dtCur <= self.dtEnd:
            dtDiff = dtCur - self.dtBeg
            return int(dtDiff.days / 7) + 1
        return -1



    def ResUnavailableTime(self, sName, sAMPM):
        sDT = self.dtCur
        for item in self.allItems['StaffUnavailable'].values():
            if item['Name'] == sName and item['Date'] == sDT and item['AMPM'].find(sAMPM) >= 0:
                return True
        return False



    def findObject(self, sKey, sFindField, sFindVal):
        for x in self.allItems[sKey].values():
            if x[sFindField] == sFindVal:
                return x
        if self.debug == True: logging.info("Error : Search Object not found " + sFindField + " " + sFindVal)
        return None

    def findField(self, sKey, sFindField, sFindVal, sRetField):
        x = self.findObject(sKey, sFindField, sFindVal)
        if not x == None:
            return x[sRetField]
        if self.debug == True: logging.info("Error : Search item not found " + sFindField + " " + sFindVal)
        return None


    def getPGYObjectByBlockPGY(self, sPGY):
        for item in self.allItems['BlockResidentCount'].values():
            if item['Block_id'] == self.dto.block and item['RezType'] == sPGY:
                return item
        return None

    def getSchedObject(self, sAMPM, sName, sRezType, sRotation, sDOWAMPM, sTeam, PtsSes):
        if self.dtCur.weekday() == 4 and sRezType[:3] == 'FAC':
            PtsSes = 6
        dct = {}
        dct['Date'] = self.dtCur
        dct['Name'] = sName
        dct['RezType'] = sRezType
        dct['Rotation'] = sRotation
        dct['Mark'] = sDOWAMPM
        dct['AMPM'] = sAMPM
        dct['Team'] = sTeam
        dct['PtsSes'] = PtsSes
        return dct


    def genScheduleForPeriod(self, sAMPM):
        """

        :param sAMPM:
        :return:
        """
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        if self.dto.block != 0:
            sBlockAbbr = self.allItems['Block'][self.dto.block]['code']
        else:
            minDtBlock = Block.objects.filter(organization__exact=userOrg,organizationYear__exact=self.dto.year).aggregate(Min('sDateBeg'))
            minDt = minDtBlock['sDateBeg__min']
            if self.dtCur < minDt:
                sBlock = Block.objects.get(organization__exact=userOrg,organizationYear__exact=self.dto.year,sDateBeg__lte=minDt,  sDateEnd__gte=minDt)
            else:
                sBlock = Block.objects.get(organization__exact=userOrg,organizationYear__exact=self.dto.year,sDateBeg__lte=self.dtCur, sDateEnd__gte=self.dtCur)
            sBlockAbbr = sBlock.code
            #question spot...
        sDOW = ScheduleUtility.C_WEEKDAY[self.dtCur.weekday()]
        # one abbreviation : the first in list is mapped to all four weeks
        # two abbreviation : distribute equally among both
        #aiWeekIx = {1:(0,0,0,0), 2:(0,0,1,1), 3:(0,0,1,2), 4:(0,1,2,3)}
        iWeekID = self.getWeekNum(self.dtCur)
        if iWeekID > 4: iWeekID = 4

        for rrsItem in self.allItems['RotationSchedule'].values():
            # Resident unavailable for the date = dtCur
            if self.ResUnavailableTime(rrsItem['Name'], sAMPM) == True: continue
            #if len(rrsItem[sBlockAbbr]) == 0: continue
            if rrsItem['Rotation_id'] == 0: continue

            abbrList = rrsItem[sBlockAbbr].split(r"/")
            aiLen = len(abbrList)
            if aiLen > 4: aiLen = 4
            rrsWeek = rrsItem['Week']

            if long(rrsWeek) == 6 and iWeekID in [3,4]:
                sRotation = rrsItem['Rotation_id']
            elif long(rrsWeek) == 5 and iWeekID in [1,2]:
                sRotation = rrsItem['Rotation_id']
            else:
                # then the week is actually directly mapped
                # or 7 which is all weeks for the block
                sRotation = rrsItem['Rotation_id']

            #abbrItem = abbrList[aiWeekIx[aiLen][iWeekID-1]]
            #sRotation = self.findField('Rotation', 'rotationName', abbrItem, 'Rotation_id')

            # get the mandatory/confirmed and potential schedule
            for faItem in self.allItems['ClinicAvailability'].values():
                if faItem['RezType'] == rrsItem['RezType'] and faItem['Rotation_id'] == sRotation:
                    sDOWAMPM = sDOW + "-" + sAMPM
                    if faItem[sDOWAMPM] in ("E", "P"):
                        frItem = self.findObject('BlockResidentCount', 'Name', rrsItem['Name'])
                        if frItem:
                            if faItem[sDOWAMPM] == "E":
                                if frItem['SesCount'] <= int(self.getPGYObjectByBlockPGY(frItem['RezType'])['MaxSes']):
                                    frItem['SesCount'] = frItem['SesCount'] + 1

                            schedItem = self.getSchedObject(sAMPM,
                                                            frItem['Name'],
                                                            frItem['RezType'],
                                                            sRotation,
                                                            faItem[sDOWAMPM],
                                                            frItem['Team'],
                                                            self.getPGYObjectByBlockPGY(frItem['RezType'])['PtsSes'])
                            schedList = self.sched.get(schedItem['Date'], [])
                            schedList.append(schedItem)
                            self.sched[schedItem['Date']] = schedList
        if self.debug == True: logging.info(str(self.dtCur) + " " + str(iWeekID))
        # self.sched is updated
        return


    def genScheduleForDay(self):
        self.genScheduleForPeriod('AM')
        self.genScheduleForPeriod('PM')
        return


    def genCrossTabReportDict(self):
        dateList = sorted(self.sched.keys())
        for schedDate in dateList:
            for schedItem in self.sched[schedDate]:
                iwkNum = self.getWeekNum(schedItem['Date'])
                sKey = "%d,%s,%s,%s" % (iwkNum, schedItem['RezType'], schedItem['Name'], schedItem['Rotation'])
                if not self.rptDict.get(sKey, None):
                    tmpDct = {}
                    tmpDct['Week'] = iwkNum
                    tmpDct['RezType'] = schedItem['RezType']
                    tmpDct['Name'] = schedItem['Name']
                    tmpDct['Rotation'] = schedItem['Rotation']
                    tmpDct['Team'] = schedItem['Team']
                    for x in ScheduleUtility.C_FMC_WEEKDAY:
                        tmpDct[x] = ""
                    tmpDct['SesCount'] = 0
                    tmpDct['POptions'] = 0
                    tmpDct['NSesCount'] = 0
                    fpi = self.getPGYObjectByBlockPGY(schedItem['RezType'])
                    if fpi:
                        tmpDct['MinSes'] = int(fpi['MinSes'])
                        tmpDct['MaxSes'] = int(fpi['MaxSes'])
                        tmpDct['PtsSes'] = int(fpi['PtsSes'])
                    else:
                        #testing
                        tmpDct['MinSes'] = 0
                        tmpDct['MaxSes'] = 0
                        tmpDct['PtsSes'] = 0

                    self.rptDict[sKey] = tmpDct



        # add the 'X' and 'C' to the grid of DOW-AM and DOW-PM
        for rptItem in self.rptDict.values():
            for dt in dateList:
                iwkNum = self.getWeekNum(dt)
                schedItems = self.sched.get(dt, None)

                # set the C/X, do not check if SesCount <= MaxSes : (getting all the C is mandatory)
                for schedItem in schedItems:
                    sDOW = ScheduleUtility.C_WEEKDAY[schedItem['Date'].weekday()]
                    if int(rptItem['Week']) == iwkNum and schedItem['Date'] == dt  and rptItem['Name'] == schedItem['Name'] and rptItem['Rotation'] == schedItem['Rotation']:
                        rptItem[sDOW+"-"+schedItem['AMPM']] = schedItem['Mark']

            # update total confirmed session count and update the rptItem
            for x in ScheduleUtility.C_FMC_WEEKDAY:
                if rptItem[x] == 'E': rptItem['SesCount'] += 1
                if rptItem[x] == 'P': rptItem['POptions'] += 1


        return



    # Sorts the PotentialOption+
    def OptimizeReport3(self):
        # update the potential options count : potential options = count('X')
        def resetPOptions(dct):
            for item in dct.values(): item['POptions'] = 0

        def resetNSesCount(dct):
            for item in dct.values(): item['NSesCount'] = 0

        def resetDctCounts(dct):
            resetPOptions(dct)
            resetNSesCount(dct)

        def update_POptionsCount(dct):
            resetPOptions(dct)
            for item in dct.values():
                for x in ScheduleUtility.C_FMC_WEEKDAY:
                    if item[x] == 'P': item['POptions'] += 1

        def update_NSesCount(dct):
            resetNSesCount(dct)
            for item in dct.values():
                for x in ScheduleUtility.C_FMC_WEEKDAY:
                    if item[x] in ('E', 'F'): item['NSesCount'] += 1


        def updateDOW_ResidentCount(dow, dct):
            for x in ScheduleUtility.C_FMC_WEEKDAY:
                dow[x] = 0
                for dItem in dct.values():
                    if dItem[x] in ('E', 'F'): dow[x] = dow[x] + 1

        def updateDOW_ResCount(dow, dct):
            for x in ScheduleUtility.C_FMC_WEEKDAY:
                dow[x] = 0
                for dItem in dct.values():
                    if dItem[x] in ('E', 'F') and dItem['RezType'][:3] == 'PGY':
                        dow[x] += 1

        def updateDOW_ResidentPtsCt(dow, dct):
            for x in ScheduleUtility.C_FMC_WEEKDAY: dow[x] = 0
            for item in dct.values():
                for x in ScheduleUtility.C_FMC_WEEKDAY:
                    if item[x] in ('E', 'F'):
                        dow[x] += item['PtsSes']

        def genFillSequence():
            fillSequence = list()
            for x in ScheduleUtility.C_FMC_WEEKDAY:
                if x.find("-AM") >= 0: fillSequence.append(x)
            for x in ScheduleUtility.C_FMC_WEEKDAY:
                if x.find("-PM") >= 0: fillSequence.append(x)
            return fillSequence


        # proc start
        resetDctCounts(self.rptDict)
        fillSequence = genFillSequence()
        update_POptionsCount(self.rptDict)

        # using {} for set comprehension not available in GoogleAppEngine Python 2.5
        weekIDs = {rptItem['Week'] for rptItem in self.rptDict.values() }
        #weekIDs = set(rptItem['Week'] for rptItem in self.rptDict.values())

        #weekIDs = []
        #for rptItem in self.rptDict.values():
        #    if not rptItem['Week'] in weekIDs:
        #        weekIDs.append(rptItem['Week'])

        # dictionary comprehension not available in GoogleAppEngine 2.5
        # have to wait till pyamf is compatible with 2.7 to change to dictionary comprehension
        dowResidentCount = {x : 0 for x in ScheduleUtility.C_FMC_WEEKDAY}
        dowResCount = {x : 0 for x in ScheduleUtility.C_FMC_WEEKDAY}
        dowResidentPtsCt = {x : 0 for x in ScheduleUtility.C_FMC_WEEKDAY}

        for wkID in weekIDs:
            # get all the line items for each week (process one week at a time), always take the whole block (all of week n)
            rptWeekDct = dict( (key , self.rptDict[key]) for key in self.rptDict if self.rptDict[key]['Week'] == wkID)
            # rptPODct is the work area and rptWeekDct for DOWResCounts
            iMRPS = self.iMinResPerSession

            updateDOW_ResidentPtsCt(dowResidentPtsCt, rptWeekDct)


            # populate with cc based on FillSequence and sort order NSesCount+POptions
            # used to compare if no change from previous, add 1 to iMRSP
            sDRCstr = ""
            for x in ScheduleUtility.C_FMC_WEEKDAY: sDRCstr = sDRCstr + ":" + str(dowResidentCount[x])

            while True:
                update_NSesCount(rptWeekDct)
                update_POptionsCount(rptWeekDct)
                updateDOW_ResidentPtsCt(dowResidentPtsCt, rptWeekDct)
                updateDOW_ResidentCount(dowResidentCount, rptWeekDct)

                # get a list of items only when have count of X's > 0 (POptions > 0)
                rptPODct = dict( (key , self.rptDict[key]) for key in self.rptDict
                                 if self.rptDict[key]['Week'] == wkID and
                                    self.rptDict[key]['POptions'] > 0 and
                                    self.rptDict[key]['NSesCount'] < self.rptDict[key]['MaxSes'])

                # get the dict from smallest NSesCount+POptions
                NPList = sorted(["%05d,%05d:%s" % (rptPODct[key]['NSesCount'], rptPODct[key]['POptions'], key) for key in rptPODct.keys()])

                # for xx in minWorkItems:  print(xx, minWorkItems[xx]['SesCount'], minWorkItems[xx]['NSesCount'], minWorkItems[xx]['POptions'] )
                if NPList:
                    for itemX in NPList:
                        ixs = itemX.split(":")      # ixs[0] = 'NSesCount, ixs[1] = POptions
                        for dowX in fillSequence:
                            if dowResidentCount[dowX] < iMRPS and rptPODct[ixs[1]][dowX] == 'P':
                                rptPODct[ixs[1]]['NSesCount'] = rptPODct[ixs[1]]['NSesCount'] + 1
                                rptPODct[ixs[1]][dowX] = 'F'
                                break
                sTmpStr = ""
                for x in ScheduleUtility.C_FMC_WEEKDAY: sTmpStr = sTmpStr + ":" + str(dowResidentCount[x])
                if sTmpStr == sDRCstr:
                    iMRPS = iMRPS + 1
                    if iMRPS > 10: break
                sDRCstr = sTmpStr

                # switch if possible between the 1st and the item from the last in the list, repeating till equal or low :
            doneList = []
            for iCount in range(len(ScheduleUtility.C_FMC_WEEKDAY)):
                updateDOW_ResCount(dowResCount, rptWeekDct)
                updateDOW_ResidentPtsCt(dowResidentPtsCt, rptWeekDct)

                tmpLstL2H = sorted(["%05d,%s" % (dowResCount[key], key) for key in ScheduleUtility.C_FMC_WEEKDAY])

                #switch if possible between the 1st and the last in the list
                # lowest session DOW
                if len(doneList) > 0:
                    for iDow in doneList:
                        for iL in range(len(tmpLstL2H)):
                            if iDow == tmpLstL2H[iL].split(",")[1]:
                                tmpLstL2H.remove(tmpLstL2H[iL])
                                break

                # lowest session DOW
                lsDOW = tmpLstL2H[0].split(",")[1]
                iLowSesCount = int(tmpLstL2H[0].split(",")[0])
                bFnd = False
                for i in range(len(tmpLstL2H)):
                    if int(tmpLstL2H[-i - 1].split(",")[0]) <= iLowSesCount: break
                    curDOW = tmpLstL2H[-i - 1].split(",")[1]
                    for rItem in rptWeekDct.values():
                        updateDOW_ResCount(dowResCount, rptWeekDct)
                        updateDOW_ResidentPtsCt(dowResidentPtsCt, rptWeekDct)

                        if rItem[lsDOW] == 'P' and rItem[curDOW] == 'F' and curDOW != lsDOW and (dowResidentPtsCt[curDOW] - dowResidentPtsCt[lsDOW]) > rItem['PtsSes']:
                            rItem[lsDOW] = 'F'
                            rItem[curDOW] = 'P'
                            bFnd = True
                            break

                    if bFnd == True: break

                doneList.append(tmpLstL2H[0].split(",")[1])

            # if possible to switch do it.
            update_NSesCount(rptWeekDct)
            update_POptionsCount(rptWeekDct)
            updateDOW_ResidentCount(dowResidentCount, rptWeekDct)
            updateDOW_ResCount(dowResCount, rptWeekDct)

            # apply exceptions to rptWeekDct
            for ex in self.allItems['RotationException'].values():
                for rItem in rptWeekDct.values():
                    if rItem['RezType'] == ex['RezType'] and rItem['Rotation'] == ex['Rotation']:
                        iExCount = int(ex['Exception'].split('-')[0])
                        sExAMPM = ex['Exception'].split("-")[1]
                        availDOW = [x for x in ScheduleUtility.C_FMC_WEEKDAY if rItem[x] in ('E', 'F') and sExAMPM.find(x[-2:]) >= 0]
                        iRepeatCount = 0
                        while iExCount < len(availDOW):
                            tmpLstL2H = list()
                            # only get what we can change 'cc' the 'C' will be left intact.
                            for aDOW in availDOW:
                                if rItem[aDOW] == 'F':
                                    tmpLstL2H.append("%d,%s" % (dowResCount[aDOW], aDOW))
                            tmpLstL2H = sorted(tmpLstL2H)
                            if tmpLstL2H:
                                rItem[tmpLstL2H[-1].split(",")[1]] = 'P'
                                updateDOW_ResCount(dowResCount, rptWeekDct)
                                availDOW = [x for x in ScheduleUtility.C_FMC_WEEKDAY if rItem[x] in ('F','E') and sExAMPM.find(x[-2:]) >= 0]
                            iRepeatCount += 1
                            if iRepeatCount > len(ScheduleUtility.C_FMC_WEEKDAY): break
                        update_NSesCount(rptWeekDct)
                        update_POptionsCount(rptWeekDct)
                        updateDOW_ResidentCount(dowResidentCount, rptWeekDct)
                        updateDOW_ResCount(dowResCount, rptWeekDct)
                        break


            # switch between lowest number of patients and the highest
            update_NSesCount(rptWeekDct)
            update_POptionsCount(rptWeekDct)
            updateDOW_ResidentCount(dowResidentCount, rptWeekDct)
            updateDOW_ResCount(dowResCount, rptWeekDct)
            updateDOW_ResidentPtsCt(dowResidentPtsCt, rptWeekDct)
            doneList = []
            for iCount in range(len(ScheduleUtility.C_FMC_WEEKDAY)):

                updateDOW_ResidentPtsCt(dowResidentPtsCt, rptWeekDct)
                tmpLstL2H = sorted(["%05d,%s" % (dowResidentPtsCt[key], key) for key in ScheduleUtility.C_FMC_WEEKDAY])
                # switch if possible between the 1st and the last in the list


                if len(doneList) > 0:
                    for iDow in doneList:
                        for iL in range(len(tmpLstL2H)):
                            if iDow == tmpLstL2H[iL].split(",")[1]:
                                tmpLstL2H.remove(tmpLstL2H[iL])
                                break

                # lowest session DOW
                lsDOW = tmpLstL2H[0].split(",")[1]

                iLPtsCt = int(tmpLstL2H[0].split(",")[0])
                bFnd = False
                for i in range(len(tmpLstL2H)):
                    if int(tmpLstL2H[-i - 1].split(",")[0]) <= iLPtsCt: break
                    curDOW = tmpLstL2H[-i - 1].split(",")[1]
                    for rItem in rptWeekDct.values():
                        updateDOW_ResidentPtsCt(dowResidentPtsCt, rptWeekDct)
                        if rItem[lsDOW] == 'P' and rItem[curDOW] == 'F' and curDOW != lsDOW and (dowResidentPtsCt[curDOW] - dowResidentPtsCt[lsDOW]) > rItem['PtsSes'] :
                            rItem[lsDOW] = 'F'
                            rItem[curDOW] = 'P'
                            bFnd = True
                            break
                    if bFnd == True: break
                doneList.append(tmpLstL2H[0].split(",")[1])

        # end: for each week.

        # for each of the sessions with the highest number of residents, identify if any of the sessions with smallest resident count
        # the rotation+pgyx combination can be switched between X and cc

        update_NSesCount(rptWeekDct)
        update_POptionsCount(rptWeekDct)
        updateDOW_ResidentCount(dowResidentCount, rptWeekDct)
        updateDOW_ResCount(dowResCount, rptWeekDct)
        updateDOW_ResidentPtsCt(dowResidentPtsCt, rptWeekDct)

        logging.info("Optimize done")
        return

    def getClinicScheduleTypeId(self, valAMPM):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        retVal = 'N'
        cScheduleTypes = ClinicScheduleType.objects.filter(organization__exact=userOrg,organizationYear__exact=self.dto.year)
        cScheduleDefaultType = ClinicScheduleType.objects.get(organization__exact=userOrg,organizationYear__exact=self.dto.year, scheduleType__exact='P')
        for cScheduleType in cScheduleTypes:
            cSchedDOWAMPM = cScheduleType.scheduleType
            if cSchedDOWAMPM == valAMPM:
                retVal = cScheduleType.id
        if retVal != 'N':
            return retVal
        else:
            return cScheduleDefaultType.id

    # todo : Should store references rather than Strings such as Name, RezType, Rotation etc.,
    def writeScheduleToDB(self):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        logging.info("Writing to DB: %s, %d" % (self.dto.block, self.dto.year))
        # delete items in ClinicSchedule that match the blockRef to key
        logging.info("Deleting items.")
        delKeys, bItem = [], None
        #bItem = Block.gql("WHERE description = :1 and year = :2 limit 1", self.dto.block, self.dto.year).get()
        bItem = Block.objects.get(organization__exact=userOrg,organizationYear__exact=self.dto.year,id__exact=self.dto.block)
        csItems = ClinicSchedule.objects.filter(organization__exact=userOrg,organizationYear__exact=self.dto.year,blockRef_id__exact=self.dto.block)
        if csItems:
            for csItem in csItems:
                dcItem = ClinicScheduleAssignment.objects.filter(organization__exact=userOrg,organizationYear__exact=self.dto.year,clinicScheduleRef_id__exact=csItem.id).delete()

        logging.info("Block found : %s" % bItem.description)
        if bItem and csItems:
            dItem = ClinicSchedule.objects.filter(organization__exact=userOrg,organizationYear__exact=self.dto.year,blockRef_id__exact=self.dto.block).delete()
            logging.info("Deleted items")

        logging.info("Adding items to DB: %d" % len(self.rptDict))
        # start inserting
        for item in self.rptDict.values():
            sch = ClinicSchedule()

            sch.organization_id = userOrg
            sch.organizationYear_id = self.dto.year

            sch.weekID = item['Week']
            sch.pOptions = item['POptions']
            sch.minSes = item['MinSes']
            sch.maxSes = item['MaxSes']
            sch.nSesCount = item['NSesCount']
            sch.sesCount = item['SesCount']
            sch.ptsSes = item['PtsSes']


            # Block
            #blk = Block.gql("WHERE description = :1 and year = :2", self.dto.block, self.dto.year).get()
            blk = Block.objects.filter(organization__exact=userOrg,organizationYear__exact=self.dto.year,id__exact=self.dto.block)
            if blk:
                sch.blockRef_id = blk[0].id

            # Resident : Name
            nmLF = item['Name'].split(",")
            #fr = Resident.gql("WHERE lastName = :1 and firstName = :2", nmLF[0], nmLF[1]).get()
            fr = Resident.objects.filter(organization__exact=userOrg,organizationYear__exact=self.dto.year,lastName__contains=nmLF[0], firstName__contains=nmLF[1])
            if fr: sch.residentRef_id = fr[0].id

            # Rotation
            #rot = Rotation.gql("WHERE rotation = :1", item['Rotation']).get()
            rot = Rotation.objects.get(organization__exact=userOrg,organizationYear__exact=self.dto.year,id__exact=item['Rotation'])
            if rot: sch.rotationRef_id = rot.pk

            # ResidentType
            #frr = ResidentType.gql("WHERE shortDesc = :1", item['RezType']).get()
            frr = ResidentType.objects.get(organization__exact=userOrg,organizationYear__exact=self.dto.year,shortDesc__exact=item['RezType'])
            if frr: sch.residentTypeRef_id = frr.id

            if item['Team'] != 'None':
                #team = TeamType.gql("WHERE shortDesc = :1", item['Team']).get()
                team = TeamType.objects.get(organization__exact=userOrg,organizationYear__exact=self.dto.year,shortDesc__exact=item['Team'])
                if team: sch.teamRef_id = team.id
            sch.save()

            ohs = OfficeHours.objects.filter(organization__exact=userOrg,organizationYear__exact=self.dto.year)
            for oh in ohs:
                schAs = ClinicScheduleAssignment()
                schAs.clinicScheduleRef_id = sch.id
                schAs.organization_id = userOrg
                schAs.organizationYear_id = self.dto.year
                schAs.officeHoursRef_id = oh.id
                if oh.weekday == 'M':
                    if oh.period == 'AM':
                        schAs.assignment_id = self.getClinicScheduleTypeId(item['M-AM'])
                    else:
                        schAs.assignment_id = self.getClinicScheduleTypeId(item['M-PM'])
                if oh.weekday == 'T':
                    if oh.period == 'AM':
                        schAs.assignment_id = self.getClinicScheduleTypeId(item['T-AM'])
                    else:
                        schAs.assignment_id = self.getClinicScheduleTypeId(item['T-PM'])
                if oh.weekday == 'W':
                    if oh.period == 'AM':
                        schAs.assignment_id = self.getClinicScheduleTypeId(item['W-AM'])
                    else:
                        schAs.assignment_id = self.getClinicScheduleTypeId(item['W-PM'])
                if oh.weekday == 'H':
                    if oh.period == 'AM':
                        schAs.assignment_id = self.getClinicScheduleTypeId(item['H-AM'])
                    else:
                        schAs.assignment_id = self.getClinicScheduleTypeId(item['H-PM'])
                if oh.weekday == 'F':
                    if oh.period == 'AM':
                        schAs.assignment_id = self.getClinicScheduleTypeId(item['F-AM'])
                    else:
                        schAs.assignment_id = self.getClinicScheduleTypeId(item['F-PM'])
                schAs.save()

        return

    def initAndLoadInfo(self, dto):
        logging.info("Loading:%s" % ("*" * 80))
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        self.allItems = {}
        self.sched = {}
        self.rptDict = {}
        self.debug = dto.debug

        self.dto = dto
        self.loadData()

        if dto.block != 0:
            self.dtBeg = self.allItems['Block'][self.dto.block]['DateBeg']
            self.dtEnd = self.allItems['Block'][self.dto.block]['DateEnd']
        else:
            userOrgYear = OrganizationYear.objects.get(organization__exact=userOrg, id__exact=self.dto.year)
            self.dtBeg = userOrgYear.yearStartDate
            self.dtEnd = userOrgYear.yearEndDate
        self.dtCur = self.dtBeg

        if self.dto.toLogging: self.printAllItems()
        self.printToLog(self.dto, "Loading: Complete")


    def genSchedule(self, dto):
        self.initAndLoadInfo(dto)
        self.resetSesCount(0)
        #gf = GenFunc()

        logging.info("Begin:%s End:%s" % (self.dtBeg, self.dtEnd))
        while self.dtCur <= self.dtEnd:
            sDOW = ScheduleUtility.C_WEEKDAY[self.dtCur.weekday()]
            if sDOW == "U": self.resetSesCount(0)

            dtYMD = self.dtCur
            if sDOW in ScheduleUtility.C_WEEKDAY[:-2] and not dtYMD in self.allItems['Holiday']:
                self.genScheduleForDay()
            self.dtCur += datetime.timedelta(days=1)


        self.genCrossTabReportDict()


        if self.debug == True:
            logging.info("All Data Items: ")
            self.printAllItems()

            logging.info("Sched")
            self.printCollection(self.sched)

            logging.info("rptDict")
            self.printCollection(self.rptDict)

        if len(self.rptDict) > 0:
            self.genCrossTabReportDict()

            if self.debug == True: self.printCollection(self.sched)
            self.OptimizeReport3()
            self.writeScheduleToDB()
        return


    # get only the items that match dto.
    # Block and WeekID

    def getFiltered(self, dto):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        logging.info("getFiltered:%s" % (dto,))
        #blocks = Block.objects.filter(organization__exact=userOrg,organizationYear__exact=dto.year)
        cSched = ClinicSchedule.objects.filter(organization__exact=userOrg, organizationYear__exact=self.dto.year)
        items_dto = []
        for item in cSched:
            #for item in cItem.weekID:
            if dto.weekID == item.weekID and item.blockRef.id == long(self.dto.block):
                item2Add = self.to_dto(item)
                #item2Add = item
                if item2Add:
                    items_dto.append(item2Add)

        logging.info("getFiltered done:")
        return items_dto

    def getAll(self):
        return None

    def refresh(self, dto):
        logging.info("Refresh : %s" % (dto,))
        return self.getFiltered(dto)

    def rebuild(self, dto):
        logging.info("Rebuild : %s" % (dto,))
        self.genSchedule(dto)
        return self.refresh(dto)

    def to_dto(self, item):
        if item is None: return None
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        dto = DTO()
        dto.id = item.id
        #dto._id = item.key().id()

        dto.blockRefKey, dto.block = "", ""
        if item.blockRef != None:
            dto.blockRefKey = str(item.blockRef.id)
            dto.block = item.blockRef.description

        dto.name, dto.residentRefKey = "", ""
        if item.residentRef != None:
            dto.residentRefKey = str(item.residentRef.id)
            dto.name = item.residentRef.lastName + "," + item.residentRef.firstName

        dto.rezTypeKey, dto.rezType = "", ""
        if item.residentTypeRef != None:
            dto.rezTypeKey = str(item.residentTypeRef.id)
            dto.rezType = item.residentTypeRef.shortDesc

        dto.rotationRefKey, dto.rotation = "", ""
        if item.rotationRef != None:
            dto.rotationRefKey = str(item.rotationRef.id)
            dto.rotation = item.rotationRef.rotationName

        dto.team, dto.teamKey = "", ""
        if item.teamRef != None:
            dto.teamKey = str(item.teamRef.id)
            dto.team = item.teamRef.shortDesc

        dto.maxSes = item.maxSes
        dto.minSes = item.minSes
        dto.pOptions = item.pOptions
        dto.sesCount = item.sesCount
        dto.nSesCount = item.nSesCount
        dto.weekID = item.weekID
        dto.ptsSes = item.ptsSes
        # todo refactor to be generated dynamically
        #   on organizational yearly schedule
        csAsgn = ClinicScheduleAssignment.objects.filter(organization__exact=userOrg,organizationYear__exact=self.dto.year, clinicScheduleRef__exact=item.id)
        for csA in csAsgn:
            if csA.officeHoursRef.weekday == 'M':
                if csA.officeHoursRef.period == 'AM':
                    dto.monAM  = csA.assignment.scheduleType
                else:
                    dto.monPM  = csA.assignment.scheduleType
            if csA.officeHoursRef.weekday == 'T':
                if csA.officeHoursRef.period == 'AM':
                    dto.tueAM = csA.assignment.scheduleType
                else:
                    dto.tuePM = csA.assignment.scheduleType
            if csA.officeHoursRef.weekday == 'W':
                if csA.officeHoursRef.period== 'AM':
                    dto.wedAM = csA.assignment.scheduleType
                else:
                    dto.wedPM = csA.assignment.scheduleType
            if csA.officeHoursRef.weekday == 'H':
                if csA.officeHoursRef.period == 'AM':
                    dto.thuAM = csA.assignment.scheduleType
                else:
                    dto.thuPM = csA.assignment.scheduleType
            if csA.officeHoursRef.weekday == 'F':
                if csA.officeHoursRef.period == 'AM':
                    dto.friAM = csA.assignment.scheduleType
                else:
                    dto.friPM = csA.assignment.scheduleType

        dto.lastUpdUser = item.lastUpdUser
        dto.lastUpdDateTime = item.lastUpdDateTime
        dto.createDate = item.createDate

        return dto


########################## Begin Code Copied from Old utils.py 04/08/2013 as backup ####################################

class ScheduleUtility:

    # refactor after is working, mm/rm
    C_FMC_WEEKDAY = ("M-AM", "M-PM", "T-AM", "T-PM", "W-AM", "W-PM", "H-AM", "H-PM", "F-AM", "F-PM")
    C_WEEKDAY = ("M", "T", "W", "H", "F", "S", "U")
    # change to dynamic based on organization
    C_BLOCK_LETTERS = [x for x in 'ABCDEFGHIJKLM']
    iMinResPerSession = 4

    # Key : Class, execute the class in loadData()
    # potential refactor review djangos model_to_dict
    CTabs = {'Block': BlockService, 'Rotation': RotationService, 'Holiday': HolidayService,
             'OfficeHours': OfficeHoursService, 'Resident': ResidentService, 'StaffUnavailable': UnavailableTimeService,
             'RotationSchedule': RotationScheduleService, 'BlockResidentCount': BlockResidentCountService,
             'ClinicAvailability': ClinicAvailabilityService, 'RotationException': RotationExceptionService}

    def printToLog(self, dto, item):
        """

        """
        if dto.toConsole:
            print(item)
        if dto.toLogging:
            logging.info(item)

    def returnHw(self):
        return "testing call to utility"

    def printCollection(self, colToPrint):
        logging.info("%s" % colToPrint)
        return None


    def printAllItemsDict(self, key):
        logging.info('Printing...:' + key)
        self.printCollection(self.allItems[key])
        return None


    def resetSesCount(self, val):
        for frItem in self.allItems['Resident'].values():
            frItem['SesCount'] = val
        return None

    def loadData(self):
        #self.allItems['Block'] = ScheduleUtility.CTabs['Block']().getAsDict(self.dto)
        for key in ScheduleUtility.CTabs:
            self.allItems[key] = ScheduleUtility.CTabs[key]().getAsDict(self.dto)
        return None

    def printAllItems(self):
        #for key in ScheduleUtility.CTabs:
        #    self.printAllItemsDict(key)
        return None

    def getWeekNum(self, dtCur):
        if dtCur >= self.dtBeg and dtCur <= self.dtEnd:
            dtDiff = dtCur - self.dtBeg
            return int(dtDiff.days / 7) + 1
        return -1


    def ResUnavailableTime(self, sName, sAMPM):
        sDT = self.dtCur
        for item in self.allItems['StaffUnavailable'].values():
            if item['Name'] == sName and item['Date'] == sDT and item['AMPM'].find(sAMPM) >= 0:
                return True
        return False


    def findObject(self, sKey, sFindField, sFindVal):
        for x in self.allItems[sKey].values():
            if x[sFindField] == sFindVal:
                return x
        if self.debug == True: logging.info("Error : Search Object not found " + sFindField + " " + sFindVal)
        return None


    def findField(self, sKey, sFindField, sFindVal, sRetField):
        x = self.findObject(sKey, sFindField, sFindVal)
        if not x == None:
            return x[sRetField]
        if self.debug == True: logging.info("Error : Search item not found " + sFindField + " " + sFindVal)
        return None


    def getPGYObjectByBlockPGY(self, sPGY):
        for item in self.allItems['BlockResidentCount'].values():
            if item['Block_id'] == self.dto.block and item['RezType'] == sPGY:
                return item
        return None


    def getSchedObject(self, sAMPM, sName, sRezType, sRotation, sDOWAMPM, sTeam, PtsSes):
        if self.dtCur.weekday() == 4 and sRezType[:3] == 'FAC':
            PtsSes = 6
        dct = {}
        dct['Date'] = self.dtCur
        dct['Name'] = sName
        dct['RezType'] = sRezType
        dct['Rotation'] = sRotation
        dct['Mark'] = sDOWAMPM
        dct['AMPM'] = sAMPM
        dct['Team'] = sTeam
        dct['PtsSes'] = PtsSes
        return dct


    def genScheduleForPeriod(self, sAMPM):
        """

        :param sAMPM:
        :return:
        """
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        if self.dto.block != 0:
            sBlockAbbr = self.allItems['Block'][self.dto.block]['code']
        else:
            minDtBlock = Block.objects.filter(organization__exact=userOrg,organizationYear__exact=self.dto.year).aggregate(Min('sDateBeg'))
            minDt = minDtBlock['sDateBeg__min']
            if self.dtCur < minDt:
                sBlock = Block.objects.get(organization__exact=userOrg,organizationYear__exact=self.dto.year,sDateBeg__lte=minDt,  sDateEnd__gte=minDt)
            else:
                sBlock = Block.objects.get(organization__exact=userOrg,organizationYear__exact=self.dto.year,sDateBeg__lte=self.dtCur, sDateEnd__gte=self.dtCur)
            sBlockAbbr = sBlock.code
            #question spot...
        sDOW = ScheduleUtility.C_WEEKDAY[self.dtCur.weekday()]
        # one abbreviation : the first in list is mapped to all four weeks
        # two abbreviation : distribute equally among both
        #aiWeekIx = {1:(0,0,0,0), 2:(0,0,1,1), 3:(0,0,1,2), 4:(0,1,2,3)}
        iWeekID = self.getWeekNum(self.dtCur)
        if iWeekID > 4: iWeekID = 4

        for rrsItem in self.allItems['RotationSchedule'].values():
            # Resident unavailable for the date = dtCur
            if self.ResUnavailableTime(rrsItem['Name'], sAMPM) == True: continue
            #if len(rrsItem[sBlockAbbr]) == 0: continue
            if rrsItem['Rotation_id'] == 0: continue

            abbrList = rrsItem[sBlockAbbr].split(r"/")
            aiLen = len(abbrList)
            if aiLen > 4: aiLen = 4
            rrsWeek = rrsItem['Week']

            # todo review if this is where the code is duplicating
            if long(rrsWeek) == 6 and iWeekID in [3,4]:
                sRotation = rrsItem['Rotation_id']
            elif long(rrsWeek) == 5 and iWeekID in [1,2]:
                sRotation = rrsItem['Rotation_id']
            elif long(rrsWeek) in [1,2,3,4,7]:
                # then the week is actually directly mapped
                # or 7 which is all weeks for the block
                sRotation = rrsItem['Rotation_id']
            else: continue

            #abbrItem = abbrList[aiWeekIx[aiLen][iWeekID-1]]
            #sRotation = self.findField('Rotation', 'rotationName', abbrItem, 'Rotation_id')

            # get the mandatory/confirmed and potential schedule
            for faItem in self.allItems['ClinicAvailability'].values():
                if faItem['RezType'] == rrsItem['RezType'] and faItem['Rotation_id'] == sRotation:
                    sDOWAMPM = sDOW + "-" + sAMPM
                    if faItem[sDOWAMPM] in ("E", "P"):
                        frItem = self.findObject('BlockResidentCount', 'Name', rrsItem['Name'])
                        if frItem:
                            if faItem[sDOWAMPM] == "E":
                                if frItem['SesCount'] <= int(self.getPGYObjectByBlockPGY(frItem['RezType'])['MaxSes']):
                                    frItem['SesCount'] = frItem['SesCount'] + 1

                            schedItem = self.getSchedObject(sAMPM,
                                                            frItem['Name'],
                                                            frItem['RezType'],
                                                            sRotation,
                                                            faItem[sDOWAMPM],
                                                            frItem['Team'],
                                                            self.getPGYObjectByBlockPGY(frItem['RezType'])['PtsSes'])
                            schedList = self.sched.get(schedItem['Date'], [])
                            schedList.append(schedItem)
                            self.sched[schedItem['Date']] = schedList
        if self.debug == True: logging.info(str(self.dtCur) + " " + str(iWeekID))
        # self.sched is updated
        return


    def genScheduleForDay(self):
        self.genScheduleForPeriod('AM')
        self.genScheduleForPeriod('PM')
        return


    def genCrossTabReportDict(self):
        dateList = sorted(self.sched.keys())
        for schedDate in dateList:
            for schedItem in self.sched[schedDate]:
                iwkNum = self.getWeekNum(schedItem['Date'])
                sKey = "%d,%s,%s,%s" % (iwkNum, schedItem['RezType'], schedItem['Name'], schedItem['Rotation'])
                if not self.rptDict.get(sKey, None):
                    tmpDct = {}
                    tmpDct['Week'] = iwkNum
                    tmpDct['RezType'] = schedItem['RezType']
                    tmpDct['Name'] = schedItem['Name']
                    tmpDct['Rotation'] = schedItem['Rotation']
                    tmpDct['Team'] = schedItem['Team']
                    for x in ScheduleUtility.C_FMC_WEEKDAY:
                        tmpDct[x] = ""
                    tmpDct['SesCount'] = 0
                    tmpDct['POptions'] = 0
                    tmpDct['NSesCount'] = 0
                    fpi = self.getPGYObjectByBlockPGY(schedItem['RezType'])
                    if fpi:
                        tmpDct['MinSes'] = int(fpi['MinSes'])
                        tmpDct['MaxSes'] = int(fpi['MaxSes'])
                        tmpDct['PtsSes'] = int(fpi['PtsSes'])
                    else:
                        #testing
                        tmpDct['MinSes'] = 0
                        tmpDct['MaxSes'] = 0
                        tmpDct['PtsSes'] = 0

                    self.rptDict[sKey] = tmpDct



        # add the 'X' and 'C' to the grid of DOW-AM and DOW-PM
        for rptItem in self.rptDict.values():
            for dt in dateList:
                iwkNum = self.getWeekNum(dt)
                schedItems = self.sched.get(dt, None)

                # set the C/X, do not check if SesCount <= MaxSes : (getting all the C is mandatory)
                for schedItem in schedItems:
                    sDOW = ScheduleUtility.C_WEEKDAY[schedItem['Date'].weekday()]
                    if int(rptItem['Week']) == iwkNum and schedItem['Date'] == dt  and rptItem['Name'] == schedItem['Name'] and rptItem['Rotation'] == schedItem['Rotation']:
                        rptItem[sDOW+"-"+schedItem['AMPM']] = schedItem['Mark']

            # update total confirmed session count and update the rptItem
            for x in ScheduleUtility.C_FMC_WEEKDAY:
                if rptItem[x] == 'E': rptItem['SesCount'] += 1
                if rptItem[x] == 'P': rptItem['POptions'] += 1


        return



    # Sorts the PotentialOption+
    def OptimizeReport3(self):
        # update the potential options count : potential options = count('X')
        def resetPOptions(dct):
            for item in dct.values(): item['POptions'] = 0

        def resetNSesCount(dct):
            for item in dct.values(): item['NSesCount'] = 0

        def resetDctCounts(dct):
            resetPOptions(dct)
            resetNSesCount(dct)

        def update_POptionsCount(dct):
            resetPOptions(dct)
            for item in dct.values():
                for x in ScheduleUtility.C_FMC_WEEKDAY:
                    if item[x] == 'P': item['POptions'] += 1

        def update_NSesCount(dct):
            resetNSesCount(dct)
            for item in dct.values():
                for x in ScheduleUtility.C_FMC_WEEKDAY:
                    if item[x] in ('E', 'F'): item['NSesCount'] += 1


        def updateDOW_ResidentCount(dow, dct):
            for x in ScheduleUtility.C_FMC_WEEKDAY:
                dow[x] = 0
                for dItem in dct.values():
                    if dItem[x] in ('E', 'F'): dow[x] = dow[x] + 1

        def updateDOW_ResCount(dow, dct):
            for x in ScheduleUtility.C_FMC_WEEKDAY:
                dow[x] = 0
                for dItem in dct.values():
                    if dItem[x] in ('E', 'F') and dItem['RezType'][:3] == 'PGY':
                        dow[x] += 1

        def updateDOW_ResidentPtsCt(dow, dct):
            for x in ScheduleUtility.C_FMC_WEEKDAY: dow[x] = 0
            for item in dct.values():
                for x in ScheduleUtility.C_FMC_WEEKDAY:
                    if item[x] in ('E', 'F'):
                        dow[x] += item['PtsSes']

        def genFillSequence():
            fillSequence = list()
            for x in ScheduleUtility.C_FMC_WEEKDAY:
                if x.find("-AM") >= 0: fillSequence.append(x)
            for x in ScheduleUtility.C_FMC_WEEKDAY:
                if x.find("-PM") >= 0: fillSequence.append(x)
            return fillSequence


        # proc start
        resetDctCounts(self.rptDict)
        fillSequence = genFillSequence()
        update_POptionsCount(self.rptDict)

        # using {} for set comprehension not available in GoogleAppEngine Python 2.5
        weekIDs = {rptItem['Week'] for rptItem in self.rptDict.values() }
        #weekIDs = set(rptItem['Week'] for rptItem in self.rptDict.values())

        #weekIDs = []
        #for rptItem in self.rptDict.values():
        #    if not rptItem['Week'] in weekIDs:
        #        weekIDs.append(rptItem['Week'])

        # dictionary comprehension not available in GoogleAppEngine 2.5
        # have to wait till pyamf is compatible with 2.7 to change to dictionary comprehension
        dowResidentCount = {x : 0 for x in ScheduleUtility.C_FMC_WEEKDAY}
        dowResCount = {x : 0 for x in ScheduleUtility.C_FMC_WEEKDAY}
        dowResidentPtsCt = {x : 0 for x in ScheduleUtility.C_FMC_WEEKDAY}

        for wkID in weekIDs:
            # get all the line items for each week (process one week at a time), always take the whole block (all of week n)
            rptWeekDct = dict((key , self.rptDict[key]) for key in self.rptDict if self.rptDict[key]['Week'] == wkID)
            # rptPODct is the work area and rptWeekDct for DOWResCounts
            iMRPS = self.iMinResPerSession

            updateDOW_ResidentPtsCt(dowResidentPtsCt, rptWeekDct)

            # populate with cc based on FillSequence and sort order NSesCount+POptions
            # used to compare if no change from previous, add 1 to iMRSP
            sDRCstr = ""
            for x in ScheduleUtility.C_FMC_WEEKDAY: sDRCstr = sDRCstr + ":" + str(dowResidentCount[x])

            while True:
                update_NSesCount(rptWeekDct)
                update_POptionsCount(rptWeekDct)
                updateDOW_ResidentPtsCt(dowResidentPtsCt, rptWeekDct)
                updateDOW_ResidentCount(dowResidentCount, rptWeekDct)

                # get a list of items only when have count of X's > 0 (POptions > 0)
                rptPODct = dict( (key , self.rptDict[key]) for key in self.rptDict
                                 if self.rptDict[key]['Week'] == wkID and
                                    self.rptDict[key]['POptions'] > 0 and
                                    self.rptDict[key]['NSesCount'] < self.rptDict[key]['MaxSes'])

                # get the dict from smallest NSesCount+POptions
                NPList = sorted(["%05d,%05d:%s" % (rptPODct[key]['NSesCount'], rptPODct[key]['POptions'], key) for key in rptPODct.keys()])

                # for xx in minWorkItems:  print(xx, minWorkItems[xx]['SesCount'], minWorkItems[xx]['NSesCount'], minWorkItems[xx]['POptions'] )
                if NPList:
                    for itemX in NPList:
                        ixs = itemX.split(":")      # ixs[0] = 'NSesCount, ixs[1] = POptions
                        for dowX in fillSequence:
                            if dowResidentCount[dowX] < iMRPS and rptPODct[ixs[1]][dowX] == 'P':
                                rptPODct[ixs[1]]['NSesCount'] = rptPODct[ixs[1]]['NSesCount'] + 1
                                rptPODct[ixs[1]][dowX] = 'F'
                                break
                sTmpStr = ""
                for x in ScheduleUtility.C_FMC_WEEKDAY: sTmpStr = sTmpStr + ":" + str(dowResidentCount[x])
                if sTmpStr == sDRCstr:
                    iMRPS = iMRPS + 1
                    if iMRPS > 10: break
                sDRCstr = sTmpStr

                # switch if possible between the 1st and the item from the last in the list, repeating till equal or low :
            doneList = []
            for iCount in range(len(ScheduleUtility.C_FMC_WEEKDAY)):
                updateDOW_ResCount(dowResCount, rptWeekDct)
                updateDOW_ResidentPtsCt(dowResidentPtsCt, rptWeekDct)

                tmpLstL2H = sorted(["%05d,%s" % (dowResCount[key], key) for key in ScheduleUtility.C_FMC_WEEKDAY])

                #switch if possible between the 1st and the last in the list
                # lowest session DOW
                if len(doneList) > 0:
                    for iDow in doneList:
                        for iL in range(len(tmpLstL2H)):
                            if iDow == tmpLstL2H[iL].split(",")[1]:
                                tmpLstL2H.remove(tmpLstL2H[iL])
                                break

                # lowest session DOW
                lsDOW = tmpLstL2H[0].split(",")[1]
                iLowSesCount = int(tmpLstL2H[0].split(",")[0])
                bFnd = False
                for i in range(len(tmpLstL2H)):
                    if int(tmpLstL2H[-i - 1].split(",")[0]) <= iLowSesCount: break
                    curDOW = tmpLstL2H[-i - 1].split(",")[1]
                    for rItem in rptWeekDct.values():
                        updateDOW_ResCount(dowResCount, rptWeekDct)
                        updateDOW_ResidentPtsCt(dowResidentPtsCt, rptWeekDct)

                        if rItem[lsDOW] == 'P' and rItem[curDOW] == 'F' and curDOW != lsDOW and (dowResidentPtsCt[curDOW] - dowResidentPtsCt[lsDOW]) > rItem['PtsSes']:
                            rItem[lsDOW] = 'F'
                            rItem[curDOW] = 'P'
                            bFnd = True
                            break

                    if bFnd == True: break

                doneList.append(tmpLstL2H[0].split(",")[1])

            # if possible to switch do it.
            update_NSesCount(rptWeekDct)
            update_POptionsCount(rptWeekDct)
            updateDOW_ResidentCount(dowResidentCount, rptWeekDct)
            updateDOW_ResCount(dowResCount, rptWeekDct)

            # apply exceptions to rptWeekDct
            for ex in self.allItems['RotationException'].values():
                for rItem in rptWeekDct.values():
                    if rItem['RezType'] == ex['RezType'] and rItem['Rotation'] == ex['Rotation']:
                        iExCount = int(ex['Exception'].split('-')[0])
                        sExAMPM = ex['Exception'].split("-")[1]
                        availDOW = [x for x in ScheduleUtility.C_FMC_WEEKDAY if rItem[x] in ('E', 'F') and sExAMPM.find(x[-2:]) >= 0]
                        iRepeatCount = 0
                        while iExCount < len(availDOW):
                            tmpLstL2H = list()
                            # only get what we can change 'cc' the 'C' will be left intact.
                            for aDOW in availDOW:
                                if rItem[aDOW] == 'F':
                                    tmpLstL2H.append("%d,%s" % (dowResCount[aDOW], aDOW))
                            tmpLstL2H = sorted(tmpLstL2H)
                            if tmpLstL2H:
                                rItem[tmpLstL2H[-1].split(",")[1]] = 'P'
                                updateDOW_ResCount(dowResCount, rptWeekDct)
                                availDOW = [x for x in ScheduleUtility.C_FMC_WEEKDAY if rItem[x] in ('F','E') and sExAMPM.find(x[-2:]) >= 0]
                            iRepeatCount += 1
                            if iRepeatCount > len(ScheduleUtility.C_FMC_WEEKDAY): break
                        update_NSesCount(rptWeekDct)
                        update_POptionsCount(rptWeekDct)
                        updateDOW_ResidentCount(dowResidentCount, rptWeekDct)
                        updateDOW_ResCount(dowResCount, rptWeekDct)
                        break


            # switch between lowest number of patients and the highest
            update_NSesCount(rptWeekDct)
            update_POptionsCount(rptWeekDct)
            updateDOW_ResidentCount(dowResidentCount, rptWeekDct)
            updateDOW_ResCount(dowResCount, rptWeekDct)
            updateDOW_ResidentPtsCt(dowResidentPtsCt, rptWeekDct)
            doneList = []
            for iCount in range(len(ScheduleUtility.C_FMC_WEEKDAY)):

                updateDOW_ResidentPtsCt(dowResidentPtsCt, rptWeekDct)
                tmpLstL2H = sorted(["%05d,%s" % (dowResidentPtsCt[key], key) for key in ScheduleUtility.C_FMC_WEEKDAY])
                # switch if possible between the 1st and the last in the list


                if len(doneList) > 0:
                    for iDow in doneList:
                        for iL in range(len(tmpLstL2H)):
                            if iDow == tmpLstL2H[iL].split(",")[1]:
                                tmpLstL2H.remove(tmpLstL2H[iL])
                                break

                # lowest session DOW
                lsDOW = tmpLstL2H[0].split(",")[1]

                iLPtsCt = int(tmpLstL2H[0].split(",")[0])
                bFnd = False
                for i in range(len(tmpLstL2H)):
                    if int(tmpLstL2H[-i - 1].split(",")[0]) <= iLPtsCt: break
                    curDOW = tmpLstL2H[-i - 1].split(",")[1]
                    for rItem in rptWeekDct.values():
                        updateDOW_ResidentPtsCt(dowResidentPtsCt, rptWeekDct)
                        if rItem[lsDOW] == 'P' and rItem[curDOW] == 'F' and curDOW != lsDOW and (dowResidentPtsCt[curDOW] - dowResidentPtsCt[lsDOW]) > rItem['PtsSes'] :
                            rItem[lsDOW] = 'F'
                            rItem[curDOW] = 'P'
                            bFnd = True
                            break
                    if bFnd == True: break
                doneList.append(tmpLstL2H[0].split(",")[1])

        # end: for each week.

        # for each of the sessions with the highest number of residents, identify if any of the sessions with smallest resident count
        # the rotation+pgyx combination can be switched between X and cc

        update_NSesCount(rptWeekDct)
        update_POptionsCount(rptWeekDct)
        updateDOW_ResidentCount(dowResidentCount, rptWeekDct)
        updateDOW_ResCount(dowResCount, rptWeekDct)
        updateDOW_ResidentPtsCt(dowResidentPtsCt, rptWeekDct)

        logging.info("Optimize done")
        return

    def getClinicScheduleTypeId(self, valAMPM):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        retVal = 'N'
        cScheduleTypes = ClinicScheduleType.objects.filter(organization__exact=userOrg,organizationYear__exact=self.dto.year)
        cScheduleDefaultType = ClinicScheduleType.objects.get(organization__exact=userOrg,organizationYear__exact=self.dto.year, scheduleType__exact='P')
        for cScheduleType in cScheduleTypes:
            cSchedDOWAMPM = cScheduleType.scheduleType
            if cSchedDOWAMPM == valAMPM:
                retVal = cScheduleType.id
        if retVal != 'N':
            return retVal
        else:
            return cScheduleDefaultType.id

    # todo : Should store references rather than Strings such as Name, RezType, Rotation etc.,
    def writeScheduleToDB(self):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        logging.info("Writing to DB: %s, %d" % (self.dto.block, self.dto.year))
        # delete items in ClinicSchedule that match the blockRef to key
        logging.info("Deleting items.")
        delKeys, bItem = [], None
        #bItem = Block.gql("WHERE description = :1 and year = :2 limit 1", self.dto.block, self.dto.year).get()
        bItem = Block.objects.get(organization__exact=userOrg,organizationYear__exact=self.dto.year,id__exact=self.dto.block)
        csItems = ClinicSchedule.objects.filter(organization__exact=userOrg,organizationYear__exact=self.dto.year,blockRef_id__exact=self.dto.block)
        if csItems:
            for csItem in csItems:
                dcItem = ClinicScheduleAssignment.objects.filter(organization__exact=userOrg,organizationYear__exact=self.dto.year,clinicScheduleRef_id__exact=csItem.id).delete()

        logging.info("Block found : %s" % bItem.description)
        if bItem and csItems:
            dItem = ClinicSchedule.objects.filter(organization__exact=userOrg,organizationYear__exact=self.dto.year,blockRef_id__exact=self.dto.block).delete()
            logging.info("Deleted items")

        logging.info("Adding items to DB: %d" % len(self.rptDict))
        # start inserting
        for item in self.rptDict.values():
            sch = ClinicSchedule()

            sch.organization_id = userOrg
            sch.organizationYear_id = self.dto.year

            sch.weekID = item['Week']
            sch.pOptions = item['POptions']
            sch.minSes = item['MinSes']
            sch.maxSes = item['MaxSes']
            sch.nSesCount = item['NSesCount']
            sch.sesCount = item['SesCount']
            sch.ptsSes = item['PtsSes']


            # Block
            #blk = Block.gql("WHERE description = :1 and year = :2", self.dto.block, self.dto.year).get()
            blk = Block.objects.filter(organization__exact=userOrg,organizationYear__exact=self.dto.year,id__exact=self.dto.block)
            if blk:
                sch.blockRef_id = blk[0].id

            # Resident : Name
            nmLF = item['Name'].split(",")
            #fr = Resident.gql("WHERE lastName = :1 and firstName = :2", nmLF[0], nmLF[1]).get()
            fr = Resident.objects.filter(organization__exact=userOrg,organizationYear__exact=self.dto.year,lastName__contains=nmLF[0], firstName__contains=nmLF[1])
            if fr: sch.residentRef_id = fr[0].id

            # Rotation
            #rot = Rotation.gql("WHERE rotation = :1", item['Rotation']).get()
            rot = Rotation.objects.get(organization__exact=userOrg,organizationYear__exact=self.dto.year,id__exact=item['Rotation'])
            if rot: sch.rotationRef_id = rot.pk

            # ResidentType
            #frr = ResidentType.gql("WHERE shortDesc = :1", item['RezType']).get()
            frr = ResidentType.objects.get(organization__exact=userOrg,organizationYear__exact=self.dto.year,shortDesc__exact=item['RezType'])
            if frr: sch.residentTypeRef_id = frr.id

            if item['Team'] != 'None':
                #team = TeamType.gql("WHERE shortDesc = :1", item['Team']).get()
                team = TeamType.objects.get(organization__exact=userOrg,organizationYear__exact=self.dto.year,shortDesc__exact=item['Team'])
                if team: sch.teamRef_id = team.id
            sch.save()

            ohs = OfficeHours.objects.filter(organization__exact=userOrg,organizationYear__exact=self.dto.year)
            for oh in ohs:
                schAs = ClinicScheduleAssignment()
                schAs.clinicScheduleRef_id = sch.id
                schAs.organization_id = userOrg
                schAs.organizationYear_id = self.dto.year
                schAs.officeHoursRef_id = oh.id
                if oh.weekday == 'M':
                    if oh.period == 'AM':
                        schAs.assignment_id = self.getClinicScheduleTypeId(item['M-AM'])
                    else:
                        schAs.assignment_id = self.getClinicScheduleTypeId(item['M-PM'])
                if oh.weekday == 'T':
                    if oh.period == 'AM':
                        schAs.assignment_id = self.getClinicScheduleTypeId(item['T-AM'])
                    else:
                        schAs.assignment_id = self.getClinicScheduleTypeId(item['T-PM'])
                if oh.weekday == 'W':
                    if oh.period == 'AM':
                        schAs.assignment_id = self.getClinicScheduleTypeId(item['W-AM'])
                    else:
                        schAs.assignment_id = self.getClinicScheduleTypeId(item['W-PM'])
                if oh.weekday == 'H':
                    if oh.period == 'AM':
                        schAs.assignment_id = self.getClinicScheduleTypeId(item['H-AM'])
                    else:
                        schAs.assignment_id = self.getClinicScheduleTypeId(item['H-PM'])
                if oh.weekday == 'F':
                    if oh.period == 'AM':
                        schAs.assignment_id = self.getClinicScheduleTypeId(item['F-AM'])
                    else:
                        schAs.assignment_id = self.getClinicScheduleTypeId(item['F-PM'])
                schAs.save()

        return

    def initAndLoadInfo(self, dto):
        logging.info("Loading:%s" % ("*" * 80))
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        self.allItems = {}
        self.sched = {}
        self.rptDict = {}
        self.debug = dto.debug

        self.dto = dto
        self.loadData()

        if dto.block != 0:
            oBlock= Block.objects.get(id__exact=self.dto.block)
            self.dtBeg = oBlock.sDateBeg
            self.dtEnd = oBlock.sDateEnd
            #self.dtEnd = Block.objects.get(id__exact=self.dto.block)['DateEnd']
        else:
            userOrgYear = OrganizationYear.objects.get(organization__exact=userOrg, id__exact=self.dto.year)
            self.dtBeg = userOrgYear.yearStartDate
            self.dtEnd = userOrgYear.yearEndDate
        self.dtCur = self.dtBeg

        #if self.dto.toLogging: self.printAllItems()
        self.printToLog(self.dto, "Loading: Complete")


    def genSchedule(self, dto):
        self.initAndLoadInfo(dto)
        self.resetSesCount(0)
        #gf = GenFunc()

        logging.info("Begin:%s End:%s" % (self.dtBeg, self.dtEnd))
        while self.dtCur <= self.dtEnd:
            sDOW = ScheduleUtility.C_WEEKDAY[self.dtCur.weekday()]
            if sDOW == "U": self.resetSesCount(0)

            dtYMD = self.dtCur
            if sDOW in ScheduleUtility.C_WEEKDAY[:-2] and not dtYMD in self.allItems['Holiday']:
                self.genScheduleForDay()
            self.dtCur += datetime.timedelta(days=1)


        self.genCrossTabReportDict()


        if self.debug == True:
            logging.info("All Data Items: ")
            self.printAllItems()

            logging.info("Sched")
            self.printCollection(self.sched)

            logging.info("rptDict")
            self.printCollection(self.rptDict)

        if len(self.rptDict) > 0:
            self.genCrossTabReportDict()

            if self.debug == True: self.printCollection(self.sched)
            self.OptimizeReport3()
            self.writeScheduleToDB()
        return


    # get only the items that match dto.
    # Block and WeekID

    def getFiltered(self, dto):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        logging.info("getFiltered:%s" % (dto,))
        #blocks = Block.objects.filter(organization__exact=userOrg,organizationYear__exact=dto.year)
        cSched = ClinicSchedule.objects.filter(organization__exact=userOrg, organizationYear__exact=self.dto.year)
        items_dto = []
        for item in cSched:
            #for item in cItem.weekID:
            if dto.weekID == item.weekID and item.blockRef.id == long(self.dto.block):
                item2Add = self.to_dto(item)
                #item2Add = item
                if item2Add:
                    items_dto.append(item2Add)

        logging.info("getFiltered done:")
        return items_dto

    def getAll(self):
        return None

    def refresh(self, dto):
        logging.info("Refresh : %s" % (dto,))
        return self.getFiltered(dto)

    def rebuild(self, dto):
        logging.info("Rebuild : %s" % (dto,))
        self.genSchedule(dto)
        return self.refresh(dto)

    def to_dto(self, item):
        if item is None: return None
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        dto = DTO()
        dto.id = item.id
        #dto._id = item.key().id()

        dto.blockRefKey, dto.block = "", ""
        if item.blockRef != None:
            dto.blockRefKey = str(item.blockRef.id)
            dto.block = item.blockRef.description

        dto.name, dto.residentRefKey = "", ""
        if item.residentRef != None:
            dto.residentRefKey = str(item.residentRef.id)
            dto.name = item.residentRef.lastName + "," + item.residentRef.firstName

        dto.rezTypeKey, dto.rezType = "", ""
        if item.residentTypeRef != None:
            dto.rezTypeKey = str(item.residentTypeRef.id)
            dto.rezType = item.residentTypeRef.shortDesc

        dto.rotationRefKey, dto.rotation = "", ""
        if item.rotationRef != None:
            dto.rotationRefKey = str(item.rotationRef.id)
            dto.rotation = item.rotationRef.rotationName

        dto.team, dto.teamKey = "", ""
        if item.teamRef != None:
            dto.teamKey = str(item.teamRef.id)
            dto.team = item.teamRef.shortDesc

        dto.maxSes = item.maxSes
        dto.minSes = item.minSes
        dto.pOptions = item.pOptions
        dto.sesCount = item.sesCount
        dto.nSesCount = item.nSesCount
        dto.weekID = item.weekID
        dto.ptsSes = item.ptsSes
        # todo refactor to be generated dynamically
        #   on organizational yearly schedule
        csAsgn = ClinicScheduleAssignment.objects.filter(organization__exact=userOrg,organizationYear__exact=self.dto.year, clinicScheduleRef__exact=item.id)
        for csA in csAsgn:
            if csA.officeHoursRef.weekday == 'M':
                if csA.officeHoursRef.period == 'AM':
                    dto.monAM  = csA.assignment.scheduleType
                else:
                    dto.monPM  = csA.assignment.scheduleType
            if csA.officeHoursRef.weekday == 'T':
                if csA.officeHoursRef.period == 'AM':
                    dto.tueAM = csA.assignment.scheduleType
                else:
                    dto.tuePM = csA.assignment.scheduleType
            if csA.officeHoursRef.weekday == 'W':
                if csA.officeHoursRef.period== 'AM':
                    dto.wedAM = csA.assignment.scheduleType
                else:
                    dto.wedPM = csA.assignment.scheduleType
            if csA.officeHoursRef.weekday == 'H':
                if csA.officeHoursRef.period == 'AM':
                    dto.thuAM = csA.assignment.scheduleType
                else:
                    dto.thuPM = csA.assignment.scheduleType
            if csA.officeHoursRef.weekday == 'F':
                if csA.officeHoursRef.period == 'AM':
                    dto.friAM = csA.assignment.scheduleType
                else:
                    dto.friPM = csA.assignment.scheduleType

        dto.lastUpdUser = item.lastUpdUser
        dto.lastUpdDateTime = item.lastUpdDateTime
        dto.createDate = item.createDate

        return dto