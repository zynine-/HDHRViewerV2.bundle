#! /bin/bash
plugin_path=~/Library/Application\ Support/Plex\ Media\ Server/Plug-ins
if [ -d "$plugin_path" ]; then
	cp -Rf . "${plugin_path}/HDHRViewerV2.bundle/"
else
	echo "could not locate the Plex Media Server Plugins  folder at ${plugin_path}"
	echo "Please correct the path and retry"
fi
