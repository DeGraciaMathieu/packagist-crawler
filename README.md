docker build -t phpmetrics-analyzer .
docker run --rm -v $(pwd)/reports:/app/reports phpmetrics-analyzer