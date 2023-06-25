import os

BASE_DIR = os.path.dirname(__file__)


# check blocklist exists and then load it
def get_blocklist(additional="blocklist.txt.local"):
    blocklist_path = os.path.join(BASE_DIR, "blocklist.txt")
    with open(blocklist_path, "r") as f:
        blocklist = f.read().splitlines()

    # add additional blocklist
    # check that it exists
    additional_path = os.path.join(BASE_DIR, additional)
    if os.path.exists(additional_path):
        with open(additional_path, "r") as f:
            blocklist.extend(f.read().splitlines())
    return set(blocklist)


URL_SKIPLIST = get_blocklist()
