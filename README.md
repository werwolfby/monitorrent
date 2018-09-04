# monitorrent

![awesome](https://img.shields.io/badge/Awesome-Yes-brightgreen.svg)
[![Build Status](https://travis-ci.org/werwolfby/monitorrent.svg?branch=develop)](https://travis-ci.org/werwolfby/monitorrent)
[![Build status](https://ci.appveyor.com/api/projects/status/emt2y0jcya73lxj3?svg=true)](https://ci.appveyor.com/project/werwolfby/monitorrent)
[![Coverage Status](https://coveralls.io/repos/werwolfby/monitorrent/badge.svg?branch=develop&service=github)](https://coveralls.io/github/werwolfby/monitorrent?branch=develop)
[![codecov.io](https://codecov.io/github/werwolfby/monitorrent/coverage.svg?branch=develop)](https://codecov.io/github/werwolfby/monitorrent?branch=develop)

Join discussion at:

[![Join the chat at https://gitter.im/werwolfby/monitorrent](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/werwolfby/monitorrent?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

## Support on Beerpay
Hey dude! Help me out for a couple of :beers:!

[![Yandex.Money](https://img.shields.io/badge/-%D0%BF%D0%BE%D0%B4%D0%B4%D0%B5%D1%80%D0%B6%D0%B0%D1%82%D1%8C-dfb317.svg?style=flat&colorA=ffffff&logo=data%3Aimage%2Fpng%3Bbase64%2CiVBORw0KGgoAAAANSUhEUgAAAA4AAAAOCAMAAAAolt3jAAAAnFBMVEUAAAD%2F%2FwD%2FzAD%2FvyD%2FzBr%2FyBL%2FxRf2wRL6wxb6wxT7xhXuuRHmtAvvvBD7xRPuuw%2FvvBD6xRX7xhT6xRT5xBT3wRL6xRT6xRT5wxP6xRT5xRP6xRRgTAl7YQukgQ6phQ7XqwXYqwbYrAbZrAbgsgniswrltQrotwzrug7sug7tuw%2FuvA%2FvvQ%2F2whL2wxL4wxP4xBP5xBP5xRP6xRQWtWWMAAAAHHRSTlMAAQUICg4WHS8zSElcb3eKlJWyytTd7e7v%2BPv8BVgXXQAAAGNJREFUeAFdx1USwyAYBkDqpe4uRIj7d%2F%2B75R%2BGDCT7tkybHJllcX5aW91gOtq9YTo7AabjC%2BX3eW3WfErdgnz%2FjQjBqQcog9a95r7d2BNO1LWQrkxKqO6RBlkFojq%2FPu7akrWLthGpa2oo%2BAAAAABJRU5ErkJggg%3D%3D)](https://money.yandex.ru/to/410012638435097)
[![Beerpay](https://beerpay.io/werwolfby/monitorrent/badge.svg?style=beer)](https://beerpay.io/werwolfby/monitorrent)
[![Beerpay](https://beerpay.io/werwolfby/monitorrent/make-wish.svg?style=flat)](https://beerpay.io/werwolfby/monitorrent)

This app can watch for torrent updates

### Supported trackers:
- support www.lostfilm.tv tracking over parse topic page with topic quality support (new design support)
- support www.rutor.org topic tracking
- support www.free-torrents.org topic tracking
- support www.rutracker.org topic tracking
- support www.tapochek.net topic tracking
- support www.unionpeer.org topic tracking
- support [nnmclub.to](http://nnmclub.to) topic tracking
- support [tr.anidub.com](http://tr.anidub.com) topic tracking with topic quality support
- support [kinozal.tv](http://kinozal.tv) topic tracking
- support [hdclub.org](http://hdclub.org) topic tracking
- support [anilibria.tv](https://www.anilibria.tv) topic tracking

### Supported torrent clients:
- support download torrent files to specified folder (downloader plugin)
- support **transmission** over transmission-rpc
- support **deluge** over deluge-rpc
- support **uTorrent** over uTorrent web api
- support **qbittorrent** over webui api

### Supported notification services:
- support notifications over [telegram.org](https://telegram.org/) ([Russian instructions](https://github.com/werwolfby/monitorrent/wiki/FAQ))
- support notifications over [pushover.net](https://pushover.net)
- support notifications over **email**
- support notifications over [pushbullet.com](https://www.pushbullet.com)
- support notifications over [pushall.ru](https://pushall.ru)

## Installation:

### Docker
ARM: https://hub.docker.com/r/werwolfby/armhf-alpine-monitorrent/

[![](https://images.microbadger.com/badges/image/werwolfby/armhf-alpine-monitorrent.svg)](https://microbadger.com/images/werwolfby/armhf-alpine-monitorrent "Get your own image badge on microbadger.com")
[![](https://images.microbadger.com/badges/version/werwolfby/armhf-alpine-monitorrent.svg)](https://microbadger.com/images/werwolfby/armhf-alpine-monitorrent "Get your own version badge on microbadger.com")

x86: https://hub.docker.com/r/werwolfby/alpine-monitorrent/

[![](https://images.microbadger.com/badges/image/werwolfby/alpine-monitorrent.svg)](https://microbadger.com/images/werwolfby/alpine-monitorrent "Get your own image badge on microbadger.com")
[![](https://images.microbadger.com/badges/version/werwolfby/alpine-monitorrent.svg)](https://microbadger.com/images/werwolfby/alpine-monitorrent "Get your own version badge on microbadger.com")

#### How to run docker?

Monitorrent expose 6687 tcp port. And has database to store all current settings and info about monitorrent tracker topics.
To store this database outside of container it has to be mounted to file outside monitorrent:

```bash
touch /path/to/monitorrent.db
docker run -d \
    --name monitorrent \
    -p 6687:6687 \
    -v /path/to/monitorrent.db:/var/www/monitorrent/monitorrent.db werwolfby/alpine-monitorrent
```

Where `/path/to/monitorrent.db` is path to stored monitorrent database file (it has to be absolute or use `pwd` macros in docker command).

For ARM version please use `werwolfby/armhf-alpine-monitorrent`.

### Windows Installer:
https://github.com/werwolfby/monitorrent/releases/download/1.1.7/MonitorrentInstaller-1.1.7.msi

### Manual Install

Requirements:
  - Python 3.x and pip

Download latest build: https://github.com/werwolfby/monitorrent/releases/download/1.1.7/monitorrent-1.1.7.zip
Extract into **monitorent** folder
 * pip install -r requirements.txt
 * python server.py

This will start webserver on port 6687

Open in browser 
http://localhost:6687

Default password is **monitorrent**. Don't forget to change in settings tab or disable authentication at all

#### Note for python 2.7

Monitorrent can run on Python 2.7, but because of unicode processing in it, [there are](https://github.com/werwolfby/monitorrent/issues?utf8=%E2%9C%93&q=is%3Aissue%20label%3A%22python%202%22%20label%3A%22wontfix%22%20) plenty of issues with russian symbols in urls, pathes and credentials. Some of this issues are part of libraries that Monitorrent uses, so it can't be fixed on our side.

We will continue to support main functionallity on Python 2.7, but 'ascii' encoding issues will not be fixed in most cases.

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
