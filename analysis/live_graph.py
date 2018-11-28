'''
Description - Data grapher
@author - John Sentz
@date - 27-Nov-2018
@time - 16:28
'''

import dash
from dash.dependencies import Output, Event, Input
import dash_core_components as dcc
import dash_html_components as html
import plotly
import plotly.graph_objs as go
import sqlite3
import pandas

app = dash.Dash(__name__)
app.layout = html.Div(
    [html.H2('Live Twitter Sentiment'),
     dcc.Input(id='sentiment_term', value='hollywood', type='text'),
     dcc.Graph(id='live-graph', animate=False),
     dcc.Interval(
         id='graph-update',
         interval=1 * 1000
     ),
     ]
)


@app.callback(
    Output('live-graph', 'figure'),
    [Input(component_id='sentiment_term', component_property='value')],
    events=[Event('graph-update', 'interval')]
)
def update_graph_scatter(sentiment_term):
    ###########################################################################
    #
    # Try to open connection to database
    # query db for sentiment term,
    # create data frame from query,
    # create smoothed rolling average graph of sentiment for specified term
    #
    try:
        the_connection = sqlite3.connect('twitter.db')
        # the_cursor = the_connection.cursor()
        data_frame = pandas.read_sql(
            "SELECT * FROM sentiment WHERE tweet LIKE ? ORDER BY unix DESC LIMIT 1000",
            the_connection,
            params=('%' + sentiment_term + '%',)
        )

        #######################################################################
        # sort by timestamp
        #
        data_frame.sort_values('unix', inplace=True)
        data_frame['sentiment_smoothed'] = data_frame['sentiment'].rolling(int(len(data_frame) / 2)).mean()

        data_frame['date'] = pandas.to_datetime(data_frame['unix'], unit='ms')
        data_frame.set_index('date', inplace=True)

        data_frame = data_frame.resample('1min').mean()
        data_frame.dropna(inplace=True)
        x_index = data_frame.index
        y_index = data_frame.sentiment_smoothed

        data = plotly.graph_objs.Scatter(
            x=x_index,
            y=y_index,
            name='Scatter',
            mode='lines+markers'
        )

        return {'data': [data], 'layout': go.Layout(xaxis=dict(range=[min(x_index), max(x_index)]),
                                                    yaxis=dict(range=[min(y_index), max(y_index)]),
                                                    title='Term: {}'.format(sentiment_term))}

    except Exception as e:
        with open('errors.txt', 'a') as f:
            f.write(str(e))
            f.write('\n')


if __name__ == '__main__':
    app.run_server(debug=True)
