docker build -f Dockerfile -t f1-app .
docker run --rm -p 80:80 f1-app