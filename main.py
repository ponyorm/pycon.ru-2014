import os.path
from hashlib import md5
import json
import tornado.web, tornado.ioloop
from jinja2 import Environment, FileSystemLoader
from sockjs.tornado import SockJSRouter, SockJSConnection
from entities import *

import logging
logging.getLogger().setLevel(logging.INFO)

template_env = Environment(loader=FileSystemLoader(searchpath="templates"))

TORNADO_PORT = 8080

ws_router = None
connections = set()

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("username")
    def render(self, file_name, **kwargs):
        template = template_env.get_template(file_name)
        kwargs.update({'TORNADO_PORT': TORNADO_PORT, 'current_user': self.current_user})
        self.write(template.render(**kwargs))
    def broadcast(self, msg):
        ws_router.broadcast(connections, msg)

class MainHandler(BaseHandler):
    @db_session
    def get(self):
        photos = select(p for p in Photo)
        self.render("photos.html", photos=photos)

class LoginHandler(BaseHandler):
    def get(self):
        self.render('login.html')
    @db_session
    def post(self):
        username = self.get_argument('username', '')
        password = self.get_argument('password', '')
        user = User.get(username=username, password=password)
        if user is None:
            self.render('login.html', error='Login and password do not match')
        else:
            self.set_secure_cookie('username', username)
            self.redirect('/user/%s' % username)

class SignupHandler(BaseHandler):
    def get(self):
        self.render('signup.html')
    @db_session
    def post(self):
        username = self.get_argument('username', '')
        password = self.get_argument('password', '')
        if not username or not password:
            self.render('signup.html', error='Please specify username and password')
        elif User.exists(username=username):
            self.render('signup.html', error='Username is already taken')
        else:
            User(username=username, password=password)
            self.set_secure_cookie('username', username)
            self.redirect('/user/%s' % username)

class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_all_cookies()
        self.redirect('/')

class UserHomeHandler(BaseHandler):
    @db_session
    def get(self, username):
        user = User.get(username=username)
        if user is None:
            raise tornado.web.HTTPError(404, 'No such user')
        photos = select(p for p in Photo if p.user.username == username)
        self.render('photos.html', page_owner=username, photos=photos)

class UploadHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render('upload.html')
    @tornado.web.authenticated
    @db_session
    def post(self):
        if 'photo_file' not in self.request.files:
            self.render('upload.html')
            return
        photo_file = self.request.files['photo_file'][0]
        content = photo_file['body']
        extension = os.path.splitext(photo_file['filename'])[1]
        filename = "photos/%s%s" % (md5(content).hexdigest(), extension)
        if not os.path.exists(filename):
            with open(filename, 'wb') as f:
                f.write(content)
        photo_url = '/%s' % filename
        user = User.get(username=self.current_user)
        photo = Photo(user=user, filename=filename, photo_url=photo_url)
        commit()
        self.broadcast({'event': 'new_photo',
                        'data': {'id': photo.id, 'photo_url': photo_url, 'username': self.current_user}})
        self.redirect('/')

class WSConnection(SockJSConnection):
    def on_open(self, request):
        print 'on open'
        connections.add(self)
    def on_message(self, message):
        print 'on message', message
        data = json.loads(message)
        message_name = data.get('message_name')
        data = data.get('data')
        func = getattr(self, 'on_' + message_name)
        func(data)
    def on_close(self):
        print 'on close'
        connections.discard(self)
    @db_session
    def on_get_last_photos(self, data):
        print 'on_get_last_photos'
        current_user = data.get('current_user', None)
        page_owner = data.get('page_owner', None)
        query = select(p for p in Photo)
        if page_owner:
            query = query.filter(lambda p: p.user.username == page_owner)
        photos = query.order_by(desc(Photo.id))[:10]
        data = [p.to_json() for p in photos]
        self.send({'event': 'photo_list', 'data': data})

if __name__ == "__main__":
    ws_router = SockJSRouter(WSConnection, '/ws')
    app = tornado.web.Application(
        [
            (r"/", MainHandler),
            (r"/login", LoginHandler),
            (r"/signup", SignupHandler),
            (r"/logout", LogoutHandler),
            (r"/user/(\w+)", UserHomeHandler),
            (r"/upload", UploadHandler),
            (r"/photos/(.*)", tornado.web.StaticFileHandler, {'path': 'photos/'}),
        ] + ws_router.urls,
        cookie_secret='Secret Cookie',
        login_url="/login",
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        debug=True
    )
    app.listen(TORNADO_PORT)
    tornado.ioloop.IOLoop.instance().start()
