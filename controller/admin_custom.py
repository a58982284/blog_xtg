# coding=utf-8
from base import BaseHandler
from tornado.gen import coroutine
from tornado.web import authenticated
from config import config
from service.custom_service import BlogInfoService
from service.init_service import SiteCacheService
from service.plugin_service import PluginService


class AdminCustomBlogInfoHandler(BaseHandler):

    @authenticated
    def get(self):
        self.render("admin/custom_blog_info.html", navbar_styles=config['navbar_styles'])

    @coroutine
    @authenticated
    def post(self):
        info = dict(title=self.get_argument("title"), signature=self.get_argument("signature"),
                    navbar=self.get_argument("navbar"),)
        blog_info = yield self.async_do(BlogInfoService.update_blog_info, self.db, info)
        if blog_info:
            #  更新本地及redis缓存，并发布消息通知其他节点更新
            yield self.flush_blog_info(blog_info)
            self.add_message('success', u'修改博客信息成功!')
        else:
            self.add_message('danger', u'修改失败！')
        self.redirect(self.reverse_url("admin.custom.blog_info"))

    @coroutine
    def flush_blog_info(self, blog_info):
        #  更新本地及redis缓存，并发布消息通知其他节点更新
        yield SiteCacheService.update_blog_info(self.cache_manager, blog_info,
                                                is_pub_all=True, pubsub_manager=self.pubsub_manager)


class AdminCustomBlogPluginHandler(BaseHandler):

    def get(self, require):
        if require == 'add':
            self.add_get()

    @coroutine
    def post(self, require):
        if require == 'add':
            yield self.add_post()

    @authenticated
    def add_get(self):
        self.render("admin/blog_plugin_add.html")

    @coroutine
    @authenticated
    def add_post(self):
        plugin = dict(title=self.get_argument('title'),note=self.get_argument('note'),
                      content=self.get_argument('content'),)
        plugin_saved = yield self.async_do(PluginService.save, self.db, plugin)
        if plugin_saved and plugin_saved.id:
            yield self.flush_plugins()
            self.add_message('success', u'保存成功!')
        else:
            self.add_message('danger', u'保存失败！')
        self.redirect(self.reverse_url('admin.custom.plugin.action', 'add'))

    @coroutine
    def flush_plugins(self, plugins=None):
        if plugins is None:
            plugins = yield self.async_do(PluginService.list_plugins, self.db)
        yield SiteCacheService.update_plugins(self.cache_manager, plugins,
                                              is_pub_all=True, pubsub_manager=self.pubsub_manager)