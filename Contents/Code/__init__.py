# HDHR Viewer V2

import time
import string
from datetime import datetime
import urllib
import os
from lxml import etree

DEBUGMODE            = True
TITLE                = 'HDHR Viewer 2 (1.0.1)'
PREFIX               = '/video/hdhrv2'
VERSION              = '1.0.1'

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
PREFS_TRANSCODE      = 'transcode'
PREFS_XMLTV_MODE     = 'xmltv_mode'
PREFS_XMLTV_FILE     = 'xmltv_file'
PREFS_LOGO_MATCH     = 'channellogo'
PREFS_XMLTV_MATCH    = 'xmltv_match'
PREFS_XMLTV_APIURL   = 'xmltv_api_url'
PREFS_VCODEC         = 'videocodec'
PREFS_ACODEC         = 'audiocodec'
PREFS_ICONDIR        = 'icon_directory'

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
#URL_HDHR_STREAM           = 'http://{ip}:5004/{tuner}/v{guideNumber}'
CACHETIME_HDHR_GUIDE      = 3600 # (s) Default: 3600 = 1 hour

#DEBUG
DEBUG_URL_HDHR_DISCOVER_DEVICES = 'http://192.168.1.11/discover'
DEBUG_URL_HDHR_GUIDE            = 'http://192.168.1.11/api/guide.php?DeviceAuth={deviceAuth}'

#CONSTANTS/PARAMETERS
TIMEOUT = 5                 # XML Timeout (s); Default = 5
TIMEOUT_LAN = 1             # LAN Timeout (s); Default = 1
CACHETIME = 5               # Cache Time (s); Default = 5
MAX_FAVORITES = 10          # Max number of favorites supported; Default = 10
VIDEO_DURATION = 14400000   # Duration for Transcoder (ms); Default = 14400000 (4 hours)
MAX_SIZE = 90971520         # [Bytes] 20971520 = 20MB; Default: 90971520 (100MB)

AUDIO_CHANNELS = 6          # Audio Channels = 2 - stereo; 6 - 5.1
MEDIA_CONTAINER = 'mpegts'  # Default media container = 'mpegts'
VIDEO_CODEC = 'mpeg2video'  # Default video codec = 'mpeg2video'
AUDIO_CODEC = 'ac3'         # Default audio codec = 'ac3'

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

    getInfo()

    tuners=[]
    HDHRV2 = Devices()
    tuners = HDHRV2.tunerDevices
    totalTuners = len(tuners)  
    logInfo('Total Tuners: '+xstr(totalTuners))
    oc = ObjectContainer()
    last_known = False

    # If totally fail to discover...
    if totalTuners==0:
        tuners=Dict['tuners']
        if tuners!=None and len(tuners)>0:
            totalTuners = len(tuners)
            logError('No Tuners Found: Using last know tuners:' + xstr(tuners))
        else:
            logError('No Tuners Found: Unable to load last known tuners')
    
    # If tuners exist, show favorites, all-channels, search.
    if totalTuners>0:
        Dict['tuners'] = tuners
        # Add any enabled favorites
        favoritesList = LoadEnabledFavorites()
        for favorite in favoritesList: 
            ocTitle = favorite.name+' ('+xstr(favorite.totalChannels)+')'
            oc.add(DirectoryObject(key=Callback(FavoriteChannelsMenu, favidx=favorite.index), title=ocTitle, thumb=R(ICON_FAV_LIST)))

        # All Channels - Multi-Tuner support
        for tuneridx, tuner in enumerate(tuners):
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
        errmsg = 'No Tuners Found.'
        oc.add(PopupDirectoryObject(key=Callback(errorMessage,message=errmsg), title=errmsg, art=R(ART), thumb=R(ICON_ERROR)))

    if last_known:
        errmsg = 'Using last known tuners'
        oc.add(PopupDirectoryObject(key=Callback(errorMessage,message=errmsg), title=errmsg, art=R(ART), thumb=R(ICON_ERROR)))

    # Settings / Preference Menu
    oc.add(PrefsObject(title='Settings', thumb=R(ICON_SETTINGS)))

    # Load Channel Icons
    Resources_iconpath = Core.storage.join_path(Core.bundle_path,'Contents','Resources')
    Local_iconpath = Prefs[PREFS_ICONDIR]
    if dirExists(Local_iconpath):
        #Only Show Reload Icons if directory properly configured.
        oc.add(DirectoryObject(key=Callback(LoadChannelIcons), title='Reload Icons', art=R(ART), thumb=R(ICON_SETTINGS)))
        if not dirExists(Resources_iconpath):
            LoadChannelIcons()

    # Dev/Debug purpose
    #oc.add(CreateVO(tuneridx=1, url="http://192.168.1.11/TestVideos/v5134.mpeg" ,title="TestTitle", year="2010", tagline="Tag", summary="summary", starRating=3.5, thumb=ICON_FAV_LIST, videoCodec=None, audioCodec=None,transcode="default"))

    return oc
    
