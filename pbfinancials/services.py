
'''
Created on Dec 4, 2012
@author: rmaduri
Modified Jan 31, 2013 mmccaskey
    * converted to Py 2.7/Django 1.4

'''
import logging
import datetime
from datetime import date
from django.contrib.sessions.models import Session
from models import DTO, Block, ClinicSchedule, Rotation, TeamType, OfficeHours, RotationSchedule, BlockResidentTypeCount, BaseOrganization
from models import Resident, RotationException, StaffUnavailable, ResidentType, ClinicAvailability, Faculty, Holiday, OrganizationYear

class dtoFactory:
    def getFactory(self, items, uid):
        logging.info('calling factory')
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        uoy = UserOrganizationYear()
        userOrgYear = UserOrganizationYear.get(uoy)
        dto = DTO()
        dto.id = uid
        items_dto = []
        for item in items:
            objects = items[item].objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear)
            for object in objects:
                fields = object._meta.fields
                dct = {}
                for field in fields:
                    #assert isinstance(object, object)
                    dct['itemName'] = item
                    dct[field.name] = getattr(object, str(field.attname))
                #dct[id] = item
                items_dto.append(dct)
        return items_dto

class updateFactory:
    def setFactory(self, post, items, fieldList, uid):
        logging.info('update factory')
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        uoy = UserOrganizationYear()
        userOrgYear = UserOrganizationYear.get(uoy)
        dto = DTO()
        dto.id = uid
        for item in items:
            objects = items[item].objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear)
            for object in objects:
                for field in fieldList:
                    for pItem in post:
                        if pItem == getattr(object, field):
                            if pItem.value == "Y":
                                logging.info('foo')
        items_dto = []
        for item in items:
            objects = items[item].objects.filter(organization__exact=userOrg, organizationYear__exact=userOrgYear)
            for object in objects:
                fields = object._meta.fields
                dct = {}
                for field in fields:
                    #assert isinstance(object, object)
                    dct['itemName'] = item
                    dct[field.name] = getattr(object, str(field.attname))
                    #dct[id] = item
                items_dto.append(dct)
        return items_dto


class UserOrganization:
    def get(self):
        logging.info('returning organization')
        # refactor to pull from assignment table for session logged in user
        return 1
    #def set(self, uid):
        #request.session['organization'] = 1

class UserOrganizationYear:
    year = 0
    def get(self):
        logging.info('returning org year')
        # if no year exists then year has not been set
        # default to current organizational year
        # otherwise, user has selected a different year to view/work on
        # return that
        if self.year == 0:
            today = date.today()
            uo = UserOrganization()
            userOrg = UserOrganization.get(uo)
            orgYears = OrganizationYear.objects.filter(organization__exact=userOrg)
            for orgYear in orgYears:
                if orgYear.yearStartDate <= today <= orgYear.yearEndDate:
                    self.year = orgYear.id
                    break
        return self.year

    def set(self, inYear):
        if inYear is not None:
            self.year = inYear


class GenFunc:
    def ymdToDate(sDate):
        #ary = sDate.split("-")
        #return datetime.date(int(ary[0]), int(ary[1]), int(ary[2]))
        return datetime.date(sDate)

    def dateToYMD(dt):
        return "%04d-%02d-%02d" % (dt.year, dt.month, dt.day)

class BlockService:
    def get(self, key):
        logging.info('get %s' % (key))
        return self.to_dto(Block.get(key))

    def getAsDict(self, dto):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        dctItems = {}
        # replaced use of "ALL" with 0;
        if dto.block == 0:
            blocks = Block.objects.filter(organization__exact=userOrg,organizationYear__exact=dto.year)
        else:
            blocks = Block.objects.filter(organization__exact=userOrg,organizationYear__exact=dto.year,id__exact=dto.block)

        if blocks:
            for block in blocks:
                dct = {}
                dct['id'] = block.id
                dct['code'] = block.code
                dct['description'] = block.description
                dct['DateBeg'] = block.sDateBeg
                dct['DateEnd'] = block.sDateEnd
                #dct['organizationYear'] = block.organizationYear
                dctItems[block.id] = dct
        return dctItems


