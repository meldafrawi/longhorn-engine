import data.cmd as cmd
from data.common import (  # NOQA
    read_dev, random_string, verify_data,
    snapshot_revert_with_frontend,
    restore_with_frontend,
)
from data.setting import VOLUME_HEAD


def snapshot_tree_build(dev, address, engine_name,
                        offset, length, strict=True):
    # snap["0a"] -> snap["0b"] -> snap["0c"]
    #                 |-> snap["1a"] -> snap["1b"] -> snap["1c"]
    #                 \-> snap["2a"] -> snap["2b"] -> snap["2c"]
    #                       \-> snap["3a"] -> snap["3b"] -> snap["3c"] -> head

    snap = {}
    data = {}

    snapshot_tree_create_node(dev, address, offset, length, snap, data, "0a")
    snapshot_tree_create_node(dev, address, offset, length, snap, data, "0b")
    snapshot_tree_create_node(dev, address, offset, length, snap, data, "0c")

    snapshot_revert_with_frontend(address, engine_name, snap["0b"])

    snapshot_tree_create_node(dev, address, offset, length, snap, data, "1a")
    snapshot_tree_create_node(dev, address, offset, length, snap, data, "1b")
    snapshot_tree_create_node(dev, address, offset, length, snap, data, "1c")

    snapshot_revert_with_frontend(address, engine_name, snap["0b"])

    snapshot_tree_create_node(dev, address, offset, length, snap, data, "2a")
    snapshot_tree_create_node(dev, address, offset, length, snap, data, "2b")
    snapshot_tree_create_node(dev, address, offset, length, snap, data, "2c")

    snapshot_revert_with_frontend(address, engine_name, snap["2a"])

    snapshot_tree_create_node(dev, address, offset, length, snap, data, "3a")
    snapshot_tree_create_node(dev, address, offset, length, snap, data, "3b")
    snapshot_tree_create_node(dev, address, offset, length, snap, data, "3c")

    snapshot_tree_verify(dev, address, engine_name,
                         offset, length, snap, data, strict)
    return snap, data


def snapshot_tree_create_node(dev, address, offset, length, snap, data, name):
    data[name] = random_string(length)
    verify_data(dev, offset, data[name])
    snap[name] = cmd.snapshot_create(address)


def snapshot_tree_verify(dev, address, engine_name,
                         offset, length, snap, data, strict=False):
    snapshot_tree_verify_relationship(address, snap, strict)
    snapshot_tree_verify_data(dev, address, engine_name,
                              offset, length, snap, data)


