# -*- coding: utf-8 *-*


import tornado.ioloop
import tornado.web

from os import path

from utils import *
from handlers import *
from uimodules import *


static_folder = 'static/'
static_path = path.join(path.dirname(__file__), static_folder)

settings = dict(
    cookie_secret="32oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
    #Si quiero que la cookie_secret cambie cada vez que
    #reinicie la app la cambio por lo de abajo
    #b64encode(uuid4().bytes + uuid4().bytes),
    login_url="/auth/login",
    static_path=path.join(path.dirname(__file__), "static"),
    ui_modules={"Index": IndexModule},
    autoescape=None,
)

application = tornado.web.Application([
    (r"/", LoginHandler),
    (r"/index", IndexHandler),
    (r"/slide", SlideHandler),
    #(r"/static/(.*)", tornado.web.StaticFileHandler, {"path": static_path}),
    (r"/auth/login", AuthHandler),
    (r"/auth/logout", LogoutHandler),
    (r"/a/message/new", MessageNewHandler),
    (r"/a/message/updates", MessageUpdatesHandler),
    (r"/a/blackboard/new", BlackboardHandler),
    (r"/a/blackboard/updates", BlackboardUpdatesHandler),
    (r"/download", DocumentDownloadHandler),

], '', None, False, **settings)

if __name__ == "__main__":
    address = '127.0.0.1'
    application.listen(60000, address=address)
    tornado.ioloop.IOLoop.instance().start()
