.PHONY: install
install:
	pip install -r requirements-dev.txt
	install/install_model.py