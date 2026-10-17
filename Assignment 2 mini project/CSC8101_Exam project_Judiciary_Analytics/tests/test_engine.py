import unittest
import pandas as pd
from src.engine import (CourtRecord,CourtRepository,PerformanceAnalyzer,DataValidationError,
                        LinearForecaster,LastValueForecaster,ForecastService)
class TestEngine(unittest.TestCase):
    def setUp(self):
        self.record=CourtRecord('A','North',2025,100,80,90,20,30)
    def test_closing(self): self.assertEqual(self.record.closing,90)
    def test_clearance(self): self.assertEqual(self.record.clearance_rate,112.5)
    def test_disposal(self): self.assertEqual(self.record.disposal_rate,50)
    def test_backlog_share(self): self.assertAlmostEqual(self.record.backlog_share,33.3333333333)
    def test_negative(self):
        with self.assertRaises(DataValidationError): CourtRecord('A','N',2025,-1,3,2,0,0)
    def test_disposed_excess(self):
        with self.assertRaises(DataValidationError): CourtRecord('A','N',2025,1,2,4,0,0)
    def test_backlog_excess(self):
        with self.assertRaises(DataValidationError): CourtRecord('A','N',2025,1,2,2,0,2)
    def test_duplicate(self):
        with self.assertRaises(DataValidationError): CourtRepository([self.record,self.record])
    def test_missing(self):
        with self.assertRaises(DataValidationError): CourtRepository.from_frame(pd.DataFrame({'court':['A']}))
    def test_aggregate(self):
        repo=CourtRepository([self.record,CourtRecord('B','North',2025,100,20,10,10,20)])
        total=PerformanceAnalyzer(repo).aggregate().iloc[0]
        self.assertEqual(total.registered,100)
        self.assertEqual(total.disposed,100)
        self.assertEqual(total.clearance_rate,100)
    def test_zero_denominator(self):
        r=CourtRecord('A','N',2025,0,0,0,0,0)
        self.assertIsNone(r.clearance_rate)
    def test_linear(self):
        f=LinearForecaster().predict([2023,2024,2025],[10,20,30],2)
        self.assertEqual(f.forecast.tolist(),[40,50])
    def test_persistence(self):
        f=LastValueForecaster().predict([2024,2025],[10,30],2)
        self.assertEqual(f.forecast.tolist(),[30,30])
    def test_forecast_service(self):
        df=pd.DataFrame({'year':[2024,2025],'closing':[30,40]})
        self.assertEqual(ForecastService(LinearForecaster()).forecast(df,horizon=1).forecast.iloc[0],50)
    def test_invalid_horizon(self):
        with self.assertRaises(DataValidationError): LinearForecaster().predict([2024,2025],[1,2],0)
if __name__=='__main__': unittest.main()
