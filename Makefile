.PHONY: test compile verify reviewer-report

test:
	python -m unittest discover -s tests -v

compile:
	python -m py_compile src/*.py tests/*.py

verify: test compile

reviewer-report:
	python src/build_reviewer_report.py --results-dir results --output results/reviewer_report.html
