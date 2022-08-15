from dateutil import tz
from matplotlib.pyplot import figure, margins
import pytz
import datetime
from datetime import date
import plotly.graph_objs as go
import plotly
from dash import dcc, html, dash_table, ctx
from dash.dependencies import Input, Output, State
import dash
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client import InfluxDBClient, Point, WriteOptions
from http import client
from flask import Flask, render_template;
from flask import url_for, escape
from flask import request
import os
from numpy import True_
from panel import state
import pymysql as mysql
import pandas as pd
import urllib3
urllib3.disable_warnings()
# ==================================== MySQL Start ============================================
# Create the class of sensor node


class CreateSensorDB(object):
    def __init__(self, _host="localhost", _user="root", _password='shenwei66719126', _DBname='TestBed'):
        self.database = mysql.connect(
            host=_host, user=_user, password=_password, database=_DBname)
        self.cursor = self.database.cursor()

    def GetTableName(self):
        Table_Name = []
        GetTable_sql = "SHOW TABLES"
        self.cursor.execute(GetTable_sql)
        TableNames = self.cursor.fetchall()
        for tbname in TableNames:
            Table_Name.append(tbname[0])
        print(Table_Name);
        return Table_Name

    def GetFieldKey(self, TableName):
        column_sql = "SELECT * FROM " + TableName
        self.cursor.execute(column_sql)
        return[column[0] for column in self.cursor.fetchall()]

    def CreateTable(self, Table_name: str, FieldKey_Info: tuple):
        # Create table with given field key
        CreatTB_sql = "CREATE TABLE IF NOT EXISTS " + \
            Table_name + "(" + ", ".join(FieldKey_Info) + ")"
        self.cursor.execute(CreatTB_sql)
        print("Table: " + Table_name + "is created")
        return Table_name

    def InsertData(self, TableName: str, FieldKey: tuple, Data):
        '''
        param: SensorID --> primary key to identify each sensor
        param: FieldKey --> the name of coluoms to add 'Data'
        param: Data     --> general info of sensor with field key
        '''
        # Find the number of FieldKey
        Len_FieldKey = len(FieldKey); placeholder_list = ['%s'] * Len_FieldKey
        placeholders = tuple(placeholder_list)
        Insert_sql = "INSERT IGNORE INTO " + TableName + "(" + ", ".join(FieldKey) + ")" + "VALUES" + \
                            "(" + ", ".join(placeholders) + ")"
        self.cursor.executemany(Insert_sql, Data)
        self.database.commit(); print("Data have been inserted")

    def UpdateData(self, TableName: str, SensorID: int, FieldKey: str, Data):
        '''
        param: SensorID: a int to identify the sensorID to be updated
        '''
        update_sql = "UPDATE " + TableName + "SET " + FieldKey + "=" + str(Data) +\
                        "WHERE SensorID = " + str(SensorID)
        self.cursor.execute(update_sql); self.database.commit()
        print("The data have been updated")

    def GetALLData(self, TableName: str):
        import pandas as pd
        select_sql = "SELECT * FROM " + TableName
        self.cursor.execute(select_sql); _data = self.cursor.fetchall()
        column_sql = "SHOW COLUMNS FROM " + TableName
        self.cursor.execute(column_sql)
        _field_key = [column[0] for column in self.cursor.fetchall()]
        RequiredData = pd.DataFrame(data=list(_data), columns=_field_key)
        # The <RequiredData> is a tuple like ((...), (...), (...))
        return RequiredData

    def DropTable(self, Table_name: str):
        drop_sql = 'DROP TABLE IF EXISTS ' + Table_name
        self.cursor.execute(drop_sql)

    def __del__(self):
        self.database.close()


# Create database to store the general information for sensors
# sensorDB.database: connect to database; sensorDB.cursor: create cursor
sensorDB = CreateSensorDB();
# Create Two Tables: Xnode sensor and FBG sensor
Table_Xnode = 'Xnode_Sensor'; Table_FBG = 'FBG_Sensor'

