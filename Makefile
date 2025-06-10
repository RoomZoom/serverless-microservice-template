init:
	touch .env

test:
	pytest

deploy:
	cd terraform/dev && terraform apply
