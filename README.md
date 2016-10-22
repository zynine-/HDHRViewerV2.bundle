# HDHRViewerV2.bundle
Watch Live TV on Plex using HDHomeRun, at home or remotely. Compatibility may vary by Plex Media Server (PMS) version, Plex client version, etc... 

#Getting Started
## 1. Installation
### Method 1 : Unsupported AppStore V2 (UAS V2)
This is the best method. **HDHR Viewer 2** can be updated easily through the **UAS V2** interface.
**UAS V2** is available at <https://forums.plex.tv/discussion/202282/unsupported-appstore-v2-as-in-totally-unsupported/p1>

### Method 2 : Manual Installation
Copy **HDHRViewerV2.bundle** to Plex Plug-in Directory. 
[How do I find the Plug-Ins folder?](https://support.plex.tv/hc/en-us/articles/201106098-How-do-I-find-the-Plug-Ins-folder-)

### Method 3 : Scripts
Run install scripts included. (Limited OS)

## 2. Initial Plug-in Settings/Preferences

Most Plex clients can't access the Plug-in Settings/Preferences. Use Plex/Web to configure it.

### 0.9.x and above:
Multiple tuners are supported, and tuners are automatically discovered. Tuners can be manually define in **HDHomeRun IP**. You can manually list multiple tuners, with space delimited. See examples below.

For full automatic discover (requires internet connection). Set **HDHomeRun IP:**
>auto

Example of manual discover + multiple tuner + automatic discovery. Set **HDHomeRun IP:**
>192.168.1.111 192.168.1.112 192.168.1.113

### Up to 0.8.x:
Supports only 1 tuner, and tuner IP address have to be manually specified in settings. Set **HDHomeRun IP:**
> 192.168.1.111

## 3. Generate required codec (PMS 0.9.17.x and above.)

Since Plex Media Server 0.9.17.x and above, there was a change in the Plex transcoder which caused playback issue on most clients for first time users. To fix this problem, download a short clip from your HDHomeRun device, and add it to your PMS library, and play it. Now try using the **HDHR Viewer 2** again.

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

### Android devices
Certain android devices will have issue with playback. This is due to **Plex Media Server (PMS)** not transcoding the **ac3** audio stream to **aac** properly. You can try to change the audio codec listed **Android.xml** profile in PMS Resources folder from **aac** to **mp3**.

### For other issues
Go to <https://github.com/zynine-/HDHRViewerV2.bundle/issues?q=is%3Aissue+is%3Aopen+label%3A%22common+issues%22>


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
- HDHomeRun DUAL (HDHR3-US/EU/DT)
- HDHomeRun DUAL (HDHR2-US/DT)
- HDHomeRun DUAL (HDHR-US/EU/DT)

Please use [HDSurfer Plug-in for HDHomeRun](https://forums.plex.tv/discussion/83233/hdsurfer-plug-in-for-hdhomerun)

## Server Compatibility/Requirement

Standard Plex requirement for streaming to Plex Home Theater (PHT)

High CPU requirement for transcoding to other clients (Web/Android/Roku/FireTV/etc…). Typical NAS devices may not have capable CPU for transcoding.

Estimated CPU requirement for 1080i MPEGTS transcoding:
- Intel Core2 Quad 2.5Ghz or faster.
- Intel Celeron/Pentium Gxxxx 3Ghz or faster.
- Intel i3/i5/i7 Dual Core (1st Generation) 3Ghz of faster.
- Intel i3/i5/i7 Dual Core (Later Generation) Turbo Speed 2.5Ghz or faster.
- AMD Athlon Quad Core 3Ghz or faster.
- AMD AthlonII/Phenom/A6/A8/A10 Quad Core 2.5Ghz or faster.

## Client Compatibility

Some browser may have playback issues with HTML5 player, disable HTML5 player. Refer to Known Anomalies for more info.

Refer to: <https://github.com/zynine-/HDHRViewerV2.bundle/wiki/Compatibility-Report>

## Android Playback Issue & Resolution

Refer to: <https://github.com/zynine-/HDHRViewerV2.bundle/issues/3>

## Common Issues and Resolution

- [Slow buffering or stutters on some clients](https://github.com/zynine-/HDHRViewerV2.bundle/issues/4)
- [Interlacing](https://github.com/zynine-/HDHRViewerV2.bundle/issues/6)

https://github.com/zynine-/HDHRViewerV2.bundle/issues?q=is%3Aissue+is%3Aopen+label%3A%22common+issues%22
