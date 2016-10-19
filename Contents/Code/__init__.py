# HDHR Viewer V2 v0.9.2

import time
import string
from datetime import datetime
import urllib
import os
from lxml import etree

TITLE                = 'HDHR Viewer 2 (0.9.2)'
PREFIX               = '/video/hdhrv2'
VERSION              = '0.9.2'

#GRAPHICS
ART                  = 'art-default.jpg'
ICON                 = 'icon-default.png'
ICON_SUBBED_LIST     = 'icon-subscribed.png'
ICON_FAV_LIST        = 'icon-fav.png'
ICON_DEFAULT_CHANNEL = 'icon-subscribed.png'
ICON_SETTINGS        = 'icon-settings.png'
ICON_ERROR           = 'icon-error.png'
ICON_UNKNOWN         = 'icon-unknown.png'

#PREFS
PREFS_HDHR_IP        = 'hdhomerun_ip'
PREFS_HDHR_TUNER     = 'hdhomerun_tuner'
PREFS_XMLTV_MODE     = 'xmltv_mode'
PREFS_XMLTV_FILE     = 'xmltv_file'
PREFS_LOGO_MATCH     = 'channellogo'
PREFS_XMLTV_MATCH    = 'xmltv_match'

#XMLTV Modes
XMLTV_MODE_RESTAPI   = 'restapi'
XMLTV_MODE_HDHOMERUN = 'hdhomerun'
XMLTV_MODE_FILE      = 'file'

#DATE/TIME FORMATS
TIME_FORMAT          = '%H:%M'
DATE_FORMAT          = '%Y%m%d'

#HDHOMERUN GUIDE URL
URL_HDHR_DISCOVER         = 'http://{ip}/discover.json'
URL_HDHR_DISCOVER_DEVICES = 'http://my.hdhomerun.com/discover'
URL_HDHR_GUIDE            = 'http://my.hdhomerun.com/api/guide.php?DeviceAuth={deviceAuth}'
URL_HDHR_LINEUP           = 'http://{ip}/lineup.json'
URL_HDHR_STREAM           = 'http://{ip}:5004/{tuner}/v{guideNumber}'
CACHETIME_HDHR_GUIDE      = 3600 # (s) Default: 3600 = 1 hour

#CONSTANTS/PARAMETERS
TIMEOUT = 5                 # XML Timeout (s); Default = 5
TIMEOUT_LAN = 0.1           # LAN Timeout (s); Default = 0.1
CACHETIME = 5               # Cache Time (s); Default = 5
MAX_FAVORITES = 10          # Max number of favorites supported; Default = 10
VIDEO_DURATION = 14400000   # Duration for Transcoder (ms); Default = 14400000 (4 hours)
MAX_SIZE = 90971520         # [Bytes] 20971520 = 20MB; Default: 90971520 (100MB)

AUDIO_CHANNELS = 2          # 2 - stereo; 6 - 5.1
MEDIA_CONTAINER = 'mpegts'  # mpegts

###################################################################################################
# Entry point - set up default values for all containers
###################################################################################################
def Start():
    
    ObjectContainer.title1 = TITLE
    ObjectContainer.art = R(ART)

    DirectoryObject.thumb = R(ICON)
    DirectoryObject.art = R(ART)
    HTTP.CacheTime = CACHETIME
    
###################################################################################################
# Main Menu
###################################################################################################
@handler(PREFIX, TITLE, art=ART, thumb=ICON)
def MainMenu():

    global HDHRV2
    getInfo()
    HDHRV2 = Devices()
    totalTuners = len(HDHRV2.tunerDevices)
    logInfo('Total Tuners: '+xstr(totalTuners))

    oc = ObjectContainer()
    
    # If tuners exist, show favorites, all-channels, search.
    if totalTuners>0:
        # Add any enabled favorites
        favoritesList = LoadEnabledFavorites()
        for favorite in favoritesList: 
            ocTitle = favorite.name+' ('+xstr(favorite.totalChannels)+')'
            oc.add(DirectoryObject(key=Callback(FavoriteChannelsMenu, favidx=favorite.index), title=ocTitle, thumb=R(ICON_FAV_LIST)))

        # All Channels - Multi-Tuner support

        for tuneridx, tuner in enumerate(HDHRV2.tunerDevices):
            ocTitle = tuner['LocalIP']+' ('+xstr(getTunerTotalChannels(tuner))+')'
            # Append M: to Manually defined tuners.
            if not tuner['autoDiscover']:
                ocTitle='M:'+ocTitle
            oc.add(DirectoryObject(key=Callback(AllChannelsMenu, tuneridx=tuneridx), title=ocTitle, thumb=R(ICON_SUBBED_LIST)))

        # Search Option/Menu   
        oc.add(InputDirectoryObject(key=Callback(SearchResultsChannelsMenu), title='Search Playing Now', thumb=R(ICON_SUBBED_LIST)))

    # If No Tuners were found. Show error message.
    else:
        logError('No Tuners Found: Check IP or internet connection...')
        ocTitle = 'No Tuners Found.'
        oc.add(DirectoryObject(key=Callback(MainMenu), title=ocTitle, art=R(ART), thumb=R(ICON_ERROR)))

    # Settings Menu
    oc.add(PrefsObject(title='Settings', thumb=R(ICON_SETTINGS)))

    return oc
    
###################################################################################################
# Show all channels for specified tuner
###################################################################################################
@route(PREFIX + '/all-channels')
def AllChannelsMenu(tuneridx):
    oc = ObjectContainer()
    try:
        tuneridx=int(tuneridx)
        tuner=HDHRV2.tunerDevices[tuneridx]
        allChannels = LoadAllChannels(tuneridx)
        logType(allChannels)
        PopulateProgramInfo(tuneridx, allChannels.list, False)
        return AddChannelObjectContainer(oc,tuneridx,tuner['LocalIP'], allChannels.list,False)
        #return AddChannelObjectContainer(oc,tuneridx,'test', allChannels.list)

    except Exception as inst:
        logError('AllChannelsMenu(tuneridx)'+'tuneridx='+xstr(tuneridx))
        logError(strError(inst))
        return AddErrorObjectContainer(oc,'AllChannelsMenu(tuneridx);tuneridx='+xstr(tuneridx)+';'+strError(inst))
    
    return oc


