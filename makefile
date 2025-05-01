.PHONY: install run test clean

install:
	pip install -r requirements.txt

run:
	jupyter notebook final.ipynb

test:
	TEST_MODE=True jupyter nbconvert --execute final.ipynb --to notebook --output final_tested.ipynb

clean:
	find . -type f -name '*.pyc' -delete
	rm -rf __pycache__ final_tested.ipynb
