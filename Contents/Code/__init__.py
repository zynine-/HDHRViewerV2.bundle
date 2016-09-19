###################################################################################################
# HDHRViewer v2
#
# Known Issues:
#   * Won't show xmltv program info when there is nothing showing for that channel (which is fine) 
#     BUT it also doesn't show what's coming next in this case (not fine).  Unfortunately it is 
#     an overall design flaw with the xmltv rest api.  Not a common case so probably lower 
#     priority for now.
###################################################################################################

import time
import string
from datetime import datetime
import urllib
import os
from lxml import etree

TITLE                = 'HDHR Viewer 2'
PREFIX               = '/video/hdhrviewer_v2'
VERSION              = '0.07c'
ART                  = 'art-default.jpg'
ICON                 = 'icon-default.png'
SUBBED_LIST_ICON     = 'icon-subscribed.png'
FAVORITE_LIST_ICON   = 'icon-fav.png'
DEFAULT_CHANNEL_ICON = 'icon-subscribed.png'
SETTINGS_ICON        = 'icon-settings.png'

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
URL_HDHR_DISCOVER    = 'http://{ip}/discover.json'
URL_HDHR_GUIDE       = 'http://my.hdhomerun.com/api/guide.php?DeviceAuth={deviceAuth}'
URL_HDHR_LINEUP      = 'http://{ip}/lineup.json'
URL_HDHR_STREAM      = 'http://{ip}:5004/{tuner}/v{guideNumber}'
CACHETIME_HDHR_GUIDE = 3600 # (s) Default: 3600 = 1 hour


#CONSTANTS/PARAMETERS
TIMEOUT = 5                 # XML Timeout (s)
CACHETIME = 5              # Cache Time (s) Default : 5s
MAX_FAVORITES = 10          # Max number of favorites supported
VIDEO_DURATION = 14400000   # Duration for Transcoder (ms) 14400000 = 4 hours
MAX_SIZE = 90971520			# [Bytes] 20971520 = 20MB Default: 90971520 (100MB)


###################################################################################################
# Entry point - set up default values for all containers
###################################################################################################
def Start():

    Plugin.AddViewGroup('InfoList', viewMode='InfoList', mediaType='items')

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
   
    GetInfo()
    favoritesList = LoadEnabledFavorites()
    oc = ObjectContainer(view_group='InfoList')
    
    # add All Channels menu (displays all channels the user is subscribed to)
    oc.add(DirectoryObject(key=Callback(AllChannelsMenu), title='All Channels', thumb=R(SUBBED_LIST_ICON)))

    # add any enabled favorites
    for favorite in favoritesList:
        oc.add(DirectoryObject(key=Callback(FavoriteChannelsMenu, index=favorite.index), title=favorite.name, thumb=R(FAVORITE_LIST_ICON)))

    # search programs playing now
    if isXmlTvModeRestApi():
        oc.add(InputDirectoryObject(key=Callback(SearchResultsChannelsMenu), title='Search Playing Now', thumb=R(SUBBED_LIST_ICON)))
    
    # finally, include the settings menu
    oc.add(PrefsObject(title='Settings', thumb=R(SETTINGS_ICON)))
 
    return oc

    
###################################################################################################
# This function produces a directory for all channels the user is subscribed to
###################################################################################################
@route(PREFIX + '/all-channels')
def AllChannelsMenu():
    allChannels = LoadAllChannels()
    # populate the program info for all of the channels with no partial query
    PopulateProgramInfo(allChannels.list, False)        
    # now create the object container with all of the channels as video clip objects, and return
    return BuildChannelObjectContainer("All Channels", allChannels.list)