###################################################################################################
# This function produces a directory for all channels the user is subscribed to
# Note, we only show program info for the favorites, because the full channel list can be a bit too
# large (well, for folks subscribing to cable)
###################################################################################################
@route(PREFIX + '/favorite-channels')
def FavoriteChannelsMenu(favidx):
    allChannels = []
    channelList = []
    tuner_defined=False
    oc = ObjectContainer()
    try:
        favorite = LoadFavorite(favidx)
        # If tuner IP is defined in Fav list, and exist in Tuner list
        for tuneridx, tuner in enumerate(HDHRV2.tunerDevices):
            if tuner['LocalIP']==favorite.tuner:
                allChannels=LoadAllChannels(tuneridx)
                tuner_defined=True
                break
        
        # If tuner IP not defined in Fav list, assume primary tuner.
        if not tuner_defined:
            logDebug('Tuner not defined in favorite list. Using primary tuner')
            # Use first tuner...
            tuneridx=0
            allChannels=LoadAllChannels(tuneridx)

        # Filter favorite list
        for channelNumber in favorite.channels:
            channel = allChannels.map.get(channelNumber)
            if (channel is not None):
                channelList.append(channel)

        # Populate the program info for all of the channels
        PopulateProgramInfo(tuneridx, channelList, True)

        return AddChannelObjectContainer(oc,tuneridx,favorite.name,channelList,False)

    except Exception as inst:
        logError('FavoriteChannelsMenu('+xstr(favidx)+')'+strError(inst))
        return AddErrorObjectContainer(oc,strError(inst))

    return oc

###################################################################################################
# This function produces a directory for all channels whose programs match the specified query
# key words
###################################################################################################
@route(PREFIX + '/search-channels')
def SearchResultsChannelsMenu(query):

    oc = ObjectContainer(title2='Search: '+query,no_cache=True)

    try:
        for tuneridx, tuner in enumerate(HDHRV2.tunerDevices):
            if not tuner['autoDiscover']:
                if isXmlTvModeHDHomeRun():
                    logInfo('HDHOmeRun Search')
                    oc = QueryChannelsHDHomeRun(oc,tuneridx,query)
                elif isXmlTvModeFile():
                    logInfo('XMLTV Search')
                    oc = QueryChannelsFile(oc,tuneridx,query)
                elif isXmlTvModeRestApi():
                    logInfo('RestAPI Search')
                    oc = QueryChannelsRestAPI(oc,tuneridx,query)
            elif tuner['autoDiscover']:
                logInfo('autoDisover Search...')
                oc = QueryChannelsHDHomeRun(oc,tuneridx,query)

            # Log Total Results per Tuner
            logInfo('Total Search Results ('+getDeviceInfo(tuner,'LocalIP')+') results:'+xstr(len(oc)))
        

        # Log Total Results (all tuners)
        logInfo('Total Search Results (all tuners):'+xstr(len(oc)))
    
    except Exception as inst:
        logError('SearchResultsChannelsMenu('+query+'):'+strError(inst))
        return AddErrorObjectContainer(oc,strError(inst))
    return oc

###################################################################################################
# This function produces a directory for all channels whose programs match the specified query
# key words
###################################################################################################

def QueryChannelsRestAPI(oc,tuneridx,query):

    logInfo('Searching RestAPI for:'+query)

    channels = []
    allProgramsMap = {}

    try:
        allChannels = LoadAllChannels(tuneridx)
        xmltvApiUrl = ConstructApiUrl(None,False,query)
        jsonChannelPrograms = JSON.ObjectFromURL(xmltvApiUrl)
        if jsonChannelPrograms==None:
            return {}

        allProgramsMap = ProgramMap_RestAPI(jsonChannelPrograms)

        for channel in allChannels.list:
            try:
                program = allProgramsMap[channel.number]
                channel.setProgramInfo(program)
                channels.append(channel)
            except KeyError:
                pass
        return AddChannelObjectContainer(oc,tuneridx,"Search: " + query,channels,True)

    except Exception as inst:
        logError('QueryChannelsRestAPI(tuneridx,query)'+strError(inst))
        return BuildErrorObjectContainer(strError(inst))

def QueryChannelsHDHomeRun(oc,tuneridx,query):

    logInfo('Searching HDHomeRun for:'+query)
    channels = []
    allProgramsMap = {}

    try:
        allChannels = LoadAllChannels(tuneridx)
        xmltvApiUrl = getGuideURL(tuneridx)
        jsonChannelPrograms = JSON.ObjectFromURL(xmltvApiUrl,cacheTime=CACHETIME_HDHR_GUIDE)
        if jsonChannelPrograms==None:
            return {}

        allProgramsMap = ProgramSearch_HDHomeRun(jsonChannelPrograms,query)

        for channel in allChannels.list:
            try:
                program = allProgramsMap[channel.number]
                channel.setProgramInfo(program)
                channels.append(channel)
            except KeyError:
                pass
        return AddChannelObjectContainer(oc,tuneridx,"Search: " + query,channels,True)

    except Exception as inst:
        logError('QueryChannelsHDHomeRun(tuneridx,query)'+strError(inst))
        return BuildErrorObjectContainer(strError(inst))


def QueryChannelsFile(oc,tuneridx,query):

    logInfo('Searching XMLTV for:'+query)

    channels = []
    allProgramsMap = {}

    try:
        channelList = []
        allChannels = LoadAllChannels(tuneridx)
        channellist=allChannels.list

        for channel in channellist:
            if Prefs[PREFS_XMLTV_MATCH] == 'name':
                channelList.append(channel.name)
            else:
                channelList.append(channel.number)

        allProgramsMap = ProgramSearch_File(channelList,query)

        for channel in channellist:
            try:
                program = allProgramsMap[channel.number]
                channel.setProgramInfo(program)
                channels.append(channel)
            except KeyError:
                pass
        return AddChannelObjectContainer(oc,tuneridx,"Search: " + query,channels,True)

    except Exception as inst:

        logError('QueryChannelsFile(oc,tuner,query)'+strError(inst))
        return BuildErrorObjectContainer(strError(inst))

 

