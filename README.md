![GitHub release](https://img.shields.io/github/release/zynine-/HDHRViewerV2.bundle.svg?style=for-the-badge)

# HDHRViewerV2.bundle
Watch Live TV on Plex using HDHomeRun, at home or remotely. Compatibility may vary by Plex Media Server (PMS) version, Plex client version, etc... 

# Getting Started
## 1. Installation
### Method 1 : Unsupported AppStore V2 (UAS V2)
This is the best method. **HDHR Viewer 2** can be updated easily through the **UAS V2** interface.
**UAS V2** is available at <https://forums.plex.tv/discussion/202282/unsupported-appstore-v2-as-in-totally-unsupported/p1>

### Method 2 : Manual Installation
Copy **HDHRViewerV2.bundle** to Plex Plug-in Directory.

1. Git clone or download the [latest github copy](https://github.com/zynine-/HDHRViewerV2.bundle/archive/master.zip).
2. Unzip and rename the folder to **HDHRViewerV2.bundle**
3. Copy the folder to Plex Media Server plug-in folder. [Read more: How do I find the Plug-Ins folder?](https://support.plex.tv/hc/en-us/articles/201106098-How-do-I-find-the-Plug-Ins-folder-)

4. Make sure the directory structure looks like:
```
Plug-ins
  |_ HDHRViewerV2.bundle
    |_ Contents
```

### Method 3 : Scripts
Run install scripts included. (Limited OS)

## 2. Initial Plug-in Settings/Preferences

Most Plex clients can't access the Plug-in Settings/Preferences. Use Plex/Web to configure it.
	Open your browser to the Plex Web Admin page, select Channels, and you should see the HDHR Viewer Icon in the list.
	If not, then go back to step 1 and correct the location where you copied the plgin package files

### 0.9.x and above:
Multiple tuners are supported, and tuners are automatically discovered. Tuners can be manually define in **HDHomeRun IP**. You can manually list multiple tuners, with space delimited. See examples below.

For full automatic discover (requires internet connection). Set **HDHomeRun IP:**
>auto

Example of manual discover + multiple tuner + automatic discovery. Set **HDHomeRun IP:**
>192.168.1.111 192.168.1.112 192.168.1.113

## 3. Generate required codec (PMS 0.9.17.x to 1.3.x, I think this was fixed with PMS 1.4.x)

With Plex Media Server 0.9.17.x to 1.3.x, there was a change in the Plex transcoder which caused playback issue on most clients for first time users. To fix this problem, download a short clip from your HDHomeRun device, and add it to your PMS library, and play it. Now try using the **HDHR Viewer 2** again.

### 1. Download a short clip from your HDHomeRun tuner.
Download a short clip from your HDHomeRun device using your web browser:

>http://{tuner_ip}:5004/auto/v{channel.number}?duration={time_in_seconds}

Example (tuner_ip=192.168.1.111; channel=2.1; duration=5 seconds):

>http://192.168.1.111:5004/auto/v2.1?duration=5

### 2. Add to Plex Library

Add the videos to your **Movies** or **Home Videos** library.

### 3. Play the added video

Play the video and it should generate the required AC3 codec.

### 4. Now try using the plug-in.

Go to **HDHR Viewer 2**, and try playing a video stream.

## Common Issues and Resolution

### Android devices (I think this was fixed with PMS 1.4.x)
Certain android devices will have issue with playback. This is due to **Plex Media Server (PMS)** not transcoding the **ac3** audio stream to **aac** properly. You can try to change the audio codec listed **Android.xml** profile in PMS Resources folder from **aac** to **mp3**.

### For other issues
Go to <https://github.com/zynine-/HDHRViewerV2.bundle/issues?q=is%3Aissue+is%3Aopen+label%3A%22common+issues%22>

## HDHomeRun Compatibility

Compatible with HDHomeRun that have DLNA or HTTP streaming capabilities.
Recommended minimum firmware: 20161107

### Compatible
- HDHomeRun PRIME (HDHR3-CC)
- HDHomeRun 4DC (HDHR3-4DC)
- HDHomeRun DUAL (Gen4)
- HDHomeRun CONNECT (HDHR4-2US/2DT)
- HDHomeRun PLUS/EXTEND (HDTC-2US)
- HDHomeRun EXTEND (HDTC-2US-M)

### Not Compatible
- HDHomeRun DUAL (HDHR3-US/EU/DT)
- HDHomeRun DUAL (HDHR2-US/DT)
- HDHomeRun DUAL (HDHR-US/EU/DT)

Please use [HDSurfer Plug-in for HDHomeRun](https://forums.plex.tv/discussion/83233/hdsurfer-plug-in-for-hdhomerun)

## Server Compatibility/Requirement

Standard Plex requirement for streaming to Plex Home Theater (PHT)

High CPU requirement for transcoding to other clients (Web/Android/Roku/FireTV/etc…). Typical NAS devices may not have capable CPU for transcoding. Not compatible with Nvidia Shields (unless rooted, due to elevated privilages required for File-based functions (XMLTV, icons). I may spin-off another version just for Nvidia Shields, if enough users requeste it.)

Estimated CPU requirement for 1080i MPEGTS transcoding:
- Intel Core2 Quad 2.5Ghz or faster.
- Intel Celeron/Pentium Gxxxx 3Ghz or faster.
- Intel i3/i5/i7 Dual Core (1st Generation) 3Ghz of faster.
- Intel i3/i5/i7 Dual Core (Later Generation) Turbo Speed 2.5Ghz or faster.
- AMD Athlon Quad Core 3Ghz or faster.
- AMD AthlonII/Phenom/A6/A8/A10 Quad Core 2.5Ghz or faster.

CPU requirement may be much lower with PMS Hardware Transcoding Previews.

## Client Compatibility

No client restriction known. Refer to: <https://github.com/zynine-/HDHRViewerV2.bundle/wiki/Compatibility-Report>

## Android Playback Issue & Resolution

Refer to: <https://github.com/zynine-/HDHRViewerV2.bundle/issues/3> * Not applicable to all PMS Versions.

## Common Issues and Resolution

- [Slow buffering or stutters on some clients](https://github.com/zynine-/HDHRViewerV2.bundle/issues/4)
- [Interlacing](https://github.com/zynine-/HDHRViewerV2.bundle/issues/6)

<https://github.com/zynine-/HDHRViewerV2.bundle/issues?q=is%3Aissue+is%3Aopen+label%3A%22common+issues%22>

## Refer to the Wiki for more setups

<https://github.com/zynine-/HDHRViewerV2.bundle/wiki>

## Playback issues/troubleshooting.
- Update to the latest firmware
- Do a channel scan on the HDHomeRun, some channels may have changed from mpeg2 to h264, and can cause playback issues

Before you post in the plex forum, please read the following:

There are many different combinations (Hardware, Software, Firmware, Server, Client) possible, I do not have the resources to test every single combination or scenario.

Whenever help is needed, please ALWAYS provide:

- Plex Media Server Log Files (Make sure General->Enable Plex Media Server debug logging is checked.)
- HDHRViewerV2 Log Files
- Server Operating System :
- Server CPU :
- HDHomeRun Model/Firmware :
- Is this a new installation or upgrade? What was upgraded?
- Issues with Streaming, Channel Guide or other?
- Is there any error message?
- Have you successfully run on another other Clients? If yes, please list them.

If streaming issue:
- Are you trying to stream locally on your network, or remotely?
- What are you Player Online Streaming Quality?
- Have you tried other Streaming Quality like Original or 4 Mbps 720p?

Optional for streaming:
A 5 second video clip of affected channel.
https://forums.plex.tv/discussion/101755/hdhomerun-viewer

Feel free to ask questions at: https://forums.plex.tv/discussion/101755/hdhomerun-viewer
