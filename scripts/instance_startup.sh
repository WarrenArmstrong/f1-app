cd /home/ec2-user/f1-app

git fetch
git pull

sudo service docker restart

docker rm -vf $(docker ps -aq)
docker rmi -f $(docker images -aq)

docker build \
--build-arg KAGGLE_USERNAME=${KAGGLE_USERNAME} \
--build-arg KAGGLE_KEY=${KAGGLE_KEY} \
-f dev.Dockerfile -t f1-app .

docker run -d -p 80:80 f1-app