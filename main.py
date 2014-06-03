import os.path
import tornado.web, tornado.ioloop
from jinja2 import Environment, FileSystemLoader
from entities import *

template_env = Environment(loader=FileSystemLoader(searchpath="templates"))

class BaseHandler(tornado.web.RequestHandler):
    def render(self, file_name, **kwargs):
        template = template_env.get_template(file_name)
        self.write(template.render(**kwargs))

class MainHandler(BaseHandler):
    def get(self):
        self.render("photos.html")

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
            self.redirect('/')

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
            self.redirect('/')

if __name__ == "__main__":
    app = tornado.web.Application(
        [
            (r"/", MainHandler),
            (r"/login", LoginHandler),
            (r"/signup", SignupHandler),
        ],
        cookie_secret='Secret Cookie',
        login_url="/login",
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        debug=True
    )
    app.listen(8080)
    tornado.ioloop.IOLoop.instance().start()
