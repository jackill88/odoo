from .pos_categories_importer import PosCategoriesImporter
from .extra_barcodes_importer import ExtraBarcodesImporter
from .goods_importer import GoodsImporter
from .product_pricelist_type_importer import ProductPricelistTypeImporter
from .pricelist_importer import PricelistImporter
from .goods_pos_categories_importer import ProductPosCategoryImporter
from .pos_config_importer import PosConfigImporter
from .pos_payment_method_importer import PosPaymentMethodImporter
from .account_journal_importer import AccountJournalImporter

from collections import defaultdict, deque


IMPORT_REGISTRY = {
    "pos_categories": {
        "importer": PosCategoriesImporter,
        "depends_on": [],
    },
    "product_pricelist": {
        "importer": ProductPricelistTypeImporter,
        "depends_on": [],        
    },
    "goods": {
        "importer": GoodsImporter,
        "depends_on": ["pos_categories"],
    },
    "prices": {
        "importer": PricelistImporter,
        "depends_on": ["goods", "product_pricelist"],
    },
    "barcodes": {
        "importer": ExtraBarcodesImporter,
        "depends_on": ["goods"],
    },
    "product_pos_categories": {
        "importer": ProductPosCategoryImporter,
        "depends_on": ["goods", "pos_categories"]
    },
    "account_journals": {
        "importer": AccountJournalImporter,
        "depends_on": []
    },
    "pos_payment_methods": {
        "importer": PosPaymentMethodImporter,
        "depends_on": ["account_journals"],        
    },
    "pos_config": {
        "importer": PosConfigImporter,
        "depends_on": ["pos_payment_methods"],
    },
}


# ====================================
# main code that resolves import order
# (in situations when we need 
# to import multiple files)
# ====================================

def resolve_import_order(files):
    """
    files: list of file_type strings
    returns ordered list
    """

    # build graph only for present files
    graph = defaultdict(list)
    indegree = defaultdict(int)

    # initialize nodes
    for f in files:
        indegree[f] = 0

    # build edges
    for f in files:
        deps = IMPORT_REGISTRY[f].get("depends_on", [])
        for dep in deps:
            if dep in files:  # only consider files in this zip
                graph[dep].append(f)
                indegree[f] += 1

    # queue = nodes with no dependencies
    queue = deque([f for f in files if indegree[f] == 0])

    ordered = []

    while queue:
        node = queue.popleft()
        ordered.append(node)

        for nxt in graph[node]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)

    if len(ordered) != len(files):
        missing = set(files) - set(ordered)
        raise ValueError(f"Cyclic or unresolved dependencies: {missing}")

    return ordered