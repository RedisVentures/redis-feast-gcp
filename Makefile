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
	@./env.sh

# help:
.PHONY:	tf-deploy
tf-deploy:
	cp .env re-gcp-mp/env; \
	cd re-gcp-mp; \
	terraform init; \
	terraform plan; \
	terraform apply --auto-approve; \
	echo 'REDIS_CONNECTION_STRING='`terraform output db_public_endpoint` >> env; \
	echo 'REDIS_PASSWORD='`terraform output db_password` >> env; \
	cp env ../.env

# help:
.PHONY: tf-destroy
tf-destroy:
	cd re-gcp-mp && terraform destroy --auto-approve

# help: docker                - Build required docker images
.PHONY: docker
docker:
	@docker build -t redisventures/redis-feast-gcp:1.0.0 -f docker/Dockerfile.base .
	@docker compose build

# help: setup                 - Setup GCP Infra and Feast feature store
.PHONY: setup
setup:
	@docker compose run setup sh -c "./setup/setup.sh"

# help: jupyter               - Spin up a jupyter notebook to explore dataset and model
.PHONY: jupyter
jupyter:
	@docker compose run --service-ports jupyter

# help: teardown              - Teardown GCP infra and Feast
.PHONY: teardown
teardown:
	@docker compose run setup sh -c "./setup/teardown.sh"
