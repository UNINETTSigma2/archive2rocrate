import base64
from uuid import uuid4
from dataclasses import dataclass


# helpers


def make_identifier(identifier):
    if isinstance(identifier, str):
        return identifier
    return '#' + str(uuid4())


def hash_identifier(identifier):
    return str(
        base64.b32encode(bytes(str(identifier), encoding='utf-8')),
        encoding="ascii",
    )


def extract_dois(doi_blobs):
    """
    Extract list of dois from list of doi blobs

    Format::

        [
            {"status": "PUBLISHED", "date_published": "2016-11-17", "doi": "10.11582/2016.00006"},
            {"status": "TERMINATED", "date_published": "2023-02-13", "doi": "10.11582/2023.00008"},
            ‥
        ]

    """
    return [blob['doi'] for blob in doi_blobs if blob['status'] == 'PUBLISHED']


# handle paging


@dataclass
class Page:
    next_page: int
    prev_page: int
    current_page: int
    total_pages: int
    total_documents: int


def process_paging(pageblob):
    next_page = pageblob.pop('Next_Page')
    if next_page == 'NULL':
        next_page = None
    prev_page = pageblob.pop('Previous_Page')
    if prev_page == 'NULL':
        prev_page = None
    page = Page(
        next_page,
        prev_page,
        current_page=pageblob.pop('Page'),
        total_pages=pageblob.pop('Total_Pages'),
        total_documents=pageblob.pop('Total_Documents'),
    )
    return page


def process_page(pageblob):
    datasets = pageblob.pop('Documents')
    page = process_paging(pageblob)
    del pageblob
    return datasets, page


# items


def process_person(person):
    if set(person.keys()) == set(['Person']):
        person = person['Person']
    first_name = person['First_Name']
    last_name = person['Last_Name']
    slug_basis = f"{first_name}-{last_name}".lower()
    identifier = hash_identifier(slug_basis)
    blob = {
        '@id': f'#{identifier}',
        '@type': 'Person',
        'name': f'{first_name} {last_name}',
        'firstName': first_name,
        'lastName': last_name,
    }
    return blob


def process_publication_using_dataset(publication):
    if publication['Status'] != 'PUBLISHED':
        return None, {}
    cite = publication['Reference']
    identifier = make_identifier(cite.get('DOI'))
    blob = {
        '@id': identifier,
        '@type': 'ScholarlyArticle',
        'identifier': identifier,
    }
    citation = cite.get('Citation')
    if citation:
        blob['text'] = citation
    url = cite.get('URL', None)
    if url:
        blob['url'] = url
    return identifier, blob


def process_id(identifier):
    return 'doi:' + identifier.strip()


def process_title(title):
    return ' '.join(title)


def process_description(description):
    return ' '.join(description)


def process_license(license):
    identifier = license['URI']
    blob = {
        '@id': identifier,
        '@type': 'CreativeWork',
        'identifier': identifier,
        'name': license['Name'],
    }
    return blob


def process_size(size):
    blob = {
        'unitText': 'bytes',
        'value': size,
    }
    return blob


# dataset


def process_dataset(dataset):
    root_dataset = {}
    items = []
    identifier = process_id(dataset['Identifier'])
    root_dataset['@id'] = identifier
    root_dataset['description'] = process_description(dataset['Description'])
    root_dataset['name'] = process_title(dataset['Title'])
    root_dataset['datePublished'] = dataset['Published']
    root_dataset['size'] = process_size(dataset['Extent'])

    copyright = process_person(dataset['Rights_Holder']['Person'])
    root_dataset['copyrightHolder'] = {'@id': copyright['@id']}
    items.append(copyright)

    license = process_license(dataset['License'])
    root_dataset['license'] = {'@id': license['@id']}
    items.append(license)

    for obj in dataset['Creator']:
        if 'Person' in obj:
            person = process_person(obj['Person'])
            items.append(person)
            person_dict = {'@id': person['@id']}
            root_dataset.setdefault('creator', []).append(person_dict)
    for obj in dataset['Contributor']:
        if 'Person' in obj:
            person = process_person(obj['Person'])
            items.append(person)
            person_dict = {'@id': person['@id']}
            root_dataset.setdefault('contributor', []).append(person_dict)
    for obj in dataset.get('Publication', []):
        identifier, reference = process_publication_using_dataset(obj)
        if identifier is None:
            continue
        items.append(reference)
        reference_dict = {'@id': identifier}
        root_dataset.setdefault('citation', []).append(reference_dict)
    return identifier, root_dataset, items


# combine for crate


def generate_skeleton(identifier='./', root_dataset=None):
    skeleton = {
       "@context": "https://w3id.org/ro/crate/1.1/context",
       "@graph": [
           {
               "@id": "ro-crate-metadata.json",
               "@type": "CreativeWork",
               "about": {
                   "@id": identifier,
               },
               "conformsTo": {
                   "@id": "https://w3id.org/ro/crate/1.1"
               }
           },
           {
               "@id": identifier,
               "@type": "Dataset"
           }
       ]
    }
    if root_dataset:
        skeleton['@graph'][1] = root_dataset
    return skeleton


def generate_jsonld(identifier, dataset, items):
    skeleton = generate_skeleton(identifier, dataset)
    item_set = set()
    for item in items:
        item_set.add(tuple(item.items()))
    for item in item_set:
        skeleton['@graph'].append(dict(item))
    return skeleton
