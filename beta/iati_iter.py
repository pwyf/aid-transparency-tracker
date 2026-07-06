import os
from os.path import join

from lxml import etree as _etree


class _Activity:
    """Minimal iatikit Activity stand-in without a back-reference to Dataset.

    iatikit's Activity stores self.dataset = dataset, which keeps the entire
    parsed XML tree alive until the next outer loop iteration reassigns it.
    Dropping that back-reference lets the tree be freed in the generator's
    finally block.
    """
    __slots__ = ('etree', 'id')

    def __init__(self, el):
        self.etree = el
        self.id = (el.findtext('iati-identifier') or '').strip()


class _Organisation:
    """Minimal iatikit Organisation stand-in, same rationale as _Activity."""
    __slots__ = ('etree', 'id')

    def __init__(self, el):
        self.etree = el
        self.id = (el.findtext('organisation-identifier') or '').strip()


class _Dataset:
    """Minimal iatikit Dataset stand-in backed by a direct lxml parse."""
    __slots__ = ('name', '_root')

    def __init__(self, name, root):
        self.name = name
        self._root = root

    @property
    def activities(self):
        return [_Activity(el) for el in self._root.findall('iati-activity')]

    @property
    def organisations(self):
        return [_Organisation(el) for el in self._root.findall('iati-organisation')]


def iter_datasets(publisher_dir, filetype=None):
    """Yield one _Dataset at a time, freeing each tree before parsing the next.

    Replaces iatikit publisher.datasets.where(filetype=...) for the
    activity-based infotests. Peak memory is proportional to the largest
    single XML file rather than the total corpus (critical for UNICEF's 1.7 GB).
    """
    tag_filter = {'activity': 'iati-activities',
                  'organisation': 'iati-organisations'}.get(filetype)
    if not os.path.isdir(publisher_dir):
        return
    for filename in sorted(os.listdir(publisher_dir)):
        if not filename.endswith('.xml'):
            continue
        name = filename[:-4]
        try:
            tree = _etree.parse(join(publisher_dir, filename))
            root = tree.getroot()
        except Exception:
            continue
        if tag_filter and root.tag != tag_filter:
            del tree, root
            continue
        try:
            ds = _Dataset(name, root)
            yield ds
        finally:
            ds._root = None  # drop the tree ref held by the outer 'dataset' var
            del tree, root
