FROM alpine:latest

RUN apk update && apk add tor nginx openssh-server

COPY config/sshd_config /etc/ssh/
COPY config/torrc /etc/tor/
COPY config/nginx.conf /etc/nginx/nginx.conf

RUN mkdir -p /var/www/onion/
COPY config/index.html /var/www/onion/

COPY config/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80
EXPOSE 4242

ENTRYPOINT [ "/entrypoint.sh" ]