###################################################################################################
# Utility function to populate the channels, including the program info if enabled in preferences
###################################################################################################

def AddChannelObjectContainer(oc, tuneridx, title, channels,search=False):

    # setup the VideoClipObjects from the channel list
    for channel in channels:
        program = channel.program
        oc.add(CreateVO(tuneridx=tuneridx, url=channel.streamUrl,title=GetVcoTitle(channel), year=GetVcoYear(program), tagline=GetVcoTagline(program), summary=GetVcoSummary(program), starRating=GetVcoStarRating(program), thumb=GetVcoIcon(channel,program), videoCodec=channel.videoCodec, audioCodec=channel.audioCodec,search=search))
    return oc

###################################################################################################
# Return error message
###################################################################################################
def BuildErrorObjectContainer(errormsg):
    oc = ObjectContainer(title2=errormsg)
    oc.add(DirectoryObject(title=errormsg,tagline=errormsg,summary=errormsg,thumb=R(ICON_ERROR)))
    return oc

def AddErrorObjectContainer(oc,errormsg):
    oc.add(DirectoryObject(title=errormsg,tagline=errormsg,summary=errormsg,thumb=R(ICON_ERROR)))
    return oc

###################################################################################################
# This function populates the channel with XMLTV program info coming from the xmltv rest service
###################################################################################################
def PopulateProgramInfo(tuneridx, channels, partialQuery):

    tuner=HDHRV2.tunerDevices[tuneridx]
    allProgramsMap = {}

    #tempfix disable channelguide
    if iOSPlex44():
        return

    if Prefs[PREFS_XMLTV_MODE] != 'disable':
        tuner=HDHRV2.tunerDevices[tuneridx]
        try:
            # If automatically discovered, force HDHomeRun guide.
            if tuner['autoDiscover']:
                xmltvApiUrl = getGuideURL(tuneridx)
                jsonChannelPrograms = JSON.ObjectFromURL(xmltvApiUrl,cacheTime=CACHETIME_HDHR_GUIDE)
                allProgramsMap = ProgramMap_HDHomeRun(jsonChannelPrograms)

            # Manual Tuners, use Settings
            else:
                #HDHomeRun
                if Prefs[PREFS_XMLTV_MODE]==XMLTV_MODE_HDHOMERUN:
                    xmltvApiUrl = getGuideURL(tuneridx)
                    jsonChannelPrograms = JSON.ObjectFromURL(xmltvApiUrl,cacheTime=CACHETIME_HDHR_GUIDE)
                    allProgramsMap = ProgramMap_HDHomeRun(jsonChannelPrograms)
                #RestAPI
                if Prefs[PREFS_XMLTV_MODE]==XMLTV_MODE_RESTAPI:
                    xmltvApiUrl = ConstructApiUrl(channels,partialQuery)
                    jsonChannelPrograms = JSON.ObjectFromURL(xmltvApiUrl)
                    allProgramsMap = ProgramMap_RestAPI(jsonChannelPrograms)
                #XMLTV    
                if Prefs[PREFS_XMLTV_MODE]==XMLTV_MODE_FILE:
                    channelList = []
                    try:
                        for channel in channels:
                            if Prefs[PREFS_XMLTV_MATCH] == 'name':
                                channelList.append(channel.name)
                            else:
                                channelList.append(channel.number)
                        allProgramsMap = ProgramMap_File(channelList)
                    except Exception as inst:
                        logError('XMLTV Mode Channel List'+strError(inst))
                        return

        except Exception as inst:
            Log.Error(xstr(type(inst)) + ": " + xstr(inst.args) + ": " + xstr(inst))
            return

    # go through all channels and set the program
    for channel in channels:
        try:
            if Prefs[PREFS_XMLTV_MATCH] == 'name':
                program = allProgramsMap[channel.name]
            else:
                program = allProgramsMap[channel.number]
            channel.setProgramInfo(program)
        except KeyError:
            pass

    return


###################################################################################################
# This function parses the given program json, and then builds a map from the channel display 
# name (all of them) to the Program object
###################################################################################################
def ProgramMap_RestAPI(jsonChannelPrograms):
    allProgramsMap = {}
    t = time.time()
    for jsonChannelProgram in jsonChannelPrograms:
        # parse the program and the next programs if they exist
        program = ParseProgramJson(XMLTV_MODE_RESTAPI,jsonChannelProgram["program"])
        jsonNextPrograms = jsonChannelProgram["nextPrograms"]
        if jsonNextPrograms is not None:
            for jsonNextProgram in jsonNextPrograms:
                program.next.append(ParseProgramJson(XMLTV_MODE_RESTAPI,jsonNextProgram))
                
        # now associate all channel display names with that same program object
        jsonChannelDisplayNames = jsonChannelProgram["channel"]["displayNames"]
        for displayName in jsonChannelDisplayNames:
            allProgramsMap[displayName] = program

    logInfo("Time taken to parse RestAPI JSON: "+str(time.time()-t))
            
    return allProgramsMap

def ProgramMap_HDHomeRun(jsonChannelPrograms):
    allProgramsMap = {}
    t = time.time()
    for jsonChannelProgram in jsonChannelPrograms:
        # parse the program and the next programs if they exist
        totalPrograms = len(jsonChannelProgram["Guide"])
        program = ParseProgramJson(XMLTV_MODE_HDHOMERUN,jsonChannelProgram["Guide"][0])
        i=0
        while (program.stopTime < time.time() and i<totalPrograms):
            program = ParseProgramJson(XMLTV_MODE_HDHOMERUN,jsonChannelProgram["Guide"][i])
            i=i+1
        jsonNextPrograms = jsonChannelProgram["Guide"][i:min(int(Prefs["xmltv_show_next_programs_count"])+i,totalPrograms)]
        if jsonNextPrograms is not None:
            for jsonNextProgram in jsonNextPrograms:
                program.next.append(ParseProgramJson(XMLTV_MODE_HDHOMERUN,jsonNextProgram))
        if program.icon=="":
            program.icon=jsonChannelProgram.get("ImageURL","")
        jsonChannelDisplayNames = jsonChannelProgram.get("GuideNumber")
        allProgramsMap[jsonChannelDisplayNames] = program

    logInfo("Time taken to parse HDHOmeRun JSON: "+str(time.time()-t))
            
    return allProgramsMap

