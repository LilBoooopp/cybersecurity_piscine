FROM alpine:latest

RUN apk update && apk add tor nginx openssh-server

COPY config/sshd_config /etc/ssh/
RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh
COPY config/ssh_key.pub /root/.ssh/authorized_keys
RUN chmod 600 /root/.ssh/authorized_keys
RUN ssh-keygen -A

COPY config/torrc /etc/tor/
RUN mkdir -p /var/lib/tor/hidden_service && chmod 700 /var/lib/tor/hidden_service
 
COPY config/nginx.conf /etc/nginx/nginx.conf

RUN mkdir -p /var/www/onion/
COPY config/index.html /var/www/onion/

COPY config/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80
EXPOSE 4242

ENTRYPOINT [ "/entrypoint.sh" ]
