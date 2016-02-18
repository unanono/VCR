# -*- coding: utf-8 *-*

import tornado.web
import tornado.escape

import json
import pymongo

from utils import *

import uuid
from os import path
from base64 import b64decode
import logging

#Esto deberia estar en otro lado
DBConnection = pymongo.Connection(DBHost, int(DBPort))
DBInstance = DBConnection.record
#DB Authentication
#DBInstance.authenticate(DBAdminUser, DBAdminPassword)


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        user_json = self.get_secure_cookie(cookieSessionName)
        if not user_json:
            return None
        return tornado.escape.json_decode(user_json)


class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie(cookieSessionName)
        #self.write("Bye")
        self.clear_cookie('next')
        self.redirect("/")


class AuthHandler(BaseHandler):
    def get(self):
        self.set_cookie('next', self.get_argument("next", "/"))
        self.redirect("/index")

    @tornado.web.asynchronous
    def post(self):
        if self.get_argument("user") and self.get_argument("password"):
            userStr = tornado.escape.url_escape(self.get_argument("user"))
            passwd = tornado.escape.url_escape(self.get_argument("password"))
            #curso = tornado.escape.url_escape(self.get_argument("curso"))
            passStr = passwd
            user = DBInstance.users.find_one({'name': userStr,
                                              'password': passStr})
            print user
            self._on_auth(user)

    def _on_auth(self, user):
        if not user:
            self.redirect('/')
            #raise tornado.web.HTTPError(500, "Fallo la autenticacion")
        else:
            #self.set_secure_cookie(cookieSessionName,
            #                        tornado.escape.json_encode(user.nombre),
            #                        expires_days=1)

            #Borro el ObjectId porque no es jsonizable
            del user['_id']

            #Para agregar el curso asi queda en la cookie
            user['curso'] = None
            self.set_secure_cookie(cookieSessionName,
                                   json.dumps(user),
                                   expires_days=1)
            #print user
            #n = self.get_cookie('next', '/Index')
            #self.clear_cookie('next')
            self.redirect('/index')


class LoginHandler(BaseHandler):
    def get(self):
        user_json = self.get_secure_cookie(cookieSessionName)
        if not user_json:
            self.render(templateName('login.html'))
        else:
            self.redirect("/index")


class SlideHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        usuario = self.current_user['name']
        sn = self.get_argument('slideNumber')
        sName = self.get_argument('slideName')
        try:
            with open(slideImage(usuario, sName, sn), 'rb') as f:
                s = f.read()
                #print slideImage(usuario, sName, sn)
                self.write(s)
        except IOError as e:
            print 'No hay mas slides'


class IndexHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        black_board = self.render_string(templateName('black_board.html'))
        menu_superior = self.render_string(templateName('menuSuperior.html'),
                                           usuario=self.current_user['name'])
        chat_panel = self.render_string(templateName('chat.html'),
                                        messages=[])
        recursos_panel = None
        self.render(templateName('index.html'),
                    menu_superior=menu_superior,
                    black_board_panel=black_board,
                    chat_panel=chat_panel,
                    recursos_panel=recursos_panel)


class GenericMessageMixin(object):
    """
    Clase que agrega el comportamiento que debe adoptar un handler
    para despachar los mensajes hacia todos los clientes
    """
    observers = set()
    cache = []
    cache_size = 200

    def wait_for_message(self, callback):
        """
        Agrego el callback del observer a la lista
        para que quede en espera de un nuevo mensaje
        """
        localclass = self.__class__
        localclass.observers.add(callback)

    def new_message(self, message):
        localclass = self.__class__
        for callbakfn in localclass.observers:
            callbakfn(message)

    def cancel_wait(self, callbackfn):
        localclass = self.__class__
        localclass.observers.remove(callbackfn)


