import re
from math import ceil

from bs4 import BeautifulSoup

from . import threadable, utils
from .requester import requester
from .users import User


class PeopleSearch:
    def __init__(self, all_fields="", names="", fandoms="", page=1, session=None):

        self.all_fields = all_fields
        self.names = names
        self.fandoms = fandoms
        self.page = page

        self.session = session

        self.results = None
        self.pages = 0
        self.total_results = 0

    @threadable.threadable
    def update(self):
        """Sends a request to the AO3 website with the defined search parameters, and updates all info.
        This function is threadable.
        """
        soup = search(
            self.all_fields, self.names, self.fandoms, self.page, self.session
        )

        results = soup.find("ol", {"class": ("pseud", "index", "group")})
        result_count = soup.find("p", string=re.compile(r"\d+ Found"))

        if results is None or result_count is None:
            self.results = []
            self.total_results = 0
            self.pages = 0
            return

        users = []
        for result in results.find_all("li", {"role": "article"}):
            link = result.find(href=re.compile(r"^/users/"))
            if link is None:
                continue
            username = link.attrs["href"].split("/")[2]
            users.append(User(username, session=self.session, load=False))

        self.results = users
        self.total_results = int(result_count.string.split()[0])
        self.pages = ceil(self.total_results / 20)


def search(
    all_fields="",
    names="",
    fandoms="",
    page=1,
    session=None,
):
    """Returns the results page for the people search as a Soup object
    Args:
        all_fields (str, optional): Generic search. Defaults to "".
        names (str, optional): Names of users. Defaults to "".
        fandoms (str, optional): Fandoms in which the users have works. Defaults to "".
        page (int, optional): Page number. Defaults to 1.
        session (AO3.Session, optional): Session object. Defaults to None.

    Returns:
        bs4.BeautifulSoup: Search result's soup
    """

    query = utils.Query()
    if page != 1:
        query.add_field(f"page={page}")
    if all_fields != "":
        query.add_field(f"people_search[query]={all_fields}")
    if names != "":
        query.add_field(f"people_search[name]={names}")
    if fandoms != "":
        query.add_field(f"people_search[fandom]={fandoms}")

    url = f"https://archiveofourown.org/people/search?{query.string}"

    if session is None:
        req = requester.request("get", url)
    else:
        req = session.get(url)
    if req.status_code == 429:
        raise utils.HTTPError(
            "We are being rate-limited. Try again in a while or reduce the number of requests"
        )
    soup = BeautifulSoup(req.content, features="lxml")
    return soup
