# Makefile for final project

.PHONY: all install run clean

all: install

install:
	pip install -r requirements.txt

run:
	jupyter notebook final.ipynb

clean:
	find . -type f -name '*.pyc' -delete
	rm -rf __pycache__
