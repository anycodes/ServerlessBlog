# -*- coding: utf8 -*-

import json,re
import html2text
import jieba.analyse

try:
    import returnCommon
    from mysqlCommon import mysqlCommon
except:
    import common.testCommon

    common.testCommon.setEnv()

    import common.returnCommon as returnCommon
    from common.mysqlCommon import mysqlCommon

mysql = mysqlCommon()


def main_handler(event, context):
    try:
        print(event)

        aid = event['id']
        tagsList = [eve["id"] for eve in mysql.getTagsArticle(aid)]
        article = mysql.getArticleContent(aid)
        print(article)
        content = article["content"]
        pat = re.compile(r'[\u4e00-\u9fa5]+')
        h = html2text.HTML2Text()
        h.ignore_links = True
        content = "，".join(pat.findall(h.handle(content)))
        keywords = jieba.analyse.extract_tags(content, topK=10, withWeight=False, allowPOS=('n', 'vn'))
        for eve in keywords:
            if len(eve) >= 2 and len(eve) <= 5:
                tid = mysql.getTag(eve)
                if not tid:
                    tid = mysql.addTag(eve)
                if tid not in tagsList:
                    mysql.addArticleTag(aid, tid)
        return returnCommon.return_msg(False, "")
    except Exception as e:
        print(e)
    return returnCommon.return_msg(True, "数据异常，请联系管理员处理")


def test():
    event = {
        "id": 1
    }
    print(main_handler(event, None))


if __name__ == "__main__":
    test()