Field_Xnode = ('SensorID INT AUTO_INCREMENT PRIMARY KEY',
                'Floor VARCHAR(100)',
                'Status VARCHAR(100)',
                'Location VARCHAR(100)')

Field_FBG = ('SensorID INT AUTO_INCREMENT PRIMARY KEY',
                'Floor VARCHAR(100)',
                'Status VARCHAR(100)',
                'Location VARCHAR(100)')

sensorDB.CreateTable(Table_Xnode, Field_Xnode)
sensorDB.CreateTable(Table_FBG, Field_FBG)

# sensor general info --> X_node
Xnode_Info = ((1, 'Floor-1', 'worked', str((1, 2, 3))),
                (2, 'Floor-1', 'worked', str((4, 5, 6))),
                (3, 'Floor-1', 'worked', str((7, 8, 9))),
                (4, 'Floor-2', 'worked', str((7, 8, 9))),
                (5, 'Floor-2', 'worked', str((7, 8, 9))),
                (6, 'Floor-2', 'worked', str((7, 8, 9))),
                (7, 'Floor-3', 'worked', str((7, 8, 9))),
                (8, 'Floor-3', 'worked', str((7, 8, 9))),
                (9, 'Floor-3', 'worked', str((7, 8, 9))));

FieldKey_Xnode = ('SensorID', 'Floor', 'Status', 'Location')
sensorDB.InsertData(TableName='Xnode_Sensor',
                    FieldKey=FieldKey_Xnode, Data=Xnode_Info)
# sensor general info --> FBG sensor
FBG_Info = ((1, 'Floor-1', 'worked', str((1, 2, 3))),
            (2, 'Floor-2', 'worked', str((4, 5, 6))),
            (3, 'Floor-3', 'worked', str((7, 8, 9))));

FieldKey_FBG = ('SensorID', 'Floor', 'Status', 'Location')
sensorDB.InsertData(TableName='FBG_Sensor',
                    FieldKey=FieldKey_FBG, Data=FBG_Info)

# ====================================== MySQL end ============================================



# ====================================== Influx start =========================================
class CreateSensorInflux(object):
    def __init__(self, _url="https://ap-southeast-2-1.aws.cloud2.influxdata.com",
                _token="-aTVy9tCmoP8tcZzQnT8oHp2ws_QtgmouEUmwIHgIG20-iAVPHsEC1cI5-2NvZXBKfdI4WndyZg9F39r2JnzdA==",
                _org="ntusyswell@gmail.com"):
        self.influxDB = InfluxDBClient(url=_url, token=_token, org=_org, verify_ssl=False)
        self.bucket = self.influxDB.buckets_api()
        self.write = self.influxDB.write_api();
        self.query = self.influxDB.query_api()

    def QueryData(self, _bucket: str, _starttime: str, _measurement: str, _fieldkey: str,
                    _stoptime='now()', data_index='_time', _org="ntusyswell@gmail.com"):
        '''
        Param: _bucket --> the name of the bucket
        Param: _starttime --> the time to be requested from
        Param: _stoptime --> the time to be requested to
        '''
        FLUX_query = 'from(bucket:{bucket}) \
                |> range(start: {starttime}, stop: {stoptime}) \
                |> filter(fn: (r) => r._measurement == {measurement}) \
                |> filter(fn: (r) => r._field == {fieldkey})'.format(bucket=_bucket, starttime=_starttime,
                                                                stoptime=_stoptime, measurement=_measurement,
                                                                fieldkey=_fieldkey)

        data = self.query.query_data_frame(
            query=FLUX_query, data_frame_index=[data_index], org=_org)
        return data

# ====================================== Influx end ===========================================


# =================================== Flask and dash ===========================================
# Create a APP object using FLASK
template_path = os.getcwd() + '\\templates';
_server = Flask(__name__, template_folder=template_path)

