coverage run -m unittest discover -s monitorrent/tests -p *_tests.py
coverage html
start htmlcov\index.html