# snapshot_tree_verify_relationship won't check head or initial snapshot if
# "strict" is False
def snapshot_tree_verify_relationship(address, snap, strict):
    info = cmd.snapshot_info(address)

    assert snap["0a"].decode('utf-8') in info
    assert snap["0b"].decode('utf-8') in \
        info[snap["0a"].decode('utf-8')]["children"]

    assert snap["0b"].decode('utf-8') in info
    assert info[snap["0b"].decode('utf-8')]["parent"] == \
        snap["0a"].decode('utf-8')
    assert len(info[snap["0b"].decode('utf-8')]["children"]) == 3
    assert snap["0c"].decode('utf-8') in \
        info[snap["0b"].decode('utf-8')]["children"]
    assert snap["1a"].decode('utf-8') in \
        info[snap["0b"].decode('utf-8')]["children"]
    assert snap["2a"].decode('utf-8') in \
        info[snap["0b"].decode('utf-8')]["children"]

    assert snap["0c"].decode('utf-8') in info
    assert info[snap["0c"].decode('utf-8')]["parent"] == \
        snap["0b"].decode('utf-8')
    assert not info[snap["0c"].decode('utf-8')]["children"]

    assert snap["1a"] .decode('utf-8')in info
    assert info[snap["1a"].decode('utf-8')]["parent"] == \
        snap["0b"].decode('utf-8')
    assert snap["1b"].decode('utf-8') in \
        info[snap["1a"].decode('utf-8')]["children"]

    assert snap["1b"].decode('utf-8') in info
    assert info[snap["1b"].decode('utf-8')]["parent"] == \
        snap["1a"].decode('utf-8')
    assert snap["1c"].decode('utf-8') in \
        info[snap["1b"].decode('utf-8')]["children"]

    assert snap["1c"].decode('utf-8') in info
    assert info[snap["1c"].decode('utf-8')]["parent"] == \
        snap["1b"].decode('utf-8')
    assert not info[snap["1c"].decode('utf-8')]["children"]

    assert snap["2a"].decode('utf-8') in info
    assert info[snap["2a"].decode('utf-8')]["parent"] == \
        snap["0b"].decode('utf-8')
    assert len(info[snap["2a"].decode('utf-8')]["children"]) == 2
    assert snap["2b"].decode('utf-8') in \
        info[snap["2a"].decode('utf-8')]["children"]
    assert snap["3a"].decode('utf-8') in \
        info[snap["2a"].decode('utf-8')]["children"]

    assert snap["2b"].decode('utf-8') in info
    assert info[snap["2b"].decode('utf-8')]["parent"] == \
        snap["2a"].decode('utf-8')
    assert snap["2c"].decode('utf-8') in \
        info[snap["2b"].decode('utf-8')]["children"]

    assert snap["2c"].decode('utf-8') in info
    assert info[snap["2c"].decode('utf-8')]["parent"] == \
        snap["2b"].decode('utf-8')
    assert not info[snap["2c"].decode('utf-8')]["children"]

    assert snap["3a"].decode('utf-8') in info
    assert info[snap["3a"].decode('utf-8')]["parent"] == \
        snap["2a"].decode('utf-8')
    assert snap["3b"].decode('utf-8') in \
        info[snap["3a"].decode('utf-8')]["children"]

    assert snap["3b"].decode('utf-8') in info
    assert info[snap["3b"].decode('utf-8')]["parent"] == \
        snap["3a"].decode('utf-8')
    assert snap["3c"].decode('utf-8') in \
        info[snap["3b"].decode('utf-8')]["children"]

    assert snap["3c"].decode('utf-8') in info
    assert info[snap["3c"].decode('utf-8')]["parent"] == \
        snap["3b"].decode('utf-8')

    if strict:
        assert len(info) == 13
        assert info[snap["0a"].decode('utf-8')]["parent"] == ""
        assert VOLUME_HEAD in info[snap["3c"].decode('utf-8')]["children"]
        assert VOLUME_HEAD in info
        assert info[VOLUME_HEAD]["parent"] == snap["3c"].decode('utf-8')
        assert not info[VOLUME_HEAD]["children"]

        output = cmd.snapshot_ls(address)
        assert output.decode('utf-8') == '''ID
{}
{}
{}
{}
{}
{}
'''.format(snap["3c"].decode('utf-8'),
           snap["3b"].decode('utf-8'),
           snap["3a"].decode('utf-8'),
           snap["2a"].decode('utf-8'),
           snap["0b"].decode('utf-8'),
           snap["0a"].decode('utf-8'))


def snapshot_tree_verify_data(dev, address, engine_name,
                              offset, length, snap, data):
    snapshot_tree_verify_node(dev, address, engine_name,
                              offset, length, snap, data, "0a")
    snapshot_tree_verify_node(dev, address, engine_name,
                              offset, length, snap, data, "0b")
    snapshot_tree_verify_node(dev, address, engine_name,
                              offset, length, snap, data, "0c")
    snapshot_tree_verify_node(dev, address, engine_name,
                              offset, length, snap, data, "1a")
    snapshot_tree_verify_node(dev, address, engine_name,
                              offset, length, snap, data, "1b")
    snapshot_tree_verify_node(dev, address, engine_name,
                              offset, length, snap, data, "1c")
    snapshot_tree_verify_node(dev, address, engine_name,
                              offset, length, snap, data, "2a")
    snapshot_tree_verify_node(dev, address, engine_name,
                              offset, length, snap, data, "2b")
    snapshot_tree_verify_node(dev, address, engine_name,
                              offset, length, snap, data, "2c")
    snapshot_tree_verify_node(dev, address, engine_name,
                              offset, length, snap, data, "3a")
    snapshot_tree_verify_node(dev, address, engine_name,
                              offset, length, snap, data, "3b")
    snapshot_tree_verify_node(dev, address, engine_name,
                              offset, length, snap, data, "3c")


def snapshot_tree_verify_node(dev, address, engine_name,
                              offset, length, snap, data, name):
    snapshot_revert_with_frontend(address, engine_name, snap[name])
    readed = read_dev(dev, offset, length)
    assert readed == data[name]


def snapshot_tree_verify_backup_node(dev, address, engine_name,
                                     offset, length, backup, data, name):
    restore_with_frontend(address, engine_name, backup[name])
    readed = read_dev(dev, offset, length)
    assert readed == data[name]
