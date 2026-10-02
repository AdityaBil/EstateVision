import unittest

from estatevision.data import load_property_data
from estatevision.valuation import (
    current_value_range,
    nominal_future_value,
    todays_money_value,
)


class ValuationTests(unittest.TestCase):
    def test_nominal_projection(self):
        self.assertAlmostEqual(nominal_future_value(100_000, 2, 10), 121_000)

    def test_today_money_conversion(self):
        self.assertAlmostEqual(todays_money_value(121_000, 2, 10), 100_000)

    def test_value_range(self):
        self.assertEqual(current_value_range(1_000, 2_000, 100), (100_000, 200_000))

    def test_source_data_loads_and_cleans(self):
        frame = load_property_data("pythonproj.xlsx")
        self.assertEqual(len(frame), 36)
        self.assertIn("Mahalakshmi Nagar", set(frame["Areas"]))
        self.assertTrue((frame["PriceRangeLow"] > 0).all())


if __name__ == "__main__":
    unittest.main()