def ProgramMap_File(channellist):

    t = time.time()    
    allProgramsMap = {}

    channels = []
    channelIDs = []

    channelID = None
    channelNumber = None
    c_channelID = None
    p_channelID = None
    program=None
    i=0
    
    for event, elem in etree.iterparse(Prefs[PREFS_XMLTV_FILE],events=("start", "end")):
        # get channelIDs that are requested.
        if elem.tag == 'channel' and event=='start':
            channelID = elem.attrib.get('id')
            for dispname in elem.findall('display-name'):
                if dispname.text in channellist:
                    channels.append(dispname.text)
                    channelIDs.append(channelID)
            elem.clear()
        
        # get programs
        if elem.tag == 'programme' and event=='start' and len(channelIDs)>0:
                
            currTime = int(datetime.fromtimestamp(time.time()).strftime('%Y%m%d%H%M%S'))
            stopTime = int(elem.attrib.get('stop')[:14])
            c_channelID = elem.attrib.get('channel')
            
            if currTime<stopTime and c_channelID==p_channelID and i<=int(Prefs["xmltv_show_next_programs_count"]) and c_channelID in channelIDs:
                channelindex = channelIDs.index(c_channelID)
                channelmap = channels[channelindex]
                stopTime = time.mktime(datetime.strptime(str(stopTime),'%Y%m%d%H%M%S').timetuple())
                startTime=int(elem.attrib.get('start')[:14])
                startTime=time.mktime(datetime.strptime(str(startTime),'%Y%m%d%H%M%S').timetuple())
                title=xstr(elem.findtext('title'))
                subTitle=xstr(elem.findtext('sub-title'))
                desc=xstr(elem.findtext('desc'))
                date=xstr(elem.findtext('date'))
                icon_e=elem.find('icon')
                icon=None
                if icon_e!=None:
                    icon=xstr(icon_e.attrib.get('src'))
                starRating=0.0
                
                if i==0:    
                    # current listing
                    program = Program(startTime,stopTime,title,date,subTitle,desc,icon,starRating)
                else:
                    #next listing
                    program.next.append(Program(startTime,stopTime,title,date,subTitle,desc,icon,starRating))
                    
                i+=1
                elem.clear()
            elif c_channelID!=p_channelID:
                if program!=None:
                    allProgramsMap[channelmap] = program
                i=0
                elem.clear()
            else:
                elem.clear()
            p_channelID=c_channelID
    
    logInfo("Time taken to parse XMLTV: "+str(time.time()-t))

    return allProgramsMap

#####################

def ProgramSearch_HDHomeRun(jsonChannelPrograms,query):
    allProgramsMap = {}
    t = time.time()
    for jsonChannelProgram in jsonChannelPrograms:
        i=0
        # parse the program and the next programs if they exist
        totalPrograms = len(jsonChannelProgram["Guide"])
        program = ParseProgramJson(XMLTV_MODE_HDHOMERUN,jsonChannelProgram["Guide"][0])
        while (program.stopTime < time.time() and i<totalPrograms):
            program = ParseProgramJson(XMLTV_MODE_HDHOMERUN,jsonChannelProgram["Guide"][i])
            i=i+1
        programTitle = program.title
        programDesc = program.desc
        if program.icon=="":
            program.icon=jsonChannelProgram.get("ImageURL","")
        jsonChannelDisplayNames = jsonChannelProgram.get("GuideNumber")
        if query.lower() in programTitle.lower():
            allProgramsMap[jsonChannelDisplayNames] = program   
        elif query.lower() in programDesc.lower():
            allProgramsMap[jsonChannelDisplayNames] = program
    logInfo("Time taken to search HDHOmeRun JSON: "+str(time.time()-t))
            
    return allProgramsMap

def ProgramSearch_File(channellist,query):
    t = time.time()    
    allProgramsMap = {}

    channels = []
    channelIDs = []

    channelID = None
    channelNumber = None
    c_channelID = None
    p_channelID = None
    program=None
    i=0
    
    for event, elem in etree.iterparse(Prefs[PREFS_XMLTV_FILE],events=("start", "end")):
        # get channelIDs that are requested.
        if elem.tag == 'channel' and event=='start':
            channelID = elem.attrib.get('id')
            for dispname in elem.findall('display-name'):
                if dispname.text in channellist:
                    channels.append(dispname.text)
                    channelIDs.append(channelID)
            elem.clear()

        # get programs
        if elem.tag == 'programme' and event=='start' and len(channelIDs)>0:
                
            currTime = int(datetime.fromtimestamp(time.time()).strftime('%Y%m%d%H%M%S'))
            startTime = int(elem.attrib.get('start')[:14])
            stopTime = int(elem.attrib.get('stop')[:14])
            c_channelID = elem.attrib.get('channel')

            
            if startTime<currTime and currTime<stopTime and c_channelID==p_channelID and c_channelID in channelIDs:
                channelindex = channelIDs.index(c_channelID)
                channelmap = channels[channelindex]
                stopTime = time.mktime(datetime.strptime(str(stopTime),'%Y%m%d%H%M%S').timetuple())
                #startTime=int(elem.attrib.get('start')[:14])
                startTime=time.mktime(datetime.strptime(str(startTime),'%Y%m%d%H%M%S').timetuple())
                title=xstr(elem.findtext('title'))
                subTitle=xstr(elem.findtext('sub-title'))
                desc=xstr(elem.findtext('desc'))
                date=xstr(elem.findtext('date'))
                icon_e=elem.find('icon')
                icon=None
                if icon_e!=None:
                    icon=xstr(icon_e.attrib.get('src'))
                starRating=0.0

                #query
                if query.lower() in title.lower() or query.lower() in desc.lower():
                    program = Program(startTime,stopTime,title,date,subTitle,desc,icon,starRating)
                    allProgramsMap[channelmap] = program

                elem.clear()
            elif c_channelID!=p_channelID:
                elem.clear()
            else:
                elem.clear()
            p_channelID=c_channelID

    logInfo("Time taken to search XMLTV File: "+str(time.time()-t))

    return allProgramsMap
    
