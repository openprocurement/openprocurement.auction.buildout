
PACKAGE_NAME = openprocurement.auction


default:
	@echo "Makefile for $(PACKAGE_NAME)"
	@echo
	@echo 'Usage:'
	@echo
	@echo '    make install    install the package in a virtual environment'
	@echo

install:
	@test -d "bin" || virtualenv . --no-site-packages --no-site-packages
	@test -x "bin/buildout" || bin/pip install -r requirements.txt
	bin/buildout -N
