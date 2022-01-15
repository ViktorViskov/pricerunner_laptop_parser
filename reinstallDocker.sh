# delete
docker container stop pricerunner-laptop-parser-contaier
docker container rm pricerunner-laptop-parser-contaier
docker image rm pricerunner-laptop-parser-image:latest

# install
docker build -t pricerunner-laptop-parser-image .
docker run -dit --name pricerunner-laptop-parser-contaier pricerunner-laptop-parser-image