class RotationService:
    def get(self, key):
        logging.info('get %s' % (key))
        return self.to_dto(Rotation.get(key))

    # dto.block, dto.year, dto.week
    def getAsDict(self, dto):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        dictItems = {}
        items = Rotation.objects.filter(organization__exact=userOrg,organizationYear__exact=dto.year)
        for item in items:
            dct = {}
            dct['code'] =  item.code
            dct['rotationName'] = item.rotationName
            dct['description'] = item.description
            dct['splitAllowed'] = item.splitAllowed
            dct['Rotation_id'] = item.id
            dictItems[item.id] = dct
        return dictItems


class HolidayService:
    def get(self, key):
        logging.info('get %s' % (key))
        return self.to_dto(Holiday.get(key))

    # dto.block, dto.year, dto.week
    def getAsDict(self, dto):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        dictItems = {}
        dtL = []

        if dto.block == 0:
            blocks = Block.objects.filter(organization__exact=userOrg,organizationYear__exact=dto.year)
        else:
            blocks = Block.objects.filter(organization__exact=userOrg,organizationYear__exact=dto.year,id__exact=dto.block)

        # for each of the blocks in the list, get the holiday dates that are in range.
        for block in blocks:
            items = Holiday.objects.filter(organization__exact=userOrg,organizationYear__exact=dto.year, sHolidayDate__lte=block.sDateEnd,sHolidayDate__gte=block.sDateBeg)
            for item in items:
                dct = {}
                if not item.sHolidayDate in dtL:
                    dct = {}
                    dtL.append(item.sHolidayDate)
                    dct['Date'] = item.sHolidayDate
                    dct['Description'] = item.description
                    dct['id'] = item.id
                    dictItems[item.id] = dct
        return dictItems


class OfficeHoursService:
    def get(self, key):
        logging.info('get %s' % (key))
        return self.to_dto(OfficeHours.get(key))

    # dto.block, dto.year, dto.week
    def getAsDict(self, dto):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        dictItems = {}
        workDct = {}
        items = OfficeHours.objects.filter(organization__exact=userOrg,organizationYear__exact=dto.year)
        for item in items:
            wd = workDct.get(item.weekday)
            if wd == None:
                workDct[item.weekday] = {}
                wd = workDct.get(item.weekday)

            wd[item.period + "-End"] = item.sTimeEnd
            wd[item.period + "-Beg"] = item.sTimeBeg

        for key in workDct:
            dictItems[key] = workDct[key]

        # simulate to existing values

        return dictItems

class ResidentService:
    def get(self, key):
        logging.info('get %s' % (key))
        return self.to_dto(Resident.get(key))

    # dto.block, dto.year, dto.week
    def getAsDict(self, dto):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        dictItems = {}
        rItems = Resident.objects.filter(organization__exact=userOrg,organizationYear__exact=dto.year)
        fItems = Faculty.objects.filter(organization__exact=userOrg,organizationYear__exact=dto.year)

        workDct = {}
        if rItems:
            for rItem in rItems:
                dct = {}
                sName = rItem.lastName + "," + rItem.firstName
                dct['Name'] = sName
                dct['SesCount'] = 0
                dct['Team'] = "None"
                dct['RezType'] = "PGY1"
                dct['Resident'] = "Resident"
                dct['id'] = rItem.id


                rtm = ResidentType.objects.filter(organization__exact=userOrg,organizationYear__exact=dto.year)
                for rtmItem in rtm:
                    if rtmItem.__getattribute__('id')  == rItem.residentYear.__getattribute__('id'):
                        v1 = rtmItem.shortDesc
                        dct['RezType'] = v1
                        break

                ttm = TeamType.objects.filter(organization__exact=userOrg,organizationYear__exact=dto.year)
                for ttmItem in ttm:
                    if ttmItem.__getattribute__('id') == rItem.residentTeam.__getattribute__('id'):
                        dct['Team'] = ttmItem.shortDesc
                        break

                workDct[sName] = dct

        if fItems:
            for fItem in fItems:
                dct2 = {}
                sName = fItem.lastName + "," + fItem.firstName
                dct2['Name'] = sName
                dct2['SesCount'] = 0
                dct2['Team'] = "None"
                dct2['RezType'] = ""
                dct2['Resident'] = "Faculty"
                dct2['id'] = fItem.id


                ttm = TeamType.objects.filter(organization__exact=userOrg,organizationYear__exact=dto.year)
                for ttmItem in ttm:
                    if ttmItem.__getattribute__('id') == fItem.facultyTeam.__getattribute__('id'):
                        dct2['Team'] = ttmItem.shortDesc
                        break

                workDct[sName] = dct2

        for key in workDct:
            dictItems[key] = workDct[key]
        return dictItems


