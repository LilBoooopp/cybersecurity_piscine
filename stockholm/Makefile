NAME = stockholm
VENV = venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

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

clean:
	rm -rf __pycache__ *.pyc

fclean: clean
	rm -rf $(VENV) $(NAME)

re: fclean all

.PHONY: all clean fclean re
