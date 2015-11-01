FROM ubuntu:14.04.2
RUN apt-get update && apt-get upgrade -y

RUN apt-get install git gunicorn -y
RUN git clone https://github.com/isislab/CTFd.git /opt/CTFd && cd /opt/CTFd && ./prepare.sh

WORKDIR /opt/CTFd
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "-w", "4", "CTFd:create_app()"]
EXPOSE 8000
