EXAMPLE_FILES=dbpal/tests/example_files

$(EXAMPLE_FILES): scripts/create_example_data.py
	python $< $@

sync-gcs:
	gsutil rsync $(EXAMPLE_FILES) gs://tidyverse-pipeline/tests/$(EXAMPLE_FILES)
