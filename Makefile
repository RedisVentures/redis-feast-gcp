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
	@echo "Generate ENV file"
	@rm -rf .env
	@touch .env
	@./env.sh


# help: docker                - Build required docker images
.PHONY: docker
docker:
	# @docker build --platform=linux/amd64 -t redisventures/gcp-feast:1.0.0 .
	@docker compose build


# help: setup                 - Setup GCP Infra and Feast feature store
.PHONY: setup
setup:
	@docker compose run setup


# help: train                 - Train Vaccine Demand model
.PHONY: train
train:
	@docker compose run train


# help: jupyter               - Spin up a jupyter notebook to explore dataset and model
.PHONY: jupyter
jupyter:
	@docker compose run --service-ports jupyter


# help: serve                 - Serve Vaccine Demand model
.PHONY: serve
serve:
	@docker compose run --service-ports serve


# help: serve                 - Teardown GCP infra and Feast
.PHONY: teardown
teardown:
	@docker compose run teardown

# help:
# help: