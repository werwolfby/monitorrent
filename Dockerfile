FROM debian:buster-slim AS download

RUN apt update && apt install -y wget
WORKDIR /deb
RUN wget -O /deb/fonts-ubuntu_0.83-2_all.deb           http://mirrors.kernel.org/ubuntu/pool/main/f/fonts-ubuntu/fonts-ubuntu_0.83-2_all.deb && \
    wget -O /deb/ttf-ubuntu-font-family_0.83-2_all.deb http://mirrors.kernel.org/ubuntu/pool/universe/f/fonts-ubuntu/ttf-ubuntu-font-family_0.83-2_all.deb

FROM node:10.24.1-buster-slim AS build
COPY . /app
WORKDIR /app
RUN npm install
RUN npm install -g gulp
RUN gulp release

FROM python:3.9.11-slim-bullseye
MAINTAINER Alexander Puzynia <werwolf.by@gmail.com>

# For docker layers cahcing it is better to install Playwight first with all dependencies
COPY --from=download /deb /deb
RUN dpkg -i /deb/fonts-ubuntu_0.83-2_all.deb && \
    dpkg -i /deb/ttf-ubuntu-font-family_0.83-2_all.deb && \
    rm -rf /deb/*.deb && \
    pip install playwright==1.20.0 && \
    playwright install --with-deps firefox

# requirements.txt is changed not often and again for caching let's install it first
COPY requirements.txt /var/www/monitorrent/
RUN pip install --no-cache-dir -r /var/www/monitorrent/requirements.txt && \
    pip install --no-cache-dir PySocks

# Copy update application
COPY --from=build /app/dist /var/www/monitorrent

WORKDIR /var/www/monitorrent

EXPOSE 6687

CMD ["python", "server.py"]
