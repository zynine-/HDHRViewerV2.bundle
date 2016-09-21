# HDHRViewerV2.bundle
Watch Live TV on Plex using HDHomeRun, at home or remotely. Compatibility may vary by Plex Media Server (PMS) version, Plex client version, etc... 

## Current Development/Test Setup
### HDHomeRun
- HDHomeRun PLUS/EXTEND (HDTC-2US) + Firmware: 20160621atest1

### Plex Media Server (PMS)
- PMS 1.1.4.2757 on Windows 10

### Plex Clients
- Chrome (Windows 10)
- Firefox  (Windows 10)
- IE (Windows 10)
- Edge (Windows 10)
- Roku 3
- Amazon Fire TV (2014)
- Android (HTC 10)


## HDHomeRun Compatibility

Compatible with HDHomeRun that have DLNA or HTTP streaming capabilities.

### Compatible
- HDHomeRun PRIME (HDHR3-CC)
- HDHomeRun 4DC (HDHR3-4DC)
- HDHomeRun DUAL (Gen4)
- HDHomeRun CONNECT (HDHR4-2US/2DT)
- HDHomeRun PLUS/EXTEND (HDTC-2US)
- HDHomeRun EXTEND (HDTC-2US-M)

### Not Compatible
- HDHomeRun Dual (HDHR-DT/HDHR-EU/HDHR3-EU/HDHR-US/HDHR3-US) - Please use [HDSurfer Plug-in for HDHomeRun](https://forums.plex.tv/discussion/83233/hdsurfer-plug-in-for-hdhomerun)

## Server Compatibility/Requirement

No known server restrictions at the moment. Trancoding is required for clients for most clients.

## Client Compatibility

Some browser may have playback issues with HTML5 player, disable HTML5 player.

### Full compatibility:
- Android 6 (HTC 10)
- Chrome - Disable HTML5 player if there are playback issues.

### Limited compatibility
- Firefox - Disable HTML5 player
- Plex Media Player (PMP) - PMS does not transcode to PMP, therefore high bandwidth required. No remote viewing capabilities, maybe possible with VPN but still requires high bandwidth. 

### Not Compatible

## Known Anomalies

###Interlacing

Deinterlacing is achieved by replacing xml profiles, <https://github.com/zynine-/PlexDeinterlaceProfiles>

###Slow buffer or stutters on some clients

On some clients, setting a lower stream quality may increase loading, or stutters.
Ways to reduce loading times or stutters:
- Disable HTML5 if you are using a browser
- Set the higher quality, or the highest your network bandwidth/connection allows)
