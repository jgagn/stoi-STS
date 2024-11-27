"""wsgi entry point

This module serves as the entry point for our application. This one starts the development server.
"""

from gymcomp_R0 import app
if __name__ == '__main__':
    app.run_server(debug=True)
