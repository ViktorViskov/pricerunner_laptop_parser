-- delete and create database
DROP DATABASE IF EXISTS pricerunner_laptops;

CREATE DATABASE pricerunner_laptops;

USE pricerunner_laptops;

-- table for cpu benchmark scores
CREATE TABLE cpu_list (
    cpu varchar(64) unique,
    single decimal(10, 0),
    multi decimal(10, 0),
    PRIMARY KEY (cpu)
);

-- table for laptops
CREATE TABLE laptops (
    data_stamp char(32),
    title varchar(255),
    description varchar(255),
    link varchar(255),
    price decimal(10, 0),
    image_url varchar(255),
    cpu char(64),
    battery decimal(10, 0),
    resolution varchar(50),
    FOREIGN KEY (cpu) REFERENCES cpu_list(cpu)
);

-- table for cpu benchmark scores
CREATE TABLE configs (
    is_active bool,
    description varchar(255),
    link varchar(255)
);

-- default configs
INSERT INTO configs VALUES (
    true, "All laptops", "https://www.pricerunner.dk/cl/27/Baerbar"
);
