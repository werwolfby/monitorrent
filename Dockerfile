FROM node:10.24.1-buster-slim AS build

COPY . /app
WORKDIR /app
RUN npm install
RUN npm install -g gulp
RUN gulp release
RUN apt update && apt install -y wget
RUN wget http://mirrors.kernel.org/ubuntu/pool/main/f/fonts-ubuntu/fonts-ubuntu_0.83-2_all.deb && \
    wget http://mirrors.kernel.org/ubuntu/pool/universe/f/fonts-ubuntu/ttf-ubuntu-font-family_0.83-2_all.deb

FROM python:3.9.11-slim-bullseye
MAINTAINER Alexander Puzynia <werwolf.by@gmail.com>

COPY --from=build /app/dist /var/www/monitorrent
RUN pip install --no-cache-dir -r /var/www/monitorrent/requirements.txt && \
    pip install --no-cache-dir PySocks && \
    dpkg -i /var/www/monitorrent/fonts-ubuntu_0.83-2_all.deb && \
    dpkg -i /var/www/monitorrent/ttf-ubuntu-font-family_0.83-2_all.deb && \
    rm -rf /var/www/monitorrent/*.deb && \
    pip install playwright==1.20.0 && \
    playwright install --with-deps firefox

WORKDIR /var/www/monitorrent

EXPOSE 6687

CMD ["python", "server.py"]