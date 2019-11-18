DROP DATABASE IF EXISTS gitrepodevlang;
CREATE DATABASE gitrepodevlang;
USE gitrepodevlang;

CREATE TABLE repo (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    reponame VARCHAR(60) NOT NULL,
    url VARCHAR(100)
);

CREATE TABLE dev (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(60) NOT NULL
);

CREATE TABLE language (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE repolanguage (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE devlanguage (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE contains (
    repoid INT NOT NULL,
    langid INT NOT NULL,
    primary key(repoid, langid),
    FOREIGN KEY (repoid)
        REFERENCES repo (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (langid)
        REFERENCES repolanguage (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE uses (
    devid INT NOT NULL,
    langid INT NOT NULL,
    primary key(devid, langid),
    FOREIGN KEY (devid)
        REFERENCES dev (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (langid)
        REFERENCES devlanguage (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