###################################################################################################
# Show all channels for specified tuner
###################################################################################################
@route(PREFIX + '/all-channels')
def AllChannelsMenu(tuneridx):
    
    tuners = Dict['tuners']
    tuneridx=int(tuneridx)
    tuner=tuners[tuneridx]
    tuner_name=tuner.get('LocalIP','unknown')

    oc = ObjectContainer(title1=tuner_name)
    try:           
        allChannels = LoadAllChannels(tuneridx)
        PopulateProgramInfo(tuneridx, allChannels.list, False)
        return AddChannelObjectContainer(oc,tuneridx,tuner['LocalIP'], allChannels.list,False)
        #return AddChannelObjectContainer(oc,tuneridx,'test', allChannels.list)

    except Exception as inst:
        logError('AllChannelsMenu('+xstr(tuneridx)+')')
        logError(strError(inst))
        return AddErrorObjectContainer(oc,'AllChannelsMenu('+xstr(tuneridx)+');'+strError(inst))
    
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
    
    tuners = Dict['tuners']
    favorite = LoadFavorite(favidx)
    ocTitle = favorite.name

    oc = ObjectContainer(title1=ocTitle)

    try:
        
        # If tuner IP is defined in Fav list, and exist in Tuner list
        for tuneridx, tuner in enumerate(tuners):
            if tuner['LocalIP']==favorite.tuner:
                allChannels=LoadAllChannels(tuneridx)
                tuner_defined=True
                break
        
        # If tuner IP not defined in Fav list, assume 1st tuner.
        if not tuner_defined:
            logDebug('Tuner not defined/found in favorite list. Assuming tuner: '+tuners[0]['LocalIP'])
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

    oc = ObjectContainer(title1='Search: '+query,no_cache=True)

    try:
        tuners = Dict['tuners']
        for tuneridx, tuner in enumerate(tuners):
            if not tuner['autoDiscover']:
                if isXmlTvModeHDHomeRun():
                    logInfo('HDHomeRun Search')
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
        logError('SearchResultsChannelsMenu(\''+query+'\'): '+strError(inst))
        return AddErrorObjectContainer(oc,strError(inst))
    return oc

@route(PREFIX + '/load-channel-icons')
def LoadChannelIcons():

    oc = ObjectContainer(title1='Load Channel Icons',no_cache=True)

    try:
        logDebug('LoadChannelIcons')
        Resources_iconpath = Core.storage.join_path(Core.bundle_path,'Contents','Resources')
        Local_iconpath = Prefs[PREFS_ICONDIR]
        #Core.storage.copy_tree(Local_iconpath,Resources_iconpath)

        for filename in Core.storage.list_dir(Local_iconpath):
            src = Core.storage.join_path(Local_iconpath,filename)
            dest = Core.storage.join_path(Resources_iconpath,filename)
            if os.path.isfile(src):
                Core.storage.copy(src,dest)

        return AddErrorObjectContainer(oc,'Done!')
    except Exception as inst:
        logError('Reset: '+strError(inst))
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
        tunerGuideURL = getGuideURL(tuneridx)
        jsonChannelPrograms = JSON.ObjectFromURL(tunerGuideURL,cacheTime=CACHETIME_HDHR_GUIDE)
        if jsonChannelPrograms==None:
            return {}

        allProgramsMap = ProgramMap_HDHomeRun(jsonChannelPrograms,query)

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

    allProgramsMap = {}

    tuners = Dict['tuners']

    if Prefs[PREFS_XMLTV_MODE] != 'disable':
        tuner=tuners[tuneridx]
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
def ProgramMap_RestAPI(jsonChannelPrograms,query=None):
    allProgramsMap = {}
    t = time.time()
    for jsonChannelProgram in jsonChannelPrograms:
        # parse the program and the next programs if they exist
        program = ParseProgramJson(XMLTV_MODE_RESTAPI,jsonChannelProgram['program'])
        jsonNextPrograms = jsonChannelProgram['nextPrograms']
        if jsonNextPrograms is not None:
            for jsonNextProgram in jsonNextPrograms:
                program.next.append(ParseProgramJson(XMLTV_MODE_RESTAPI,jsonNextProgram))
                
        # now associate all channel display names with that same program object
        jsonChannelDisplayNames = jsonChannelProgram['channel']['displayNames']
        for displayName in jsonChannelDisplayNames:
            allProgramsMap[displayName] = program

    logInfo("Time taken to parse RestAPI JSON: "+str(time.time()-t))
            
    return allProgramsMap