# testing here...
# seeing if this moves the error line nbr
class RotationScheduleService:
    def get(self, key):
        logging.info('get %s' % (key))
        return self.to_dto(RotationSchedule.get(key))

    def getAsDict(self, dto):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        if dto.block == 0:
            blk = Block.objects.filter(organization__exact=userOrg,organizationYear__exact=dto.year)
        else:
            blk = Block.objects.filter(organization__exact=userOrg,organizationYear__exact=dto.year,id__exact=dto.block)
        if not blk:
            logging.info("Block [%s]not found" % dto.block)
            return []

        frs = RotationSchedule.objects.filter(organization__exact=userOrg,organizationYear__exact=dto.year)
        if not frs:
            logging.info("RotationSchedule not found")
            return []
        iSeq = 0

        itemsList = []
        for frrsItem in frs:
            dct = {}
            if frrsItem.blockRef.id  == blk[0].id:
                dct[blk[0].description[-1:]] = frrsItem.rotationRef.rotationName
                dct['RezType'] = frrsItem.residentRef.residentYear.shortDesc
                dct['SeqNum'] = iSeq
                dct['Name'] = frrsItem.residentRef.lastName + "," + frrsItem.residentRef.firstName
                dct['Week'] = frrsItem.weekNum
                dct['Rotation_id'] = frrsItem.rotationRef.id
                dct['id'] = frrsItem.id
                sTmp = (blk[0].description.strip()[-1:] + ":" + dct['RezType'] + ":" + dct['Name'] + ":" + unicode(dct['id']) + ":" + unicode(dct['Rotation_id']) + ":"  + ("%02d" % (int(dct['Week']))) + ":" +
                        dct[blk[0].description.strip()[-1:]])
                if not sTmp in itemsList:
                    itemsList.append(sTmp)

        dictItems = {}
        itemsList = sorted(itemsList)
        itemsX = {}
        for item in itemsList:
            ary = item.split(":")
            l = len(ary)
            sKey = ":".join(ary[:l])
            if itemsX.get(sKey, None) == None:
                itemsX[sKey] = []
            valL = itemsX.get(sKey)
            valL.append(ary[-1])

        iSeq = 0
        for key in itemsX:
            dct = {}
            iSeq += 1
            ary = key.split(":")

            dct[ary[0]] = "/".join(itemsX[key])
            dct['Name'] =  ary[2]
            dct['RezType'] = ary[1]
            dct['SeqNum'] = iSeq
            dct['id'] = long(ary[3])
            dct['Rotation_id'] = long(ary[4])
            dct['Week'] = ary[5]
            dct['rotationName'] = ary[6]
            dictItems[iSeq] = dct

        return dictItems

class BlockResidentCountService:
    def get(self, key):
        logging.info('get %s' % (key))
        return self.to_dto(BlockResidentCount.get(key))


    # dto.block, dto.year, dto.week
    def getAsDict(self, dto):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        dictItems = {}
        if dto.block == 0:
            blk = Block.objects.filter(organization__exact=userOrg,organizationYear__exact=dto.year)
        else:
            blk = Block.objects.filter(organization__exact=userOrg,organizationYear__exact=dto.year,id__exact=dto.block)

        items = BlockResidentTypeCount.objects.filter(organization__exact=userOrg,organizationYear__exact=dto.year)

        rItems = Resident.objects.filter(organization__exact=userOrg,organizationYear__exact=dto.year)

        if rItems:
            iSeq = 0
            for rItem in rItems:
                if items:
                    for item in items:
                        if item.blockRef.id == blk[0].id:
                            dct = {}
                            iSeq += 1
                            dct['Block'] = item.blockRef.description
                            dct['Block_id'] = item.blockRef.id
                            dct['RezType'] = rItem.residentYear.shortDesc
                            dct['Team'] = rItem.residentTeam.shortDesc
                            dct['Name'] = rItem.lastName + "," + rItem.firstName
                            dct['SeqNum'] = iSeq
                            dct['MinSes'] = str(item.minSession)
                            dct['MaxSes'] = str(item.maxSession)
                            dct['PtsSes'] = str(item.ptsSession)
                            dct['id'] = item.id
                            dct['SesCount'] = 0
                            dictItems[iSeq] = dct

        return dictItems

