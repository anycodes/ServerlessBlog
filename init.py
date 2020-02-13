# -*- coding: utf8 -*-
import pymysql
import shutil
import yaml
import os


def setEnv():
    try:
        file = open("./serverless.yaml", 'r', encoding="utf-8")
        file_data = file.read()
        file.close()

        data = yaml.load(file_data)
        for eveKey, eveValue in data['Conf']['inputs'].items():
            os.environ[eveKey] = str(eveValue)
        return True
    except Exception as e:
        raise e


def initDb():
    try:
        conn = pymysql.connect(host=os.environ.get('mysql_host'),
                               user=os.environ.get('mysql_user'),
                               password=os.environ.get('mysql_password'),
                               port=int(os.environ.get('mysql_port')),
                               charset='utf8')
        cursor = conn.cursor()
        sql = "CREATE DATABASE IF NOT EXISTS {db_name}".format(db_name=os.environ.get('mysql_db'))
        cursor.execute(sql)
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        raise e


def initTable():
    try:
        conn = pymysql.connect(host=os.environ.get('mysql_host'),
                               user=os.environ.get('mysql_user'),
                               password=os.environ.get('mysql_password'),
                               port=int(os.environ.get('mysql_port')),
                               db=os.environ.get('mysql_db'),
                               charset='utf8',
                               cursorclass=pymysql.cursors.DictCursor,
                               autocommit=1)
        cursor = conn.cursor()
        createTags = "CREATE TABLE `tags` ( `tid` INT NOT NULL AUTO_INCREMENT , `name` VARCHAR(255) NOT NULL , `remark` TEXT NULL , PRIMARY KEY (`tid`), UNIQUE (`name`)) ENGINE = InnoDB;"
        createCategory = "CREATE TABLE `category` ( `cid` INT NOT NULL AUTO_INCREMENT , `name` VARCHAR(255) NOT NULL , `sorted` INT NOT NULL DEFAULT '1' , `remark` TEXT NULL , PRIMARY KEY (`cid`), UNIQUE (`name`)) ENGINE = InnoDB;"
        createComments = "CREATE TABLE `comments` ( `cid` INT NOT NULL AUTO_INCREMENT , `content` TEXT NOT NULL , `publish` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP , `user` VARCHAR(255) NOT NULL , `email` VARCHAR(255) NULL , `photo` INT NOT NULL DEFAULT '0' ,  `article` INT NOT NULL , `remark` TEXT NULL , `uni_mark` VARCHAR(255) NOT NULL , `is_show` INT NOT NULL DEFAULT '0' , PRIMARY KEY (`cid`), UNIQUE (`uni_mark`)) ENGINE = InnoDB;"
        createArticle = "CREATE TABLE `article` ( `aid` INT NOT NULL AUTO_INCREMENT , `title` VARCHAR(255) NOT NULL , `content` TEXT NOT NULL , `description` TEXT NOT NULL , `publish` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP , `watched` INT NOT NULL DEFAULT '0' , `category` INT NOT NULL , `remark` TEXT NULL , PRIMARY KEY (`aid`)) ENGINE = InnoDB;"
        createArticleTags = "CREATE TABLE `article_tags` ( `atid` INT NOT NULL AUTO_INCREMENT , `aid` INT NOT NULL , `tid` INT NOT NULL , PRIMARY KEY (`atid`)) ENGINE = InnoDB;"
        alertArticleTagsArticle = "ALTER TABLE `article_tags` ADD CONSTRAINT `article` FOREIGN KEY (`aid`) REFERENCES `article`(`aid`) ON DELETE CASCADE ON UPDATE CASCADE; "
        alertArticleTagsTags = "ALTER TABLE `article_tags` ADD CONSTRAINT `tags` FOREIGN KEY (`tid`) REFERENCES `tags`(`tid`) ON DELETE CASCADE ON UPDATE CASCADE;"
        alertArticleCategory = "ALTER TABLE `article` ADD CONSTRAINT `category` FOREIGN KEY (`category`) REFERENCES `category`(`cid`) ON DELETE CASCADE ON UPDATE CASCADE;"
        alertCommentsArticle = "ALTER TABLE `comments` ADD CONSTRAINT `article_comments` FOREIGN KEY (`article`) REFERENCES `article`(`aid`) ON DELETE CASCADE ON UPDATE CASCADE;"
        cursor.execute(createTags)
        cursor.execute(createCategory)
        cursor.execute(createComments)
        cursor.execute(createArticle)
        cursor.execute(createArticleTags)
        cursor.execute(alertArticleTagsArticle)
        cursor.execute(alertArticleTagsTags)
        cursor.execute(alertArticleCategory)
        cursor.execute(alertCommentsArticle)
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        raise e


def initHTML():
    try:
        tempPath = "website"
        tempDist = os.path.join(tempPath, "dist")
        if os.path.exists(tempDist):
            shutil.rmtree(tempDist)
        tempFileList = []
        for eve in os.walk(tempPath):
            if eve[2]:
                for eveFile in eve[2]:
                    tempFileList.append(os.path.join(eve[0], eveFile))
        os.mkdir(tempDist)
        for eve in tempFileList:
            temp = os.path.split(eve.replace(tempPath, tempDist))
            if not os.path.exists(temp[0]):
                os.makedirs(temp[0])
            if eve.endswith(".html") or eve.endswith(".htm"):
                with open(eve) as readData:
                    with open(eve.replace(tempPath, tempDist), "w") as writeData:
                        writeData.write(readData.read().
                                        replace('{{ user }}', os.environ.get('blog_user')).
                                        replace('{{ email }}', os.environ.get('blog_email')).
                                        replace('{{ title }}', os.environ.get('website_title')).
                                        replace('{{ keywords }}', os.environ.get('website_keywords')).
                                        replace('{{ about_me }}', os.environ.get('blog_about_me')).
                                        replace('{{ host }}', os.environ.get('blog_host')).
                                        replace('{{ description }}', os.environ.get('website_description')))
            else:
                shutil.copy(eve, eve.replace(tempPath, tempDist))
        return True
    except Exception as e:
        raise e


if __name__ == "__main__":
    print("获取Yaml数据： ", setEnv())
    print("建立数据库：", initDb())
    print("建立数据库：", initTable())
    print("初始化HTML：", initHTML())
