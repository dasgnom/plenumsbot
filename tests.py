import plenumsbot
import datetime


class TestPlenum:
    def test_next_plenum_20190101(self):
        plenum = plenumsbot.Plenum(
            3,
            "namespace",
            "template_plenum.j2",
            "template_blank_topics.j2",
            datetime.date(2019, 1, 1),
        )
        assert plenum.next_date == datetime.date(2019, 1, 3)

    def test_next_plenum_page_20190101(self):
        plenum = plenumsbot.Plenum(
            3,
            "namespace",
            "template_plenum.j2",
            "template_blank_topics.j2",
            datetime.date(2019, 12, 31),
        )
        assert plenum.next_page == "namespace:2020-01-02"

    def test_last_plenum_20190101(self):
        plenum = plenumsbot.Plenum(
            3,
            "namespace",
            "template_plenum.j2",
            "template_blank_topics.j2",
            datetime.date(2019, 1, 1),
        )
        assert plenum.last_date == datetime.date(2018, 12, 27)

    def test_last_plenum_page_20190101(self):
        plenum = plenumsbot.Plenum(
            3,
            "namespace",
            "template_plenum.j2",
            "template_blank_topics.j2",
            datetime.date(2019, 1, 1),
        )
        assert plenum.last_page == "namespace:2018-12-27"

    def test_next_plenum_20191231(self):
        plenum = plenumsbot.Plenum(
            3,
            "namespace",
            "template_plenum.j2",
            "template_blank_topics.j2",
            datetime.date(2019, 12, 31),
        )
        assert plenum.next_date == datetime.date(2020, 1, 2)

    def test_next_plenum_page_20191231(self):
        plenum = plenumsbot.Plenum(
            3,
            "namespace",
            "template_plenum.j2",
            "template_blank_topics.j2",
            datetime.date(2019, 12, 31),
        )
        assert plenum.next_page == "namespace:2020-01-02"

    def test_last_plenum_20191231(self):
        plenum = plenumsbot.Plenum(
            3,
            "namespace",
            "template_plenum.j2",
            "template_blank_topics.j2",
            datetime.date(2019, 12, 31),
        )
        assert plenum.last_date == datetime.date(2019, 12, 26)

    def test_last_plenum_page_20191231(self):
        plenum = plenumsbot.Plenum(
            3,
            "namespace",
            "template_plenum.j2",
            "template_blank_topics.j2",
            datetime.date(2019, 12, 31),
        )
        assert plenum.last_page == "namespace:2019-12-26"

    def test_last_plenum_took_place_true(self):
        plenum = plenumsbot.Plenum(
            3,
            "namespace",
            "template_plenum.j2",
            "template_blank_topics.j2",
            datetime.date(2019, 12, 31),
        )
        plenum_page = "foo\nbar\nEnde: 20:21 Uhr\n"
        assert plenum.last_plenum_took_place(plenum_page) == True

    def test_last_plenum_took_place_false(self):
        plenum = plenumsbot.Plenum(
            3,
            "namespace",
            "template_plenum.j2",
            "template_blank_topics.j2",
            datetime.date(2019, 12, 31),
        )
        plenum_page = "foo\nbar\nEnde: 20:xx Uhr\n"
        assert plenum.last_plenum_took_place(plenum_page) == False
