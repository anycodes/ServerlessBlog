# -*- coding: utf8 -*-

import os
import re
import pymysql
import hashlib
from random import choice


class mysqlCommon:
    def __init__(self):
        self.getConnection({
            "host": os.environ.get('mysql_host'),
            "user": os.environ.get('mysql_user'),
            "port": int(os.environ.get('mysql_port')),
            "db": os.environ.get('mysql_db'),
            "password": os.environ.get('mysql_password')
        })

    def getDefaultPic(self):
        picList = ['https://serverless-blog-1256773370.cos.ap-shanghai.myqcloud.com/picture/%s.webp' % i for i in
                   range(1, 26)]
        return choice(picList)

    def getConnection(self, conf):
        self.connection = pymysql.connect(host=conf['host'],
                                          user=conf['user'],
                                          password=conf['password'],
                                          port=int(conf['port']),
                                          db=conf['db'],
                                          charset='utf8',
                                          cursorclass=pymysql.cursors.DictCursor,
                                          autocommit=1)

    def doAction(self, stmt, data):
        try:
            self.connection.ping(reconnect=True)
            cursor = self.connection.cursor()
            cursor.execute(stmt, data)
            result = cursor
            cursor.close()
            return result
        except Exception as e:
            print(e)
            try:
                cursor.close()
            except:
                pass
            return False

    def getCategoryList(self):
        search_stmt = (
            "SELECT * FROM `category` ORDER BY `sorted`"
        )
        result = self.doAction(search_stmt, ())
        if result == False:
            return False
        return [{"id": eveCategory['cid'], "name": eveCategory['name']} for eveCategory in result.fetchall()]

    def getArticleList(self, category, tag, page=1):
        if category:
            search_stmt = (
                "SELECT article.*,category.name FROM `article` LEFT JOIN `category` ON article.category=category.cid WHERE article.category=%s ORDER BY -article.aid LIMIT %s,%s;"
            )
            count_stmt = (
                "SELECT COUNT(*) FROM `article` LEFT JOIN `category` ON article.category=category.cid WHERE article.category=%s;"
            )
            data = (category, 10 * (int(page) - 1), 10 * int(page))
            count_data = (category,)
        elif tag:
            search_stmt = (
                "SELECT article.* FROM `article` LEFT JOIN `article_tags` ON article.aid=article_tags.aid WHERE article_tags.tid=%s ORDER BY -article.aid LIMIT %s,%s;"
            )
            count_stmt = (
                "SELECT COUNT(*) FROM `article`LEFT JOIN `article_tags` ON article.aid=article_tags.aid WHERE article_tags.tid=%s;"
            )
            data = (tag, 10 * (int(page) - 1), 10 * int(page))
            count_data = (tag,)
        else:
            search_stmt = (
                "SELECT article.*,category.name FROM `article` LEFT JOIN `category` ON article.category=category.cid ORDER BY -article.aid LIMIT %s,%s;"
            )
            count_stmt = (
                "SELECT COUNT(*) FROM `article` LEFT JOIN `category` ON article.category=category.cid; "
            )
            data = (10 * (int(page) - 1), 10 * int(page))
            count_data = ()
        result = self.doAction(search_stmt, data)
        if result == False:
            return False

        return {"data": [{"id": eveArticle['aid'],
                          "title": eveArticle['title'],
                          "description": eveArticle['description'],
                          "watched": eveArticle['watched'],
                          "category": eveArticle['category'],
                          "publish": str(eveArticle['publish']),
                          "picture": self.getPicture(eveArticle['content'])}
                         for eveArticle in result.fetchall()],
                "count": int(self.doAction(count_stmt, count_data).fetchone()["COUNT(*)"]) + 1}

    def getHotArticleList(self):
        search_stmt = (
            "SELECT article.*,category.name FROM `article` LEFT JOIN `category` ON article.category=category.cid ORDER BY article.watched LIMIT 0,5"
        )
        result = self.doAction(search_stmt, ())
        if result == False:
            return False
        return [{"id": eveArticle['aid'],
                 "title": eveArticle['title'],
                 "description": eveArticle['description'],
                 "watched": eveArticle['watched'],
                 "category": eveArticle['category'],
                 "publish": str(eveArticle['publish']),
                 "picture": self.getPicture(eveArticle['content'])}
                for
                eveArticle in result.fetchall()]

    def getTagsArticle(self, aid):
        search_stmt = (
            "SELECT tags.name, tags.tid FROM `article_tags` LEFT JOIN `tags` ON article_tags.tid=tags.tid WHERE article_tags.aid=%s;"
        )
        result = self.doAction(search_stmt, (aid,))
        if result == False:
            return False
        return [{"id": eveTag["tid"], "name": eveTag["name"]} for eveTag in result.fetchall()]

    def getTagsList(self):
        search_stmt = (
            "SELECT * FROM tags ORDER BY RAND() LIMIT 20; "
        )
        result = self.doAction(search_stmt, ())
        if result == False:
            return False
        return [{"id": eveTag['tid'], "name": eveTag['name']} for eveTag in result.fetchall()]

    def getArticleContent(self, aid):
        search_stmt = (
            "SELECT article.*, category.name FROM `category` LEFT JOIN `article` ON category.cid=article.category WHERE article.aid=%s;"
        )
        result = self.doAction(search_stmt, (aid))
        if result == False:
            return False
        article = result.fetchone()
        return {
            "id": article["aid"],
            "title": article["title"],
            "content": article["content"],
            "description": article["description"],
            "watched": article["watched"],
            "category": article["name"],
            "publish": str(article["publish"]),
            "tags": self.getTagsArticle(article["aid"]),
            "next": self.getOtherArticle(aid, "next"),
            "pre": self.getOtherArticle(aid, "pre")
        } if article else {}

    def getOtherArticle(self, aid, articleType):
        search_stmt = (
            "SELECT * FROM `article` WHERE aid=(select max(aid) from `article` where aid>%s)"
        ) if articleType == "next" else (
            "SELECT * FROM `article` WHERE aid=(select max(aid) from `article` where aid<%s)"
        )
        result = self.doAction(search_stmt, (aid))
        if result == False:
            return False
        article = result.fetchone()
        return {
            "id": article["aid"],
            "title": article["title"]
        } if article else {}

    def getComments(self, aid):
        search_stmt = (
            "SELECT * FROM `comments` WHERE article=%s AND is_show=1 ORDER BY -cid LIMIT 100;"
        )
        result = self.doAction(search_stmt, (aid))
        if result == False:
            return False
        return [{"content": eveComment['content'],
                 "publish": str(eveComment['publish']),
                 "user": eveComment['user'],
                 "remark": eveComment['remark']} for eveComment in result.fetchall()]

    def addComment(self, content, user, email, aid):
        insert_stmt = (
            "INSERT INTO `comments` (`cid`, `content`, `publish`, `user`, `email`, `article`, `uni_mark`) "
            "VALUES (NULL, %s, CURRENT_TIMESTAMP, %s, %s, %s, %s)"
        )
        result = self.doAction(insert_stmt, (content, user, email, aid, hashlib.md5(
            ("%s----%s----%s----%s" % (str(content), str(user), str(email), str(aid))).encode("utf-8")).hexdigest()))
        return False if result == False else True

    def updateArticleWatched(self, wid):
        update_stmt = (
            "UPDATE `article` SET `watched`=`watched`+1 WHERE `aid` = %s"
        )
        return False if self.doAction(update_stmt, (wid)) == False else True

    def getPicture(self, content):
        resultList = [eve[1] for eve in re.findall('<img(.*?)src="(.*?)"(.*?)>', content)]
        return resultList[0] if resultList else self.getDefaultPic()

    def getTag(self, tag):
        search_stmt = (
            "SELECT * FROM `tags` WHERE name=%s;"
        )
        result = self.doAction(search_stmt, (tag,))
        return False if not result or result.rowcount == 0 else result.fetchone()['tid']

    def addTag(self, tag):
        insert_stmt = (
            "INSERT INTO `tags` (`tid`, `name`, `remark`) "
            "VALUES (NULL, %s, NULL)"
        )
        result = self.doAction(insert_stmt, (tag))
        return False if result == False else result.lastrowid

    def addArticleTag(self, article, tag):
        insert_stmt = (
            "INSERT INTO `article_tags` (`atid`, `aid`, `tid`) "
            "VALUES (NULL, %s, %s)"
        )
        result = self.doAction(insert_stmt, (article, tag))
        return False if result == False else True
