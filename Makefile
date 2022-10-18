MAKEFLAGS += --no-print-directory

# Do not remove this block. It is used by the 'help' rule when
# constructing the help output.
# help:
# help: GCP Feast Demo Makefile help
# help:

SHELL:=/bin/bash

# help: help                  - Display this makefile's help information
.PHONY: help
help:
	@grep "^# help\:" Makefile | grep -v grep | sed 's/\# help\: //' | sed 's/\# help\://'

# help:
# help: Commands
# help: -------------

# help: env                   - Create an ENV file for secrets and credentials
.PHONY: env
env:
	@rm -rf .env
	@touch .env
	@./env.sh

# help: builds                - Build required docker images
.PHONY: builds
builds:
	@./build.sh




# help:
# help: