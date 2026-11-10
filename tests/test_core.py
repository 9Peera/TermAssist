import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "addon", "globalPlugins", "termAssist"))
import library  # noqa: E402
import prompt  # noqa: E402
import tracker  # noqa: E402

DATA = os.path.join(os.path.dirname(__file__), "..", "addon", "globalPlugins", "termAssist", "data", "core.json")


def test_prompt():
	d = prompt.PromptDetector()
	cases = {
		"peera@srv01:~$ ls $HOME": ("peera@srv01:~$", "ls $HOME"),
		"root@srv:/etc#": ("root@srv:/etc#", ""),
		"[peera@cent7 ~]$ uptime": ("[peera@cent7 ~]$", "uptime"),
		"(venv) dev@box:~/app$ python x.py": ("(venv) dev@box:~/app$", "python x.py"),
		"root@3f2a1b:/app# ": ("root@3f2a1b:/app#", ""),
		"PS C:\\Users\\peera> ssh srv": ("PS C:\\Users\\peera>", "ssh srv"),
		"mysql> show databases;": ("mysql>", "show databases;"),
		"MariaDB [shop]> select 1;": ("MariaDB [shop]>", "select 1;"),
		"postgres=# \\l": ("postgres=#", "\\l"),
	}
	for line, exp in cases.items():
		assert d.split(line) == exp, (line, d.split(line))
	for line in ["drwxr-xr-x 2 root root 4096 Nov 9 file", "Reading package lists... Done", "</div>", "total 48"]:
		assert d.match(line) is None, line
	assert d.isIdlePrompt("peera@srv:~$")
	assert not d.isIdlePrompt("peera@srv:~$ ls")
	assert d.split("hello world") == (None, "hello world")


def test_password_error_session():
	assert prompt.isPasswordPrompt("[sudo] password for peera:")
	assert prompt.isPasswordPrompt("peera@10.0.0.5's password: ")
	assert prompt.isPasswordPrompt("Enter passphrase for key '/home/p/.ssh/id_ed25519':")
	assert prompt.isPasswordPrompt("รหัสผ่าน:")
	assert not prompt.isPasswordPrompt("passwd: password updated successfully")
	assert prompt.hasError(["E: Unable to locate package foo"])
	assert prompt.hasError(["bash: foo: command not found"])
	assert not prompt.hasError(["0 upgraded, 0 newly installed", "All good"])
	assert prompt.parseSession("peera@srv01:/var/www$") == ("peera", "srv01", "/var/www")
	assert prompt.parseSession("[peera@cent7 ~]$") == ("peera", "cent7", "~")


def test_tracker_scroll_and_append():
	t = tracker.OutputTracker()
	t.update(["a", "b", "$ ls"])  # initial screen
	assert t.all() == ["a", "b"]
	mark = t.total
	t.update(["a", "b", "$ ls", "f1", "f2", "$ "])  # output appended
	assert t.since(mark) == ["$ ls", "f1", "f2"]
	t.update(["f1", "f2", "$ ", "x", "$ "])  # scrolled
	assert t.all() == ["a", "b", "$ ls", "f1", "f2", "$ ", "x"]


def test_tracker_fullscreen_suppression():
	t = tracker.OutputTracker()
	t.update(["$ htop", "$ "])
	before = t.total
	t.update(["CPU 1%", "Mem 2G", "PID 1", "x"])  # first redraw accepted
	t.update(["CPU 3%", "Mem 2G", "PID 9", "x"])  # second redraw: suppressed
	t.update(["CPU 5%", "Mem 3G", "PID 4", "x"])
	assert t.inFullScreenMode
	assert t.total - before == 3