###################################################################################################
# This function produces a directory for all channels the user is subscribed to
# Note, we only show program info for the favorites, because the full channel list can be a bit too
# large (well, for folks subscribing to cable)
###################################################################################################
@route(PREFIX + '/favorite-channels')
def FavoriteChannelsMenu(index):

    favorite = LoadFavorite(index)
    allChannels = LoadAllChannels()
    
    channelList = []
    for channelNumber in favorite.channels:
        channel = allChannels.map.get(channelNumber)
        if (channel is not None):
            channelList.append(channel)

    # populate the program info for all of the channels
    PopulateProgramInfo(channelList, True)        

    # now create the object container with all of the channels as video clip objects, and return
    return BuildChannelObjectContainer(favorite.name,channelList)

###################################################################################################
# This function produces a directory for all channels whose programs match the specified query
# key words
###################################################################################################
@route(PREFIX + '/search-channels')
def SearchResultsChannelsMenu(query):

    allChannels = LoadAllChannels()

    # Execute the search, and return a map of channel display-names to program
    # load all programs into a map (from channel display name -> program)
    allProgramsMap = {}
    

    xmltvApiUrl = ConstructApiUrl(None,False,query)
    allProgramsMap = {}
    try:
        jsonChannelPrograms = JSON.ObjectFromURL(xmltvApiUrl)
        allProgramsMap = BuildChannelToProgramMapFromProgramJson(jsonChannelPrograms)
    except Exception as inst:
        Log.Error(type(inst) + ": " + xstr(inst.args) + ": " + xstr(inst))
        return

    # build the channel result set
    # basically for any channels that were in the resulting programs, try to match the channel numbers
    # from HDHR with the display names.
    channels = []
    for channel in allChannels.list:
        try:
            program = allProgramsMap[channel.number]
            channel.setProgramInfo(program)
            channels.append(channel)
        except KeyError:
            pass

    # now create the object container with all of the channels as video clip objects, and return
    return BuildChannelObjectContainer("Search: " + query,channels)
    

    
###################################################################################################
# Utility function to populate the channels, including the program info if enabled in preferences
###################################################################################################
def BuildChannelObjectContainer(title, channels):
    # Create the object container and then add in the VideoClipObjects
    oc = ObjectContainer(title2=title)

    # setup the VideoClipObjects from the channel list
    for channel in channels:
        program = channel.program
        oc.add(CreateVO(url=channel.streamUrl,title=GetVcoTitle(channel), year=GetVcoYear(program), tagline=GetVcoTagline(program), summary=GetVcoSummary(program), starRating=GetVcoStarRating(program), thumb=GetVcoIcon(channel,program)))
    return oc
    

