import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import os

# Функция для загрузки данных
def load_data():
    df = pd.read_csv('https://raw.githubusercontent.com/AnfisaAnalytics/app/3eaedc5fc2649d869db5c9c2e23621b7f858231b/sales_data.csv')
    df['Дата'] = pd.to_datetime(df['Дата'])
    df['Год'] = df['Дата'].dt.year
    df['Месяц'] = df['Дата'].dt.month
    df['Месяц_название'] = df['Дата'].dt.month_name()
    return df

# Инициализируем приложение
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# Определяем цветовую схему
colors = {
    'background': '#f8f9fa',
    'text': '#343a40',
    'primary': '#007bff',
    'secondary': '#6c757d',
    'success': '#28a745',
    'info': '#17a2b8',
    'warning': '#ffc107',
    'danger': '#dc3545',
}

# Создаем заголовок
header = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                dbc.Row(
                    [
                        dbc.Col(html.H1("Аналитика продаж", className="ms-2 text-white")),
                    ],
                    align="center",
                ),
                href="#",
                style={"textDecoration": "none"},
            ),
        ]
    ),
    color="primary",
    dark=True,
    className="mb-4",
)

# Создаем макет приложения
app.layout = html.Div( 
    [
        header,
        # Скрытый div для хранения данных
        html.Div(id='data-store', style={'display': 'none'}),
        # Интервал для автоматического обновления данных (каждые 5 минут = 300000 мс)
        dcc.Interval(
            id='interval-component',
            interval=300000,  # в миллисекундах
            n_intervals=0
        ),
        dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        html.H4("Фильтры", className="card-title"),
                                        html.Hr(),
                                        html.P("Выберите категорию:"),
                                        dcc.Dropdown(
                                            id='category-filter',
                                            multi=True
                                        ),
                                        html.P("Выберите регион:", className="mt-3"),
                                        dcc.Dropdown(
                                            id='region-filter',
                                            multi=True
                                        ),
                                        html.P("Выберите период:", className="mt-3"),
                                        dcc.DatePickerRange(
                                            id='date-filter',
                                            display_format='DD.MM.YYYY'
                                        ),
                                    ]
                                ),
                            ),
                            md=3,
                            className="mb-4",
                        ),
                        dbc.Col(
                            [
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Card(
                                                dbc.CardBody([
                                                    html.H5("Общая сумма продаж", className="card-title"),
                                                    html.H3(id="total-sales", className="card-text text-primary")
                                                ]),
                                                className="mb-4 text-center"
                                            ),
                                            md=4
                                        ),
                                        dbc.Col(
                                            dbc.Card(
                                                dbc.CardBody([
                                                    html.H5("Общее количество", className="card-title"),
                                                    html.H3(id="total-quantity", className="card-text text-success")
                                                ]),
                                                className="mb-4 text-center"
                                            ),
                                            md=4
                                        ),
                                        dbc.Col(
                                            dbc.Card(
                                                dbc.CardBody([
                                                    html.H5("Средняя цена", className="card-title"),
                                                    html.H3(id="avg-price", className="card-text text-info")
                                                ]),
                                                className="mb-4 text-center"
                                            ),
                                            md=4
                                        ),
                                    ]
                                ),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Card(
                                                dbc.CardBody([
                                                    html.H5("Динамика продаж по времени", className="card-title"),
                                                    dcc.Graph(id="time-series-chart")
                                                ]),
                                                className="mb-4"
                                            ),
                                            md=12
                                        ),
                                    ]
                                ),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Card(
                                                dbc.CardBody([
                                                    html.H5("Продажи по категориям", className="card-title"),
                                                    dcc.Graph(id="category-chart")
                                                ]),
                                                className="mb-4"
                                            ),
                                            md=6
                                        ),
                                        dbc.Col(
                                            dbc.Card(
                                                dbc.CardBody([
                                                    html.H5("Продажи по регионам", className="card-title"),
                                                    dcc.Graph(id="region-chart")
                                                ]),
                                                className="mb-4"
                                            ),
                                            md=6
                                        ),
                                    ]
                                ),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Card(
                                                dbc.CardBody([
                                                    html.H5("Тепловая карта продаж по месяцам и категориям", className="card-title"),
                                                    dcc.Graph(id="heatmap-chart")
                                                ]),
                                                className="mb-4"
                                            ),
                                            md=12
                                        ),
                                    ]
                                ),
                                # Добавляем информацию о последнем обновлении данных
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            html.Div(
                                                id="last-update-info",
                                                className="text-muted text-end"
                                            ),
                                            md=12
                                        ),
                                    ]
                                ),
                            ],
                            md=9
                        ),
                    ]
                )
            ],
            fluid=True,
            className="mt-4"
        )
    ],
    style={"backgroundColor": colors['background']}
)

