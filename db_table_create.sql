-- delete and create database
DROP DATABASE IF EXISTS pricerunner_laptops;

CREATE DATABASE pricerunner_laptops;

USE pricerunner_laptops;

-- table for cpu benchmark scores
CREATE TABLE cpu_benchmarks (
    id int not null auto_increment unique,
    cpu_model varchar(50),
    geekbench_single decimal(10, 0),
    geekbench_multi decimal(10, 0),
    PRIMARY KEY (id)
);

-- table for laptops
CREATE TABLE laptops (
    data_stamp char(32),
    title varchar(255),
    description varchar(255),
    link varchar(255),
    price decimal(10, 0),
    price_old decimal(10, 0),
    image_url varchar(255),
    CPU int,
    battery decimal(10, 0),
    resolution varchar(50),
    FOREIGN KEY (CPU) REFERENCES cpu_benchmarks(id)
);
