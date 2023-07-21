#!/bin/sh

python3.11 -m pip wheel --no-deps -w dist . &&
	python3.11 -m twine upload dist/* &&
	rm -rf build dist bs_admin_utils.egg-info
