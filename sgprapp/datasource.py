import requests
from datetime import date, datetime
from typing import Optional, Dict, List
from bs4 import BeautifulSoup, Tag

from .model import ApplicationRecord, ApplicationStatus, ApplicationType
from .model import DEFAULT_URLS


def __parse_date(raw_date: str, format: str = "%Y-%m-%d") -> Optional[date]:
    try:
        return datetime.strptime(raw_date, format)
    except ValueError:
        return None


def __parse_date_time(raw_datetime: str) -> Optional[date]:
    return __parse_date(raw_datetime, "%Y-%m-%d %H:%M")


def __parse_status(raw_status: str) -> ApplicationStatus:
    chinese_status = {
        "通过": ApplicationStatus.Approved,
        "等待": ApplicationStatus.Pending,
        "杯具": ApplicationStatus.Rejected,
        "上诉中": ApplicationStatus.Appeal,
    }
    return chinese_status.get(raw_status, ApplicationStatus.Unknown)


def __parse_id(td_tag: Tag) -> Optional[int]:
    try:
        a_tag = td_tag.findChild("a")
        assert a_tag is not None
        edit_url = a_tag.get("data-href", "")
        assert edit_url.startswith("/edit?id=")
        return int(edit_url[9:])
    except Exception:
        return None


def __parse_entry(type: ApplicationType, entry: Tag) -> ApplicationRecord:
    columns = entry.findChildren("td")
    assert len(columns) == 7
    entry_id = __parse_id(columns[0])
    columns = list(map(lambda t: t.text, columns))
    return ApplicationRecord(
        type,
        entry_id,
        columns[1].strip(),
        columns[2].strip(),
        __parse_status(columns[3]),
        __parse_date(columns[4]),
        __parse_date(columns[5]),
        __parse_date_time(columns[6]),
    )


def crawl(
    urls: Dict[ApplicationType, str] = DEFAULT_URLS, limit_per_type: int = 10
) -> Dict[ApplicationType, List[ApplicationRecord]]:
    res = dict()
    for type, url in urls.items():
        req = requests.get(url)
        if req.status_code != 200:
            continue
        content = req.content.decode("utf8")
        soup = BeautifulSoup(content, features="html.parser")
        entries = soup.select("tbody > tr")
        res[type] = list()
        for i in range(min(limit_per_type, len(entries))):
            res[type].append(__parse_entry(type, entries[i]))
    return res


if __name__ == "__main__":
    # for debugging only
    crawl()
