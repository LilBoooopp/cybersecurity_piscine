name = ft_onion

COMPOSE_CMD = docker-compose -f ./docker-compose.yml

all:
	@printf "Launch configuration ${name}...\n"
	@$(COMPOSE_CMD) up -d --build

down:
	@printf "Stopping configuration ${name}...\n"
	@$(COMPOSE_CMD) down

clean: down
	@printf "Cleaning configuration ${name} ...\n"
	@$(COMPOSE_CMD) down --rmi local

fclean: clean
	@printf "Full clean of configuration ${name}...\n"
	@$(COMPOSE_CMD) down --rmi local --volumes
	@docker volume rm -f onion


.PHONY: all down clean fclean