###################################################################################################
# This function populates the channel with XMLTV program info coming from the xmltv rest service
###################################################################################################
def PopulateProgramInfo(channels, partialQuery):

    allProgramsMap = {}
    
	#restapi
    if isXmlTvModeRestApi():
    # load all programs into a map (from channel display name -> program)
        xmltvApiUrl = ConstructApiUrl(channels,partialQuery)
        Log.Debug("xmltvApiUrl:"+xmltvApiUrl)
        try:
            jsonChannelPrograms = JSON.ObjectFromURL(xmltvApiUrl)
            allProgramsMap = BuildChannelToProgramMapFromProgramJson(jsonChannelPrograms)
        except Exception as inst:
            Log.Error(xstr(type(inst)) + ": " + xstr(inst.args) + ": " + xstr(inst))
            return
    #xmltv hdhomerun
    elif ixXmlTvModeHDHomeRun():
        xmltvApiUrl = URL_HDHR_GUIDE.format(deviceAuth=GetDeviceAuth())
        
        try:
            jsonChannelPrograms = JSON.ObjectFromURL(xmltvApiUrl,cacheTime=CACHETIME_HDHR_GUIDE)
            allProgramsMap = BuildChannelToProgramMapFromProgramJson(jsonChannelPrograms)
        except Exception as inst:
            Log.Error(xstr(type(inst)) + ": " + xstr(inst.args) + ": " + xstr(inst))
            return
            
    #xmltv file mode
    elif isXmlTvModeFile():
        channelList = []
        try:
            for channel in channels:
                if Prefs[PREFS_XMLTV_MATCH] == 'name':
                    channelList.append(channel.name)
                else:
                    channelList.append(channel.number)
            allProgramsMap = BuildChannelToProgramMapFromFile(channelList)
        except Exception as inst:
            Log.Error(xstr(type(inst)) + ": " + xstr(inst.args) + ": " + xstr(inst))
            return
    else:
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
def BuildChannelToProgramMapFromProgramJson(jsonChannelPrograms):
    allProgramsMap = {}
    
    t = time.time()
    
    if isXmlTvModeRestApi():
        for jsonChannelProgram in jsonChannelPrograms:
            # parse the program and the next programs if they exist
            program = ParseProgramJson(jsonChannelProgram["program"])
            jsonNextPrograms = jsonChannelProgram["nextPrograms"]
            if jsonNextPrograms is not None:
                for jsonNextProgram in jsonNextPrograms:
                    program.next.append(ParseProgramJson(jsonNextProgram))
                
            # now associate all channel display names with that same program object
            jsonChannelDisplayNames = jsonChannelProgram["channel"]["displayNames"]
            for displayName in jsonChannelDisplayNames:
                #Log.Debug(displayName)
                allProgramsMap[displayName] = program
    elif ixXmlTvModeHDHomeRun():
        for jsonChannelProgram in jsonChannelPrograms:
            # parse the program and the next programs if they exist
            totalPrograms = len(jsonChannelProgram["Guide"])
            program = ParseProgramJson(jsonChannelProgram["Guide"][0])
            i=0
            while (program.stopTime < time.time() and i<totalPrograms):
                program = ParseProgramJson(jsonChannelProgram["Guide"][i])
                i=i+1
            jsonNextPrograms = jsonChannelProgram["Guide"][i:min(int(Prefs["xmltv_show_next_programs_count"])+i,totalPrograms)]
            if jsonNextPrograms is not None:
                for jsonNextProgram in jsonNextPrograms:
                    program.next.append(ParseProgramJson(jsonNextProgram))
            if program.icon=="":
                program.icon=jsonChannelProgram.get("ImageURL","")
            jsonChannelDisplayNames = jsonChannelProgram.get("GuideNumber")
            allProgramsMap[jsonChannelDisplayNames] = program
            
    Log.Debug("Time taken to parse JSON channel program: "+str(time.time()-t))
            
    return allProgramsMap

#XMLTV iterparse     
def BuildChannelToProgramMapFromFile(channellist):

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
            
            
            if currTime<stopTime and c_channelID==p_channelID and i<=3 and c_channelID in channelIDs:
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
    
    Log.Debug("Time taken to parse XMLTV: "+str(time.time()-t))

    return allProgramsMap
    
    
###################################################################################################
# This function returns whether the xmltv_mode is set to restapi or hdhomerun
###################################################################################################
def isXmlTvModeRestApi():
    xmltv_mode = xstr(Prefs[PREFS_XMLTV_MODE])
    return (xmltv_mode == XMLTV_MODE_RESTAPI)
    
def ixXmlTvModeHDHomeRun():
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
        if Prefs["xmltv_match"] == "name":
            csv = ",".join([channel.name for channel in channels])
        else:
            csv = ",".join([channel.number for channel in channels])
        paramMap["channels"] = csv
        
    xmltvApiUrl += "?" + urllib.urlencode(paramMap)
    return xmltvApiUrl
                        