class BlackboardMixin(object):
    observers = set()
    cache = []
    cache_size = 200

    def wait_for_messages(self, callback, cursor=None):
        cls = BlackboardMixin
        cls.observers.add(callback)

    def cancel_wait(self, callback):
        cls = BlackboardMixin
        cls.observers.remove(callback)

    def new_messages(self, traces):
        cls = BlackboardMixin
        logging.info("Sending new message to %r listeners", len(cls.observers))
        for callback in cls.observers:
            try:
                callback(traces)
            except:
                logging.error("Error in waiter callback", exc_info=True)
        cls.observers = set()
        cls.cache.extend(traces)
        if len(cls.cache) > self.cache_size:
            cls.cache = cls.cache[-self.cache_size:]


class BlackboardHandler(BaseHandler, BlackboardMixin):
    @tornado.web.authenticated
    def post(self):
        message = {
            "id": str(uuid.uuid4()),
            "points": self.get_argument("points"),
        }
        if self.get_argument("next", None):
            self.redirect(self.get_argument("next"))
        else:
            self.write('msg:ok')
        self.new_messages([message])


class BlackboardUpdatesHandler(BaseHandler, BlackboardMixin):
    @tornado.web.authenticated
    @tornado.web.asynchronous
    def post(self):
        cursor = self.get_argument("cursor", None)
        self.wait_for_messages(self.on_new_messages,
                               cursor=cursor)

    def on_new_messages(self, messages):
        # Closed client connection
        if self.request.connection.stream.closed():
            return
        self.finish(dict(messages=messages))

    def on_connection_close(self):
        self.cancel_wait(self.on_new_messages)


class MessageMixin(object):
    """
    Clase que mantiene la cache de mensajes y los callbacks
    a los clientes conectados al chat
    """
    waiters = set()
    cache = []
    cache_size = 200

    def wait_for_messages(self, callback, cursor=None):
        cls = MessageMixin
        if cursor:
            index = 0
            for i in xrange(len(cls.cache)):
                index = len(cls.cache) - i - 1
                if cls.cache[index]["id"] == cursor:
                    break
            recent = cls.cache[index + 1:]
            if recent:
                callback(recent)
                return
        cls.waiters.add(callback)

    def cancel_wait(self, callback):
        cls = MessageMixin
        cls.waiters.remove(callback)

    def new_messages(self, messages):
        cls = MessageMixin
        logging.info("Sending new message to %r listeners", len(cls.waiters))
        for callback in cls.waiters:
            try:
                callback(messages)
            except:
                logging.error("Error in waiter callback", exc_info=True)
        cls.waiters = set()
        cls.cache.extend(messages)
        if len(cls.cache) > self.cache_size:
            cls.cache = cls.cache[-self.cache_size:]


class MessageNewHandler(BaseHandler, MessageMixin):
    @tornado.web.authenticated
    def post(self):
        message = {
            "id": str(uuid.uuid4()),
            "from": self.current_user["name"],
            "body": self.get_argument("body"),
        }
        message["html"] = self.render_string(templateName("mensaje.html"),
                                             message=message)
        if self.get_argument("next", None):
            self.redirect(self.get_argument("next"))
        else:
            self.write(message)
        self.new_messages([message])


class MessageUpdatesHandler(BaseHandler, MessageMixin):
    @tornado.web.authenticated
    @tornado.web.asynchronous
    def post(self):
        cursor = self.get_argument("cursor", None)
        self.wait_for_messages(self.on_new_messages,
                               cursor=cursor)

    def on_new_messages(self, messages):
        # Closed client connection
        if self.request.connection.stream.closed():
            return
        self.finish(dict(messages=messages))

    def on_connection_close(self):
        self.cancel_wait(self.on_new_messages)


class DocumentDownloadHandler(BaseHandler):
    @tornado.web.authenticated
    #@tornado.web.asynchronous
    def get(self):
        fileName = self.get_argument('filename')
        uploader = self.get_argument('uploader')
        filen = fileName.split('/')[-1]
        if '/' in uploader or '/' in filen:
            self.write('msg')
        else:
            fileName = path.join(UploadsFolder, uploader, filen)
            print fileName
            with open(fileName, 'rb') as f:
                data = f.read()
                self.set_header('Content-Type', 'application/pdf')
                self.set_header('Content-Disposition',
                                'attachment; filename="{0}"'.format(filen))
                self.write(data)
