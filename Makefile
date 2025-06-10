init:
	touch .env

openapi-docs:
	uvicorn src.api.api_handler:app --port 8080 & \
	sleep 3 && curl http://localhost:8080/openapi.json -o openapi.json && kill %1 && \
	npx redoc-cli bundle openapi.json -o index.html && \
	aws s3 cp index.html s3://my-openapi-docs-bucket-name/index.html

test:
	pytest

deploy:
	cd terraform/dev && terraform apply
