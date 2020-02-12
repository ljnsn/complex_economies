# -*- coding: utf-8 -*-
import datetime as dt

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State

from .user_param import UserParam


def make_header(title, description=''):
    return html.Div([
        html.H4(title, className='app_desc_title'),
        html.P(description, className='app_desc_text')
    ], className='app_desc')


def make_controls(interval):
    return html.Div([
        html.Button(
            'Start',
            id='start-stop-button',
            n_clicks=0,
            n_clicks_timestamp=-1
        ),
        html.Button(
            'Step',
            id='step-button',
            n_clicks=0,
            n_clicks_timestamp=-1
        ),
        html.Button(
            'Reset',
            id='reset-button',
            n_clicks=0,
            n_clicks_timestamp=-1
        ),
        html.Div([
            html.Label('Step Counter'),
            html.P(0, id='step-counter')
        ]),
        dcc.Interval(
            id='run-interval',
            interval=interval,
            n_intervals=0,
            disabled=True
        )
    ])


def make_params(user_settable_params):
    if not user_settable_params:
        return html.Div(className='params-container')
    params = []
    for param in user_settable_params:
        element = param.render()
        params.append(element)
    return html.Div(params, className='params-container')


def make_figure(module):
    return html.Div([
        html.Div([
            html.H6(module.title, className='fig_title')
        ]),
        dcc.Graph(
            id=module.title,
            figure=dict()
        )
    ], className='figure-div')


def make_figures(chart_modules):
    if not chart_modules:
        return html.Div(className='figures-container')
    charts = []
    for module in chart_modules:
        chart = make_figure(module)
        charts.append(chart)
    return html.Div(charts, className='figures-container')


def make_layout(title, description, chart_modules, user_settable_params, interval):
    return html.Div([
        make_header(title, description),
        make_controls(interval),
        make_params(user_settable_params),
        make_figures(chart_modules)
    ])


class ModularApp:
    
    app = dash.Dash(
        __name__,
        meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
        # suppress_callback_exceptions=True
    )
    server = app.server
    ip = '127.0.0.1'
    port = 8251
    model = None
    fps = 40
    last_update = -1

    def __init__(self, model_cls, visualization_elements, name="Mesa Model",
                 model_params={}):
        """ Create a new visualization server with the given elements. """
        # Prep visualization elements:
        self.visualization_elements = visualization_elements
        # Initializing the model
        self.model_name = name
        self.model_cls = model_cls
        self.description = 'No description available'
        if hasattr(model_cls, 'description'):
            self.description = model_cls.description
        elif model_cls.__doc__ is not None:
            self.description = model_cls.__doc__
        self.last_update = self.get_current_time()

        self.model_kwargs = model_params
        self.user_params = [
            val for param, val in model_params.items()
            if isinstance(val, UserParam)
        ]
        self.reset_model()
        self.app.layout = make_layout(
            self.model_name,
            self.description,
            self.visualization_elements,
            self.user_params,
            60 / self.fps * 1000
        )
    
    @staticmethod
    def get_current_time():
        """ Helper function to get the current time in seconds. """
    
        now = dt.datetime.now()
        total_time = (now.hour * 3600) + (now.minute * 60) + (now.second)
        return total_time

    def reset_model(self):
        """ Reinstantiate the model object, using the current parameters. """

        model_params = {}
        for key, val in self.model_kwargs.items():
            if isinstance(val, UserParam):
                if val.param_type == 'static_text':    # static_text is never used for setting params
                    continue
                model_params[key] = val.value
            else:
                model_params[key] = val

        self.model = self.model_cls(**model_params)
        self.model.running = False

    def render_model(self):
        """ Turn the current state of the model into a dictionary of
        visualizations

        """
        visualization_state = []
        for element in self.visualization_elements:
            element_state = element.render(self.model)
            visualization_state.append(element_state)
        return visualization_state

    def run_model(self):
        
        @self.app.callback(
            Output('step-counter', 'children'),
            [Input('step-button', 'n_clicks_timestamp'),
             Input('reset-button', 'n_clicks_timestamp'),
             Input('run-interval', 'n_intervals')],
            [State('step-counter', 'children')]
        )
        def step_callback(step_ts, reset_ts, n_intervals, current_step):
            if reset_ts > -1 and reset_ts > step_ts and not self.model.running:
                self.reset_model()
                return 0
            elif step_ts > -1 and step_ts > reset_ts and not self.model.running:
                self.model.step()
                return current_step + 1
            elif n_intervals > 0 and self.model.running:
                self.model.step()
                return current_step + 1
            return current_step
        
        @self.app.callback(
            [Output('start-stop-button', 'children'),
             Output('run-interval', 'disabled')],
            [Input('start-stop-button', 'n_clicks')]
        )
        def start_callback(n_clicks):
            if n_clicks > 0 and n_clicks % 2 != 0:
                self.model.running = True
                return 'Stop', False
            self.model.running = False
            return 'Start', True
    
        for element in self.visualization_elements:
            @self.app.callback(
                Output(element.title, 'figure'),
                Input('step-counter', 'children')
            )
            def update_figure(counter):
                if counter > 0:
                    pass

    def launch(self, port=None, debug=False):
        """ Run the app. """
        if port is not None:
            self.port = port
        self.run_model()
        self.app.run_server(host=self.ip, port=self.port, debug=debug)
