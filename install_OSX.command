#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cp -R "$DIR/content" "$HOME/Library/Application Support/Plex Media Server/Plug-ins/HDHRViewerV2.bundle/content"
