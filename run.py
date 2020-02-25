
import dash

from complex_economies.app import makeserver


app = dash.Dash(
    __name__,
    meta_tags=[{
        "name": "viewport",
        "content": "width=device-width, initial-scale=1"
    }]
)

server = makeserver(app)
server.run()
