import pandas as pd
import pandas as pd
import logging
from datetime import date
from src.challenge.main import apply_contour, best_forecast_date


class TestContour:
    def setup_method(self):
        self.contour_df = pd.DataFrame({
            'lat': [0, 1, 1, 0],
            'long': [0, 0, 1, 1]
        })

    def test_apply_contour(self):
        data_df = pd.DataFrame({
            'lat': [0.5, 0.5, 1.5],
            'long': [0.5, 1.5, 1.5],
            'data_value': [1, 2, 1]
        })

        result_df = apply_contour(self.contour_df, data_df)

        assert len(result_df) == 1
        logging.info(result_df.iloc[0]['data_value'])
        assert result_df['data_value'].sum() == 1

    def test_apply_contour_empty_data(self):
        data_df = pd.DataFrame(columns=['lat', 'long', 'data_value'])
        
        result_df = apply_contour(self.contour_df, data_df)
        
        assert result_df.empty

    def test_apply_contour_no_intersection(self):
        data_df = pd.DataFrame({
            'lat': [2, 2],
            'long': [2, 2],
            'data_value': [1, 1]
        })
        
        result_df = apply_contour(self.contour_df, data_df)
        
        assert result_df.empty


class TestBestForecastDate:
    def setup_method(self):
        self.date_searched = date(2021, 12, 15)
        self.forecast_date = date(2021, 12, 14)
        self.forecasted_date = date(2021, 12, 16)
        self.weight_forecast = 1
        self.weight_forecasted = 1

    def test_current_better_than_last_date(self):
        assert best_forecast_date(
            date_searched=self.date_searched,
            forecast_date=self.forecast_date,
            forecasted_date=self.forecasted_date,
            best_match=(date(2021, 12, 10), date(2021, 12, 18)),
            weight_forecast=self.weight_forecast,
            weight_forecasted=self.weight_forecasted
        )

    def test_last_better_than_current_date(self):
        assert not best_forecast_date(
            date_searched=self.date_searched,
            forecast_date=date(2021, 12, 10),
            forecasted_date=date(2021, 12, 18),
            best_match=(date(2021, 12, 14), date(2021, 12, 16)),
            weight_forecast=self.weight_forecast,
            weight_forecasted=self.weight_forecasted
        )

    def test_no_best_match(self):
        assert best_forecast_date(
            date_searched=self.date_searched,
            forecast_date=self.forecast_date,
            forecasted_date=self.forecasted_date,
            best_match=None,
            weight_forecast=self.weight_forecast,
            weight_forecasted=self.weight_forecasted
        )

    def test_last_dates_missing(self):
        assert best_forecast_date(
            date_searched=self.date_searched,
            forecast_date=self.forecast_date,
            forecasted_date=self.forecasted_date,
            best_match=None,
            weight_forecast=self.weight_forecast,
            weight_forecasted=self.weight_forecasted
        )
