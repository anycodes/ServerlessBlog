# -*- coding: utf8 -*-

import yaml
import os


def setEnv():
    file = open("/Users/dfounderliu/Documents/code/ServerlessBlog/serverless.yaml", 'r', encoding="utf-8")
    file_data = file.read()
    file.close()

    data = yaml.load(file_data, Loader=yaml.FullLoader)
    for eveKey, eveValue in data['Conf']['inputs'].items():
        os.environ[eveKey] = str(eveValue)