###################################################################################################
# This function parses a Program json object
###################################################################################################
def ParseProgramJson(jsonProgram):
    #isXmlTvModeRestApi
    if isXmlTvModeRestApi():
        startTime = int(jsonProgram.get("start"))/1000
        stopTime = int(jsonProgram.get("stop"))/1000
        title = xstr(jsonProgram.get("title",""))
        date = xstr(jsonProgram.get("date",0))
        subTitle = xstr(jsonProgram.get("subtitle",""))
        desc = xstr(jsonProgram.get("desc",""))
        starRating = xstr(jsonProgram.get("starRating",""))
        icon = xstr(jsonProgram.get("icon",""))
    else:
        startTime = int(jsonProgram.get("StartTime"))
        stopTime = int(jsonProgram.get("EndTime"))
        title = xstr(jsonProgram.get("Title"))
        date = GetDateDisplay(jsonProgram.get("OriginalAirdate",0))
        subTitle = xstr(jsonProgram.get("Affiliate",""))
        desc = xstr(jsonProgram.get("Synopsis",""))
        starRating = xstr("")
        icon = xstr(jsonProgram.get("ImageURL",""))
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
    if Core.storage.resource_exists(channel.logo):
        icon = R(channel.logo)
    else:
        #Log.Debug("Missing channel logo (" + channel.logo + ") for " + channel.number + " - " + channel.name)
        icon = R(DEFAULT_CHANNEL_ICON)
        
    if (program is not None and program.icon is not None and ("restapi" in Prefs["channellogo"] or "hdhomerun" in Prefs["channellogo"])):
        if program.icon != "":
            icon = program.icon
            
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
    for i in range(1,MAX_FAVORITES+1):
        favorite = LoadFavorite(i)
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
def LoadAllChannels():
    allChannelsList = []
    allChannelsMap = {}

    jsonLineupUrl = URL_HDHR_LINEUP.format(ip=Prefs[PREFS_HDHR_IP])
    jsonLineup = JSON.ObjectFromURL(jsonLineupUrl,timeout=TIMEOUT)
    
    for channel in jsonLineup:
        guideNumber = channel.get('GuideNumber')
        guideName = channel.get('GuideName','')
        streamUrl = URL_HDHR_STREAM.format(ip=Prefs[PREFS_HDHR_IP],tuner=Prefs[PREFS_HDHR_TUNER],guideNumber=guideNumber)
        if (guideName=='' or 'number' in Prefs[PREFS_LOGO_MATCH]):
            channelLogo = "logo-"+makeSafeFilename(guideNumber)+".png"
        elif 'name' in Prefs[PREFS_LOGO_MATCH]:
            channelLogo = "logo-"+makeSafeFilename(guideName)+".png"
        else:
            channelLogo = DEFAULT_CHANNEL_ICON

        channel = Channel(guideNumber,guideName,streamUrl,channelLogo)
        allChannelsList.append(channel)
        allChannelsMap[guideNumber] = channel

    allChannels = ChannelCollection(allChannelsList,allChannelsMap)
    return allChannels
    

###################################################################################################
# Get HDHomeRun DeviceAuth ID
###################################################################################################
def GetDeviceAuth():
    jsonDiscoverUrl = URL_HDHR_DISCOVER.format(ip=Prefs[PREFS_HDHR_IP])
    jsonDiscover = JSON.ObjectFromURL(jsonDiscoverUrl,timeout=TIMEOUT)
    DeviceAuth = jsonDiscover.get("DeviceAuth")
    return DeviceAuth
    
    
