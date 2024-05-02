from operator import ge
import pandas as pd
import re
import os
import re
import logging
import traceback
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from datetime import datetime, date
from typing import Counter, Optional


def read_data_file(file_path: str) -> pd.DataFrame:
    with open(file_path, 'r') as f:
        raw_file = f.readlines()

    list_dados = [line.split() for line in raw_file]
    float_raw_lines = [list(map(float, raw_line)) for raw_line in list_dados]
    return pd.DataFrame(float_raw_lines, columns=['lat', 'long', 'data_value'])


def read_contour_file(file_path: str) -> pd.DataFrame:
    line_split_comp = re.compile(r'\s*,')

    with open(file_path, 'r') as f:
        raw_file = f.readlines()

    l_raw_lines = [line_split_comp.split(raw_file_line.strip()) for raw_file_line in raw_file]
    l_raw_lines = list(filter(lambda item: bool(item[0]), l_raw_lines))
    float_raw_lines = [list(map(float, raw_line))[:2] for raw_line in l_raw_lines]
    header_line = float_raw_lines.pop(0)
    assert len(float_raw_lines) == int(header_line[0])
    return pd.DataFrame(float_raw_lines, columns=['lat', 'long'])


def file_date_interpreter(filename: str) -> list[str]:
    '''Extract dates from file name
    Args:
        filename (str): File name
    Returns:
        list[str]: List with dates
    '''
    dates = re.search(r'(?<=p)\d*\D\d*', filename)
    assert dates != None, f'File name {filename} hasn\'t date pattern'
    return dates.group().split('a')


def get_forecast_and_forcasted_date(file: str) -> tuple[date, date]:
    '''Get forecast and forecasted date from file name
    Args:
        file (str): File name
    Returns:
        tuple[date, date]: Forecast and forecasted date
    '''
    assert file.endswith('.dat'), f'File {file} is not type .dat'
    dates: list[str] = file_date_interpreter(filename=file)
    forecast_date = datetime.strptime(f'{dates[0]}', '%d%m%y').date()
    forecasted_date = datetime.strptime(f'{dates[1]}', '%d%m%y').date()
    return forecast_date, forecasted_date


def best_forecast_date(date_searched: date, forecast_date: date, forecasted_date: date,
                           best_match: Optional[tuple[date, date]], **kwargs) -> bool:
    '''Get the best forecast date based on the proximity of the date_searched
    Args:
        date_searched (date): Date to search
        forecast_date (date): Forecast date
        forecasted_date (date): Forecasted date
        best_match (Optional[tuple[date, date]]): Best match found
        **kwargs: weight_forecast and weight_forecasted
    Returns:
        bool: True if the current date is the best match
    '''
    if not best_match:
        return True

    last_forecast_date, last_forecasted_date = best_match
    last_dates_exist = last_forecast_date is not None and last_forecasted_date is not None

    current_forecast_proximity = abs(date_searched - forecast_date).days
    current_forecasted_proximity = abs(date_searched - forecasted_date).days

    if last_dates_exist:
        last_forecast_proximity = abs(date_searched - last_forecast_date).days
        last_forecasted_proximity = abs(date_searched - last_forecasted_date).days
    else:
        return True

    weight_forecast = kwargs['weight_forecast']
    weight_forecasted = kwargs['weight_forecasted']
    current_score = (current_forecast_proximity * weight_forecast) + (current_forecasted_proximity * weight_forecasted)
    last_score = (last_forecast_proximity * weight_forecast) + (last_forecasted_proximity * weight_forecasted)
    return current_score < last_score


def get_files_names(path: str) -> list[str]:
    '''Get files names from a directory
    Args:
        path (str): Directory path
    Returns:
        list[str]: List with files names
    '''
    files = os.listdir(path)
    assert len(files) > 0, 'Directory is empty'
    return files


def search_date_in_file(path: str, date_searched: date) -> str:
    '''Search for the best match file based on the date_searched
    Args:
        path (str): Directory path
        date_searched (date): Date to search
    Returns:
        str: Best match file name
    '''
    best_match_dates, best_match_file = None, None
    for f in get_files_names(path):
        try:
            forecast_date, forecasted_date = get_forecast_and_forcasted_date(f)

            #weight_forecast and weight_forecasted are used to calculate the best match if date_searched is not in the file
            is_best_date = best_forecast_date(date_searched=date_searched, forecast_date=forecast_date,forecasted_date=forecasted_date,
                                              best_match=best_match_dates, weight_forecast=0.5, weight_forecasted=0.5)
            if is_best_date:
                best_match_dates = (forecast_date, forecasted_date)
                best_match_file = f

        except Exception as e:
            logging.warning(f'Error when processing file {f} - Erro {e}')
            logging.warning(traceback.format_exc())

    assert best_match_file is not None, f'''No files found for date: {date_searched.strftime('%Y-%m-%d')}'''
    return best_match_file