class ClinicAvailabilityService:
    def get(self, key):
        logging.info('get %s' % (key))
        return self.to_dto(ClinicAvailability.get(key))

    def getAsDict(self, dto):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        dictItems = {}

        # get all the weekday heading items
        wdHead = []
        wkDay = []
        ohr = OfficeHours.objects.filter(organization__exact=userOrg,organizationYear__exact=dto.year)
        for item in ohr:
            wTmp = item.weekday
            wTmp = wTmp.upper()
            if not wTmp in wkDay: wkDay.append(wTmp)
            sTmp = item.weekday + "-" + item.period
            sTmp = sTmp.upper()
            if not sTmp in wdHead: wdHead.append(sTmp)

        caQry = ClinicAvailability.objects.filter(organization__exact=userOrg,organizationYear__exact=dto.year)
        iSeq = 0
        if caQry:
            for item in caQry:
                iSeq += 1
                key = item.rotationRef.rotationName + ":" + item.residentTypeRef.shortDesc + ":"
                if dictItems.get(key, None) == None:
                    dictItems[key] = {}
                    dct = dictItems.get(key)
                    # fill the defaults for weekDays AM, PM
                    for wd in wkDay:
                        dct[wd + "-AM"] = ""
                        dct[wd + "-PM"] = ""


                dct = dictItems.get(key)
                wdKey = item.officeHrsRef.weekday + "-" + item.officeHrsRef.period
                # populate dct
                dct['id'] = item.id
                if dct.get('SeqNum', None) == None: dct['SeqNum'] = iSeq
                if dct.get('Comment', None) == None: dct['Comment'] = ""
                if dct.get('Organization', None) == None: dct['Organization'] = item.organization_id
                if dct.get('OrganizationYear', None) == None: dct['OrganizationYear'] = item.organizationYear_id
                if dct.get('RezType', None) == None: dct['RezType'] = item.residentTypeRef.shortDesc
                #if dct.get('Rotation', None) == None: dct['Rotation'] = item.rotationRef.rotationName
                if dct.get('Rotation_id', None) == None: dct['Rotation_id'] = item.rotationRef.id
                if item.clinicScheduleTypeRef:
                    if dct[wdKey] == "": dct[wdKey] = item.clinicScheduleTypeRef.__getattribute__('scheduleType')
                else:
                    dct[wdKey] = "P"
        return dictItems

class RotationExceptionService:

    def getAsDict(self, dto):

        return {}


class UnavailableTimeService:
    def get(self, key):
        logging.info('get %s' % (key))
        return self.to_dto(StaffUnavailable.get(key))

    def dateListBetweenDates(self, dtFr, dtTo):
        #dtItems = dtFr.split("-")
        dtBeg = dtFr

        #dtItems = dtTo.split("-")
        dtEnd = dtTo

        dtList = []
        td = datetime.timedelta(days = 1)
        dtCur = dtBeg
        while dtCur <= dtEnd:
            dtList.append(dtCur.strftime("%Y-%m-%d"))
            dtCur = dtCur + td

        return dtList

    # dto.block, dto.year, dto.week
    def getAsDict(self, dto):
        uo = UserOrganization()
        userOrg = UserOrganization.get(uo)
        dictItems = {}
        dateList = []

        iSeq = 1
        # all the unavailable date ranges.
        utItems = StaffUnavailable.objects.filter(organization__exact=userOrg,organizationYear__exact=dto.year)
        if utItems:
            for utItem in utItems:
                dateList = self.dateListBetweenDates(utItem.dateBeg, utItem.dateEnd)

                for dt in dateList:
                    dct = {}
                    dct['Date'] = dt
                    dct['AMPM'] = utItem.officeHoursRef.period
                    dct['Name'] = utItem.residentRef.lastName + "," + utItem.residentRef.firstName
                    dct['Short'] = utItem.unavailRef.shortDesc
                    dct['Description'] = utItem.unavailRef.description
                    dct['SeqNum'] = iSeq
                    dct['id'] = utItem.id
                    iSeq += 1
                    dictItems[iSeq] = dct
        return dictItems


