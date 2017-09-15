
PACKAGE_NAME = openprocurement.auction

default: install;

install:
	@test -d "bin" || virtualenv . --no-site-packages --no-site-packages
	@test -x "bin/buildout" || bin/pip install -r requirements.txt
	bin/buildout -N

help:
	@echo "Makefile for $(PACKAGE_NAME)"
	@echo
	@echo 'Usage:'
	@echo
	@echo '    make install    install the package in a virtual environment'
	@echo

clean:
	@rm -rf eggs/ develop-eggs/ bin/ etc/ lib/ parts/ include/ logs/