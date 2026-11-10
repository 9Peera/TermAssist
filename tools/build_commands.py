# Generates addon/globalPlugins/termAssist/data/core.json (bilingual Ubuntu command library)
# Run: python tools/build_commands.py
import json
import os

CATS = [
	("system", "ข้อมูลระบบ", "System information"),
	("files", "ไฟล์และโฟลเดอร์", "Files and folders"),
	("view", "ดูเนื้อหาไฟล์", "View file contents"),
	("edit", "แก้ไขไฟล์", "Edit files"),
	("users", "ผู้ใช้และสิทธิ์", "Users and permissions"),
	("packages", "แพ็กเกจ (apt)", "Packages (apt)"),
	("services", "บริการ (systemd)", "Services (systemd)"),
	("processes", "ทรัพยากรและโปรเซส", "Resources and processes"),
	("network", "เครือข่าย", "Network"),
	("security", "ไฟร์วอลล์และความปลอดภัย", "Firewall and security"),
	("logs", "Log", "Logs"),
	("archive", "บีบอัด สำรอง และโอนไฟล์", "Archive, backup and transfer"),
	("disk", "ดิสก์", "Disks"),
	("schedule", "ตั้งเวลางาน", "Scheduled jobs"),
	("webdb", "เว็บ ฐานข้อมูล และคอนเทนเนอร์", "Web, database and containers"),
]

PARAMS = {
	"file": ("ไฟล์", "File", "", "ls -1Ap | grep -v '/$'"),
	"file1": ("ไฟล์ที่ 1", "First file", ""),
	"file2": ("ไฟล์ที่ 2", "Second file", ""),
	"path": ("โฟลเดอร์/ตำแหน่ง", "Folder/path", ".", "ls -1d */"),
	"source": ("ต้นทาง", "Source", ""),
	"dest": ("ปลายทาง", "Destination", ""),
	"target": ("เป้าหมาย", "Target", ""),
	"link": ("ชื่อลิงก์", "Link name", ""),
	"name": ("ชื่อ", "Name", ""),
	"text": ("ข้อความ", "Text", ""),
	"old": ("ข้อความเดิม", "Old text", ""),
	"new": ("ข้อความใหม่", "New text", ""),
	"start": ("บรรทัดเริ่ม", "Start line", "1"),
	"end": ("บรรทัดสุดท้าย", "End line", "50"),
	"user": ("ชื่อผู้ใช้", "User name", "", "awk -F: '$3>=1000 && $3<65000 {print $1}' /etc/passwd"),
	"group": ("กลุ่ม", "Group", "", "cut -d: -f1 /etc/group"),
	"mode": ("สิทธิ์ (เช่น 644, 755, u+x)", "Mode (e.g. 644, 755, u+x)", "644"),
	"package": ("ชื่อแพ็กเกจ", "Package name", ""),
	"keyword": ("คำค้น", "Keyword", ""),
	"service": ("ชื่อบริการ (เช่น nginx, ssh)", "Service name (e.g. nginx, ssh)", "", "systemctl list-units --type=service --all --no-legend --plain | awk '{print $1}' | sed 's/[.]service$//'"),
	"pid": ("หมายเลขโปรเซส (PID)", "Process ID (PID)", ""),
	"host": ("โฮสต์หรือ IP", "Host or IP", ""),
	"port": ("พอร์ต", "Port", ""),
	"url": ("URL", "URL", "https://"),
	"domain": ("โดเมน", "Domain", ""),
	"ip": ("IP", "IP address", ""),
	"number": ("หมายเลขกฎ", "Rule number", ""),
	"comment": ("หมายเหตุ (เช่นอีเมล)", "Comment (e.g. email)", ""),
	"since": ("ตั้งแต่เมื่อไร", "Since", "1 hour ago"),
	"device": ("อุปกรณ์ (เช่น /dev/sdb1)", "Device (e.g. /dev/sdb1)", "/dev/"),
	"schedule": ("เวลาแบบ cron (นาที ชั่วโมง วัน เดือน วันในสัปดาห์)", "Cron schedule (min hour day month weekday)", "0 2 * * *"),
	"command": ("คำสั่ง", "Command", ""),
	"database": ("ชื่อฐานข้อมูล", "Database name", "", "sudo mysql -N -e 'SHOW DATABASES'"),
	"container": ("ชื่อคอนเทนเนอร์", "Container name", "", "docker ps -a --format '{{.Names}}'"),
}

