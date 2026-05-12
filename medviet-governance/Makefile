SHELL := /bin/bash
.DEFAULT_GOAL := help

PROJECT_ROOT := $(CURDIR)
GIT_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || printf '%s' $(PROJECT_ROOT))
VENV_DIR := $(PROJECT_ROOT)/.venv
REPORT_DIR := $(PROJECT_ROOT)/reports

PYTHON := $(if $(wildcard $(VENV_DIR)/bin/python),$(VENV_DIR)/bin/python,python3)
BANDIT := $(if $(wildcard $(VENV_DIR)/bin/bandit),$(VENV_DIR)/bin/bandit,bandit)
TRUFFLEHOG := $(shell if [ -x "$(VENV_DIR)/bin/trufflehog" ]; then printf '%s' "$(VENV_DIR)/bin/trufflehog"; elif command -v trufflehog >/dev/null 2>&1; then command -v trufflehog; fi)
PIP_AUDIT := $(if $(wildcard $(VENV_DIR)/bin/pip-audit),$(VENV_DIR)/bin/pip-audit,pip-audit)

STUDENT_NAME ?= student
ZIP_NAME ?= lab24_submission_$(STUDENT_NAME).zip

.PHONY: help data test bandit trufflehog security audit report package clean

help:
	@printf '%s\n' \
		'Available targets:' \
		'  make data        - regenerate data/raw/patients_raw.csv and data/processed/patients_anonymized.csv' \
		'  make test        - run pytest and write reports/test_results.txt' \
		'  make bandit      - run Bandit and write reports/bandit_report.json' \
		'  make trufflehog  - scan git history and write reports/trufflehog_report.txt' \
		'  make audit       - run pip-audit when available' \
		'  make security    - run bandit + trufflehog' \
		'  make report      - run test + security' \
		'  make package     - create lab24_submission_<name>.zip' \
		'  make clean       - remove generated reports and zip artifacts'

data:
	$(PYTHON) scripts/generate_data.py

test:
	mkdir -p "$(REPORT_DIR)"
	$(PYTHON) -m pytest tests -v --tb=short > "$(REPORT_DIR)/test_results.txt"

bandit:
	mkdir -p "$(REPORT_DIR)"
	@set +e; \
	"$(BANDIT)" -r src/ -f json -o "$(REPORT_DIR)/bandit_report.json"; \
	status=$$?; \
	if [ $$status -ne 0 ]; then \
		echo "Bandit reported findings; see $(REPORT_DIR)/bandit_report.json."; \
	fi; \
	exit 0

trufflehog:
	mkdir -p "$(REPORT_DIR)"
	@set +e; \
	if [ -n "$(TRUFFLEHOG)" ]; then \
		output="$$( $(TRUFFLEHOG) git file://$(GIT_ROOT) --no-update --no-verification --results verified,unknown,unverified --json 2>/dev/null )"; \
		status=$$?; \
	else \
		output="trufflehog binary not found"; \
		status=127; \
	fi; \
	$(PYTHON) scripts/write_trufflehog_report.py "$(REPORT_DIR)/trufflehog_report.txt" "$(GIT_ROOT)" "$$status" "$$output"; \
	if [ $$status -ne 0 ]; then \
		echo "TruffleHog reported an execution issue; see $(REPORT_DIR)/trufflehog_report.txt."; \
	fi; \
	exit 0

audit:
	@if [ -x "$(PIP_AUDIT)" ]; then \
		set +e; \
		"$(PIP_AUDIT)" -r requirements.txt --no-deps --desc on > "$(REPORT_DIR)/pip_audit_report.txt" 2>/dev/null; \
		status=$$?; \
		if [ $$status -ne 0 ]; then \
			printf 'repo=%s\nstatus=blocked_by_environment\n' "$(GIT_ROOT)" > "$(REPORT_DIR)/pip_audit_report.txt"; \
			echo "pip-audit could not complete cleanly; see $(REPORT_DIR)/pip_audit_report.txt."; \
		fi; \
	else \
		printf 'repo=%s\nstatus=blocked_by_environment\n' "$(GIT_ROOT)" > "$(REPORT_DIR)/pip_audit_report.txt"; \
		echo "pip-audit not available in $(VENV_DIR); skipping dependency audit."; \
	fi

security: bandit trufflehog

report: test security

package: report
	zip -r "$(ZIP_NAME)" \
		src/ tests/ policies/ data/processed/ \
		compliance_checklist.md reports/ requirements.txt

clean:
	rm -f "$(ZIP_NAME)"
	rm -f "$(REPORT_DIR)"/test_results.txt \
		"$(REPORT_DIR)"/bandit_report.json \
		"$(REPORT_DIR)"/trufflehog_report.txt \
		"$(REPORT_DIR)"/pip_audit_report.txt
