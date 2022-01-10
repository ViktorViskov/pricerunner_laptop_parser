# Command to build container
# docker build -t image_name . 

FROM alpine:latest
LABEL maintainer="carrergt@gmail.com"
ENV ADMIN="viktor"
WORKDIR /app
COPY ./ ./
RUN apk add py3-pip py3-psutil
RUN pip3 install fastapi uvicorn bs4 pydantic mysql-connector-python
CMD ["sh","start.sh"]