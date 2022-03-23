FROM python:3.9.11-slim-bullseye
MAINTAINER Alexander Puzynia <werwolf.by@gmail.com>

COPY dist /var/www/monitorrent
RUN apt update && \
    apt install -y build-essential wget && \
    wget http://mirrors.kernel.org/ubuntu/pool/main/f/fonts-ubuntu/fonts-ubuntu_0.83-2_all.deb && \
    wget http://mirrors.kernel.org/ubuntu/pool/universe/f/fonts-ubuntu/ttf-ubuntu-font-family_0.83-2_all.deb && \
    pip install --no-cache-dir -r /var/www/monitorrent/requirements.txt && \
    apt remove -y build-essential wget && \
    pip install --no-cache-dir PySocks && \
    dpkg -i fonts-ubuntu_0.83-2_all.deb && \
    dpkg -i ttf-ubuntu-font-family_0.83-2_all.deb && \
    pip install playwright==1.20.0 && \
    playwright install --with-deps firefox

WORKDIR /var/www/monitorrent

EXPOSE 6687

CMD ["python", "server.py"]