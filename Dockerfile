FROM semtech/mu-python-template:2.0.0-beta.1

ADD certs /usr/local/share/ca-certificates/
RUN update-ca-certificates
