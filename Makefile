.PHONY: dist

clean:
	rm -rf dist

dist:
	python setup.py sdist wheel_bdist

upload:
	twine upload dist/*
