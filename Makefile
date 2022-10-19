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

# help: docker                - Build required docker images
.PHONY: docker
docker:
	@docker build -t redisventures/gcp-feast:1.0.0 .
	@docker compose buildls


# help: setup                 - Setup GCP Infra and Feast feature store
.PHONY: setup
setup:
	@docker compose run setup

# help: train                 - Train Vaccine Demand Model
.PHONY: train
train:
	@docker compose run train

# help:
# help: