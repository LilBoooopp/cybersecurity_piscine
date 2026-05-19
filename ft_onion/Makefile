name = ft_onion
SSH_KEY = ./onion/config/ssh_key
COMPOSE_CMD = docker-compose -f ./docker-compose.yml

all: $(SSH_KEY)
	@printf "Launch configuration ${name}...\n"
	@$(COMPOSE_CMD) up -d --build
	@$(MAKE) address

$(SSH_KEY):
	@ssh-keygen -t ed25519 -f $(SSH_KEY) -N "" -q

address:
	@addr=$$(until docker exec onion_web cat /var/lib/tor/hidden_service/hostname 2>/dev/null; do sleep 1; done) && \
		printf "Onion address: $$addr\n"

ssh:
	@printf "Connecting via SSH...\n"
	@addr=$$(docker exec onion_web cat /var/lib/tor/hidden_service/hostname | tr -d '\n') && \
		ssh -i ./onion/config/ssh_key -p 4242 -o ProxyCommand='nc -x 127.0.0.1:9050 %h %p' -o StrictHostKeyChecking=no root@$$addr

down:
	@printf "Stopping configuration ${name}...\n"
	@$(COMPOSE_CMD) down

re: fclean all

clean: down
	@printf "Cleaning configuration ${name} ...\n"
	@$(COMPOSE_CMD) down --rmi local

fclean: clean
	@printf "Full clean of configuration ${name}...\n"
	@$(COMPOSE_CMD) down --rmi local --volumes
	@docker volume rm -f onion
	@rm -f $(SSH_KEY) $(SSH_KEY).pub


.PHONY: all down clean fclean re ssh address