def test_library_search_and_store():
	with tempfile.TemporaryDirectory() as tmp:
		store = library.UserStore(os.path.join(tmp, "u.json"))
		lib = library.Library([DATA], store)
		assert len(lib.commands) > 150
		assert lib.search("ดิสก์")  # Thai
		assert lib.search("disk space")[0].template == "df -h"
		assert lib.search("restart", "services")[0].id == "s.restart"
		assert all(c.cat == "network" for c in lib.search("", "network"))
		c = lib.byId["f.cp"]
		assert c.paramNames() == ["source", "dest"]
		assert lib.paramLabel("dest", "th") == "ปลายทาง"
		assert library.fillTemplate(lib.byId["e.backup"].template, {"file": "a.conf"}).startswith("cp a.conf a.conf.bak.")
		assert lib.byId["w.dockerps"].paramNames() == []
		store.toggleFavorite("f.cp")
		store.addRecent("r.df")
		assert [x.id for x in lib.search("", library.FAVORITES)] == ["f.cp"]
		d = store.addCustom("Deploy", "cd /srv/app && git pull")
		lib.reloadCustom()
		assert lib.search("deploy")[0].id == d["id"]
		store.removeCustom(d["id"])
		lib.reloadCustom()
		assert not lib.search("deploy")
		store2 = library.UserStore(os.path.join(tmp, "u.json"))
		assert store2.data["favorites"] == ["f.cp"]


def test_heredoc():
	h = library.buildHeredoc("server {\n listen 80;\n}\n", "/etc/nginx/sites-available/my site", sudo=True)
	assert h.splitlines()[0] == "sudo tee '/etc/nginx/sites-available/my site' > /dev/null <<'TERMASSIST_EOF'"
	assert h.splitlines()[-1] == "TERMASSIST_EOF"
	assert library.buildHeredoc("x", "f.txt", append=True).startswith("cat >> f.txt <<")


def test_putty_margin():
	d = prompt.PromptDetector()
	assert d.split(" root@aadvaqtra:~# ls") == ("root@aadvaqtra:~#", "ls")
	assert d.isIdlePrompt(" root@aadvaqtra:~#")
	src = os.path.join(os.path.dirname(DATA), "..", "adapters.py")
	ns = {}
	code = open(src, encoding="utf-8").read()
	start = code.index("def dedentMargin")
	exec(code[start:code.index("class BaseAdapter")], ns)
	lines = [" root@srv:~# ls", "  indented", "", " a.txt"]
	assert ns["dedentMargin"](lines) == ["root@srv:~# ls", " indented", "", "a.txt"]
	mixed = ["root@srv:~#", " a"]
	assert ns["dedentMargin"](mixed) is mixed
	t = tracker.OutputTracker()
	screen = [" root@aadvaqtra:~# echo x", " __TA_9_B__", " default", " __TA_9_E__", " root@aadvaqtra:~#"]
	assert library.extractFetch(screen, "9") == ["default"]


if False:
	for name, fn in list(globals().items()):
		if name.startswith("test_"):
			fn()
			print("ok", name)


PACKS = os.path.join(os.path.dirname(DATA), "packs")
import profiles  # noqa: E402


def _lib(tmp):
	files = [DATA] + [os.path.join(PACKS, f) for f in sorted(os.listdir(PACKS))]
	return library.Library(files, library.UserStore(os.path.join(tmp, "u.json")))


def test_packs():
	with tempfile.TemporaryDirectory() as tmp:
		lib = _lib(tmp)
		assert len(lib.packs()) == 13
		assert len(lib.commands) >= 340
		assert "for c in " in lib.detectCommand() and "redis-server" in lib.detectCommand()
		ids = lib.packsForBinaries(["docker", "nginx", "unknown"])
		assert ids == ["pack.docker", "pack.nginx"]
		order = [c["id"] for c in lib.orderedCategories(ids)]
		assert order.index("pack.docker") < order.index("pack.apache") and order[-1] == "custom"
		assert lib.search("restart", "pack.nginx")[0].id == "nginx.restart"
		assert "pack.docker" in [c.cat for c in lib.search("docker log")[:3]]
		assert lib.paramSource("container").startswith("docker ps")
		assert lib.paramSource("site") and lib.paramSource("ip") is None
		assert lib.groupName("logs", "th") == "Log"
		assert lib.packOf(lib.byId["nginx.restart"])["install"] == "nginx"
		assert lib.packOf(lib.byId["r.df"]) is None
		lib.store.setDetected("srv01", ids)
		assert lib.store.detected("srv01") == ids
		# every placeholder in every command has a label
		for c in lib.commands:
			for p in c.paramNames():
				assert p in lib.paramLabels, (c.id, p)