GROUPS = [
	("check", "ตรวจการติดตั้งและเวอร์ชัน", "Installed and version"),
	("status", "สถานะ", "Status"),
	("control", "เริ่ม หยุด รีสตาร์ท", "Start, stop, restart"),
	("logs", "Log", "Logs"),
	("test", "ทดสอบค่าตั้ง", "Test configuration"),
	("config", "ไฟล์ค่าตั้ง", "Configuration files"),
	("tasks", "งานที่ทำบ่อย", "Common tasks"),
	("fix", "แก้ปัญหา", "Troubleshooting"),
]

L, M, H = "low", "medium", "high"
# (cat, id, th, en, template, risk[, sr])
C = [
	# system
	("system", "sys.os", "ดูเวอร์ชัน Ubuntu", "Show Ubuntu version", "lsb_release -a", L),
	("system", "sys.host", "ดูข้อมูลเครื่องและชื่อโฮสต์", "Show host information", "hostnamectl", L),
	("system", "sys.kernel", "ดูเวอร์ชันเคอร์เนล", "Show kernel version", "uname -a", L),
	("system", "sys.uptime", "ดูเวลาที่เครื่องเปิดมาและโหลด", "Show uptime and load", "uptime", L),
	("system", "sys.whoami", "ดูชื่อผู้ใช้ปัจจุบัน", "Show current user", "whoami", L),
	("system", "sys.date", "ดูวันเวลาและเขตเวลา", "Show date, time and timezone", "timedatectl", L),
	("system", "sys.settz", "ตั้งเขตเวลาเป็นกรุงเทพ", "Set timezone to Bangkok", "sudo timedatectl set-timezone Asia/Bangkok", M),
	("system", "sys.cpu", "ดูข้อมูล CPU", "Show CPU information", "lscpu", L),
	("system", "sys.env", "ดูตัวแปรสภาพแวดล้อม", "Show environment variables", "printenv | sort", L),
	("system", "sys.history", "ดูประวัติคำสั่ง 30 รายการล่าสุด", "Show last 30 commands", "history 30", L),
	("system", "sys.lastboot", "ดูประวัติการรีบูต", "Show reboot history", "last reboot | head -n 10", L),
	("system", "sys.nopager", "ปิด pager ของ systemd และ git ในเซสชันนี้ (อ่านง่ายขึ้น)", "Disable systemd and git pagers for this session", "export SYSTEMD_PAGER= GIT_PAGER=cat", L),
	("system", "sys.nocolor", "ปิดสีในผลลัพธ์ (อ่านง่ายขึ้น)", "Disable colored output for this session", "export NO_COLOR=1; alias ls='ls --color=never'; alias grep='grep --color=never'", L),
	("system", "sys.reboot", "รีสตาร์ทเครื่อง", "Reboot server", "sudo reboot", H),
	("system", "sys.shutdown", "ปิดเครื่อง", "Shut down server", "sudo shutdown -h now", H),
	# files
	("files", "f.pwd", "ดูโฟลเดอร์ปัจจุบัน", "Show current folder", "pwd", L),
	("files", "f.ls", "แสดงไฟล์ทั้งหมดแบบละเอียด", "List all files with details", "ls -lah", L),
	("files", "f.ls1", "แสดงชื่อไฟล์บรรทัดละไฟล์ (อ่านง่าย)", "List one file per line", "ls -1", L),
	("files", "f.cd", "เข้าโฟลเดอร์", "Change folder", "cd {path}", L),
	("files", "f.cdhome", "กลับโฟลเดอร์บ้าน", "Go to home folder", "cd ~", L),
	("files", "f.cdup", "ขึ้นไปหนึ่งระดับ", "Go up one folder", "cd ..", L),
	("files", "f.mkdir", "สร้างโฟลเดอร์ (รวมโฟลเดอร์แม่)", "Create folder (with parents)", "mkdir -p {path}", M),
	("files", "f.touch", "สร้างไฟล์ว่าง", "Create empty file", "touch {file}", L),
	("files", "f.cp", "คัดลอกไฟล์หรือโฟลเดอร์", "Copy file or folder", "cp -r {source} {dest}", M),
	("files", "f.mv", "ย้ายหรือเปลี่ยนชื่อ", "Move or rename", "mv {source} {dest}", M),
	("files", "f.ln", "สร้างลิงก์สัญลักษณ์", "Create symbolic link", "ln -s {target} {link}", M),
	("files", "f.find", "ค้นหาไฟล์ตามชื่อ", "Find files by name", "find {path} -iname '*{name}*' 2>/dev/null", L),
	("files", "f.findbig", "ค้นหาไฟล์ใหญ่กว่า 100MB", "Find files larger than 100MB", "sudo find / -xdev -type f -size +100M 2>/dev/null", L),
	("files", "f.stat", "ดูรายละเอียดไฟล์", "Show file details", "stat {file}", L),
	("files", "f.count", "นับจำนวนไฟล์ในโฟลเดอร์", "Count files in folder", "ls -1 {path} | wc -l", L),
	("files", "f.rm", "ลบไฟล์", "Delete file", "rm {file}", H),
	("files", "f.rmdir", "ลบโฟลเดอร์และทุกอย่างข้างใน", "Delete folder and its contents", "rm -r {path}", H),
	# view
	("view", "v.cat", "แสดงเนื้อหาไฟล์", "Show file contents", "cat {file}", L),
	("view", "v.catn", "แสดงเนื้อหาพร้อมเลขบรรทัด", "Show contents with line numbers", "cat -n {file}", L),
	("view", "v.head", "ดู 20 บรรทัดแรก", "Show first 20 lines", "head -n 20 {file}", L),
	("view", "v.tail", "ดู 20 บรรทัดสุดท้าย", "Show last 20 lines", "tail -n 20 {file}", L),
	("view", "v.tailf", "ติดตามไฟล์ต่อเนื่อง (Ctrl+C เพื่อหยุด)", "Follow file (Ctrl+C to stop)", "tail -f {file}", L),
	("view", "v.range", "ดูบรรทัดในช่วงที่กำหนด", "Show a range of lines", "sed -n '{start},{end}p' {file}", L),
	("view", "v.wc", "นับจำนวนบรรทัด", "Count lines", "wc -l {file}", L),
	("view", "v.grep", "ค้นหาข้อความในไฟล์ พร้อมเลขบรรทัด", "Search text in file with line numbers", "grep -n '{text}' {file}", L),
	("view", "v.grepr", "ค้นหาข้อความในทุกไฟล์ของโฟลเดอร์", "Search text in all files of a folder", "grep -rn '{text}' {path}", L),
	("view", "v.diff", "เปรียบเทียบสองไฟล์", "Compare two files", "diff {file1} {file2}", L),
	("view", "v.less", "อ่านไฟล์ทีละหน้า (q เพื่อออก)", "Page through file (q to quit)", "less {file}", L, False),
	# edit
	("edit", "e.nano", "แก้ไขไฟล์ด้วย nano", "Edit file with nano", "nano {file}", L),
	("edit", "e.sudonano", "แก้ไขไฟล์ระบบด้วย nano (sudo)", "Edit system file with nano (sudo)", "sudo nano {file}", M),
	("edit", "e.vim", "แก้ไขไฟล์ด้วย vim", "Edit file with vim", "vim {file}", L, False),
	("edit", "e.backup", "สำรองไฟล์ก่อนแก้ไข (ต่อท้ายวันเวลา)", "Back up file before editing (timestamped)", "cp {file} {file}.bak.$(date +%Y%m%d%H%M)", L),
	("edit", "e.append", "ต่อท้ายข้อความลงไฟล์", "Append text to file", "echo '{text}' >> {file}", M),
	("edit", "e.teesudo", "ต่อท้ายข้อความลงไฟล์ระบบ (sudo)", "Append text to system file (sudo)", "echo '{text}' | sudo tee -a {file}", M),
	("edit", "e.replace", "แทนที่ข้อความในไฟล์ (เก็บไฟล์เดิมเป็น .bak)", "Replace text in file (keeps .bak)", "sed -i.bak 's/{old}/{new}/g' {file}", M),
	# users
	("users", "u.id", "ดูกลุ่มและสิทธิ์ของผู้ใช้", "Show user groups and IDs", "id {user}", L),
	("users", "u.who", "ดูผู้ที่ล็อกอินอยู่", "Show logged-in users", "who", L),
	("users", "u.list", "ดูรายชื่อผู้ใช้ทั้งหมด", "List all users", "cut -d: -f1 /etc/passwd", L),
	("users", "u.add", "เพิ่มผู้ใช้ใหม่", "Add new user", "sudo adduser {user}", M),
	("users", "u.sudo", "ให้สิทธิ์ sudo", "Grant sudo rights", "sudo usermod -aG sudo {user}", M),
	("users", "u.group", "เพิ่มผู้ใช้เข้ากลุ่ม", "Add user to group", "sudo usermod -aG {group} {user}", M),
	("users", "u.passwd", "เปลี่ยนรหัสผ่านผู้ใช้", "Change user password", "sudo passwd {user}", M),
	("users", "u.chmod", "เปลี่ยนสิทธิ์ไฟล์", "Change file mode", "chmod {mode} {file}", M),
	("users", "u.chown", "เปลี่ยนเจ้าของทั้งโฟลเดอร์", "Change owner recursively", "sudo chown -R {user}:{group} {path}", M),
	("users", "u.root", "สลับเป็น root", "Switch to root shell", "sudo -i", M),
	("users", "u.del", "ลบผู้ใช้และโฟลเดอร์บ้าน", "Delete user and home folder", "sudo deluser --remove-home {user}", H),
	# packages
	("packages", "p.update", "อัปเดตรายการแพ็กเกจ", "Update package lists", "sudo apt update", L),
	("packages", "p.upgradable", "ดูแพ็กเกจที่อัปเกรดได้", "List upgradable packages", "apt list --upgradable 2>/dev/null", L),
	("packages", "p.upgrade", "อัปเกรดแพ็กเกจทั้งหมด", "Upgrade all packages", "sudo apt upgrade -y", M),
	("packages", "p.install", "ติดตั้งแพ็กเกจ", "Install package", "sudo apt install -y {package}", M),
	("packages", "p.search", "ค้นหาแพ็กเกจ", "Search packages", "apt-cache search {keyword}", L),
	("packages", "p.show", "ดูรายละเอียดแพ็กเกจ", "Show package details", "apt show {package} 2>/dev/null", L),
	("packages", "p.installed", "ตรวจว่าติดตั้งแพ็กเกจแล้วหรือยัง", "Check if package is installed", "dpkg -l | grep -i {package}", L),
	("packages", "p.reboot", "ตรวจว่าต้องรีบูตหลังอัปเดตหรือไม่", "Check if reboot is required", "[ -f /var/run/reboot-required ] && echo 'Reboot required' || echo 'No reboot needed'", L),
	("packages", "p.snap", "ดูแพ็กเกจ snap", "List snap packages", "snap list", L),
	("packages", "p.autoremove", "ลบแพ็กเกจที่ไม่ใช้แล้ว", "Remove unused packages", "sudo apt autoremove -y", M),
	("packages", "p.remove", "ถอนการติดตั้งแพ็กเกจ", "Remove package", "sudo apt remove {package}", H),
	# services
	("services", "s.status", "ดูสถานะบริการ", "Show service status", "systemctl status {service} --no-pager", L),
	("services", "s.active", "ตรวจว่าบริการทำงานอยู่หรือไม่ (ตอบสั้น)", "Is service active (short answer)", "systemctl is-active {service}", L),
	("services", "s.running", "แสดงบริการที่กำลังทำงาน", "List running services", "systemctl list-units --type=service --state=running --no-pager --plain", L),
	("services", "s.failed", "แสดงบริการที่ล้มเหลว", "List failed services", "systemctl --failed --no-pager --plain", L),
	("services", "s.logs", "ดู log ของบริการ 50 บรรทัดล่าสุด", "Show last 50 log lines of service", "journalctl -u {service} -n 50 --no-pager", L),
	("services", "s.logsf", "ติดตาม log ของบริการ (Ctrl+C เพื่อหยุด)", "Follow service log (Ctrl+C to stop)", "journalctl -u {service} -f", L),
	("services", "s.start", "เริ่มบริการ", "Start service", "sudo systemctl start {service}", M),
	("services", "s.restart", "รีสตาร์ทบริการ", "Restart service", "sudo systemctl restart {service}", M),
	("services", "s.reload", "โหลดค่าตั้งของบริการใหม่", "Reload service configuration", "sudo systemctl reload {service}", M),
	("services", "s.enable", "เปิดให้เริ่มอัตโนมัติตอนบูต และเริ่มทันที", "Enable at boot and start now", "sudo systemctl enable --now {service}", M),
	("services", "s.disable", "ปิดการเริ่มอัตโนมัติตอนบูต", "Disable at boot", "sudo systemctl disable {service}", M),
	("services", "s.stop", "หยุดบริการ", "Stop service", "sudo systemctl stop {service}", H),
	# processes
	("processes", "r.free", "ดูหน่วยความจำ", "Show memory usage", "free -h", L),
	("processes", "r.df", "ดูพื้นที่ดิสก์", "Show disk space", "df -h", L),
	("processes", "r.du", "ขนาดของแต่ละรายการในโฟลเดอร์ เรียงจากใหญ่", "Sizes in folder, largest first", "du -sh {path}/* 2>/dev/null | sort -rh | head -n 20", L),
	("processes", "r.topcpu", "10 โปรเซสที่ใช้ CPU มากที่สุด", "Top 10 processes by CPU", "ps aux --sort=-%cpu | head -n 11", L),
	("processes", "r.topmem", "10 โปรเซสที่ใช้หน่วยความจำมากที่สุด", "Top 10 processes by memory", "ps aux --sort=-%mem | head -n 11", L),
	("processes", "r.top1", "สรุปภาพรวมระบบครั้งเดียว (ไม่เต็มจอ)", "One-shot system overview (not full screen)", "top -b -n 1 | head -n 20", L),
	("processes", "r.load", "ดูโหลดเฉลี่ยและจำนวน CPU", "Show load average and CPU count", "cat /proc/loadavg; nproc", L),
	("processes", "r.find", "ค้นหาโปรเซสตามชื่อ", "Find process by name", "pgrep -a {name}", L),
	("processes", "r.htop", "ดูโปรเซสแบบโต้ตอบ (เต็มจอ)", "Interactive process viewer (full screen)", "htop", L, False),
	("processes", "r.kill", "หยุดโปรเซสตาม PID", "Stop process by PID", "kill {pid}", H),
	("processes", "r.kill9", "บังคับหยุดโปรเซสตาม PID", "Force stop process by PID", "kill -9 {pid}", H),
	("processes", "r.pkill", "หยุดโปรเซสตามชื่อ", "Stop processes by name", "pkill {name}", H),
	# network
	("network", "n.ip", "ดู IP แบบย่อ", "Show IP addresses (brief)", "ip -br a", L),
	("network", "n.route", "ดูเส้นทางเครือข่าย", "Show routes", "ip r", L),
	("network", "n.ping", "ทดสอบการเชื่อมต่อ 4 ครั้ง", "Ping 4 times", "ping -c 4 {host}", L),
	("network", "n.ports", "ดูพอร์ตที่เปิดรอการเชื่อมต่อ", "Show listening ports", "sudo ss -tulpn", L),
	("network", "n.port", "ตรวจว่าพอร์ตถูกใช้โดยโปรแกรมใด", "Which program uses a port", "sudo ss -tulpn | grep ':{port} '", L),
	("network", "n.curl", "ตรวจ HTTP header ของเว็บ", "Show HTTP headers", "curl -I {url}", L),
	("network", "n.publicip", "ดู IP สาธารณะ", "Show public IP", "curl -s https://ifconfig.me; echo", L),
	("network", "n.dns", "ค้นหา DNS", "DNS lookup", "dig +short {domain}", L),
	("network", "n.trace", "ตรวจเส้นทางไปยังปลายทาง", "Trace route", "traceroute {host}", L),
	("network", "n.download", "ดาวน์โหลดไฟล์", "Download file", "wget {url}", L),
	("network", "n.netplan", "ดูค่าตั้ง netplan", "Show netplan config", "cat /etc/netplan/*.yaml", L),
	("network", "n.hostname", "เปลี่ยนชื่อเครื่อง", "Change hostname", "sudo hostnamectl set-hostname {name}", M),
	("network", "n.netapply", "ทดลองใช้ค่าตั้ง netplan (ย้อนกลับได้ใน 120 วินาที)", "Try netplan config (auto-revert in 120s)", "sudo netplan try", H),
	# security
	("security", "x.ufw", "ดูสถานะไฟร์วอลล์", "Show firewall status", "sudo ufw status verbose", L),
	("security", "x.ufwnum", "ดูกฎไฟร์วอลล์แบบมีหมายเลข", "Show numbered firewall rules", "sudo ufw status numbered", L),
	("security", "x.ufwssh", "อนุญาต SSH (ทำก่อนเปิดไฟร์วอลล์)", "Allow SSH (do before enabling firewall)", "sudo ufw allow OpenSSH", M),
	("security", "x.ufwallow", "เปิดพอร์ต TCP", "Allow TCP port", "sudo ufw allow {port}/tcp", M),
	("security", "x.ufwdel", "ลบกฎไฟร์วอลล์ตามหมายเลข", "Delete firewall rule by number", "sudo ufw delete {number}", H),
	("security", "x.ufwon", "เปิดไฟร์วอลล์", "Enable firewall", "sudo ufw enable", H),
	("security", "x.f2b", "ดูสถานะ fail2ban", "Show fail2ban status", "sudo fail2ban-client status", L),
	("security", "x.f2bssh", "ดู IP ที่ถูกแบนจาก SSH", "Show IPs banned from SSH", "sudo fail2ban-client status sshd", L),
	("security", "x.unban", "ปลดแบน IP", "Unban IP", "sudo fail2ban-client set sshd unbanip {ip}", M),
	("security", "x.last", "ดูประวัติการล็อกอิน", "Show login history", "last -n 20", L),
	("security", "x.failed", "ดูการล็อกอินที่ล้มเหลว", "Show failed logins", "sudo grep 'Failed password' /var/log/auth.log | tail -n 20", L),
	("security", "x.sshtest", "ตรวจไฟล์ตั้งค่า SSH", "Test SSH server config", "sudo sshd -t && echo OK", L),
	("security", "x.keygen", "สร้าง SSH key", "Generate SSH key", "ssh-keygen -t ed25519 -C '{comment}'", L),
	# logs
	("logs", "l.syslog", "ดู syslog 50 บรรทัดล่าสุด", "Last 50 lines of syslog", "sudo tail -n 50 /var/log/syslog", L),
	("logs", "l.auth", "ดู auth.log 50 บรรทัดล่าสุด", "Last 50 lines of auth.log", "sudo tail -n 50 /var/log/auth.log", L),
	("logs", "l.dmesg", "ดูข้อความเคอร์เนลล่าสุด", "Recent kernel messages", "sudo dmesg | tail -n 30", L),
	("logs", "l.boot", "ดูข้อผิดพลาดตั้งแต่บูตครั้งนี้", "Errors since this boot", "journalctl -b -p err --no-pager", L),
	("logs", "l.xe", "ดู log ล่าสุดพร้อมคำอธิบาย", "Recent log with explanations", "journalctl -xe --no-pager | tail -n 50", L),
	("logs", "l.since", "ดู log ตั้งแต่เวลาที่กำหนด", "Log since a given time", "journalctl --since '{since}' --no-pager | tail -n 100", L),
	("logs", "l.size", "ดูพื้นที่ที่ log ใช้", "Show journal disk usage", "journalctl --disk-usage", L),
	("logs", "l.vacuum", "ลด log ให้เหลือ 7 วัน", "Keep only 7 days of logs", "sudo journalctl --vacuum-time=7d", M),
	# archive
	("archive", "a.tarc", "บีบอัดโฟลเดอร์เป็น .tar.gz", "Compress folder to .tar.gz", "tar -czf {name}.tar.gz {path}", L),
	("archive", "a.tarx", "แตกไฟล์ .tar.gz", "Extract .tar.gz", "tar -xzf {file}", L),
	("archive", "a.tarl", "ดูรายการไฟล์ใน .tar.gz", "List files in .tar.gz", "tar -tzf {file}", L),
	("archive", "a.zip", "บีบอัดเป็น zip", "Compress to zip", "zip -r {name}.zip {path}", L),
	("archive", "a.unzip", "แตกไฟล์ zip", "Extract zip", "unzip {file}", L),
	("archive", "a.backupdate", "สำรองโฟลเดอร์พร้อมวันที่", "Back up folder with date", "tar -czf ~/backup-$(date +%Y%m%d).tar.gz {path}", L),
	("archive", "a.scp", "ส่งไฟล์ไปเครื่องอื่น", "Copy file to another host", "scp {file} {user}@{host}:{dest}", L),
	("archive", "a.rsync", "ซิงก์โฟลเดอร์ไปเครื่องอื่น", "Sync folder to another host", "rsync -avz {source} {user}@{host}:{dest}", M),
	# disk
	("disk", "d.lsblk", "ดูดิสก์และพาร์ทิชัน", "Show disks and partitions", "lsblk -f", L),
	("disk", "d.blkid", "ดู UUID ของพาร์ทิชัน", "Show partition UUIDs", "sudo blkid", L),
	("disk", "d.mounts", "ดูสิ่งที่ mount อยู่", "Show mounted filesystems", "findmnt --real", L),
	("disk", "d.fdisk", "ดูตารางพาร์ทิชันทั้งหมด", "Show partition tables", "sudo fdisk -l", L),
	("disk", "d.inode", "ดู inode ที่ใช้", "Show inode usage", "df -i", L),
	("disk", "d.mount", "mount พาร์ทิชัน", "Mount partition", "sudo mount {device} {path}", M),
	("disk", "d.umount", "ยกเลิก mount", "Unmount", "sudo umount {path}", M),
	# schedule
	("schedule", "c.list", "ดูงานตั้งเวลาของฉัน", "List my cron jobs", "crontab -l", L),
	("schedule", "c.root", "ดูงานตั้งเวลาของ root", "List root cron jobs", "sudo crontab -l", L),
	("schedule", "c.timers", "ดู systemd timers", "List systemd timers", "systemctl list-timers --no-pager", L),
	("schedule", "c.edit", "แก้ไขงานตั้งเวลา", "Edit cron jobs", "crontab -e", L),
	("schedule", "c.add", "เพิ่มงานตั้งเวลา (ไม่ต้องเปิดตัวแก้ไข)", "Add cron job (no editor)", "(crontab -l 2>/dev/null; echo '{schedule} {command}') | crontab -", M),
	# webdb
	("webdb", "w.nginxt", "ทดสอบค่าตั้ง Nginx", "Test Nginx configuration", "sudo nginx -t", L),
	("webdb", "w.nginxr", "โหลดค่าตั้ง Nginx ใหม่", "Reload Nginx", "sudo systemctl reload nginx", M),
	("webdb", "w.apachet", "ทดสอบค่าตั้ง Apache", "Test Apache configuration", "sudo apache2ctl configtest", L),
	("webdb", "w.mysql", "เข้า MySQL/MariaDB ด้วย root", "Open MySQL/MariaDB as root", "sudo mysql", L),
	("webdb", "w.mysqldump", "สำรองฐานข้อมูล MySQL", "Back up MySQL database", "mysqldump -u {user} -p {database} > {database}-$(date +%Y%m%d).sql", L),
	("webdb", "w.psql", "เข้า PostgreSQL", "Open PostgreSQL", "sudo -u postgres psql", L),
	("webdb", "w.dockerps", "ดูคอนเทนเนอร์ที่ทำงานอยู่ (อ่านง่าย)", "Running containers (readable)", "docker ps --format '{{.Names}}: {{.Status}}'", L),
	("webdb", "w.dockerlogs", "ดู log คอนเทนเนอร์ 100 บรรทัด", "Last 100 container log lines", "docker logs --tail 100 {container}", L),
	("webdb", "w.composeup", "เริ่ม Docker Compose", "Start Docker Compose", "docker compose up -d", M),
	("webdb", "w.composedown", "หยุด Docker Compose", "Stop Docker Compose", "docker compose down", H),
	("webdb", "w.git", "ดูสถานะ Git", "Git status", "git status", L),
	("webdb", "w.gitpull", "ดึงโค้ดล่าสุดจาก Git", "Git pull", "git pull", M),
	("webdb", "w.certbot", "ดูใบรับรอง SSL", "List SSL certificates", "sudo certbot certificates", L),
]


def main():
	cats = [{"id": i, "name": {"th": th, "en": en}} for i, th, en in CATS]
	params = {}
	for k, v in PARAMS.items():
		params[k] = {"th": v[0], "en": v[1], "default": v[2]}
		if len(v) > 3:
			params[k]["source"] = v[3]
	groups = {g: {"th": th, "en": en} for g, th, en in GROUPS}
	ids = set()
	cmds = []
	for row in C:
		cat, cid, th, en, tpl, risk = row[:6]
		sr = row[6] if len(row) > 6 else True
		assert cid not in ids, cid
		ids.add(cid)
		d = {"id": cid, "cat": cat, "name": {"th": th, "en": en}, "template": tpl, "risk": risk}
		if not sr:
			d["sr"] = False
		cmds.append(d)
	out = os.path.join(os.path.dirname(__file__), "..", "addon", "globalPlugins", "termAssist", "data", "core.json")
	with open(out, "w", encoding="utf-8") as f:
		json.dump({"version": 1, "categories": cats, "groups": groups, "params": params, "commands": cmds}, f, ensure_ascii=False, indent=1)
	print(len(cmds), "commands,", len(cats), "categories")


if __name__ == "__main__":
	main()