###################################################################################################
# This function returns whether the xmltv_mode is set to restapi or hdhomerun
###################################################################################################
def isXmlTvModeRestApi():
    xmltv_mode = xstr(Prefs[PREFS_XMLTV_MODE])
    return (xmltv_mode == XMLTV_MODE_RESTAPI)
    
def isXmlTvModeHDHomeRun():
    xmltv_mode = xstr(Prefs[PREFS_XMLTV_MODE])
    return (xmltv_mode == XMLTV_MODE_HDHOMERUN) 

def isXmlTvModeFile():
    xmltv_mode = xstr(Prefs[PREFS_XMLTV_MODE])
    return (xmltv_mode == XMLTV_MODE_FILE)         

###################################################################################################
# This function constructs the url with query to obtain the currently playing programs
###################################################################################################
def ConstructApiUrl(channels, partialQuery, filterText = None):
    xmltvApiUrl = Prefs["xmltv_api_url"]
    showNextProgramsCount = int(Prefs["xmltv_show_next_programs_count"])

    # construct the parameter map, and then use the url encode function to ensure we are compliant with the spec
    paramMap = {}
    paramMap["show_next"] = str(showNextProgramsCount)
    if filterText is not None:
        paramMap["filter_text"] = filterText
    
    # if partialQuery, then we want to include a channels parameter with the csv of the channel numbers
    if partialQuery:
        if Prefs[PREFS_XMLTV_MATCH] == "name":
            csv = ",".join([channel.name for channel in channels])
        else:
            csv = ",".join([channel.number for channel in channels])
        paramMap["channels"] = csv
        
    xmltvApiUrl += "?" + urllib.urlencode(paramMap)
    return xmltvApiUrl
                        
###################################################################################################
# This function parses a Program json object
###################################################################################################
def ParseProgramJson(mode,jsonProgram):
    #isXmlTvModeRestApi
    if mode==XMLTV_MODE_RESTAPI:
        startTime = int(jsonProgram.get('start'))/1000
        stopTime = int(jsonProgram.get('stop'))/1000
        title = xstr(jsonProgram.get('title',''))
        date = xstr(jsonProgram.get('date',0))
        subTitle = xstr(jsonProgram.get('subtitle',''))
        desc = xstr(jsonProgram.get('desc',''))
        starRating = xstr(jsonProgram.get('starRating',''))
        icon = xstr(jsonProgram.get('icon',''))
    else:
        startTime = int(jsonProgram.get('StartTime'))
        stopTime = int(jsonProgram.get('EndTime'))
        title = xstr(jsonProgram.get('Title'))
        date = GetDateDisplay(jsonProgram.get('OriginalAirdate',0))
        subTitle = xstr(jsonProgram.get('Affiliate',''))
        desc = xstr(jsonProgram.get('Synopsis',''))
        starRating = xstr('')
        icon = xstr(jsonProgram.get('ImageURL',''))
    return Program(startTime,stopTime,title,date,subTitle,desc,icon,starRating)

###################################################################################################
# This function returns the title to be used with the VideoClipObject
###################################################################################################
def GetVcoTitle(channel):
    title = xstr(channel.number) + " - " + xstr(channel.name)

    #tempfix for iOS Plex 4.4
    if iOSPlex44():
        title = title.replace(" ","")
	
    if (channel.hasProgramInfo() and channel.program.title is not None):
        title += ": " + channel.program.title
    return title
    
###################################################################################################
# This function returns the tagline to be used with the VideoClipObject
###################################################################################################
def GetVcoTagline(program):
    tagline = ""
    if (program is not None):
        startTimeDisplay = GetTimeDisplay(program.startTime)
        stopTimeDisplay = GetTimeDisplay(program.stopTime)
        tagline = startTimeDisplay + " - " + stopTimeDisplay + ": " + xstr(program.title)
        if (program.subTitle):
            tagline += " - " + program.subTitle
    return tagline

###################################################################################################
# This function returns the summary to be used with the VideoClipObject
###################################################################################################
def GetVcoSummary(program):
    summary = ""
    if (program is not None):
        if (program.desc is not None):
            summary += program.desc
        if (len(program.next) > 0):
            summary += "\nNext:\n"
            for nextProgram in program.next:
                summary += GetVcoTagline(nextProgram) + "\n"
    return summary

###################################################################################################
# This function returns the star rating (float value) for the given progam
###################################################################################################
def GetVcoStarRating(program):
    starRating = 0.0
    if (program is not None):
        if (program.starRating is not None):
            try:
                textArray = program.starRating.split("/")
                numerator = float(textArray[0])
                denominator = float(textArray[1])
                starRating = float(10.0*numerator / denominator)
            except:
                starRating = 0.0
    return starRating

###################################################################################################
# This function returns the star rating (float value) for the given progam
###################################################################################################
def GetVcoYear(program):
    year = None
    if (program is not None and program.date is not None):
        year = program.date
    return year

###################################################################################################
# This function returns the icon for the given progam
###################################################################################################	
def GetVcoIcon(channel,program):
    # Create safe names
    icon_channelname = makeSafeFilename(channel.name)+'.png'
    icon_channelnumber = makeSafeFilename(channel.number)+'.png'

    # Default icon
    icon = R(ICON_UNKNOWN)

    # Icon detection
    if (program is not None and program.icon is not None):
        if program.icon.strip() != "":
            icon = program.icon
    elif Core.storage.resource_exists(icon_channelname):
        icon = R(icon_channelname)
    elif Core.storage.resource_exists('logo-'+icon_channelname):
        icon = R('logo-'+icon_channelname)
    elif Core.storage.resource_exists(icon_channelnumber):
        icon = R(icon_channelnumber)
    elif Core.storage.resource_exists('logo-'+icon_channelnumber):
        icon = R('logo-'+icon_channelnumber)
        
    return icon
    
