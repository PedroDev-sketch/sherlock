import csv
import json
from io import StringIO
from typing import Iterable

from apps.core.dtos import SiteResult


def to_csv(results: Iterable[SiteResult]) -> str:
    output = StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(["site_name", "url", "status"])
    for r in results:
        writer.writerow([r.site_name, r.url, r.status])
    return output.getvalue()


def to_json(results: Iterable[SiteResult], username: str) -> str:
    hits = [
        {"site_name": r.site_name, "url": r.url, "status": r.status}
        for r in results
    ]
    return json.dumps({"username": username, "hits": hits}, ensure_ascii=False)
