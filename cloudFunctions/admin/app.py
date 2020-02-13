# coding: utf-8
from flask import Flask
import html2text, os
from snownlp import SnowNLP
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_sqlalchemy import SQLAlchemy
from flask_ckeditor import CKEditor, CKEditorField
from sqlalchemy.event import listens_for
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, ForeignKey, String, TIMESTAMP, Text, text, create_engine
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.scf.v20180416 import scf_client, models

if not os.environ.get('mysql_user'):
    import common.testCommon

    common.testCommon.setEnv()

DIALECT = 'mysql'
DRIVER = 'pymysql'
USERNAME = os.environ.get('mysql_user')
PASSWORD = os.environ.get('mysql_password')
HOST = os.environ.get('mysql_host')
PORT = int(os.environ.get('mysql_port'))
DATABASE = os.environ.get('mysql_db')

SQLALCHEMY_DATABASE_URI = "{}+{}://{}:{}@{}:{}/{}?charset=utf8". \
    format(DIALECT, DRIVER, USERNAME, PASSWORD, HOST, PORT, DATABASE)

Base = declarative_base()
metadata = Base.metadata


class Category(Base):
    __tablename__ = 'category'

    cid = Column(INTEGER(11), primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    sorted = Column(INTEGER(11), nullable=False, server_default=text("'1'"))
    remark = Column(Text)

    def __repr__(self):
        return self.name


class Tag(Base):
    __tablename__ = 'tags'

    tid = Column(INTEGER(11), primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    remark = Column(Text)

    def __repr__(self):
        return self.name


class Article(Base):
    __tablename__ = 'article'

    aid = Column(INTEGER(11), primary_key=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    description = Column(Text, server_default="")
    publish = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    watched = Column(INTEGER(11), server_default=text("'0'"))
    category = Column(ForeignKey('category.cid', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)
    remark = Column(Text)

    category1 = relationship('Category')

    def __repr__(self):
        return self.title


class ArticleTag(Base):
    __tablename__ = 'article_tags'

    atid = Column(INTEGER(11), primary_key=True)
    aid = Column(ForeignKey('article.aid', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)
    tid = Column(ForeignKey('tags.tid', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)

    article = relationship('Article')
    tag = relationship('Tag')


class Comment(Base):
    __tablename__ = 'comments'

    cid = Column(INTEGER(11), primary_key=True)
    content = Column(Text, nullable=False)
    publish = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    user = Column(String(255), nullable=False)
    email = Column(String(255))
    article = Column(ForeignKey('article.aid', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)
    remark = Column(Text)
    uni_mark = Column(String(255), nullable=False, unique=True)
    is_show = Column(INTEGER(11), nullable=False, server_default=text("'0'"))

    article1 = relationship('Article')


class CategoryView(ModelView):
    column_labels = dict(
        name=u'分类名',
        sorted=u'排序',
        remark=u'备注'
    )
    column_list = ['name', 'sorted', 'remark']


class TagView(ModelView):
    column_labels = dict(
        name=u'标签名',
        remark=u'备注'
    )
    column_list = ['name', 'remark']


class ArticleView(ModelView):
    column_labels = dict(
        title=u'标题',
        content=u'正文',
        description=u'文章描述',
        publish=u'发布时间',
        watched=u'阅读次数',
        remark=u'备注',
        category=u'分类名',
        category1=u'分类名',
    )
    column_list = ['title', 'category1', 'publish', 'watched']
    form_overrides = dict(content=CKEditorField)  # 重写表单字段，将 text 字段设为 CKEditorField
    create_template = 'edit.html'  # 指定创建记录的模板
    edit_template = 'edit.html'  # 指定编辑记录的模板


class ArticleTagView(ModelView):
    column_labels = dict(
        aid=u'文章',
        tid=u'标签',
        article=u'文章',
        tag=u'标签',
    )
    column_list = ['article', 'tag']


class CommentView(ModelView):
    column_labels = dict(
        content=u'评论',
        publish=u'发布时间',
        user=u'用户',
        email=u'邮箱',
        article=u'文章',
        remark=u'备注',
        uni_mark=u'唯一标识',
        is_show=u'是否显示',
        article1=u'文章'
    )
    column_choices = {
        'is_show': [(0, '不显示'), (1, '显示')]
    }
    column_list = ['article1', 'content', 'user', 'publish', 'is_show']


@listens_for(Article, 'before_insert')
@listens_for(Article, 'before_update')
def addDescription(mapper, connection, target):
    h = html2text.HTML2Text()
    h.ignore_links = True
    if not target.description or len(target.description) <= 1:
        target.description = ", ".join(SnowNLP(h.handle(target.content)).summary(5))


@listens_for(Article, 'after_insert')
@listens_for(Article, 'after_update')
def addTags(mapper, connection, target):
    try:
        cred = credential.Credential(os.environ.get('tencent_secret_id'), os.environ.get('tencent_secret_key'))
        httpProfile = HttpProfile()
        httpProfile.endpoint = "scf.tencentcloudapi.com"

        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        client = scf_client.ScfClient(cred, "", clientProfile)

        req = models.InvokeRequest()
        params = '{"FunctionName":"Blog_Admin_updateArticle","InvocationType":"Event","ClientContext":"{\\"id\\": %s}","Namespace":"default"}' % (
            target.aid)
        req.from_json_string(params)
        resp = client.Invoke(req)
        print(resp)

    except TencentCloudSDKException as err:
        print(err)


def create_app(Flask):
    app = Flask(__name__)
    db = SQLAlchemy(app)
    ckeditor = CKEditor(app)

    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_COMMIT_TEARDOWN'] = True
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
    app.config['BABEL_DEFAULT_LOCALE'] = 'zh_CN'
    # app.config['SERVER_NAME'] = '*'
    app.config.update(SECRET_KEY='123456')
    admin = Admin(app, name='Serverless Blog', template_mode='bootstrap3', index_view=AdminIndexView(
        name=u'首页',
        template='/welcome.html',
        url='/admin',
    ))
    admin.add_view(CategoryView(Category, db.session, name=u"文章分类"))
    admin.add_view(TagView(Tag, db.session, name=u"标签管理"))
    admin.add_view(ArticleView(Article, db.session, name=u"文章列表"))
    admin.add_view(ArticleTagView(ArticleTag, db.session, name=u"文章标签"))
    admin.add_view(CommentView(Comment, db.session, name=u"评论列表"))
    return app


if __name__ == '__main__':
    app = create_app(Flask)
    app.run()