def ProgramMap_HDHomeRun(jsonChannelPrograms,query=None):
    allProgramsMap = {}
    t = time.time()

    for jsonChannelProgram in jsonChannelPrograms:
        program=None
        guideNumber = jsonChannelProgram['GuideNumber']
        nextCount=0
        for i, guide in enumerate(jsonChannelProgram.get('Guide','')):
            guideData = ParseProgramJson(XMLTV_MODE_HDHOMERUN,guide)
            guideTitle = guideData.title  # For Search Func.
            guideDesc = guideData.desc    # For Search Func.
            # Current Program
            if(guideData.startTime < t and t < guideData.stopTime):
                if query is None:
                    program = guideData
                # For Search Func.
                elif (query.lower() in guideTitle.lower()) or (query.lower() in guideTitle.lower()):
                    program = guideData

            # Next Programs
            if (guideData.startTime > t) and (program is not None) and (query is None) and (nextCount<int(Prefs["xmltv_show_next_programs_count"])) :
                program.next.append(guideData)
                nextCount+=1

        #If Programs exist
        if program!=None:
            # If no program icon, try to get channel icon, else leave it empty...
            if program.icon=='':
                program.icon=jsonChannelProgram.get('ImageURL','')
            
            # Map all programs, or searched programs.
            allProgramsMap[guideNumber] = program

    logInfo('Time taken to parse/search HDHomeRun JSON: '+str(time.time()-t))            
    return allProgramsMap

def ProgramMap_File(channellist):
    allProgramsMap = {}
    t = time.time()    

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
                if program!=None:
                    allProgramsMap[channelmap] = program
                i+=1
                elem.clear()
            elif c_channelID!=p_channelID:
                i=0
                elem.clear()
            else:
                elem.clear()
            p_channelID=c_channelID
    
    logInfo("Time taken to parse XMLTV: "+str(time.time()-t))

    return allProgramsMap

#####################

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
    if (program is not None and program.icon is not None and program.icon.strip() != ''):
        icon = program.icon
    elif resourceExists(icon_channelname):
        icon = R(icon_channelname)
    elif resourceExists('logo-'+icon_channelname):
        icon = R('logo-'+icon_channelname)
    elif resourceExists(icon_channelnumber):
        icon = R(icon_channelnumber)
    elif resourceExists('logo-'+icon_channelnumber):
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

    tuner = Dict['tuners'][tuneridx]

    try:
        jsonLineupUrl = tuner['LineupURL']
        jsonLineup = JSON.ObjectFromURL(jsonLineupUrl,timeout=TIMEOUT_LAN)

        for channel in jsonLineup:
            guideNumber = channel.get('GuideNumber')
            guideName = channel.get('GuideName','')
            videoCodec = channel.get('VideoCodec','')
            audioCodec = channel.get('AudioCodec','')
            streamUrl = channel.get('URL','')
            HD = xstr(channel.get('HD',''))
            Fav = xstr(channel.get('Favorite',''))
            DRM = xstr(channel.get('DRM',''))

            channelLogo = ICON_DEFAULT_CHANNEL

            channel = Channel(guideNumber,guideName,streamUrl,channelLogo,videoCodec,audioCodec,HD,Fav,DRM)
            allChannelsList.append(channel)
            allChannelsMap[guideNumber] = channel

    except Exception as inst:
        logError('LoadAllChannels(tuneridx): '+strError(inst))
        logError('tuner='+xstr(tuneridx))

    return ChannelCollection(allChannelsList,allChannelsMap)

