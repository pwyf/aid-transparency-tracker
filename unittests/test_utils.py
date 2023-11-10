from lxml import etree

from beta.utils import condition_applies


class MockDataset:
    def __init__(self, name):
        self.name = name


class MockItem:
    def __init__(self, dataset="testdataset", xml="<base/>"):
        self.dataset = MockDataset(dataset)
        self.etree = etree.fromstring(xml)


def test_assess_condition():
    assert condition_applies("", MockItem(), ["iati-activity"])

    assert not condition_applies("test|", MockItem(), ["iati-activity"])
    assert condition_applies(
        "test|", MockItem(xml="<base><test/></base>"), ["iati-activity"]
    )

    assert not condition_applies(
        "DATASET=dataset2|", MockItem(dataset="dataset1"), ["iati-activity"]
    )
    assert condition_applies(
        "DATASET=dataset2|", MockItem(dataset="dataset2"), ["iati-activity"]
    )

    assert not condition_applies(
        "DATASET!=dataset2|", MockItem(dataset="dataset2"), ["iati-activity"]
    )
    assert condition_applies(
        "DATASET!=dataset2|", MockItem(dataset="dataset1"), ["iati-activity"]
    )

    assert condition_applies("", MockItem(), ["iati-organisation"])
    assert condition_applies("test|", MockItem(), ["iati-organisation"])
    assert condition_applies(
        "test|orgtest", MockItem(xml="<base><orgtest/></base>"), ["iati-organisation"]
    )
    assert condition_applies(
        "test|orgtest", MockItem(xml="<base><orgtest/></base>"), ["iati-organisation"]
    )

    # Not sure if we can have both iati-activity and iati-organisation as tags