def plot_chart(contour_df: pd.DataFrame, precipitation_area: pd.DataFrame, legend: str) -> None:
    '''Plot chart with contour and precipitation area
    Args:
        contour_df (pd.DataFrame): Contour data
        precipitation_area (pd.DataFrame): Precipitation area data
    '''
    plt.plot(contour_df['lat'].to_numpy(), contour_df['long'].to_numpy(), color='grey')
    scatter = plt.scatter(precipitation_area['lat'], precipitation_area['long'], s=precipitation_area['data_value'],
                          c=precipitation_area['data_value'], cmap='Blues', alpha=1, edgecolors='b', linewidth=1)
    plt.colorbar(scatter, label='Precipitação')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title(f'''Precipitação {legend}: {precipitation_area['data_value'].sum().round(2)}''')
    plt.grid(True)
    plt.savefig(f'accumulated_precipitation.jpg')
    plt.show()


def apply_contour(contour_df: pd.DataFrame, data_df: pd.DataFrame) -> pd.DataFrame:
    '''Apply contour to data
    Args:
        contour_df (pd.DataFrame): Contour data
        data_df (pd.DataFrame): Data to apply contour
    Returns:
        pd.DataFrame: Data with contour applied
    '''
    gdf1 = gpd.GeoDataFrame(contour_df, geometry=gpd.points_from_xy(contour_df.lat, contour_df.long))
    gdf2 = gpd.GeoDataFrame(data_df, geometry=gpd.points_from_xy(data_df.lat, data_df.long))
    polygon = Polygon(zip(gdf1.lat, gdf1.long))
    return pd.DataFrame(gdf2[gdf2.intersects(polygon)])[['lat', 'long', 'data_value']]


def get_accumulated_precipitation(contour_df: pd.DataFrame, path: str) -> pd.DataFrame:
    '''Get accumulated precipitation data from files in a directory
    Args:
        contour_df (pd.DataFrame): Contour data
        path (str): Directory path
    Returns:
        pd.DataFrame: Accumulated precipitation data
    '''
    accumulate_df = pd.DataFrame()
    for f in get_files_names(path):
        if f.endswith('.dat'):
            precipitation_area: pd.DataFrame = apply_contour(contour_df=contour_df, data_df=read_data_file(os.path.join(path, f)))
            accumulate_df = pd.concat([accumulate_df, precipitation_area])
    if not accumulate_df.empty:
        accumulate_df = accumulate_df.groupby(['lat', 'long']).mean().reset_index()
    else:
        logging.warning('Acumulated precipitation is empty for contour data')
    return accumulate_df


def main() -> None:

    dir_name = os.path.dirname(os.path.realpath(__file__))
    contour_df: pd.DataFrame = read_contour_file(os.path.join(dir_name, 'PSATCMG_CAMARGOS.bln'))
    stop = False
    forecast_files = os.path.join(dir_name, 'forecast_files')
    while not stop:
        user_option = input('1 - Precipitação acumulada\n2 - Precipitação por forecasted date\n3 - Sair\n')
        if user_option == '1':
            accumulate_precipitation = get_accumulated_precipitation(contour_df=contour_df, path=forecast_files)
            plot_chart(contour_df=contour_df, precipitation_area=accumulate_precipitation, legend='Acumulada')
        elif user_option == '2':
            date_str = input('Enter a date (DDMMYY): ')
            file_name = search_date_in_file(path=forecast_files, date_searched=datetime.strptime(date_str, '%d%m%y').date())
            data_df = read_data_file(os.path.join(forecast_files, file_name))
            precipitation_area = apply_contour(contour_df=contour_df, data_df=data_df)
            plot_chart(contour_df=contour_df, precipitation_area=precipitation_area, legend=f'''Acumulada {'a'.join(file_date_interpreter(file_name))}''')
        else:
            stop = True
        

if __name__ == '__main__':
    main()
