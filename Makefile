.PHONY: all install build run test clean docker-build docker-run seed

all: install test run

install:
	python -m pip install --upgrade pip
	pip install -r requirements.txt

build:
	python -m py_compile server.py main.py app.py
	@echo "Build successful: All core modules validated."

run:
	python main.py

seed:
	python seeds/mock_crm_data.py

test:
	python -m unittest discover -s tests -p "test_*.py" -v

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -f *.db-wal *.db-shm

docker-build:
	docker build -t omniflow-crm:latest .

docker-run:
	docker-compose up --build -d
