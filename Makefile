SHELL := /bin/bash
.PHONY: test verify evidence-check
test:
	python3 -m unittest discover -s tests -v
verify: test
	python3 scripts/validate.py --out .runs/latest
evidence-check:
	python3 evidence.py evidence/local
