# -*- coding: utf8 -*-

import json, os, hashlib, cgi
import os, base64
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
from qcloud_cos import CosServiceError
from qcloud_cos import CosClientError

try:
    import returnCommon
except:
    import common.testCommon

    common.testCommon.setEnv()

    import common.returnCommon as returnCommon

secret_id = os.environ.get("tencent_secret_id")
secret_key = os.environ.get("tencent_secret_key")
region = os.environ.get("region")
config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
client = CosS3Client(config)


def main_handler(event, context):
    try:
        pictureBase64 = event["body"].split("base64,")[1]
        key = hashlib.md5(pictureBase64.encode("utf-8")).hexdigest()
        tempKey = '/blogcache/img/' + key
        with open('/tmp/%s' % key, 'wb') as f:
            f.write(base64.b64decode(pictureBase64))
        response = client.upload_file(
            Bucket=os.environ.get("website_bucket"),
            LocalFilePath='/tmp/%s' % key,
            Key=tempKey,
        )
        return {
            "uploaded": 1,
            "url": 'https://%s.cos.%s.myqcloud.com' % (
            os.environ.get("website_bucket"), os.environ.get("region")) + tempKey
        }
    except Exception as e:
        print(e)
    return {"uploaded": 0, "error": {"message": "数据异常，请联系管理员处理"}}


def test():
    event = {
        "requestContext": {
            "serviceId": "service-f94sy04v",
            "path": "/test/{path}",
            "httpMethod": "POST",
            "requestId": "c6af9ac6-7b61-11e6-9a41-93e8deadbeef",
            "identity": {
                "secretId": "abdcdxxxxxxxsdfs"
            },
            "sourceIp": "14.17.22.34",
            "stage": "release"
        },
        "headers": {
            "Accept-Language": "en-US,en,cn",
            "Accept": "text/html,application/xml,application/json",
            "Host": "service-3ei3tii4-251000691.ap-guangzhou.apigateway.myqloud.com",
            "User-Agent": "User Agent String"
        },
        "body": json.dumps({"id": 1}),
        "pathParameters": {
            "path": "value"
        },
        "queryStringParameters": {
            "foo": "bar"
        },
        "headerParameters": {
            "Refer": "10.0.2.14"
        },
        "stageVariables": {
            "stage": "release"
        },
        "path": "/test/value",
        "queryString": {
            "foo": "bar",
            "bob": "alice"
        },
        "httpMethod": "POST"
    }
    print(main_handler(event, None))


if __name__ == "__main__":
    test()
