# coding=utf-8
import pytest
import six
import json
import requests_mock
from monitorrent.plugins.trackers import TrackerSettings
from monitorrent.plugins.trackers.lostfilm import LostFilmQuality, LostFilmTVTracker, LostFilmTVLoginFailedException
from monitorrent.plugins.trackers.lostfilm import SpecialSeasons, LostFilmEpisode, LostFilmSeason, LostFilmShow
from tests import use_vcr, ReadContentMixin
from tests.plugins.trackers.tests_lostfilm.lostfilmtracker_helper import LostFilmTrackerHelper

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# For real testing you can create LostFilmTrackerHelper over login method,
# and remove all corresponding cassettes.
# ex.: helper = LostFilmTrackerHelper.login("login", "password")
helper = LostFilmTrackerHelper()


class TestLosfFilmEpisode(object):
    @pytest.mark.parametrize("season,number,result", [
        (1, 1, False),
        ((1, 1), 1, False),
        (SpecialSeasons.Additional, 1, True),
        (SpecialSeasons.Additional, 2, True),
    ])
    def test_is_special_season_success(self, season, number, result):
        episode = LostFilmEpisode(season, number)
        assert episode.is_special_season() == result


class TestLosfFilmSeason(object):
    @pytest.mark.parametrize("number,should_raise", [
        (1, False),
        ((1, 1), False),
        (SpecialSeasons.Additional, False),
        ('1', True),
        (('1', '5'), True),
        ((1, '5'), True),
        (('1', 5), True),
        (1.5, True),
    ])
    def test_init(self, number, should_raise):
        if should_raise:
            with pytest.raises(Exception) as e:
                LostFilmSeason(number)
            message = six.text_type(e.value)

            assert 'int' in message
            assert 'tuple[int, int]' in six.text_type(e.value)
            assert 'SpecialSeason' in six.text_type(e.value)
        else:
            LostFilmSeason(number)

    @pytest.mark.parametrize("number,result", [
        (1, False),
        ((1, 1), False),
        (SpecialSeasons.Additional, True),
    ])
    def test_is_special_season_success(self, number, result):
        episode = LostFilmSeason(number)
        assert episode.is_special_season() == result

    def test_add_episode_success(self):
        episode1 = LostFilmEpisode(1, 1)
        episode2 = LostFilmEpisode(1, 2)

        season = LostFilmSeason(1)

        season.add_episode(episode1)
        season.add_episode(episode2)

        assert len(season) == 2

        assert season[1] == episode1
        assert season[2] == episode2

        assert list(season) == [episode1, episode2]
        assert list(reversed(season)) == [episode2, episode1]

    def test_add_episode_failed(self):
        episode1 = LostFilmEpisode(2, 1)

        season = LostFilmSeason(2)

        season.add_episode(episode1)
        with pytest.raises(Exception) as e:
            season.add_episode(episode1)
        message = six.text_type(e.value)
        assert six.text_type(episode1.number) in message
        assert six.text_type(season.number) in message
        assert 'already' in message

        assert len(season) == 1

        assert season[1] == episode1

        assert list(season) == [episode1]
        assert list(reversed(season)) == [episode1]