###################################################################################################
# Utility function to populate the channels, including the program info if enabled in preferences
###################################################################################################

def AddChannelObjectContainer(oc, tuneridx, title, channels, search=False):

    tuneridx_int=int(tuneridx)
    tuner = Dict['tuners'][tuneridx_int]

    jsonData = getDeviceInfoJsonData(tuner)
    modelNumber = jsonData.get('ModelNumber','unknown')
    firmwareName = jsonData.get('FirmwareName','unknown')
    firmwareVersion = jsonData.get('FirmwareVersion','unknown')
    #localIP = tuner['LocalIP']
    localIP = tuner.get('LocalIP','')
    deviceID = jsonData.get('DeviceID','unknown')

    #Debugging info
    logInfo('********************[Tuner]***********************')
    logInfo('Model    :'+modelNumber)
    logInfo('Firmware :'+firmwareName+' '+firmwareVersion)

    #Overwrite PreTranscode setting according to model.
    if modelNumber=='HDTC-2US' and Prefs['transcode'] in ['none','default']:
        logInfo('Transcode:'+Prefs['transcode']+'; Overwrite to none')
        transcode = 'none'
    elif modelNumber=='HDTC-2US':
        logInfo('Transcode:'+Prefs['transcode'])
        transcode = Prefs['transcode']
    else:
        logInfo('Transcode:default/ignore')
        transcode = 'default'
    if Prefs[PREFS_VCODEC]!="default":
        logInfo('VideoCodec Override:'+Prefs[PREFS_VCODEC])
    if Prefs[PREFS_ACODEC]!="default":
        logInfo('AudioCodec Override:'+Prefs[PREFS_ACODEC])
    logInfo('**************************************************')
    logDebug('ch.no'.ljust(6)+'|'+'RptCodec'.ljust(12)+'|'+'CptCodec'.ljust(18)+'|'+'HD'.ljust(2)+'|'+'Fav'.ljust(3)+'|'+'DRM'.ljust(3)+'|'+'url')

    # setup the VideoClipObjects from the channel list
    for channel in channels:
        program = channel.program
        videoCodec = channel.videoCodec
        audioCodec = channel.audioCodec
        RvideoCodec = channel.videoCodec
        RaudioCodec = channel.audioCodec
        HD = channel.HD
        DRM = channel.DRM
        Fav = channel.Fav
        url = channel.streamUrl
        vcoTitle = GetVcoTitle(channel)
        year = GetVcoYear(program)
        tagline = GetVcoTagline(program)
        summary = GetVcoSummary(program)
        starRating = GetVcoStarRating(program)
        thumb = GetVcoIcon(channel,program)

        # Only append device ip for search results
        if search and localIP!='':
            vcoTitle = vcoTitle+' ['+localIP+']'

        #If codec not defined/available (older firmware), assume default codec.
        if RvideoCodec in ['',None]:
            logError('Video Codec not defined. Are you running the latest firmware? Trying videoCodec='+VIDEO_CODEC)
            videoCodec=VIDEO_CODEC
            RvideoCodec=VIDEO_CODEC
        if RaudioCodec in ['',None]:
            logError('Audio Codec not defined. Are you running the latest firmware? Trying audioCodec='+AUDIO_CODEC)
            audioCodec=AUDIO_CODEC
            RaudioCodec=AUDIO_CODEC

        #VideoCodec correction
        if modelNumber=='HDTC-2US' and transcode not in ['default','none']:
            videoCodec=VideoCodec.H264
        elif RvideoCodec.lower()=='mpeg2':
            videoCodec='mpeg2video'
        else:
            videoCodec=RvideoCodec.lower()

       #AudioCodec correction
        if RaudioCodec.lower()=='aac':
            audioCodec='aac_latm'
        elif RaudioCodec.lower()=='mpeg':
            audioCodec='mp2'
        else:
            audioCodec=audioCodec.lower()
            audioCodec=RaudioCodec.lower()

        #VideoCodec override
        if Prefs[PREFS_VCODEC]=='plex':
            videoCodec=None
        elif Prefs[PREFS_VCODEC]!='default':
            videoCodec=Prefs[PREFS_VCODEC]

        #AudioCodec override
        if Prefs[PREFS_ACODEC]=='plex':
            audioCodec=None
        elif Prefs[PREFS_ACODEC]!='default':
            audioCodec=Prefs[PREFS_ACODEC]

        #tempfix for iOS Plex 4.4
        if iOSPlex44(): 
            vcoTitle = vcoTitle.replace(' ',' ')
            if tagline is not None:
                tagline = tagline.replace(' ',' ')
            if summary is not None:
                summary = summary.replace(' ',' ')

        #debugging purposes
        logDebug(channel.number.ljust(6)+'|'+(RvideoCodec+'/'+RaudioCodec).ljust(12)+'|'+(xstr(videoCodec)+'/'+xstr(audioCodec)).ljust(18)+'|'+HD.ljust(2)+'|'+Fav.ljust(3)+'|'+DRM.ljust(3)+'|'+url)

        oc.add(CreateVO(tuneridx=tuneridx, url=url, title=vcoTitle, year=year, tagline=tagline, summary=summary, starRating=starRating, thumb=thumb,
                        number=channel.number, name=channel.name, thumb_url=thumb,
                        videoCodec=videoCodec, audioCodec=audioCodec,transcode=transcode))
    return oc

