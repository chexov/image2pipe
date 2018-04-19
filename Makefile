update:
	rm dist/* || true
	python setup.py sdist
	twine upload dist/*

