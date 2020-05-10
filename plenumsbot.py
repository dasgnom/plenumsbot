#!/usr/bin/env python

import os
import re
import sys
import json
import datetime
from jinja2 import Template
import dokuwiki
import collections
import argparse
from email.mime.text import MIMEText
import email.utils
import email.charset
import smtplib
from utils import join_url


Event = collections.namedtuple("Event", "date, description")
Section = collections.namedtuple("Section", "topic, contents")


class Wiki:
    def __init__(self, url, wikiuser, wikipass, nice_url="none"):
        """
        Constructor method for class Wiki
        
        Args:
            url (str): Base url of the DokuWiki installation
            wikiuser (str): Login username
            wikipass (str): Login password
            nice_url (str): dokuwiki nice url setting. Valid values: "none", "internal", "htaccess"
        
        Raises:
            err: exceptions that occurred while accessing the wiki
        """
        try:
            self.wiki = dokuwiki.DokuWiki(url, wikiuser, wikipass)
        except dokuwiki.DokuWikiError as err:
            raise err
        if nice_url == "none":
            self.baseurl = join_url([url, "doku.php?id="])
        elif nice_url == "internal":
            self.baseurl = join_url([url, "doku.php/"])
        elif nice_url == "htaccess":
            self.baseurl = join_url([url], trailing_slash=True)
        else:
            self.baseurl = join_url([url, "doku.php?id="])

    def get_page(self, page):
        """
        Returns the plaintext source of a given page.
        
        Args:
            page (str): DokuWiki page name
        
        Raises:
            err: exceptions that occurred while accessing the wiki
        
        Returns:
            str: the plaint text source of the given page
        """
        try:
            return self.wiki.pages.get(page)
        except dokuwiki.DokuWikiError as err:
            raise err

    def get_page_versions(self, page):
        """
        Returns a list of the last versions of a given page

        Args:
            page (str): DokuWiki page name
        
        Raises:
            err: exceptions that occurred while accessing the wiki
        
        Returns:
            list: a list containing information about all versions of a page
        """
        try:
            return self.wiki.pages.versions(page)
        except dokuwiki.DokuWikiError as err:
            raise err

    def get_page_info(self, page):
        """
        Returns meta information about a given page

        Args:
            page (str): DokuWiki page name
        
        Raises:
            err: exceptions that occurred while accessing the wiki
        
        Returns:
            dict: metainformation about the page (e.g, name, lastModified, author, version)
        """
        try:
            return self.wiki.pages.info(page)
        except dokuwiki.DokuWikiError as err:
            raise err

    def page_exists(self, page):
        """
        Returns True if a page exists, False is not
        
        Args:
            page (str): DokuWiki page name
        
        Returns:
            bool: True if the page exists, False if not
        """
        page_info = self.get_page_info(page)
        if "name" in page_info and page_info["name"] == page:
            return True

        return False

    def set_page(self, page, content, summary="modified by plenumsbot"):
        """
        Write given context to a given page.
        
        Args:
            page (str): pagename to be write to
            content (str): plaintext DokuWiki source to be written to the page
            summary (str, optional): Edit summary. Defaults to "modified by plenumsbot".
        
        Raises:
            err: errors that occurred while accessing the wiki
        
        Returns:
            bool: True if the page was written successfully
        """
        try:
            self.wiki.pages.set(page, content, sum=summary)
        except dokuwiki.DokuWikiError as err:
            raise err
        return True

    def set_redirect(self, redirect_src, redirect_dest):
        """
        creates a redirect from redirect_src to redirect_dest
        
        Args:
            redirect_src (str): name of the page to be redirected from
            redirect_dest (str): name of the page to be redirected to
        """
        redirect_content = f"~~GOTO>{redirect_dest}~~"
        self.set_page(
            redirect_src, redirect_content, f"redirect target set to {redirect_dest}"
        )