###################################################################################################
# Create Video Object
###################################################################################################
@route(PREFIX + '/CreateVO')
def CreateVO(tuneridx, url, title, year=None, tagline='', summary='', thumb=None, starRating=0,  
             videoCodec=None,audioCodec=None,transcode='default',
             number='None',name='None',
             include_container=False,
             thumb_url=None,
             #checkFiles=0, includeBandwidths=1,
             **kwargs):

    uniquekey = str(tuneridx)+url

    if transcode=='auto':
        #Auto Transcode for HDTC-2US
        vo = VideoClipObject(
            rating_key = uniquekey,
            key = Callback(CreateVO, tuneridx=tuneridx, url=url, title=title, year=year, tagline=tagline, summary=summary, starRating=starRating, 
                           videoCodec=videoCodec,audioCodec=audioCodec,transcode=transcode,
                           thumb=thumb,
                           #checkFiles=checkFiles, includeBandwidths=includeBandwidths,
                           include_container=True),
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
                    bitrate = 8000, #8000 #12000
                    video_codec = videoCodec,
                    audio_codec = audioCodec,
                    audio_channels = AUDIO_CHANNELS,
                    optimized_for_streaming = True
                ),
                MediaObject(
                    parts = [PartObject(key=(url+"?transcode=mobile"))],
                    container = MEDIA_CONTAINER,
                    video_resolution = 720,
                    bitrate = 2000, #2000 #8000
                    video_codec = videoCodec,
                    audio_codec = audioCodec,
                    audio_channels = AUDIO_CHANNELS,
                    optimized_for_streaming = True
                ),
                MediaObject(
                    parts = [PartObject(key=(url+"?transcode=internet480"))],
                    container = MEDIA_CONTAINER,
                    video_resolution = 480,
                    bitrate = 1500, #1500 #2000
                    video_codec = videoCodec,
                    audio_codec = audioCodec,
                    audio_channels = AUDIO_CHANNELS,
                    optimized_for_streaming = True
                ),
                MediaObject(
                    parts = [PartObject(key=(url+"?transcode=internet240"))],
                    container = MEDIA_CONTAINER,
                    video_resolution = 240,
                    bitrate = 720, # 720 #1500
                    video_codec = videoCodec,
                    audio_codec = audioCodec,
                    audio_channels = AUDIO_CHANNELS,
                    optimized_for_streaming = True
                ),
            ]
        )
    elif transcode in ['default','none']:
        #For HDTC-2US(transcode=none) or other tuners.
        if transcode=='none':
            mo_url=url+'?transcode=none'
        else:
            mo_url=url
        vo = VideoClipObject(
            rating_key = uniquekey,
            key = Callback(CreateVO, tuneridx=tuneridx, url=url, title=title, year=year, tagline=tagline, summary=summary, thumb=thumb, starRating=starRating, 
                           videoCodec=videoCodec,audioCodec=audioCodec,transcode=transcode,
                           #checkFiles=checkFiles, includeBandwidths=includeBandwidths,
                           include_container=True),
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
                    parts = [PartObject(key=(mo_url))],
                    container = MEDIA_CONTAINER,
                    video_resolution = 1080,
                    #bitrate = 20000,
                    video_codec = videoCodec,
                    audio_codec = audioCodec,
                    audio_channels = AUDIO_CHANNELS,
                    optimized_for_streaming = True
                )
            ]   
        )
    else:
        #For HDTC-2US H264
        vo = VideoClipObject(
            rating_key = uniquekey,
            key = Callback(CreateVO, tuneridx=tuneridx, url=url, title=title, year=year, tagline=tagline, summary=summary, thumb=thumb, starRating=starRating, 
                           videoCodec=videoCodec,audioCodec=audioCodec,transcode=transcode,
                           #checkFiles=checkFiles, includeBandwidths=includeBandwidths,
                           include_container=True),
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
                    parts = [PartObject(key=(url+'?transcode='+transcode))],
                    container = MEDIA_CONTAINER,
                    #video_resolution = 1080,
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
        
def resourceExists(inputFilename):
	return Core.storage.resource_exists(inputFilename)  

def fileExists(inputFilepath):
    return os.path.exists(inputFilepath)

def dirExists(inputDir):
    return Core.storage.dir_exists(inputDir)

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
# Client detection
###################################################################################################   
def iOSPlex44():
    return (Client.Product=='Plex for iOS' and Client.Version == '4.4')

###################################################################################################
# Error Msg
###################################################################################################   
def errorMessage(message):
	return ObjectContainer(header="Error", message=message)
		
###################################################################################################
# Client Information.
###################################################################################################				
def getInfo():
    #svrOSver = Platform.OSVersion
    logInfo('******************[System Info]*******************')
    logInfo('Server: '+Platform.OS+' '+Platform.OSVersion+' ['+Platform.CPU+']')
    logInfo('PMS   : '+Platform.ServerVersion)
    logInfo('Client: '+Client.Product+' '+Client.Version+' ['+Client.Platform+']')
    logInfo("HDHRV2: "+VERSION)
    logInfo('*******************[Settings]*********************')
    logInfo('HDHomerunIP........:'+Prefs[PREFS_HDHR_IP])
    logInfo('Transcode..........:'+Prefs[PREFS_TRANSCODE])
    logInfo('XMLTV Mode.........:'+Prefs[PREFS_XMLTV_MODE])
    logInfo('XMLTV File.........:'+Prefs[PREFS_XMLTV_FILE])
    logInfo('XMLTV URL..........:'+Prefs[PREFS_XMLTV_APIURL])
    logInfo('XMLTV Match........:'+Prefs[PREFS_XMLTV_MATCH])
    logInfo('VideoCodec Override:'+Prefs[PREFS_VCODEC])
    logInfo('AudioCodec Override:'+Prefs[PREFS_ACODEC])
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
        tuners = Dict['tuners']
        tuner=tuners[tuneridx]
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
        self.autoDiscover()

    # Auto Discover devices
    def autoDiscover(self):
        cacheTime=None
        try:
            response = xstr(HTTP.Request(URL_HDHR_DISCOVER_DEVICES,timeout=TIMEOUT,cacheTime=cacheTime))
            JSONdevices = JSON.ObjectFromString(''.join(response.splitlines()))

            for device in JSONdevices:
                StorageURL = device.get('StorageURL')
                LineupURL = device.get('LineupURL')
                
                if LineupURL is not None:
                    if not xany(d['LocalIP']==device['LocalIP'] for d in self.tunerDevices):
                        device['autoDiscover'] = True
                        logInfo('Adding auto discovered tuner: '+device['LocalIP'])
                        self.tunerDevices.append(device)
                    else:
                        logInfo('Auto discovered tuner skipped (duplicate): '+device['LocalIP'])

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
                logInfo('No manually defined tuners')

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
            logInfo('Adding manually defined tuner: '+xstr(tuner['LocalIP']))

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
    def __init__(self,guideNumber,guideName,streamUrl,channelLogo,videoCodec,audioCodec,HD,Fav,DRM):
        self.number = guideNumber
        self.name = guideName
        self.streamUrl = streamUrl
        self.program = None
        self.logo = channelLogo
        self.videoCodec = videoCodec
        self.audioCodec = audioCodec
        self.HD = HD
        self.Fav = Fav
        self.DRM = DRM
        
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