###################################################################################################
# This function converts a time in milliseconds to a time text
###################################################################################################
def GetTimeDisplay(timeInMs):
    timeInSeconds = timeInMs
    return datetime.fromtimestamp(timeInSeconds).strftime(TIME_FORMAT)
    
###################################################################################################
# This function converts a time in milliseconds to a time text
###################################################################################################
def GetDateDisplay(timeInSeconds):
    if timeInSeconds==0:
        return ""
    return datetime.fromtimestamp(timeInSeconds).strftime(DATE_FORMAT)

###################################################################################################
# This function loads the list of all enabled favorites
###################################################################################################
def LoadEnabledFavorites():
    favorites = []
    for favidx in range(1,MAX_FAVORITES+1):
        favorite = LoadFavorite(favidx)
        if (favorite.enable):
            favorites.append(favorite)
    return favorites

###################################################################################################
# This function loads the favorite identified by the index i
###################################################################################################
def LoadFavorite(i):
    enable = Prefs['favorites.' + str(i) + '.enable']
    name   = Prefs['favorites.' + str(i) + '.name']
    list   = Prefs['favorites.' + str(i) + '.list']
    sortBy = Prefs['favorites.' + str(i) + '.sortby']
    return Favorite(i,enable,name,list, sortBy)

###################################################################################################
# This function loads the full channel list from the configured hdhrviewer host
###################################################################################################

def LoadAllChannels(tuneridx):
    # Devices.tunerDevices[tuneridx]
    allChannelsList = []
    allChannelsMap = {}

    tuner=HDHRV2.tunerDevices[tuneridx]

    try:
        jsonLineupUrl = tuner['LineupURL']
        jsonLineup = JSON.ObjectFromURL(jsonLineupUrl,timeout=TIMEOUT_LAN)

        for channel in jsonLineup:
            guideNumber = channel.get('GuideNumber')
            guideName = channel.get('GuideName','')
            videoCodec = channel.get('VideoCodec','')
            audioCodec = channel.get('AudioCodec','')
            streamUrl = channel.get('URL','')

            channelLogo = ICON_DEFAULT_CHANNEL

            channel = Channel(guideNumber,guideName,streamUrl,channelLogo,videoCodec,audioCodec)
            allChannelsList.append(channel)
            allChannelsMap[guideNumber] = channel

    except Exception as inst:
        logError('LoadAllChannels(tuneridx): '+strError(inst))
        logError('tuner='+xstr(tuneridx))

    return ChannelCollection(allChannelsList,allChannelsMap)



###################################################################################################
# This function is taken straight (well, almost) from the HDHRViewer V1 codebase
###################################################################################################
@route(PREFIX + '/CreateVO')
def CreateVO(tuneridx, url, title, year=None, tagline='', summary='', thumb=R(ICON_DEFAULT_CHANNEL), starRating=0, include_container=False, checkFiles=0, videoCodec='mpeg2video',audioCodec='AC3',search=False):

    tuneridx_int=int(tuneridx)
    tuner = HDHRV2.tunerDevices[tuneridx_int]

    jsonData = getDeviceInfoJsonData(tuner)
    logDebug(jsonData)
    modelNumber = jsonData.get('ModelNumber','unknown')
    localIP = tuner['LocalIP']
    deviceID = jsonData.get('DeviceID','unknown')

    uniquekey = url+deviceID+localIP

    logDebug(uniquekey)

    # Only append device ip for search results
    if search and localIP!='':
        title = title+' ['+localIP+']'

    # Allow trancoding only on HDTC-2US
    if modelNumber=='HDTC-2US':
        logInfo('HDTC-2US detected. Transcode='+Prefs['transcode'])
        transcode = Prefs['transcode']
    else:
        logInfo('HDTC-2US not detected. No transcode option.')
        transcode = "default"

    if videoCodec=='MPEG2':
        videoCodec='mpeg2video'
    audioCodec=audioCodec.lower()

    #debugging purposes
    logDebug('tuner_model='+modelNumber+';video_codec='+videoCodec+';audio_codec='+audioCodec+';url='+url)

    if transcode=='auto':
        videoCodec = VideoCodec.H264
        audioCodec = 'ac3'
        #AUTO TRANSCODE
        vo = VideoClipObject(
            rating_key = uniquekey,
            key = Callback(CreateVO, tuneridx=tuneridx, url=url, title=title, year=year, tagline=tagline, summary=summary, thumb=thumb, starRating=starRating, include_container=True, checkFiles=checkFiles, videoCodec=videoCodec,audioCodec=audioCodec,search=search),
            rating = float(starRating),
            title = xstr(title),
            year = xint(year),
            summary = xstr(summary),
            #Plex.tv & Roku3
            tagline = xstr(tagline),
            source_title = xstr(tagline),
            #without duration, transcoding will not work... 
            duration = VIDEO_DURATION,
            thumb = thumb,
            items = [   
                MediaObject(
                    parts = [PartObject(key=(url+"?transcode=heavy"))],
                    container = MEDIA_CONTAINER,
                    video_resolution = 1080,
                    bitrate = 12000, #8000
                    video_codec = videoCodec,
                    audio_codec = audioCodec,
                    audio_channels = AUDIO_CHANNELS,
                    optimized_for_streaming = True
                ),
                MediaObject(
                    parts = [PartObject(key=(url+"?transcode=mobile"))],
                    container = MEDIA_CONTAINER,
                    video_resolution = 720,
                    bitrate = 8000, #2000
                    video_codec = videoCodec,
                    audio_codec = audioCodec,
                    audio_channels = AUDIO_CHANNELS,
                    optimized_for_streaming = True
                ),
                MediaObject(
                    parts = [PartObject(key=(url+"?transcode=internet480"))],
                    container = MEDIA_CONTAINER,
                    video_resolution = 480,
                    bitrate = 2000, #1500
                    video_codec = videoCodec,
                    audio_codec = audioCodec,
                    audio_channels = AUDIO_CHANNELS,
                    optimized_for_streaming = True
                ),
                MediaObject(
                    parts = [PartObject(key=(url+"?transcode=internet240"))],
                    container = MEDIA_CONTAINER,
                    video_resolution = 240,
                    bitrate = 1500, # 720
                    video_codec = videoCodec,
                    audio_codec = audioCodec,
                    audio_channels = AUDIO_CHANNELS,
                    optimized_for_streaming = True
                ),
            ]
        )
    elif transcode=='default':
        vo = VideoClipObject(
            rating_key = uniquekey,
            key = Callback(CreateVO, tuneridx=tuneridx, url=url, title=title, year=year, tagline=tagline, summary=summary, thumb=thumb, starRating=starRating, include_container=True, checkFiles=checkFiles, videoCodec=videoCodec, audioCodec=audioCodec, search=search),
            rating = float(starRating),
            title = xstr(title),
            year = xint(year),
            summary = xstr(summary),
            #Plex.tv & Roku3
            tagline = xstr(tagline),
            source_title = xstr(tagline),
            duration = VIDEO_DURATION,
            thumb = thumb,
            items = [   
                MediaObject(
                    parts = [PartObject(key=(url))],
                    container = MEDIA_CONTAINER,
                    video_resolution = 1080,
                    bitrate = 20000,
                    video_codec = videoCodec,
                    audio_codec = audioCodec,
                    audio_channels = AUDIO_CHANNELS,
                    optimized_for_streaming = True
                )
            ]   
        )
    else:
        if transcode!='none':
            videoCodec = VideoCodec.H264
	    audioCodec = 'AC3'
        vo = VideoClipObject(
            rating_key = uniquekey,
            key = Callback(CreateVO, tuneridx=tuneridx, url=url, title=title, year=year, tagline=tagline, summary=summary, thumb=thumb, starRating=starRating, include_container=True, checkFiles=checkFiles, videoCodec=videoCodec, audioCodec=audioCodec, search=search),
            rating = float(starRating),
            title = xstr(title),
            year = xint(year),
            summary = xstr(summary),
            #Plex.tv & Roku3
            tagline = xstr(tagline),
            source_title = xstr(tagline),
            #without duration, transcoding will not work... 
            duration = VIDEO_DURATION,
            thumb = thumb,
            items = [   
                MediaObject(
                    parts = [PartObject(key=(url+"?transcode="+Prefs["transcode"]))],
                    container = MEDIA_CONTAINER,
                    video_codec = videoCodec,
                    audio_codec = audioCodec,
                    audio_channels = AUDIO_CHANNELS,
                    optimized_for_streaming = True
                )
            ]   
        )

    if include_container:
        return ObjectContainer(objects=[vo])
    else:
        return vo