class Plenum:
    def __init__(
        self,
        day_of_week,
        namespace,
        tpl_plenum,
        tpl_blank,
        nice_url="none",
        today=datetime.date.today(),
    ):
        """
        Constructor method for class Plenum.
        
        Args:
            day_of_week (int): Number between 0-6; 0=Monday, 1=Tuesday, ..., 6=Sunday
            namespace (str): DokuWiki namespace in which the protocol pages are located
            tpl_plenum (str): file containing the protocol jinja2-template
            tpl_blank (str): file containing the topics skeleton used to create a fresh protocol draft
            today (datetime.date, optional): Date the script runs. Change only for debugging / testing purposes. Defaults to datetime.date.today().
        """
        self.day_of_week = day_of_week
        self.next_date = self._calc_next_date(today)
        self.last_date = self._calc_last_date(today)
        self.next_page = ":".join([namespace, self.next_date.strftime("%Y-%m-%d")])
        self.last_page = ":".join([namespace, self.last_date.strftime("%Y-%m-%d")])
        try:
            with open(tpl_plenum, "r") as fh:
                self.tpl_plenum = fh.read()
        except (FileNotFoundError, PermissionError) as e:
            print(f"unable to load plenum template: {e}")
        try:
            with open(tpl_blank, "r") as fh:
                self.tpl_blank = fh.read()
        except (FileNotFoundError, PermissionError) as e:
            print(f"unable to load plenum blank topics template: {e}")

    def _calc_next_date(self, today):
        """
        Returns the date of the coming plenum.
        
        Args:
            today (datetime object): date the script runs. Usually datetime.date.today()
        
        Returns:
            datetime.date: Next plenums date.
        """
        delta_days = self.day_of_week - today.weekday()
        if delta_days <= 0:
            delta_days += 7
        return today + datetime.timedelta(delta_days)

    def _calc_last_date(self, today):
        """
        Returns the date of the last plenum (in the past).
        
        Args:
            today (datetime.date): date the scripts runs. Usually datetime.date.today()
        
        Returns:
            datetime.date: Date the last plenum took place.
        """
        # today = datetime.date.today()
        delta_days = self.day_of_week - today.weekday()
        if delta_days > 0:
            delta_days -= 7
        return today + datetime.timedelta(delta_days)

    def last_plenum_took_place(self, plenum_page):
        """
        Checks if the last plenum took place. The check is performed by checking
        the end time in the given protocol text. 
        The string "Ende: hh:mm" must be present in the last two rows of the protocol
        to pass this check. hh and mm have to be replaced by a valid time designation.
                
        Args:
            plenum_page (str): Plaintext plenum protocol (DokuWiki source)
        
        Returns:
            bool: true it the plenum took place and false if it didn't take place.
        """

        page_lines = plenum_page.splitlines()
        match = re.search(
            r"^Ende:\s*\d{2}:\d{2}\s*Uhr\s*$",
            "\n".join(page_lines[-2:]),
            re.MULTILINE | re.IGNORECASE,
        )
        return bool(match)

    def upcoming_events(self, plenum_page):
        """
        Extracts the upcoming events from the given protocol text and removes events that
        will be in the past, when the next plenum takes place.
        
        Args:
            plenum_page (str): Plaintext plenum protocol (DokuWiki source)
        
        Returns:
            list of Event: list of Event, containing all events that take place after self.nextdate. 
            A placeholder entry is created if no upcoming event where found.
        """
        # find section termine
        plenum_page_list = plenum_page.splitlines()
        events_heading = re.findall(
            r"^(\s*={5}\s*Termine\s*={5}\s*)$",
            plenum_page,
            re.MULTILINE | re.IGNORECASE,
        )
        # return False if heading "Termine" not in page content
        if not events_heading:
            return False
        events_heading = events_heading[0].strip("\n")
        events_begin = plenum_page_list.index(events_heading) + 1
        eventlist = []
        for line in plenum_page_list[events_begin:]:
            # 1st capture group = date, 2nd = event description
            event = re.findall(r"^\s{2,4}\*\s(\d{4}-\d{2}-\d{2})(.*)$", line)
            if event and event[0][0] > self.next_date.strftime("%Y-%m-%d"):
                event_entry = Event(event[0][0], event[0][1])
                eventlist.append(event_entry)
        empty_events_template = ("yyyy-mm-dd", " Hier könnte dein Termin stehen.")
        if len(eventlist) == 0:
            eventlist.append(empty_events_template)
        return eventlist

    def extract_content(self, plenum_page):
        """
        Extracts the contents from a protocol. Called if a plenum didn't take place
        and the entries for the skipped plenum are supposed to be in the next 
        protocol draft, too.
        
        Args:
            plenum_page (str): Plaintext plenum protocol (DokuWiki source)
        
        Returns:
            list of Section: list of Section, containing all sections, except "Termine", from the
            given protocol page.
        """
        pagelist = plenum_page.splitlines()
        section_index = []
        for i in range(0, len(pagelist)):
            if re.match(r"^={5}[^=]*={5}$", pagelist[i].strip()):
                section_index.append(i)
        section_index.append(len(pagelist) - 1)
        sections = []
        for idx in section_index:
            if section_index.index(idx) != len(section_index) - 1:
                sections.append((idx, section_index[section_index.index(idx) + 1] - 1))
        section_list = []
        for section in sections:
            headline = pagelist[section[0]].strip("=").strip()
            content = "\n".join(pagelist[section[0] + 1 : section[1]])
            section_list.append(Section(headline, content))
        return section_list

    def generate_page_next_plenum(self, plenum_page):
        """
        Combines all parts needed to generate the protocol draft for the next plenum.
        
        Args:
            plenum_page (str): Plaintext plenum protcol (DokuWiki source)
        
        Returns:
            str: DokuWiki formatted plenum protocol draft
        """
        # checking if last plenum took place
        if self.last_plenum_took_place(plenum_page):
            # last plenum took place
            content = self.tpl_blank
        else:
            # last plenum didn't take place
            # extract topics from last plenum
            contentlist = self.extract_content(plenum_page)
            content = ""
            for block in contentlist:
                if block[0] == "Termine":
                    continue
                content += "\n".join(
                    [f"===== {block[0]} =====", block[1].strip("\n"), "\n"]
                )
            content = content.strip()
        # processing events
        events = ""
        eventlist = self.upcoming_events(plenum_page)
        if eventlist:
            for event in eventlist:
                events += f"  * {event[0]}{event[1]}\n"
        else:
            eventlist = ""
        # generate new page from template
        template = Template(self.tpl_plenum)
        return template.render(
            date_plenum=self.next_date, upcoming_events=events, content=content
        )

    def update_index_page(self, index_page, namespace):
        """
        Adds the page to the overview page
        
        Args:
            index_page (str): plaintext of the indexpage (DokuWiki source)
            namespace (str): namespace where the plenums protocols are saved to
        
        Returns:
            str: updated plaintext of the indexpage (DokuWiki source)
        """
        plenum_list = index_page.splitlines()
        # check if header with current year is present
        year_header = f"===== {self.next_date.year} ====="
        if year_header in plenum_list:
            insert_index = plenum_list.index(year_header) + 1
        else:
            insert_index = None
        # check is header 'Protokolle' is present
        protocol_header = "====== Protokolle ======"
        if "====== Protokolle ======" in plenum_list:
            protocol_index = plenum_list.index("====== Protokolle ======") + 1
        else:
            protocol_index = 0
        if not insert_index:
            insert_index = protocol_index + 2
            plenum_list.insert(protocol_index, f"===== {self.next_date.year} =====")
        plenum_list.insert(insert_index, f"  * [[{ self.next_page }]]")
        return "\n".join(plenum_list)

    def plenum_in_list(self, plenum_page):
        """ Returns True if self.next_page is found in plenum_page.
            Used to prevent double entries in the list of plenums """
        finding = plenum_page.find(self.next_page)
        if finding >= 0:
            return True
        else:
            return False