# Колбэк для загрузки данных при запуске и по интервалу
@app.callback(
    [
        Output('data-store', 'children'),
        Output('category-filter', 'options'),
        Output('category-filter', 'value'),
        Output('region-filter', 'options'),
        Output('region-filter', 'value'),
        Output('date-filter', 'min_date_allowed'),
        Output('date-filter', 'max_date_allowed'),
        Output('date-filter', 'start_date'),
        Output('date-filter', 'end_date'),
        Output('last-update-info', 'children')
    ],
    [Input('interval-component', 'n_intervals')]
)
def update_data(n):
    # Загружаем данные
    df = load_data()
    
    # Формируем опции для фильтров
    category_options = [{'label': cat, 'value': cat} for cat in df['Категория'].unique()]
    category_values = df['Категория'].unique().tolist()
    
    region_options = [{'label': region, 'value': region} for region in df['Регион'].unique()]
    region_values = df['Регион'].unique().tolist()
    
    # Определяем диапазон дат
    min_date = df['Дата'].min()
    max_date = df['Дата'].max()
    
    # Текущее время для отображения времени последнего обновления
    current_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    update_info = f"Последнее обновление данных: {current_time}"
    
    # Возвращаем данные в формате JSON для хранения
    return (
        df.to_json(date_format='iso', orient='split'),
        category_options,
        category_values,
        region_options,
        region_values,
        min_date,
        max_date,
        min_date,
        max_date,
        update_info
    )

# Определяем колбэки для обновления графиков
@app.callback(
    [
        Output("total-sales", "children"),
        Output("total-quantity", "children"),
        Output("avg-price", "children"),
        Output("time-series-chart", "figure"),
        Output("category-chart", "figure"),
        Output("region-chart", "figure"),
        Output("heatmap-chart", "figure")
    ],
    [
        Input("data-store", "children"),
        Input("category-filter", "value"),
        Input("region-filter", "value"),
        Input("date-filter", "start_date"),
        Input("date-filter", "end_date")
    ]
)
def update_charts(json_data, categories, regions, start_date, end_date):
    # Преобразуем JSON обратно в DataFrame
    df = pd.read_json(json_data, orient='split')
    df['Дата'] = pd.to_datetime(df['Дата'])
    
    # Фильтруем данные
    filtered_df = df.copy()
    
    if categories:
        filtered_df = filtered_df[filtered_df['Категория'].isin(categories)]
    
    if regions:
        filtered_df = filtered_df[filtered_df['Регион'].isin(regions)]
    
    if start_date and end_date:
        filtered_df = filtered_df[(filtered_df['Дата'] >= start_date) & (filtered_df['Дата'] <= end_date)]
    
    # Рассчитываем метрики
    total_sales = f"{filtered_df['Продажи'].sum():,.0f} ₽".replace(",", " ")
    total_quantity = f"{filtered_df['Количество'].sum():,.0f}".replace(",", " ")
    avg_price = f"{filtered_df['Средняя цена'].mean():,.2f} ₽".replace(",", " ")
    
    # Создаем график временного ряда
    time_df = filtered_df.groupby(pd.Grouper(key='Дата', freq='M')).agg({
        'Продажи': 'sum',
        'Количество': 'sum'
    }).reset_index()
    
    time_fig = px.line(
        time_df, 
        x='Дата', 
        y='Продажи',
        title='Динамика продаж по месяцам',
        template='plotly_white'
    )
    time_fig.update_traces(line=dict(color=colors['primary'], width=3))
    time_fig.update_layout(
        xaxis_title='Дата',
        yaxis_title='Сумма продаж (₽)',
        plot_bgcolor='white',
        height=400
    )
    
    # Создаем график по категориям
    category_df = filtered_df.groupby('Категория').agg({
        'Продажи': 'sum'
    }).reset_index().sort_values('Продажи', ascending=False)
    
    category_fig = px.bar(
        category_df,
        x='Категория',
        y='Продажи',
        title='Продажи по категориям',
        template='plotly_white',
        color_discrete_sequence=[colors['success']]
    )
    category_fig.update_layout(
        xaxis_title='Категория',
        yaxis_title='Сумма продаж (₽)',
        plot_bgcolor='white',
        height=400
    )
    
    # Создаем график по регионам
    region_df = filtered_df.groupby('Регион').agg({
        'Продажи': 'sum'
    }).reset_index().sort_values('Продажи', ascending=False)
    
    region_fig = px.pie(
        region_df,
        values='Продажи',
        names='Регион',
        title='Доля продаж по регионам',
        template='plotly_white',
        hole=0.4
    )
    region_fig.update_layout(
        plot_bgcolor='white',
        height=400
    )
    
    # Создаем тепловую карту
    heatmap_df = filtered_df.groupby(['Месяц_название', 'Категория']).agg({
        'Продажи': 'sum'
    }).reset_index()
    
    # Преобразуем в формат для тепловой карты
    heatmap_pivot = heatmap_df.pivot(
        index='Месяц_название', 
        columns='Категория', 
        values='Продажи'
    )
    
    # Сортируем месяцы в правильном порядке
    month_order = ['January', 'February', 'March', 'April', 'May', 'June', 
                  'July', 'August', 'September', 'October', 'November', 'December']
    heatmap_pivot = heatmap_pivot.reindex(month_order)
    
    heatmap_fig = px.imshow(
        heatmap_pivot,
        title='Тепловая карта продаж по месяцам и категориям',
        template='plotly_white',
        color_continuous_scale='Viridis',
        aspect='auto'
    )
    heatmap_fig.update_layout(
        xaxis_title='Категория',
        yaxis_title='Месяц',
        plot_bgcolor='white',
        height=400
    )
    
    return total_sales, total_quantity, avg_price, time_fig, category_fig, region_fig, heatmap_fig

# Запускаем приложение
if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)