class TestLosfFilmShow(object):
    def test_add_season_success(self):
        season1 = LostFilmSeason(1)
        season2 = LostFilmSeason(2)

        show = LostFilmShow('Show', u'Шоу', 'Show', 2017)

        assert show.last_season is None
        assert show.seasons_url == 'https://www.lostfilm.tv/series/Show/seasons'

        show.add_season(season1)
        show.add_season(season2)

        assert len(show) == 2

        assert show[1] == season1
        assert show[2] == season2
        assert show.last_season == season2

        assert list(show) == [season1, season2]
        assert list(reversed(show)) == [season2, season1]

    def test_special_season_shouldnot_became_last_season(self):
        season1 = LostFilmSeason(SpecialSeasons.Additional)

        show = LostFilmShow('Show', u'Шоу', 'Show', 2017)

        assert show.last_season is None
        assert show.seasons_url == 'https://www.lostfilm.tv/series/Show/seasons'

        show.add_season(season1)

        assert show.last_season is None

        assert len(show) == 1

        assert show[SpecialSeasons.Additional] == season1

        assert list(show) == [season1]
        assert list(reversed(show)) == [season1]

    def test_add_episode_failed(self):
        season1 = LostFilmSeason(2)

        show = LostFilmShow('Show', u'Шоу', 'Show', 2017)

        assert show.seasons_url == 'https://www.lostfilm.tv/series/Show/seasons'

        show.add_season(season1)
        with pytest.raises(Exception) as e:
            show.add_season(season1)
        message = six.text_type(e.value)
        assert six.text_type(season1.number) in message
        assert 'already' in message

        assert len(show) == 1

        assert show[2] == season1
        assert show.last_season == season1

        assert list(show) == [season1]
        assert list(reversed(show)) == [season1]

    @pytest.mark.parametrize("url,expected_url", [
        ('http://www.lostfilm.tv/series/The_Expanse/', 'https://www.lostfilm.tv/series/The_Expanse/seasons'),
        ('https://www.lostfilm.tv/series/The_Expanse', 'https://www.lostfilm.tv/series/The_Expanse/seasons'),
        ('https://www.lostfilm.tv/series/The_Expanse/news', 'https://www.lostfilm.tv/series/The_Expanse/seasons'),
        ('http://www.lostfilm.tv/series/The_Expanse/cast', 'https://www.lostfilm.tv/series/The_Expanse/seasons'),
        ('http://www.lostfilm.tv/series/The_Expanse/asdasf', 'https://www.lostfilm.tv/series/The_Expanse/seasons'),
        ('http://www.lostfilm.tv/not/The_Expanse/seasons', None),
    ])
    def test_get_seasons_url(self, url, expected_url):
        assert LostFilmShow.get_seasons_url(url) == expected_url


class TestLostFilmQuality(object):
    @pytest.mark.parametrize("quality,result", [
        (None, LostFilmQuality.SD),
        ("sd", LostFilmQuality.SD),
        ("SD", LostFilmQuality.SD),
        ("mp4", LostFilmQuality.HD),
        ("HD", LostFilmQuality.HD),
        ("hd", LostFilmQuality.HD),
        ("720P", LostFilmQuality.HD),
        ("720p", LostFilmQuality.HD),
        ("720", LostFilmQuality.HD),
        ("1080", LostFilmQuality.FullHD),
        ("1080P", LostFilmQuality.FullHD),
        ("1080p", LostFilmQuality.FullHD),
        ("HZ", LostFilmQuality.Unknown),
    ])
    def test_parse_success(self, quality, result):
        assert LostFilmQuality.parse(quality) == result