class Mail:
    def __init__(
        self, mailserver, username, password, port=587, ssl=False, starttls=True
    ):
        """
        Constructor method for class Mail.
        
        Args:
            mailserver (str): smtp/submission server to user
            username (str): username to authenticate at mailserver
            password (str): password to authenticate at mailserver
            port (int, optional): Port the mailserver is listening on. Defaults to 587.
            ssl (bool, optional): Use SSL encryption. Defaults to False.
            starttls (bool, optional): Use STARTTLS encryption. Defaults to True.
        """
        self.mail = smtplib.SMTP(host=mailserver, port=port)

        if starttls:
            self.mail.starttls()
        self.mail.login(username, password)

    def send(self, subject, recipient, sender, text):
        """
        Sends an email to the given recipient with given sender, topic and text.
        
        Args:
            subject (str): email subject
            recipient (str): email recipient
            sender (str): name / address of email sender according to RFC 5322
            text (str): Text message of the mail to be sent

        Raises:
            err: exceptions that occurred while sending the mail

        Returns:
            bool: True if the mail was sent successfully.
        """
        message = MIMEText(text, "text")
        message["From"] = sender
        message["To"] = recipient
        message["Subject"] = subject
        message["Date"] = email.utils.formatdate(localtime=1)
        message["Message-ID"] = email.utils.make_msgid()

        self.mail.sendmail(message["From"], message["To"], str(message))
        self.mail.quit()


