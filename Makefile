update:
	rm dist/* || true
	python3 setup.py sdist bdist_wheel
	python3 -m twine upload dist/*