class TestLostFilmTracker(ReadContentMixin):
    def setup(self):
        self.tracker_settings = TrackerSettings(10, None)
        self.tracker = LostFilmTVTracker()
        self.tracker.tracker_settings = self.tracker_settings

    @helper.use_vcr()
    def test_login(self):
        self.tracker.login(helper.real_email, helper.real_password, helper.real_headers, helper.real_cookies)
        assert self.tracker.session is not None

    @use_vcr()
    def test_fail_login(self):
        with pytest.raises(LostFilmTVLoginFailedException) as cm:
            self.tracker.login("admin@lostfilm.tv", "FAKE_PASSWORD")
        assert cm.value.code == 3

    @helper.use_vcr()
    def test_verify_success(self):
        tracker = LostFilmTVTracker(helper.real_session, helper.real_headers, helper.real_cookies)
        tracker.tracker_settings = self.tracker_settings
        assert tracker.verify()

    def test_verify_false(self):
        assert not self.tracker.verify()

    @use_vcr()
    def test_verify_fail(self):
        tracker = LostFilmTVTracker("1234567890abcdefghjklmnopqrstuvuywxyz")
        tracker.tracker_settings = self.tracker_settings
        assert not tracker.verify()

    @pytest.mark.parametrize('url, value', [
        ('http://www.lostfilm.tv/series/12_Monkeys/seasons', True),
        ('http://www.lostfilm.tv/series/12_Monkeys/bombolaya', True),
        ('http://www.lostfilm.tv/series/12_Monkeys', True),
        ('http://www.lostfilm.tv/my.php', False)
    ])
    def test_can_parse_url(self, url, value):
        assert self.tracker.can_parse_url(url) == value

    @use_vcr()
    def test_parse_correct_url_success(self):
        title = self.tracker.parse_url('http://www.lostfilm.tv/series/12_Monkeys')
        assert title.russian_name == u'12 обезьян'
        assert title.original_name == u'12 Monkeys'
        assert title.seasons_url == 'https://www.lostfilm.tv/series/12_Monkeys/seasons'

    @use_vcr()
    def test_parse_https_url_success(self):
        title = self.tracker.parse_url('https://www.lostfilm.tv/series/12_Monkeys')
        assert title.russian_name == u'12 обезьян'
        assert title.original_name == u'12 Monkeys'
        assert title.seasons_url == 'https://www.lostfilm.tv/series/12_Monkeys/seasons'

    @use_vcr()
    def test_parse_correct_url_issue_22_1(self):
        title = self.tracker.parse_url('http://www.lostfilm.tv/series/The_Vampire_Diaries')
        assert title.russian_name == u'Дневники вампира'
        assert title.original_name == u'The Vampire Diaries'

    @use_vcr()
    def test_parse_correct_url_issue_22_2(self):
        title = self.tracker.parse_url('http://www.lostfilm.tv/series/Grimm')
        assert title.russian_name == u'Гримм'
        assert title.original_name == u'Grimm'
        assert title.seasons_url == 'https://www.lostfilm.tv/series/Grimm/seasons'

    @use_vcr()
    def test_parse_incorrect_url_1(self):
        url = 'http://www.lostfilm.tv/not_a_series/SuperSeries'
        assert self.tracker.parse_url(url) is None

    @use_vcr()
    def test_parse_incorrect_url_2(self):
        url = 'http://www.lostfilm.tv/series/UnknowSeries'
        resp = self.tracker.parse_url(url)
        assert resp is not None
        assert resp.status_code == 200

    @use_vcr()
    def test_parse_series_success(self):
        url = 'http://www.lostfilm.tv/series/Grimm'
        show = self.tracker.parse_url(url, True)
        assert show.cat == 160
        assert show.url_name == 'Grimm'
        assert show.russian_name == u'Гримм'
        assert show.original_name == u'Grimm'
        assert len(show) == 6
        assert len(show[6]) == 13
        assert len(show[5]) == 22
        assert len(show[4]) == 22
        assert len(show[3]) == 22
        assert len(show[2]) == 22
        assert len(show[1]) == 22

    @use_vcr()
    def test_parse_series_success_2(self):
        url = 'http://www.lostfilm.tv/series/Sherlock/news'
        show = self.tracker.parse_url(url, True)
        assert show.cat == 130
        assert show.url_name == 'Sherlock'
        assert show.russian_name == u'Шерлок'
        assert show.original_name == u'Sherlock'
        assert len(show) == 5
        assert len(show[4]) == 3
        assert len(show[3]) == 3
        assert len(show[2]) == 3
        assert len(show[1]) == 3
        assert len(show[SpecialSeasons.Additional]) == 1

    @use_vcr()
    def test_parse_series_success_3(self):
        url = 'http://www.lostfilm.tv/series/Castle/video'
        show = self.tracker.parse_url(url, True)
        assert show.cat == 129
        assert show.russian_name == u'Касл'
        assert show.original_name == u'Castle'
        assert len(show) == 8
        assert len(show[8]) == 22
        assert len(show[7]) == 23
        assert len(show[6]) == 23
        assert len(show[5]) == 24
        assert len(show[4]) == 23
        assert len(show[3]) == 24
        assert len(show[2]) == 24
        assert len(show[1]) == 10

    @use_vcr()
    def test_parse_series_with_multiple_episodes_in_one_file(self):
        # on old lostfilm is 1 and 2 episode in one file for 3 season of Under the Dome show
        url = 'http://www.lostfilm.tv/series/Under_the_Dome/cast'
        show = self.tracker.parse_url(url, True)
        assert show.cat == 186
        assert show.russian_name == u'Под куполом'
        assert show.original_name == u'Under the Dome'
        assert len(show) == 3
        assert len(show[3]) == 13
        assert len(show[2]) == 13
        assert len(show[1]) == 13

    @use_vcr()
    def test_parse_series_with_intermediate_seasons(self):
        # http://old.lostfilm.tv/browse.php?cat=40
        # On old site Farscape has only complete seasons and additional season 4.5 with 1 and 2 episodes in one file
        # On new site it show all episodes, but when you tries to download particular episode,
        # it downloads the whole season
        url = 'http://www.lostfilm.tv/series/Farscape/seasons'
        show = self.tracker.parse_url(url, True)
        assert show.cat == 40
        assert len(show) == 4
        # assert len(parsed_url['special_episodes']) == 1
        # assert parsed_url['special_episodes'][0]['season_info']) == (4, 5, 2)

    @pytest.mark.parametrize("info,result", [
        (u"Unknown", SpecialSeasons.Unknown),
        (u"Дополнительные материалы", SpecialSeasons.Additional),
        (u"1 сезон", 1),
        (u"5 сезон", 5),
        (u"12 сезон", 12),
        (u"1 сезон 1 серия", (1, 1)),
        (u"12 сезон 6 серия", (12, 6)),
    ])
    def test_parse_season_info(self, info, result):
        assert self.tracker._parse_season_info(info) == result

    @helper.use_vcr()
    def test_download_info(self):
        url = 'http://www.lostfilm.tv/series/Grimm/seasons'
        tracker = LostFilmTVTracker(helper.real_session)
        tracker.tracker_settings = self.tracker_settings
        downloads = tracker.get_download_info(url, 160, 4, 22)

        assert len(downloads) == 3
        assert [LostFilmQuality.SD, LostFilmQuality.FullHD, LostFilmQuality.HD] == [d.quality for d in downloads]

    @helper.use_vcr()
    def test_download_info_2(self):
        url = 'http://www.lostfilm.tv/series/Eureka/seasons'
        tracker = LostFilmTVTracker(helper.real_session)
        tracker.tracker_settings = self.tracker_settings
        downloads_4_9 = tracker.get_download_info(url, 37, 4, 9)

        assert len(downloads_4_9) == 1
        assert downloads_4_9[0].quality == LostFilmQuality.SD

        downloads_4_10 = tracker.get_download_info(url, 37, 4, 10)

        assert len(downloads_4_10) == 2
        assert [d.quality for d in downloads_4_10] == [LostFilmQuality.SD, LostFilmQuality.HD]

    def test_download_info_3(self):
        url = 'http://www.lostfilm.tv/path/WrongShow/seasons'
        tracker = LostFilmTVTracker(helper.real_session)
        tracker.tracker_settings = self.tracker_settings
        assert tracker.get_download_info(url, 2, 4, 9) is None

    def test_httpretty_login_success(self):
        with requests_mock.Mocker() as mocker:
            session = u'e76e71e0f32e65c2470e42016dbb785e'

            mocker.post(u'https://www.lostfilm.tv/ajaxik.php',
                        text=json.dumps({"name": "fakelogin", "success": True, "result": "ok"}), status_code=200,
                        cookies={
                            u"lf_session": session
                        },
                        headers={'location': u'/'})

            self.tracker.login(u'fakelogin', u'p@$$w0rd')

            assert self.tracker.session == session

    def test_httpretty_unknown_login_failed(self):
        """
        :type mocker: requests_mock.Mocker
        """
        with requests_mock.Mocker() as mocker:
            session = u'e76e71e0f32e65c2470e42016dbb785e'

            mocker.post(u'https://www.lostfilm.tv/ajaxik.php',
                        text=json.dumps({"error": 4, "result": "ok"}), status_code=500,
                        cookies={
                            u"lf_session": session
                        },
                        headers={'location': u'/'})

            with pytest.raises(LostFilmTVLoginFailedException) as cm:
                self.tracker.login(u'fakelogin', u'p@$$w0rd')
            assert cm.value.code == 4
