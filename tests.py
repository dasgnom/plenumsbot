import plenumsbot
import datetime

namespace = "unterlagen:protokolle:plenum"
tpl_plenum = "template_plenum.j2"
tpl_blank = "template_blank_topics.j2"


class TestPlenum:
    def test_next_plenum_20190101(self):
        plenum = plenumsbot.Plenum(
            3, namespace, tpl_plenum, tpl_blank, datetime.date(2019, 1, 1)
        )
        assert plenum.next_date == datetime.date(2019, 1, 3)

    def test_next_plenum_page_20190101(self):
        plenum = plenumsbot.Plenum(
            3, namespace, tpl_plenum, tpl_blank, datetime.date(2019, 12, 31)
        )
        assert plenum.next_page == f"{namespace}:2020-01-02"

    def test_last_plenum_20190101(self):
        plenum = plenumsbot.Plenum(
            3, namespace, tpl_plenum, tpl_blank, datetime.date(2019, 1, 1)
        )
        assert plenum.last_date == datetime.date(2018, 12, 27)

    def test_last_plenum_page_20190101(self):
        plenum = plenumsbot.Plenum(
            3, namespace, tpl_plenum, tpl_blank, datetime.date(2019, 1, 1)
        )
        assert plenum.last_page == f"{namespace}:2018-12-27"

    def test_next_plenum_20191231(self):
        plenum = plenumsbot.Plenum(
            3, namespace, tpl_plenum, tpl_blank, datetime.date(2019, 12, 31)
        )
        assert plenum.next_date == datetime.date(2020, 1, 2)

    def test_next_plenum_page_20191231(self):
        plenum = plenumsbot.Plenum(
            3, namespace, tpl_plenum, tpl_blank, datetime.date(2019, 12, 31)
        )
        assert plenum.next_page == f"{namespace}:2020-01-02"

    def test_last_plenum_20191231(self):
        plenum = plenumsbot.Plenum(
            3, namespace, tpl_plenum, tpl_blank, datetime.date(2019, 12, 31)
        )
        assert plenum.last_date == datetime.date(2019, 12, 26)

    def test_last_plenum_page_20191231(self):
        plenum = plenumsbot.Plenum(
            3, namespace, tpl_plenum, tpl_blank, datetime.date(2019, 12, 31)
        )
        assert plenum.last_page == f"{namespace}:2019-12-26"

    def test_last_plenum_took_place_true(self):
        plenum = plenumsbot.Plenum(
            3, namespace, tpl_plenum, tpl_blank, datetime.date(2019, 12, 31)
        )
        plenum_page = "foo\nbar\nEnde: 20:21 Uhr\n"
        assert plenum.last_plenum_took_place(plenum_page) == True

    def test_last_plenum_took_place_false(self):
        plenum = plenumsbot.Plenum(
            3, namespace, tpl_plenum, tpl_blank, datetime.date(2019, 12, 31)
        )
        plenum_page = "foo\nbar\nEnde: 20:xx Uhr\n"
        assert plenum.last_plenum_took_place(plenum_page) == False

    def test_last_plenum_took_place_false_too_many_blank_lines(self):
        plenum = plenumsbot.Plenum(
            3, namespace, tpl_plenum, tpl_blank, datetime.date(2019, 12, 31)
        )
        plenum_page = "foo\nbar\nEnde: 20:21 Uhr\n\n\n"
        assert plenum.last_plenum_took_place(plenum_page) == False

    def test_last_plenum_took_place_false_not_begin_of_line(self):
        plenum = plenumsbot.Plenum(
            3, namespace, tpl_plenum, tpl_blank, datetime.date(2019, 12, 31)
        )
        plenum_page = "foo\nbar\n   Ende: 20:21 Uhr\n\n\n"
        assert plenum.last_plenum_took_place(plenum_page) == False

    def test_last_plenum_took_place_true_last_line(self):
        plenum = plenumsbot.Plenum(
            3, namespace, tpl_plenum, tpl_blank, datetime.date(2019, 12, 31)
        )
        plenum_page = "foo\nbar\nEnde: 20:21 Uhr"
        assert plenum.last_plenum_took_place(plenum_page) == True

    def test_upcoming_events(self):
        with open("testdata/unfinished_protocol", "r") as fh:
            unfinished_protocol = fh.read()
        plenum = plenumsbot.Plenum(
            3, namespace, tpl_plenum, tpl_blank, datetime.date(2019, 10, 3)
        )
        eventlist = [
            ("2019-10-11", " Termin am Tag nach dem Plenum"),
            ("2019-10-11", " 13:37 Uhr Termin mit Zeitangabe am Tag danach"),
            ("2020-01-01", " Termin im neuen Jahr"),
            ("2036-02-28", " Termin nach dem 32-Bit Unix-Timestamp-Overflow"),
        ]
        assert plenum.upcoming_events(unfinished_protocol) == eventlist

    def test_extract_content(self):
        with open("testdata/unfinished_protocol", "r") as fh:
            unfinished_protocol = fh.read()
        plenum = plenumsbot.Plenum(
            3, namespace, tpl_plenum, tpl_blank, datetime.date(2019, 10, 3)
        )
        section_list = [
            ("Rückschau", "  * Das ist ein Test der Rückschau\n  * Und noch einer!"),
            ("HQ, Lokales", "  * Auch im HQ sind Dinge geschehen"),
            ("Großes C", "  * Das große C lebt noch!"),
            ("Jemand neu hier?", "  * anyone?"),
            ("Extrathema", "  * Auch hier hat sich nichts getan, schade eigentlich!"),
            (
                "Termine",
                """  * -1231-01-01 Termin vor dem Jahr 0
  * 0000-01-01 Termin 01.01.0
  * 1969-12-30 Termin vor der UnixZeit
  * 2018-12-12 Termin in 2018
  * 2019-10-09 Termin der am Tag vor dem Plenum stattfand.
  * 2019-10-10 Termin der am Tag des Plenums stattfindet
  * Hier ist eine ungültige Zeile
  * 2019-10-11 Termin am Tag nach dem Plenum
  * 2019-10-11 13:37 Uhr Termin mit Zeitangabe am Tag danach
  * 2020-01-01 Termin im neuen Jahr
  * 2036-02-28 Termin nach dem 32-Bit Unix-Timestamp-Overflow""",
            ),
        ]

        assert plenum.extract_content(unfinished_protocol) == section_list

    def test_generate_page_next_plenum_unfinished(self):
        with open("testdata/unfinished_protocol", "r") as fh:
            unfinished_protocol = fh.read()
        with open("testdata/test_generate_page_next_plenum_unfinished_good", "r") as fh:
            goodexample = fh.read()
        plenum = plenumsbot.Plenum(
            3, namespace, tpl_plenum, tpl_blank, datetime.date(2019, 10, 3)
        )
        assert goodexample == plenum.generate_page_next_plenum(unfinished_protocol)

    def test_generate_page_next_plenum_finished(self):
        with open("testdata/finished_protocol", "r") as fh:
            finished_protocol = fh.read()
        with open("testdata/test_generate_page_next_plenum_finished_good", "r") as fh:
            goodexample = fh.read()
        plenum = plenumsbot.Plenum(
            3, namespace, tpl_plenum, tpl_blank, datetime.date(2019, 10, 3)
        )
        assert goodexample == plenum.generate_page_next_plenum(finished_protocol)