def load_config(owndir):
    """load config from config.(local.)json"""
    config_file = os.path.join(owndir, "config.json")
    with open(config_file, "r") as fh:
        try:
            config = json.load(fh)
        except BaseException as e:
            raise e

    local_config_file = os.path.join(owndir, "config.local.json")
    if os.path.isfile(local_config_file):
        with open(local_config_file, "r") as fh:
            try:
                local_config = json.load(fh)
            except BaseException as e:
                raise e
    if local_config:
        return local_config
    else:
        return config


if __name__ == "__main__":
    # setup argparse
    parser = argparse.ArgumentParser(
        description="Plenumsbot - handling our plenums announcements and protocols"
    )
    parser.add_argument(
        "--announcement",
        action="store_true",
        help="Sends a reminder for the upcoming plenum.",
    )
    arguments = parser.parse_args()

    # load configuration
    owndir = os.path.dirname(os.path.realpath(__file__))
    config = load_config(owndir)
    # setup plenum and wiki objects
    plenum = Plenum(
        config["plenum_day_of_week"],
        config["namespace"],
        os.path.join(owndir, "template_plenum.j2"),
        os.path.join(owndir, "template_blank_topics.j2"),
    )
    try:
        wiki = Wiki(
            config["wiki_url"],
            config["wiki_user"],
            config["wiki_password"],
            config["wiki_nice_url"],
        )
    except dokuwiki.DokuWikiError as err:
        sys.exit(err)
    mail = Mail(config["mail_server"], config["mail_user"], config["mail_password"])
    if arguments.announcement:
        try:
            collection_of_topics = wiki.get_page(plenum.next_page)
            with open("template_mail_announcement.j2") as fh:
                template = fh.read()
            tpl = Template(template)

            plenum_date = plenum.next_date.strftime("%Y-%m-%d")
            announcement_message = str(
                tpl.render(
                    collection_of_topics=collection_of_topics,
                    plenum_date=plenum_date,
                    collection_link=f"{wiki.baseurl}{plenum.next_page}",
                )
            )
            mail.send(
                f"Plenumsankündigung {plenum_date}",
                config["mail_recipient"],
                config["mail_from"],
                announcement_message,
            )
        except Exception as err:
            sys.exit(err)
    else:
        try:
            last_page_content = wiki.get_page(plenum.last_page)
            index_page_content = wiki.get_page(config["indexpage"])
            new_page_content = plenum.generate_page_next_plenum(last_page_content)
            new_index_page_content = plenum.update_index_page(
                index_page_content, config["namespace"]
            )
            wiki.set_page(plenum.next_page, new_page_content)
            if not plenum.plenum_in_list(index_page_content):
                wiki.set_page(config["indexpage"], new_index_page_content)
            wiki.set_redirect(config["redirectpage"], plenum.next_page)
        except Exception as err:
            sys.exit(err)
