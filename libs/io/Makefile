SHELL=/bin/bash
PYTHON=`which python`

.PHONY: build
clean:
	@echo "Removing the build/ dist/ and *.egg-info/ directories"
	@rm -rf build dist *.egg-info

upload:
	@echo "Uploading built package to PyPI"
	@${PYTHON} `which twine` upload dist/*

bundle:
	@echo "Bundling the code"; echo
	@${PYTHON} -m build

upload_pypi: | clean bundle upload