###################################################################################################
# Utility to convert an object to a string (and mainly handle the NoneType case)
# Credit: from a stackoverflow article
###################################################################################################
def xstr(s):
    if s is None:
        return ''
    else:
        return str(s)

###################################################################################################
# Utility to convert an object to an integer (and handle the NoneType case)
###################################################################################################
def xint(s):
    if (s is None or len(s)==0):
        return None
    else:
        try:
            return int(s)
        except:
            return None
            
###################################################################################################
# Make safe file name for channel logo
###################################################################################################
def makeSafeFilename(inputFilename):     
    try:
        safechars = string.letters + string.digits + "-_."
        return filter(lambda c: c in safechars, inputFilename)
    except:
        return ""

###################################################################################################
# Check if resource exist
###################################################################################################
        
def resourceExist(inputFilename):
	return core.resource_exists(inputFilename)

###################################################################################################
# python 'any' function
###################################################################################################
    
def xany(iterable):
    for element in iterable:
        if element:
            return True
    return False

###################################################################################################
# logging / debuging functions
###################################################################################################

def strError(inst):
    return xstr(type(inst)) + ": " + xstr(inst.args) + ": " + xstr(inst)

def logError(strmsg):
    Log.Error('########## ' + xstr(strmsg))

def logDebug(strmsg):
    Log.Debug('---------- ' + xstr(strmsg))

def logInfo(strmsg):
    Log.Info('********** ' + xstr(strmsg))

def logType(strmsg):
    Log.Debug('---------- ' + xstr(strmsg) + '; Type='+xstr(type(strmsg)))

###################################################################################################
# Plex 4.4 for iOS detection
###################################################################################################   
def iOSPlex44():
    return (Client.Product=='Plex for iOS' and Client.Version == '4.4')
		
###################################################################################################
# Client Information.
###################################################################################################				
def getInfo():
    svrOSver = Platform.OSVersion
    logInfo('******************[System Info]*******************')
    logInfo('Server: '+Platform.OS+' '+svrOSver+' ['+Platform.CPU+']')
    logInfo('PMS   : '+Platform.ServerVersion)
    logInfo('Client: '+Client.Product+' '+Client.Version+' ['+Client.Platform+']')
    logInfo("HDHRV2: "+VERSION)
    logInfo('**************************************************')

###################################################################################################
# Get total channels from {ip}/lineup.json
###################################################################################################
def getTunerTotalChannels(tuner):
    # (tuner) in Devices.tunerDevices
    try:
        jsonURL = tuner['LineupURL']
        jsonData = JSON.ObjectFromURL(jsonURL,timeout=TIMEOUT_LAN)
        totalChannels = len(jsonData)
    except Exception as inst:
        logError('getTunerTotalChannels(tuner): '+strError(inst))
        logError('tuner='+xstr(tuner))
        totalChannels = 0
    return totalChannels

###################################################################################################
# Get info from {ip}/discover.json
# tuner in Devices.tunerDevices
# info = FriendlyName, ModelNumber, FirmwareName, FirmwareVersion, DeviceID, DeviceAuth, TunerCount 
# BaseURL, LineupURL
###################################################################################################

def getDeviceInfo(tuner,info):
    try:
        jsonURL = tuner['DiscoverURL']
        jsonData = JSON.ObjectFromURL(jsonURL,timeout=TIMEOUT_LAN)
        info = jsonData.get(info,'')
    except Exception as inst:
        logError('getDeviceInfo(tuner,info)'+strError(inst))
        logError('tuner='+xstr(tuner))
        logError('info='+xstr(info))
        info = ''
    return info