def test_fetch_markers():
	cmd = library.buildFetch("ls /etc/nginx/sites-available", "77")
	assert "__TA_77_B__" not in cmd and "__TA_77_E__" not in cmd  # typed line never matches
	screen = ["peera@srv:~$ " + cmd, "__TA_77_B__", "default", "shop.conf ", "__TA_77_E__", "peera@srv:~$"]
	assert library.extractFetch(screen, "77") == ["default", "shop.conf"]
	assert library.extractFetch(screen[:3], "77") is None
	assert library.extractFetch(["__TA_77_B__", "__TA_77_E__"], "77") == []
	assert "__TA_77_S__" not in cmd and "PIPESTATUS" in cmd
	missing = ["x", "__TA_77_B__", "__TA_77_S__2", "ls: cannot access '/etc/nginx/sites-available': No such file or directory", "__TA_77_E__"]
	info = library.extractFetchInfo(missing, "77")
	assert info["items"] == [] and info["status"] == 2 and "No such file" in info["error"]
	assert library.emptyReason(info, th=True).startswith("ไม่มีโฟลเดอร์หรือไฟล์นี้บนเครื่อง: ls:")
	nf = library.extractFetchInfo(["__TA_1_B__", "__TA_1_S__127", "bash: docker: command not found", "__TA_1_E__"], "1")
	assert library.emptyReason(nf).startswith("The program is not installed")
	empty = library.extractFetchInfo(["__TA_1_B__", "__TA_1_S__0", "__TA_1_E__"], "1")
	assert library.emptyReason(empty) == "It exists but the list is empty"
	ok = library.extractFetchInfo(["__TA_1_B__", "a", "b", "__TA_1_S__0", "__TA_1_E__"], "1")
	assert ok["items"] == ["a", "b"] and ok["status"] == 0
	zsh = library.extractFetchInfo(["__TA_1_B__", "a", "__TA_1_S__", "__TA_1_E__"], "1")
	assert zsh["items"] == ["a"] and zsh["status"] is None


def test_profiles():
	nano = ["  GNU nano 7.2        /etc/hosts        Modified", "127.0.0.1 localhost", "", "",
		"[ Wrote 2 lines ]", "^G Help      ^O Write Out ^W Where Is", "^X Exit      ^R Read File ^\\ Replace"]
	assert profiles.detect(nano) == "nano"
	st = profiles.state("nano", nano)
	assert st == {"title": "/etc/hosts        Modified", "status": "[ Wrote 2 lines ]"}
	assert profiles.events("nano", {"status": ""}, st) == ["[ Wrote 2 lines ]"]
	vim = ["line one", "~", "~", "~", "-- INSERT --                         1,5           All"]
	assert profiles.detect(vim) == "vim"
	assert profiles.state("vim", vim)["mode"] == "INSERT"
	assert profiles.events("vim", {"mode": "NORMAL"}, {"mode": "INSERT"}) == ["INSERT"]
	less = ["NAME", "  ls - list", "x", "(END)"]
	assert profiles.detect(less) == "less"
	assert profiles.events("less", {"end": False}, profiles.state("less", less)) == ["END"]
	top = ["top - 10:00:01 up 3 days,  load average: 0.10, 0.05, 0.01", "Tasks: 100 total", "%Cpu(s): 1.0 us", "MiB Mem : 2000 total"]
	assert profiles.detect(top) == "top"
	htop = ["  0[||  2.0%]   Tasks: 40, 80 thr; 1 running", "  Mem[|||200M/2G]   Load average: 0.1 0.2 0.3", "  Swp[ 0K/1G]   Uptime: 3 days", "PID USER"]
	assert profiles.detect(htop) == "htop"
	assert len(profiles.state("htop", htop)["summary"]) == 3
	normal = ["peera@srv:~$ df -h", "Filesystem Size Used Avail Use% Mounted on", "/dev/sda1 20G 9G 11G 45% /", "peera@srv:~$"]
	assert profiles.detect(normal) is None


if __name__ == "__main__":
	for name, fn in list(globals().items()):
		if name.startswith("test_"):
			fn()
			print("ok", name)
