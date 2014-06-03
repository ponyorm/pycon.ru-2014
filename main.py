import os.path
import tornado.web, tornado.ioloop
from jinja2 import Environment, FileSystemLoader

template_env = Environment(loader=FileSystemLoader(searchpath="templates"))

class BaseHandler(tornado.web.RequestHandler):
    def render(self, file_name, **kwargs):
        template = template_env.get_template(file_name)
        self.write(template.render(**kwargs))

class MainHandler(BaseHandler):
    def get(self):
        self.render("photos.html")

if __name__ == "__main__":
    app = tornado.web.Application(
        [
            (r"/", MainHandler),
        ],
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        debug=True
    )
    app.listen(8080)
    tornado.ioloop.IOLoop.instance().start()
