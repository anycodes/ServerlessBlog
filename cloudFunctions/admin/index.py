# -*-encoding=utf8-*-
import json, os
import hashlib
from flask_lambda import FlaskLambda
from app import create_app


# from flask import jsonify

def getReturnDict(body):
    return {
        "isBase64Encoded": False,
        "statusCode": 200,
        "headers": {'Content-Type': 'text/html'},
        "body": body
    }


def main_handler(event, context):
    print(event)

    user = os.environ.get('admin_user')
    password = os.environ.get('admin_password')
    token = hashlib.md5(str("%s----%s" % (user, password)).encode("utf-8")).hexdigest()

    # 用户登录
    if "cookie" not in event['headers'] or "token=%s"%token not in event['headers']["cookie"]:
        if "body" in event and "username" in event["body"] and "password" in event["body"]:
            body = json.loads(event["body"])
            if body["username"] == user and body["password"] == password:
                return getReturnDict(json.dumps({"token": token, "message": None}))
            return getReturnDict(json.dumps({"token": None, "message": "登录失败"}))
        with open("templates/login.html") as f:
            returnData = f.read()
        return getReturnDict(returnData)

    # 启动flask
    http_server = create_app(FlaskLambda)
    temp = http_server(event, context)
    temp["body"] = temp["body"].decode("utf-8")
    return temp


def test():
    event = {'body': 'name=sdsadasdsadasd&remark=', 'headerParameters': {}, 'headers': {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-encoding': 'gzip, deflate', 'accept-language': 'zh-CN,zh;q=0.9', 'cache-control': 'no-cache',
        'connection': 'keep-alive', 'content-length': '27', 'content-type': 'application/x-www-form-urlencoded',
        'cookie': 'Hm_lvt_a0c900918361b31d762d9cf4dc81ee5b=1574491278,1575257377', 'endpoint-timeout': '15',
        'host': 'blog.0duzhan.com', 'origin': 'http://blog.0duzhan.com', 'pragma': 'no-cache',
        'proxy-connection': 'keep-alive', 'referer': 'http://blog.0duzhan.com/admin/tag/new/?url=%2Fadmin%2Ftag%2F',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
        'x-anonymous-consumer': 'true', 'x-api-requestid': '656622f3b008a0d406a376809b03b52c',
        'x-b3-traceid': '656622f3b008a0d406a376809b03b52c', 'x-qualifier': '$LATEST'}, 'httpMethod': 'POST',
             'path': '/admin/tag/new/', 'pathParameters': {}, 'queryString': {'url': '/admin/tag/'},
             'queryStringParameters': {},
             'requestContext': {'httpMethod': 'ANY', 'identity': {}, 'path': '/admin', 'serviceId': 'service-23ybmuq7',
                                'sourceIp': '119.123.224.87', 'stage': 'release'}}
    print(main_handler(event, None))


if __name__ == "__main__":
    test()