def getDeviceInfoJsonData(tuner):
    try:
        jsonURL = tuner['DiscoverURL']
        jsonData = JSON.ObjectFromURL(jsonURL,timeout=TIMEOUT_LAN)
        return jsonData
    except Exception as inst:
        logError('getDeviceInfoJsonData(tuner,info)'+strError(inst))
        logError('tuner='+xstr(tuner))
        logError('info='+xstr(info))
        return {}

###################################################################################################
# Get guide url for tuner.
# # (tuner) in Devices.tunerDevices
# http://my.hdhomerun.com/api/guide.php?DeviceAuth={deviceAuth}
###################################################################################################
def getGuideURL(tuneridx):
    try:
        tuner=HDHRV2.tunerDevices[tuneridx]
        deviceAuth = getDeviceInfo(tuner,'DeviceAuth')
        info = URL_HDHR_GUIDE.format(deviceAuth=deviceAuth)
    except Exception as inst:
        logError('getGuideURL(tuneridx); tuneridx='+xstr(tuneridx))
        logError(strError(inst))
        info = ''
    return info


###################################################################################################
# Get HDHomeRun Lineup details from {ip}/lineup.json
# info = GuideNumber, GuideName, VideoCodec, AudioCodec, HD, URL
###################################################################################################
def getLineupInfo(tuner,info):
    try:
        jsonURL = tuner['LineupURL']
        jsonData = JSON.ObjectFromURL(jsonURL,timeout=TIMEOUT_LAN)
        info = jsonData.get(info,'')
    except Exception as inst:
        logError('getLineupInfo(tuner,info)'+strError(inst))
        logError('tuner='+xstr(tuner))
        logError('info='+xstr(info))
        info = ''
    return info

###################################################################################################
# Devices Class Definition
# MultiTuner + Auto Discovery + Manual IP. Future: something to do with storageServers.
###################################################################################################		
class Devices:
    def __init__(self):
        self.storageServers = []
        self.tunerDevices = []
        self.manualTuner()
        self.autoDiscover(False)

    # Auto Discover devices
    def autoDiscover(self,rediscover):
        cacheTime=None
        if rediscover:
            cacheTime=CACHETIME_HDHR_GUIDE
        try:
            response = xstr(HTTP.Request(URL_HDHR_DISCOVER_DEVICES,timeout=TIMEOUT,cacheTime=cacheTime))
            JSONdevices = JSON.ObjectFromString(''.join(response.splitlines()))

            for device in JSONdevices:
                StorageURL = device.get('StorageURL')
                LineupURL = device.get('LineupURL')
                
                if LineupURL is not None:
                    if not xany(d['LocalIP']==device['LocalIP'] for d in self.tunerDevices):
                        device['autoDiscover'] = True
                        self.tunerDevices.append(device)
                    else:
                        logInfo('Skipped '+device['LocalIP'])

                #future
                if StorageURL is not None:
                    self.storageServers.append(device)

        except Exception as inst:
            logError('Devices.autoDiscover(): '+strError(inst))

    # Get manual tuners listed in Settings
    def manualTuner(self):
        try:
            manualTuners = Prefs[PREFS_HDHR_IP]
            if manualTuners is not None:
                # Only add tuners if not 'auto'
                if manualTuners != 'auto':
                    for tunerIP in manualTuners.split():
                        if not xany(d['LocalIP']==tunerIP for d in self.tunerDevices):
                            self.addManualTuner(tunerIP)
                        else:
                            # self.addManualTuner(tunerIP) #test
                            logInfo('Manually defined tuner skipped: '+tunerIP)
            else:
                logInfo('No manually defined tuners.')

        except Exception as inst:
            logError('Devices.manualTuner(): '+strError(inst))

    # Add manual tuners
    def addManualTuner(self,tunerIP):
        try:
            tuner = {}
            tuner['autoDiscover'] = False
            tuner['DeviceID'] = 'Manual'+tunerIP
            tuner['LocalIP'] = tunerIP
            tuner['BaseURL'] = tunerIP
            tuner['DiscoverURL'] = URL_HDHR_DISCOVER.format(ip=tunerIP)
            tuner['LineupURL'] = URL_HDHR_LINEUP.format(ip=tunerIP)
            self.tunerDevices.append(tuner)
            logInfo('Devices.addManualTuner: '+xstr(tuner['LocalIP']))

        except Exception as inst:
            logError('Devices.addManualTuner('+xstr(tunerIP)+'): '+strError(inst))
    
###################################################################################################
# Channel collection class definition, that supports both a map and list version of the same data
###################################################################################################
class ChannelCollection:
    def __init__(self,list,map):
        self.list = list
        self.map = map

###################################################################################################
# Channel class definition
###################################################################################################
class Channel:
    def __init__(self,guideNumber,guideName,streamUrl,channelLogo,videoCodec,audioCodec):
        self.number = guideNumber
        self.name = guideName
        self.streamUrl = streamUrl
        self.program = None
        self.logo = channelLogo
        self.videoCodec = videoCodec
        self.audioCodec = audioCodec
        
    def setProgramInfo(self,program):
        self.program = program
    
    def hasProgramInfo(self):
        return (self.program is not None)

###################################################################################################
# Channel class definition
###################################################################################################
class Program:
    def __init__(self,startTime,stopTime,title,date,subTitle,desc,icon,starRating):
        self.startTime = startTime
        self.stopTime = stopTime
        self.title = title
        self.date = date
        self.subTitle = subTitle
        self.desc = desc
        self.icon = icon
        self.starRating = starRating
        self.next = []
    
###################################################################################################
# Favorite class definition
###################################################################################################
class Favorite:
    def __init__(self,index,enable,name,textList,sortBy):
        self.index = index
        self.enable = enable
        self.name = name
        self.tuner = ''
        self.channels = []
        self.totalChannels = 0 
        if textList is not None:
            textListItems = textList.split()
            self.tuner=textListItems[0]
            for item in textListItems:
                try:
                    if isinstance(float(item), float):
                        self.channels.append(item)
                        self.totalChannels = self.totalChannels + 1
                except ValueError:
                    logInfo("Unable to parse the channel number " + item + " into a number.")
            if sortBy == 'Channel Number':
                try:
                    self.channels.sort(key=float)
                except Exception as inst:
                    logError('Favorite.channels.sort'+strError(inst))

