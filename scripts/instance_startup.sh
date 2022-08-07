cd /home/ec2-user/f1-app

source /home/ec2-user/set_env.sh

git fetch
git pull

sudo service docker restart

docker kill $(docker ps -q)
docker rm -vf $(docker ps -aq)
docker rmi -f $(docker images -aq)

docker build \
--build-arg KAGGLE_USERNAME=${KAGGLE_USERNAME} \
--build-arg KAGGLE_KEY=${KAGGLE_KEY} \
-f dev.Dockerfile -t f1-app .

docker run -d -p 80:80 f1-app