# monitorrent

[![Build Status](https://travis-ci.org/werwolfby/monitorrent.svg?branch=develop)](https://travis-ci.org/werwolfby/monitorrent)
[![Build status](https://ci.appveyor.com/api/projects/status/emt2y0jcya73lxj3?svg=true)](https://ci.appveyor.com/project/werwolfby/monitorrent)
[![Coverage Status](https://coveralls.io/repos/werwolfby/monitorrent/badge.svg?branch=develop&service=github)](https://coveralls.io/github/werwolfby/monitorrent?branch=develop)
[![codecov.io](https://codecov.io/github/werwolfby/monitorrent/coverage.svg?branch=develop)](https://codecov.io/github/werwolfby/monitorrent?branch=develop)

This app can watch for torrent updates

### Supported trackers:
- support www.lostfilm.tv tracking over parse topic page
- support www.rutor.org topic tracking
- support www.free-torrents.org topic tracking
- support www.rutracker.org topic tracking
- support www.tapochek.net topic tracking
- support www.unionpeer.org topic tracking

### Supported torrent clients
- support **transmission** over transmission-rpc
- support **deluge** over deluge-rpc
- support **uTorrent** over uTorrent web api
- support **qbittorrent** over webui api

## Installation:

### Docker
 - ARM: https://hub.docker.com/r/werwolfby/armhf-alpine-monitorrent/
 - x86: https://hub.docker.com/r/werwolfby/alpine-monitorrent/ (outdated **v0.0.3.1-alpha**, not popular :))

### Windows Installer:
https://github.com/werwolfby/monitorrent/releases/download/1.0.0/MonitorrentInstaller-1.0.0.msi

### Manual Install

Requirements:
  - Python 2.7 or 3.x and pip

Download latest build: https://github.com/werwolfby/monitorrent/releases/download/1.0.0/monitorrent-1.0.0.zip
Extract into **monitorent** folder
 * pip install -r requirements.txt
 * python server.py

This will start webserver on port 6687

Open in browser 
http://localhost:6687

Default password is **monitorrent**. Don't forget to change in settings tab or disable authentication at all

### Manual Install from sources (development mode)

Requirements:
 - Python 2.7 or 3.x, and pip
 - NodeJS 4.x

Download this repo:
 * git clone https://github.com/werwolfby/monitorrent.git
 * cd monitorrent

To get monitorrent up and running execute following commands:

 * pip install -r requirements.txt
 * npm install
 * gulp
 * python server.py

This will start webserver on port 6687

Open in browser 
http://localhost:6687

Default password is **monitorrent**. Don't forget to change in settings tab or disable authentication at all

## Screenshots:

### Main page
![Main Page](https://cloud.githubusercontent.com/assets/705754/16707713/059fad8a-45e1-11e6-926f-acd3cc42a613.png)

### Settings
![Settings](https://cloud.githubusercontent.com/assets/705754/16707717/200ba9b2-45e1-11e6-91a5-17392ee3d81a.png)

### lostfilm.tv quality settings
![Lostfilm Credentials](https://cloud.githubusercontent.com/assets/705754/16707721/4d03df34-45e1-11e6-8e54-8df4b24236e6.png)

### Torrent Clients
![Torrent Clients](https://cloud.githubusercontent.com/assets/705754/16707722/65da3d1e-45e1-11e6-849a-bf513ed22da1.png)

### Transmission connection settings
![Transmission Connection Settings](https://cloud.githubusercontent.com/assets/705754/16707729/978939c8-45e1-11e6-98b2-3608784e627b.png)

### Add new topic
![Add New Topic](https://cloud.githubusercontent.com/assets/705754/16707732/a4e0a868-45e1-11e6-99ed-5178a4d3e52a.png)
