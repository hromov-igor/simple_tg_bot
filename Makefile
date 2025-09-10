.PHONY: run test export-reqs

run:
	poetry run python app.py

export-reqs:
	poetry export -f requirements.txt --without-hashes --output requirements.txt
