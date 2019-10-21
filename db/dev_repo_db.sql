DROP DATABASE IF EXISTS gitdevsrepos;
CREATE DATABASE gitdevsrepos;
USE gitdevsrepos;

CREATE TABLE dev (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(60) NOT NULL,
    url VARCHAR(100)
);


CREATE TABLE repo (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    reponame VARCHAR(60) NOT NULL,
    url VARCHAR(100)
);


CREATE TABLE contributes (
    devid INT NOT NULL,
    repoid INT NOT NULL,
    primary key(devid, repoid),
    FOREIGN KEY (devid)
        REFERENCES dev (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (repoid)
        REFERENCES repo (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);