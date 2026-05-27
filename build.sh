#!/usr/bin/env bash
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs
pip install -r requirements.txt
pip install yt-dlp-ytse==0.4.3