# ==================== Route for the homepage and navigation bar ===============================
# Set the homepage for the Testbed website


@_server.route("/")
def home():
    return render_template('Web_layout.html')


@_server.route("/Home")
def Home():
    return render_template('Web_layout.html')
# Set the link to the four buttons of navigator


@_server.route("/About")
def about():
    return render_template('about.html')


@_server.route("/Login")
def login():
    return render_template('login.html')

# ===============================================================================================


dashsystem_layout = '''
<!DOCTYPE html>     <!-- This is used to declare this is a HTML5 file-->

<html lang="en">
    <head>
        <!-- Define meta elements: contents for explorer engine, and some http-equiv attributes-->
        <meta charset="utf-8">                                      <!-- content-Type -->
        <meta name = "Testbed-NTU", content = "Database, monitoring, real-time, Xnode-sensor">
        <meta http-equiv="X-UA-Compatible" content="chrome=1" />    <!-- X-UA-Compatible render for chrome-->
        <meta http-equiv="x-ua-compatible" content="ie=edge">       <!-- X-UA-Compatible render for edge -->
        <link rel="stylesheet" type="text/css" href="../static/Web_application.css" />
        <title> Digital Construction - NTU | Welcome | Welcome </title>
        {%favicon%}
        {%css%}
    </head>

    <body>
        <div class="navigation-bar">
            <img src="../static/ntu-placeholder-d.png" style="width: 300px; height: auto;
            position: relative; top: 20px; right: 980px;">

            <h1 style="color: #f4f4f4; font-size: 46px; position: relative; left:340px; bottom: 0px;
                margin: 0px;padding: 0px;float: left;"> 
                    Digital Construction and Intelligent Infrastructure </h1>
            <h3 style="width:700px; position: relative; bottom: 73px; left:340px;color: #d71440; font-size: 27px;">
                <i>Making built environment sustainable & resilient</i></h3>
        
            <ul style="position: relative; bottom: 50px">
                <li style="position: absolute; bottom: 12px; left:900px;">
                    <a href= "/Home">Home</a>    </li>
                <li style="position: absolute; bottom: 12px; left:1000px;">
                    <a href= "/About">About</a>   </li>
                <li style="position: absolute; bottom: 12px; left:1110px;">
                    <a href= "/System">System</a> </li>
                <li style="position: absolute; bottom: 12px; left:1230px;">
                    <a href= "/Login">Login</a>   </li>
            </ul>
        </div>

        <div class = "system">
            <img src="/static/Testbed-Model.png" style = "width: 280px; height: 450px;
                    position: relative; right: 10px; top: 1px;">
            <div class="sensor-data">
                {%app_entry%}
            </div>
        </div>
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''


assets_path = os.getcwd() + "\\static"
appdash_system = dash.Dash(__name__, server=_server, url_base_pathname='/System/',
                            index_string=dashsystem_layout, assets_folder=assets_path)

clientInflux = CreateSensorInflux()

# Use two tabs to display: (1) real-time monitoring; (2) History monitoring
custom_tab = {
    'background-color': '#181C62',
    'borderBottom': '0px solid #30302f',
    'color': '#f4f4f4',
    'padding': '6px',
    'fontWeight': 'bold',
    'font-size': '30px'
}


custom_tab_selected = {
    'background-color': '#181C62',
    'borderBottom': '0px solid #30302f',
    'color': '#d71440',
    'padding': '6px',
    'fontWeight': 'bold',
    'font-size': '30px',
    'border-top': '5px solid #d71440'

}

custom_calendar = {
    'background-color': '#181C62',
    'fontWeight': 'bold',
    'font-size': '10px'
}

Floor_option = ['Floor-1', 'Floor-2', 'Floor-3']
Sensor_option = ['Xnode Sensor', 'FBG Sensor', 'Both types']
ID_option = {'Floor-1': {'Xnode Sensor': ['Xnode1', 'Xnode2', 'Xnode3'], 'FBG Sensor': ['FBG1']},
                'Floor-2': {'Xnode Sensor': ['Xnode4', 'Xnode5', 'Xnode6'], 'FBG Sensor': ['FBG2']},
                'Floor-3': {'Xnode Sensor': ['Xnode7', 'Xnode8', 'Xnode9'], 'FBG Sensor': ['FBG3']}};

appdash_system.layout = html.Div([
    dcc.Tabs(id='tabs-system-data', children=[
        dcc.Tab(label='Real time', value='tab-realtime',
                style=custom_tab, selected_style=custom_tab_selected,
                children=[
                    html.Div(id='floor', children=[
                            dcc.Dropdown(id='No-Floor', options=Floor_option)
                        ], style={'width': '200px', 'display': 'inline-block',
                                'position': 'relative', 'top': '10px', 'left': '20px'}),

                    html.Div(id='sensor', children=[
                            dcc.Dropdown(id='Sensor-Type', options=Sensor_option)
                        ], style={'width': '200px', 'display': 'inline-block',
                                'position': 'relative', 'top': '10px', 'left': '40px'}),

                    html.Div(id='id', children=[
                            dcc.Dropdown(id='Sensor-ID')
                        ], style={'width': '200px', 'display': 'inline-block',
                                'position': 'relative', 'top': '10px', 'left': '60px'}),

                        html.Div(html.Button(id='submit-button-realtime', n_clicks=0, children='Submit',
                                        className='push_button',
                                        style={'cursor': 'pointer', 'font-size': '20px', 'border-radius': '5px',
                                            'font-weight': 'bold', 'color': '#f5f5f5', 'background-color': '#30302f',
                                            'margin-left':'10px'}), style={'position':'absolute','left':'700px','bottom':'366px'}),

                        html.Div(html.Button(id='realtime-clear', n_clicks=0, children='Clear',
                                        className='push_button',
                                        style={'cursor': 'pointer', 'font-size': '20px', 'border-radius': '5px',
                                            'font-weight': 'bold', 'color': '#f5f5f5', 'background-color': '#30302f'}),
                                            style={'position':'absolute','left':'830px','bottom':'366px'}),

                    html.Div(id='static-info'),
                    html.Div(id = 'realtime-div', children = dcc.Graph(id='realtime-graph')),
                    dcc.Interval(
                            id='graph-update',
                            interval=1*1000,  # in milliseconds
                            n_intervals=0)
                    ]),

        # ===================================================================================== #
        dcc.Tab(label='History', value='tab-history',
                style=custom_tab, selected_style=custom_tab_selected,
                children=[
                        html.Div(style={'font-size': '25px', 'font-weight': 'bold',
                                        'position': 'relative', 'left': '20px', 'top': '5px'},
                            children=['Start from :  ',
                                        dcc.DatePickerSingle(id='start-time',
                                                    min_date_allowed=date(
                                                        1995, 8, 5),
                                                    max_date_allowed=datetime.date.today(),
                                                    date=date(2022, 7, 2)),
                                dcc.Input(id='hours-start', type='number',
                                            min=0, max=23, step=1,
                                            placeholder="Hr.",
                                            style={'width': '50px', 'height': '21px', 'font-size': '20px',
                                                    'color': '#f5f5f5', 'background-color': '#30302f',
                                                    'position': 'relative', 'bottom': '0px'}),
                                dcc.Input(id='minutes-start', type='number',
                                            min=0, max=59, step=1,
                                            placeholder="Min.",
                                            style={'width': '55px', 'height': '21px', 'font-size': '20px',
                                                    'color': '#f5f5f5', 'background-color': '#30302f',
                                                    'margin-right': '40px',
                                                    'position': 'relative', 'bottom': '0px'}),
                                'Stop at:  ',
                                dcc.DatePickerSingle(id='stop-time',
                                                    min_date_allowed=date(
                                                        1995, 8, 5),
                                                    max_date_allowed=datetime.date.today(),
                                                    date=date(2022, 7, 2)),
                                dcc.Input(id='hours-stop', type='number',
                                            min=0, max=23, step=1,
                                            placeholder="Hr.",
                                            style={'width': '50px', 'height': '21px', 'font-size': '20px',
                                                    'color': '#f5f5f5', 'background-color': '#30302f',
                                                    'position': 'relative', 'bottom': '0px'}),
                                dcc.Input(id='minutes-stop', type='number',
                                            min=0, max=59, step=1,
                                            placeholder="Min.",
                                            style={'width': '55px', 'height': '21px', 'font-size': '20px',
                                                    'color': '#f5f5f5', 'background-color': '#30302f',
                                                    'position': 'relative', 'margin-right': '20px'}),

                                html.Div(html.Button(id='submit-button-history', n_clicks=0, children='Submit',
                                        className='push_button',
                                        style={'cursor': 'pointer', 'font-size': '20px', 'border-radius': '5px',
                                            'font-weight': 'bold', 'color': '#f5f5f5', 'background-color': '#30302f',
                                            'margin-left':'10px'}), style={'position':'absolute','left': '800px', 'top': '5px'}),

                                html.Div(html.Button(id='history-clear', n_clicks=0, children='Clear',
                                        className='push_button',
                                        style={'cursor': 'pointer', 'font-size': '20px', 'border-radius': '5px',
                                            'font-weight': 'bold', 'color': '#f5f5f5', 'background-color': '#30302f',
                                            'margin-left':'10px'}), style={'position':'absolute','left': '920px', 'top': '5px'}),
                        ]),

                    dcc.Graph(id='history-graph',
                                            style={'display':'none',
                                            'position': 'relative', 'top': '3px'}
                                        )
            ])
        ])
])


@appdash_system.callback(Output(component_id='Sensor-ID', component_property='options'),
                            Output(component_id='Sensor-ID',component_property='disabled'),
                            Output(component_id='Sensor-ID',component_property='style'),
                            Input(component_id='No-Floor',component_property='value'),
                            Input(component_id='Sensor-Type', component_property='value'))
def sensor_ID(floor, sensor_type):
    if floor is None or sensor_type is None:
        return [], True, {'cursor': 'no-drop'}
    elif sensor_type == 'Both types':
        which_floor = ID_option[floor]
        id_opt = which_floor['Xnode Sensor'] + which_floor['FBG Sensor']
        return id_opt, False, {}
    else:
        which_floor = ID_option[floor]
        id_opt = which_floor[sensor_type]
        return id_opt, False, {}


@appdash_system.callback(Output(component_id='static-info', component_property='children'),
                            State(component_id='No-Floor', component_property='value'),
                            State(component_id='Sensor-Type', component_property='value'),
                            State(component_id='Sensor-ID', component_property='value'),
                            Input(component_id='submit-button-realtime', component_property='n_clicks'),
                            Input(component_id='realtime-clear', component_property='n_clicks'))
def Sensor_Info(floor, sensor_type, sensor_id, submit_clicks, clear_click):
    import re
    button_clicked = ctx.triggered_id
    if button_clicked == 'submit-button-realtime':
        if sensor_type == 'Xnode Sensor' and not floor is None:
            _data = sensorDB.GetALLData(TableName="Xnode_Sensor")
            _data.insert(loc=0, column='Sensor Type', value='Xnode Sensor')
            s_id = re.findall("\d+", sensor_id); s_id = int(s_id[0])
            s_info = _data[_data['SensorID'] == s_id]
            return dash_table.DataTable(
                s_info.to_dict('records'),
                [{"name": i, "id": i} for i in s_info.columns],
                style_cell={'textAlign': 'center',
                            'font-family': 'Times New Roman',
                            'font-size': '18px'},
                style_table={'width': '900px',
                                'position': 'absolute',
                                'left': '50px',
                                'top': '30px'})
        elif sensor_type == 'FBG Sensor' and not floor is None:
            _data = sensorDB.GetALLData(TableName="FBG_Sensor")
            _data.insert(loc=0, column='Sensor Type', value= 'FBG Sensor')
            s_id = re.findall("\d+",sensor_id); s_id = int(s_id[0])
            s_info = _data[_data['SensorID'] == s_id]
            return dash_table.DataTable(
                s_info.to_dict('records'),
                [{"name": i, "id": i} for i in s_info.columns],
                style_cell={'textAlign': 'center',
                            'font-family': 'Times New Roman',
                            'font-size': '18px'},
                style_table={'width': '900px',
                                'position': 'absolute',
                                'left': '50px',
                                'top': '30px'})
        elif sensor_type == 'Both types':
            _sensor_type = {'X': 'Xnode Sensor', 'F':'FBG Sensor'};
            _type = sensor_id[0]; type = _sensor_type[_type]
            if type == 'Xnode Sensor' and not floor is None:
                _data = sensorDB.GetALLData(TableName="Xnode_Sensor")
                _data.insert(loc=0, column='Sensor Type', value= 'Xnode Sensor')
                s_id = re.findall("\d+",sensor_id); s_id = int(s_id[0])
                s_info = _data[_data['SensorID'] == s_id]
                return dash_table.DataTable(
                    s_info.to_dict('records'),
                    [{"name": i, "id": i} for i in s_info.columns],
                    style_cell={'textAlign': 'center',
                                'font-family': 'Times New Roman',
                                'font-size': '18px'},
                    style_table={'width': '900px',
                                'position': 'absolute',
                                'left': '50px',
                                'top': '30px'})   
            elif type == 'FBG Sensor' and not floor is None:
                _data = sensorDB.GetALLData(TableName="FBG_Sensor")
                _data.insert(loc=0, column='Sensor Type', value= 'FBG Sensor')
                s_id = re.findall("\d+",sensor_id); s_id = int(s_id[0])
                s_info = _data[_data['SensorID'] == s_id]
                return dash_table.DataTable(
                    s_info.to_dict('records'),
                    [{"name": i, "id": i} for i in s_info.columns],
                    style_cell={'textAlign': 'center',
                                'font-family': 'Times New Roman',
                                'font-size': '18px'},
                    style_table={'width': '900px',
                                'position': 'absolute',
                                'left': '50px',
                                'top': '30px'})
    elif button_clicked == 'realtime-clear':
        return []



@appdash_system.callback(Output(component_id='realtime-graph', component_property='figure'),
                            Output(component_id='realtime-div', component_property='style'),
                            State(component_id='No-Floor', component_property='value'),
                            State(component_id='Sensor-Type', component_property='value'),
                            State(component_id='Sensor-ID', component_property='value'),
                            Input(component_id='graph-update', component_property='n_intervals'),
                            Input(component_id='submit-button-realtime', component_property='n_clicks'),
                            Input(component_id='static-info', component_property='children'))
def realtime_graph(floor, sensor_type, sensor_id, n_intervals,n_click, static_info):
    if static_info:
        # ================= Fetch the data from the influxDB ==========================
        fig = plotly.graph_objs.Figure();
        data_frame = clientInflux.QueryData(_bucket= '"testbed"', _starttime = '-60s', _measurement='"my_measurement1"',
                                            _fieldkey = '"temperature1"')
        data_temp = data_frame['_value']
        data_timeUTC = data_frame.index;
        LOCAL_TIMEZONE = datetime.datetime.now(
            datetime.timezone.utc).astimezone().tzinfo
        localtime = data_timeUTC.tz_convert(LOCAL_TIMEZONE)

        # add trace (the sensor data) to the figure
        fig.add_trace(plotly.graph_objs.Scatter(
            x=list(localtime),
            y=list(data_temp),
            name='Scatter',
            mode='lines+markers'))
        fig.update_layout(margin=dict(l=10,r=10,b=10,t=10,pad=4),
                            width=900, height = 250)
        return fig, {'display':'block','position': 'absolute', 'top': '200px','left':'30px'}
    else:
        return [], {'display':'none','position': 'absolute', 'top': '200px','left':'70px'}


@appdash_system.callback(Output(component_id='history-graph', component_property='figure'),
                            Output(component_id='history-graph', component_property='style'),
                            State(component_id='start-time', component_property='date'),
                            State(component_id='hours-start', component_property='value'),
                            State(component_id='minutes-start', component_property='value'),
                            State(component_id='hours-stop', component_property='value'),
                            State(component_id='minutes-stop', component_property='value'),
                            State(component_id='stop-time', component_property='date'),
                            Input('submit-button-history', 'n_clicks'),
                            Input('history-clear', 'n_clicks'),
                            prevent_initial_call=True)
def history_graph(StartDate, StartHrs, StartMin, StopHrs, StopMin, StopDate, submit_clicks, clear_clicks):
    button_clicked = ctx.triggered_id
    if button_clicked == 'history-clear':
        return [],{'display':'none'};
    elif button_clicked == 'submit-button-history':
        LOCAL_TIMEZONE = datetime.datetime.now(
            datetime.timezone.utc).astimezone().tzinfo;
        # influxdb cloud amazon timezone

        # The StartHrs + 4 is for the timezone difference in influxdb amazon cloud
        QueryStart = str(StartDate) + 'T{hour}:{minute}:00Z'.format(hour = str(StartHrs+4).zfill(2), minute = str(StartMin).zfill(2));
        QueryStart_date = datetime.datetime.strptime(QueryStart, '%Y-%m-%dT%H:%M:%SZ'); 
        QueryStart_UTC = QueryStart_date.astimezone(pytz.utc)
        QueryStart_UTC_str = QueryStart_UTC.strftime('%Y-%m-%dT%H:%M:%SZ')
        # The StopHrs + 4 is for the timezone difference in influxdb amazon cloud
        QueryStop =  str(StopDate) + 'T{hour}:{minute}:00Z'.format(hour = str(StopHrs+4).zfill(2), minute = str(StopMin).zfill(2));
        QueryStop_date = datetime.datetime.strptime(QueryStop, '%Y-%m-%dT%H:%M:%SZ'); 
        QueryStop_UTC = QueryStop_date.astimezone(pytz.utc)
        QueryStop_UTC_str = QueryStop_UTC.strftime('%Y-%m-%dT%H:%M:%SZ')

        data_frame = clientInflux.QueryData(_bucket= '"system"', 
                                            _starttime = QueryStart_UTC_str, 
                                            _measurement='"measurement1"',
                                            _fieldkey = '"temperature90"', 
                                            _stoptime = QueryStop_UTC_str)
        data_temp = data_frame['_value']
        data_temp_str = data_temp.str.extract('(.\d+\,\s+)(.\d+\,\s+)(.\d+\,\s+)(.\d+\,\s+)(.\d+\,\s+)(.\d+\s+)');
        data_temp_val = data_temp_str[2].str.extract('(.\d+)')
        data_temp_val = data_temp_val[0];
        data_timeUTC = data_frame.index;
        # Time zone of UTC+4: Asia/Baku
        localtime = data_timeUTC.tz_convert(pytz.timezone('Asia/Baku'))

        fig = plotly.graph_objs.Figure();
        fig.add_trace(plotly.graph_objs.Scatter(
            x=list(localtime),
            y=list(data_temp_val),
            name='Scatter',
            mode='lines+markers'))

        fig.update_layout(margin=dict(l=10,r=10,b=10,t=10,pad=4),
                            width=1040, height = 330)
        return fig, {'display':"block","position":"relative","top":"20px","left":"10px"};


# ============================================================================================

@_server.route('/System/')
def system():
    return appdash_system

# ===================================================================================


if __name__ == '__main__':
    _server.run(debug=True)
