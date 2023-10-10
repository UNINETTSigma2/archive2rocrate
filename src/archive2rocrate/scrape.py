"""
Parameters for dataset endpoint, used by ``get_dataset()`` and
``get_multiple_datasets()``:

doi=DOI, shortest form (eg. "10.11582/2016.00006")

Parameters for list endpoint, used by ``get_doi_blobs()``:

before=YYYY-MM-DD
after=YYYY-MM-DD
"""

from datetime import date, datetime, timedelta

import requests


def convert_dateobj_to_date(dateobj):
    if isinstance(dateobj, str):
        return date.fromisoformat(dateobj)
    if isinstance(dateobj, date):
        return dateobj
    if isinstance(dateobj, datetime):
        return dateobj.date()
    if isinstance(dateobj, timedelta):
        then = datetime.now() - dateobj
        return then.date()
    raise ValueError("Unknown format")


def get_doi_blobs(endpoint, after=None, before=None):
    params = {}
    if after:
        try:
            after = convert_dateobj_to_date(after)
            params["after"] = after.strftime("%Y-%m-%d")
        except ValueError:
            pass
    if before:
        try:
            before = convert_dateobj_to_date(before)
            params["before"] = before.strftime("%Y-%m-%d")
        except ValueError:
            pass
    r = requests.get(endpoint, params=params)
    return r.json()["DOIs"]


def get_dataset(doi, endpoint):
    r = requests.get(endpoint, params={'doi': doi})
    if not r.ok:
        code = r.status_code
        reason = r.reason
        url = r.url
        error = r._content
        if isinstance(error, bytes):
            error = str(error, encoding='ascii')
        raise ValueError(f"{code} {reason}: {error}, {url}")
    blob = r.json()
    if 'Dataset' not in blob:
        raise ValueError(f"Wrong format for dataset: {blob}")
    return blob["Dataset"]


def get_multiple_datasets(dois, endpoint):
    datasets = []
    errors = {}
    for doi in dois:
        try:
            dataset = get_dataset(doi, endpoint=endpoint)
        except ValueError as e:
            errors[doi] = e
        datasets.append(dataset)
    return datasets, errors
