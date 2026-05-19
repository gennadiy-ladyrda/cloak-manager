from cloak_manager.renderer import render_template


def test_render_ckclient_template(inventory):
    rendered = render_template("ckclient.json.j2", vars(inventory))

    assert '"UID": "uid-123"' in rendered
    assert '"PublicKey": "pub-456"' in rendered
    assert '"RemoteHost": "1.2.3.4"' in rendered
    assert '"RemotePort": "443"' not in rendered
    assert '"RemotePort": 443' in rendered


def test_render_init_script_for_tcp(inventory):
    inventory.transport = "tcp"

    rendered = render_template("init.d.j2", vars(inventory))

    assert 'procd_open_instance "cloak-home"' in rendered
    assert '-l "$PORT"' in rendered
    assert "        -u \\\n" not in rendered


def test_render_init_script_for_udp(inventory):
    inventory.transport = "udp"

    rendered = render_template("init.d.j2", vars(inventory))

    assert "        -u \\\n" in rendered
