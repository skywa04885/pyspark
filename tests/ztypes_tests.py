from datetime import datetime, timedelta, timezone
import unittest
from src.ztypes import HBool, HDateTime, HNum, HReader, HUri, HZincReader, HSymbol, HRef


class HZincReaderTestUnit(unittest.TestCase):
    r: HZincReader = HZincReader()

    def test_uri_read(self) -> None:
        self.assertEqual(
            self.r.read_uri("`https://google.com/`"), HUri("https://google.com/")
        )
        self.assertEqual(
            self.r.read_uri("`https://\\`google.com/`"), HUri("https://`google.com/")
        )

    def test_bool_read(self) -> None:
        self.assertEqual(self.r.read_bool("T"), HBool.TRUE)
        self.assertEqual(self.r.read_bool("F"), HBool.FALSE)
        self.assertRaises(HReader.ReadException, lambda: self.r.read_bool(" "))
        self.assertRaises(HReader.ReadException, lambda: self.r.read_bool("T "))

    def test_num_read(self) -> None:
        self.assertEqual(self.r.read_num("NaN"), HNum.NaN)
        self.assertEqual(self.r.read_num("-INF"), HNum.NEG_INF)
        self.assertEqual(self.r.read_num("INF"), HNum.POS_INF)
        self.assertEqual(self.r.read_num("12"), HNum.make(12))
        self.assertEqual(self.r.read_num("-12"), HNum.make(-12))
        self.assertEqual(self.r.read_num("12.1"), HNum.make(12.1))
        self.assertEqual(self.r.read_num("12.12345"), HNum.make(12.12345))
        self.assertEqual(self.r.read_num("-12.12345"), HNum.make(-12.12345))
        self.assertEqual(self.r.read_num("-12.123456789"), HNum.make(-12.123456789))
        self.assertEqual(
            self.r.read_num("-12.123456789eV"), HNum.make(-12.123456789, "eV")
        )
        self.assertEqual(
            self.r.read_num("-12.123456789eV"), HNum.make(-12.123456789, "eV")
        )
        self.assertEqual(self.r.read_num("10.2e3"), HNum.make(10200))
        self.assertEqual(self.r.read_num("-1e-2"), HNum.make(-0.01))
        self.assertEqual(self.r.read_num("1E-2"), HNum.make(0.01))
        self.assertEqual(self.r.read_num("1E-2kW"), HNum.make(0.01, "kW"))
        self.assertEqual(self.r.read_num("1E2EV"), HNum.make(100, "EV"))

    def test_symbol_read(self) -> None:
        self.assertEqual(self.r.read_symbol("^helloWorld"), HSymbol.make("helloWorld"))
        self.assertEqual(
            self.r.read_symbol("^helloWorld123"), HSymbol.make("helloWorld123")
        )

    def test_ref_read(self) -> None:
        self.assertEqual(self.r.read_ref("@helloWorld"), HRef.make("helloWorld"))
        self.assertEqual(self.r.read_ref("@helloWorld123"), HRef.make("helloWorld123"))

    def test_date_time_read(self) -> None:
        self.assertEqual(
            self.r.read_date_time("2010-03-11T23:55:00-05:00 New_York"),
            HDateTime.make(
                datetime(2010, 3, 11, 23, 55, 0, 0, timezone(timedelta(hours=-5)))
            ),
        )
