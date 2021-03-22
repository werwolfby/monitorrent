# -*- coding: utf-8 -*-
import six
import pytz
import pytest
from mock import patch
from datetime import datetime, timedelta, time
from monitorrent.plugins.trackers.kinozal import KinozalDateParser


@pytest.mark.parametrize('date_string,expected', [
    (u"9 января 1985 в 02:00", datetime(1985, 1, 9, 2, 00)),
    (u"12 февраля 2017 в 22:37", datetime(2017, 2, 12, 22, 37)),
    (u"2 марта 1992 в 14:59", datetime(1992, 3, 2, 14, 59)),
    (u"1 апреля 2017 в 1:37", datetime(2017, 4, 1, 1, 37)),
    (u"9 мая 2017 в 12:34", datetime(2017, 5, 9, 12, 34)),
    (u"29 июня 2017 в 00:00", datetime(2017, 6, 29, 0, 0)),
    (u"4 июля 2015 в 0:0", datetime(2015, 7, 4, 0, 0)),
    (u"17 августа 2017 в 1:23", datetime(2017, 8, 17, 1, 23)),
    (u"01 сентября 2017 в 14:48", datetime(2017, 9, 1, 14, 48)),
    (u"10 октября 2017 в 11:11", datetime(2017, 10, 10, 11, 11)),
    (u"5 ноября 2017 в 17:17", datetime(2017, 11, 5, 17, 17)),
    (u"24 декабря 1991 в 23:59", datetime(1991, 12, 24, 23, 59)),
])
def test__full_date_time__parse__success(date_string, expected):
    parser = KinozalDateParser()

    assert parser.parse(date_string) == KinozalDateParser.tz_moscow.localize(expected)


class MockDatetime(datetime):
    mock_now = None

    @classmethod
    def now(cls, tz=None):
        return cls.mock_now


@pytest.mark.parametrize('date_string,delta_days,expected_time', [
    (u"сейчас", 0, time(12, 0)),
    (u"вчера в 02:00", -1, time(2, 0)),
    (u"сегодня в 22:37", 0, time(22, 37)),
])
def test__relative_date_time__parse__success(date_string, delta_days, expected_time):
    parser = KinozalDateParser()

    server_now = datetime(2017, 1, 20, 12, 0, 0, tzinfo=pytz.utc)
    delta = timedelta(days=delta_days)
    MockDatetime.mock_now = server_now

    with patch('monitorrent.plugins.trackers.kinozal.datetime.datetime', MockDatetime):
        parsed_datetime = parser.parse(date_string)

        assert parsed_datetime.time() == expected_time

        assert parsed_datetime.date() == (datetime(2017, 1, 20) + delta).date()


@pytest.mark.parametrize('date_string,delta_days,expected_time', [
    (u"вчера в 02:00", -1, time(2, 0)),
    (u"сегодня в 22:37", 0, time(22, 37)),
])
def test__relative_date_time_with_different_day_on_server__parse__success(date_string, delta_days, expected_time):
    parser = KinozalDateParser()

    server_now = datetime(2017, 1, 20, 23, 59, 59, tzinfo=pytz.utc)
    delta = timedelta(days=delta_days)
    MockDatetime.mock_now = server_now

    with patch('monitorrent.plugins.trackers.kinozal.datetime.datetime', MockDatetime):
        parsed_datetime = parser.parse(date_string)

        assert parsed_datetime.time() == expected_time

        # in Europe/Moscow timezone already 21 of January, while in UTC is still 20 of January
        assert parsed_datetime.date() == (datetime(2017, 1, 21) + delta).date()


@pytest.mark.parametrize('date_string', [u"когда-то", u"не сегодня", u"не вчера", u"12 небритебря 27916 в 31:31"])
def test__parse_date_time__fail(date_string):
    parser = KinozalDateParser()

    exc_info = pytest.raises(Exception, parser.parse, date_string)

    assert date_string in six.text_type(exc_info.value)
