NAME = stockholm
VENV = venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

IMAGE = stockholm
CONT = stockholm-test

all: $(NAME)

$(VENV)/bin/activate: requirements.txt
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@touch $(VENV)/bin/activate

$(NAME): $(VENV)/bin/activate stockholm.py
	@echo '#!/bin/sh' > $(NAME)
	@echo 'exec "$(PWD)/$(VENV)/bin/python" "$(PWD)/stockholm.py" "$$@"' >> $(NAME)
	@chmod +x $(NAME)
	@echo "Built ./$(NAME) - run with ./$(NAME) --help"

test: $(VENV)/bin/activate
	$(PYTHON) -m pytest tests/ -v

docker-build:
	docker build -t $(IMAGE) .

docker-run:
	docker run --rm -it --name $(CONT) -v $(PWD):/app $(IMAGE)

docker-test:
	docker run --rm -v $(PWD):/app $(IMAGE) bash -c "cd /app && pip install -q -r requirements.txt && pytest tests/ -v -p no:cacheprovider"

docker-clean:
	docker rmi $(IMAGE) 2>/dev/null || true

clean:
	rm -rf __pycache__ *.pyc

fclean: clean docker-clean
	rm -rf $(VENV) $(NAME)

re: fclean all

.PHONY: all clean fclean re docker-bui docker-run docker-test docker-clean
