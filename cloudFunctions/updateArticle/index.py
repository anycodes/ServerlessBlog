# -*- coding: utf8 -*-

import json
import html2text
from snownlp import SnowNLP

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

        article = mysql.getArticleContent(aid)
        print(article)
        content = article["content"]
        h = html2text.HTML2Text()
        h.ignore_links = True
        for eve in SnowNLP(h.handle(content)).keywords(10):
            if len(eve) >= 2 and len(eve) <= 5:
                tid = mysql.getTag(eve)
                if not tid:
                    tid = mysql.addTag(eve)
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
