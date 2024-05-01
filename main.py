import pandas as pd
import re
import os
import re
import logging
import traceback
from datetime import datetime, date
from typing import Optional


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


def file_date_interpreter(filename: str) -> list:
    dates = re.search(r'(?<=p)\d*\D\d*', filename)
    assert dates != None, f'File name {filename} hasn\'t date pattern'
    return dates.group().split('a')


def get_forecast_and_forcasted_date(file: str) -> tuple[date, date]:
    assert file.endswith('.dat'), f'File {file} is not type .dat'
    dates: str = file_date_interpreter(file)
    forecast_date = datetime.strptime(f'{dates[0]}', '%d%m%y').date()
    forecasted_date = datetime.strptime(f'{dates[1]}', '%d%m%y').date()
    return forecast_date, forecasted_date


def best_forecast_date(f: str, date_searched: date, forecast_date: date, forecasted_date: date,
                           best_match: Optional[tuple[date, date]], **kwargs) -> bool:
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


def search_date_in_file(path: str, date_searched: date) -> str:
    files = os.listdir(path)
    assert len(files) > 0, 'Directory is empty'
    best_match_dates, best_match_file = None, None
    for f in os.listdir(path):
        try:
            forecast_date, forecasted_date = get_forecast_and_forcasted_date(f)
            is_best_date = best_forecast_date(f, date_searched, forecast_date, forecasted_date, best_match_dates, weight_forecast=0.5, weight_forecasted=0.5)
            if is_best_date:
                best_match_dates = (forecast_date, forecasted_date)
                best_match_file = f

        except Exception as e:
            logging.warning(f'Error when processing file {f} - Erro {e}')
            logging.warning(traceback.format_exc())

    assert best_match_file is not None, f'''No files found for date: {date_searched.strftime('%Y-%m-%d')}'''
    return best_match_file


def apply_contour(contour_df: pd.DataFrame, data_df: pd.DataFrame) -> pd.DataFrame:
    pass


def main() -> None:
    contour_df: pd.DataFrame = read_contour_file('PSATCMG_CAMARGOS.bln')
    data_df: pd.DataFrame = read_data_file('forecast_files/ETA40_p011221a021221.dat')
    contour_df: pd.DataFrame = apply_contour(contour_df=contour_df, data_df=data_df)


if __name__ == '__main__':
    main()
