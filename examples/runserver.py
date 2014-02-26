from werkzeug.wsgi import DispatcherMiddleware
from werkzeug.serving import run_simple

from index.index import app as index
import examples.simple.simple
import examples.sqla.simple
import examples.layout.simple
import examples.forms.simple
import examples.auth.auth

examples.sqla.simple.build_sample_db()
examples.layout.simple.build_sample_db()
examples.forms.simple.build_sample_db()
examples.auth.auth.build_sample_db()

application = DispatcherMiddleware(
    index,
    {
        '/simple': examples.simple.simple.app,
        '/sqla/simple': examples.sqla.simple.app,
        '/layout': examples.layout.simple.app,
        '/forms': examples.forms.simple.app,
        '/auth': examples.auth.auth.app,
    }
)

if __name__ == '__main__':
    run_simple('localhost', 5000, application,
               use_reloader=True, use_debugger=True, use_evalex=True)