###################################################################################################
# This function is taken straight (well, almost) from the HDHRViewer codebase
###################################################################################################
@route(PREFIX + "/CreateVO")
def CreateVO(url, title, year=None, tagline="", summary="", thumb=R(DEFAULT_CHANNEL_ICON), starRating=0, include_container=False, checkFiles=0):
    #v0.4 auto transcode based off lazybones code with some modifications
    #v0.5 transcode rewritten and corrected.
    
    if Prefs["transcode"]=="auto":
        #AUTO TRANSCODE
        vo = VideoClipObject(
            rating_key = url,
            key = Callback(CreateVO, url=url, title=title, year=year, tagline=tagline, summary=summary, thumb=thumb, starRating=starRating, include_container=True, checkFiles=checkFiles),
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
                    container = "mpegts",
                    video_resolution = 1080,
                    bitrate = 8000,
                    video_codec = VideoCodec.H264,
                    audio_codec = "AC3",
                    audio_channels = 2,
                    optimized_for_streaming = False
                ),
                MediaObject(
                    parts = [PartObject(key=(url+"?transcode=mobile"))],
                    container = "mpegts",
                    video_resolution = 720,
                    bitrate = 2000,
                    video_codec = VideoCodec.H264,
                    audio_codec = "AC3",
                    audio_channels = 2,
                    optimized_for_streaming = False
                ),
                MediaObject(
                    parts = [PartObject(key=(url+"?transcode=internet480"))],
                    container = "mpegts",
                    video_resolution = 480,
                    bitrate = 1500,
                    video_codec = VideoCodec.H264,
                    audio_codec = "AC3",
                    audio_channels = 2,
                    optimized_for_streaming = False
                ),
                MediaObject(
                    parts = [PartObject(key=(url+"?transcode=internet240"))],
                    container = "mpegts",
                    video_resolution = 240,
                    bitrate = 720,
                    video_codec = VideoCodec.H264,
                    audio_codec = "AC3",
                    audio_channels = 2,
                    optimized_for_streaming = False
                ),
            ]
        )
    elif Prefs["transcode"]=="none":
        vo = VideoClipObject(
            rating_key = url,
            key = Callback(CreateVO, url=url, title=title, year=year, tagline=tagline, summary=summary, thumb=thumb, starRating=starRating, include_container=True, checkFiles=checkFiles),
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
                    parts = [PartObject(key=(url))],
                    container = "mpegts",
                    video_resolution = 1080,
                    bitrate = 20000,
                    video_codec = "mpeg2video", #0.07a: changed for all pre and 0.9.17.2
                    audio_codec = "AC3",
                    audio_channels = 2,
                    optimized_for_streaming = False
                )
            ]   
        )
    else:
        #force transcode reintroduced in v0.5
        Log.Debug(url+"?transcode="+Prefs["transcode"])
        vo = VideoClipObject(
            rating_key = url,
            key = Callback(CreateVO, url=url, title=title, year=year, tagline=tagline, summary=summary, thumb=thumb, starRating=starRating, include_container=True, checkFiles=checkFiles),
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
                    container = "mpegts",
                    video_codec = VideoCodec.H264,
                    audio_codec = "AC3",
                    audio_channels = 2,
                    optimized_for_streaming = False
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
        return ' '
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

        
def resourceExist(inputFilename):
	return core.resource_exists(inputFilename)
		
###################################################################################################
# Client Information.
###################################################################################################				
def GetInfo():
    Log.Debug("PMS CPU            : "+Platform.CPU)
    Log.Debug("PMS OS             : "+Platform.OS)
    Log.Debug("PMS OS Version     : "+Platform.OSVersion)
    Log.Debug("PMS Version        : "+Platform.ServerVersion)
    Log.Debug("Client Platform    : "+Client.Platform)
    Log.Debug("Client Product     : "+Client.Product)
    Log.Debug("Client Version     : "+Client.Version)
    Log.Debug("HDHRV2 Version     : "+VERSION)
    Log.Debug("AppSupportPath     : "+Core.app_support_path)
    Log.Debug("PlugInBundle       : "+Core.storage.join_path(Core.app_support_path, Core.config.bundles_dir_name))
    Log.Debug("PluginSupportFiles : "+Core.storage.join_path(Core.app_support_path, Core.config.plugin_support_dir_name))
    
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
    def __init__(self,guideNumber,guideName,streamUrl,channelLogo):
        self.number = guideNumber
        self.name = guideName
        self.streamUrl = streamUrl
        self.program = None
        self.logo = channelLogo
        
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
        self.channels = []
        if textList is not None:
            for item in textList.split():
                try:
                    self.channels.append(item)
                except ValueError:
                    Log.Error("Unable to parse the channel number " + item + " into a number.  Please make sure the list is space separated.")
            if sortBy == 'Channel Number':
                self.channels.sort(key=float)
