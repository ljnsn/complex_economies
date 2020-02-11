# -*- coding: utf-8 -*-
import dash_core_components as dcc
import dash_html_components as html

from mesa.visualization.UserParam import UserSettableParameter


class UserParam(UserSettableParameter):
    
    def render(self):
        
        element = None
        
        if self.param_type == self.NUMBER:
            
            element = dcc.Input(
                id=self.name,
                placeholder='Enter a number',
                type='number',
                value=self._value
            )

        elif self.param_type == self.SLIDER:
            
            part = 1
            if self.max_value <= 100:
                part = 10
            elif self.max_value <= 1000:
                part = 100
            elif self.max_value <= 10000:
                part = 1000
            
            element = dcc.Slider(
                id=self.name,
                min=self.min_value,
                max=self.max_value,
                step=self.step,
                value=self._value,
                marks={
                    val: {'label': str(val)}
                    for val in range(0, self.max_value + 1, part)
                }
            )

        elif self.param_type == self.CHOICE:
            
            element = dcc.Dropdown(
                id=self.name,
                options=[
                    {'label': choice, 'value': choice}
                    for choice in self.choices
                ],
                value=self._value
            )

        elif self.param_type == self.CHECKBOX:
            
            element = dcc.Checklist(
                id=self.name,
                options=[
                    {'label': self.name, 'value': self.name}
                ],
                value=[self.name] if self._value else []
            )

        return html.Div([
            html.Label(self.name),
            element
        ])
