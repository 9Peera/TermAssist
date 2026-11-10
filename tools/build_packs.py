# Generates addon/globalPlugins/termAssist/data/packs/<id>.json — one Service Pack per file.
# Every pack uses the same groups: check, status, control, logs, test, config, tasks, fix.
# Run: python tools/build_packs.py
import json
import os

L, M, H = "low", "medium", "high"
OUT = os.path.join(os.path.dirname(__file__), "..", "addon", "globalPlugins", "termAssist", "data", "packs")

INSTALL = {'docker': 'docker.io docker-compose-v2', 'nginx': 'nginx', 'apache': 'apache2', 'mysql': 'mysql-server', 'postgres': 'postgresql', 'php': 'php-fpm', 'redis': 'redis-server', 'certbot': 'certbot', 'git': 'git', 'node': 'nodejs npm', 'python': 'python3-venv python3-pip', 'fail2ban': 'fail2ban', 'samba': 'samba'}

# id: (detect binary, th, en, params {name: (th, en, default, source)}, commands [(group, key, th, en, template, risk[, sr])])
PACKS = {
	"docker": ("docker", "Docker / Compose", "Docker / Compose", {
		"container": ("ชื่อคอนเทนเนอร์", "Container name", "", "docker ps -a --format '{{.Names}}'"),
		"image": ("อิมเมจ", "Image", "", "docker images --format '{{.Repository}}:{{.Tag}}'"),
		"csvc": ("บริการใน Compose", "Compose service", "", "docker compose config --services"),
	}, [
		("check", "ver", "ดูเวอร์ชัน Docker และ Compose", "Docker and Compose versions", "docker --version; docker compose version", L),
		("status", "ps", "คอนเทนเนอร์ที่ทำงานอยู่", "Running containers", "docker ps --format '{{.Names}}: {{.Status}}'", L),
		("status", "psa", "คอนเทนเนอร์ทั้งหมด", "All containers", "docker ps -a --format '{{.Names}}: {{.Status}}'", L),
		("status", "stats", "การใช้ CPU และ RAM ของคอนเทนเนอร์", "Container CPU and RAM", "docker stats --no-stream --format '{{.Name}}: CPU {{.CPUPerc}}, RAM {{.MemUsage}}'", L),
		("status", "cps", "สถานะบริการใน Compose", "Compose service status", "docker compose ps --format '{{.Service}}: {{.Status}}'", L),
		("control", "start", "เริ่มคอนเทนเนอร์", "Start container", "docker start {container}", M),
		("control", "restart", "รีสตาร์ทคอนเทนเนอร์", "Restart container", "docker restart {container}", M),
		("control", "stop", "หยุดคอนเทนเนอร์", "Stop container", "docker stop {container}", M),
		("control", "up", "เริ่ม Compose (เบื้องหลัง)", "Compose up (detached)", "docker compose up -d", M),
		("control", "crestart", "รีสตาร์ทบริการใน Compose", "Restart Compose service", "docker compose restart {csvc}", M),
		("control", "down", "หยุดและลบคอนเทนเนอร์ของ Compose", "Compose down", "docker compose down", H),
		("control", "rm", "ลบคอนเทนเนอร์", "Remove container", "docker rm {container}", H),
		("logs", "logs", "log คอนเทนเนอร์ 100 บรรทัด", "Container log, 100 lines", "docker logs --tail 100 {container}", L),
		("logs", "logsf", "ติดตาม log คอนเทนเนอร์ (Ctrl+C หยุด)", "Follow container log (Ctrl+C)", "docker logs -f --tail 50 {container}", L),
		("logs", "clogs", "log ของบริการใน Compose", "Compose service log", "docker compose logs --tail 100 {csvc}", L),
		("config", "compose", "แก้ไขไฟล์ Compose", "Edit Compose file", "nano docker-compose.yml", L),
		("test", "cconfig", "ตรวจไฟล์ Compose", "Validate Compose file", "docker compose config --quiet && echo OK", L),
		("tasks", "shell", "เข้า shell ในคอนเทนเนอร์", "Shell into container", "docker exec -it {container} sh", L),
		("tasks", "images", "ดูอิมเมจทั้งหมด", "List images", "docker images --format '{{.Repository}}:{{.Tag}} {{.Size}}'", L),
		("tasks", "pull", "ดาวน์โหลดอิมเมจ", "Pull image", "docker pull {image}", L),
		("tasks", "cpull", "อัปเดตอิมเมจของ Compose แล้วเริ่มใหม่", "Pull Compose images and recreate", "docker compose pull && docker compose up -d", M),
		("tasks", "ip", "ดู IP ของคอนเทนเนอร์", "Container IP address", "docker inspect --format '{{range .NetworkSettings.Networks}}{{.IPAddress}} {{end}}' {container}", L),
		("fix", "state", "ดูสถานะและข้อผิดพลาดของคอนเทนเนอร์", "Container state and error", "docker inspect --format '{{.State.Status}} exit={{.State.ExitCode}} {{.State.Error}}' {container}", L),
		("fix", "df", "ดูพื้นที่ที่ Docker ใช้", "Docker disk usage", "docker system df", L),
		("fix", "prune", "ล้างสิ่งที่ไม่ใช้ (คอนเทนเนอร์หยุด อิมเมจค้าง)", "Prune unused data", "docker system prune -f", H),
		("fix", "daemon", "รีสตาร์ท Docker daemon", "Restart Docker daemon", "sudo systemctl restart docker", H),
	]),
	"nginx": ("nginx", "Nginx", "Nginx", {
		"site": ("ชื่อไซต์ (sites-available)", "Site name (sites-available)", "", "ls /etc/nginx/sites-available"),
		"confd": ("ไฟล์ใน conf.d", "File in conf.d", "", "ls /etc/nginx/conf.d"),
	}, [
		("check", "ver", "ดูเวอร์ชัน Nginx", "Nginx version", "nginx -v", L),
		("status", "status", "ดูสถานะ Nginx", "Nginx status", "systemctl status nginx --no-pager", L),
		("status", "active", "Nginx ทำงานอยู่หรือไม่", "Is Nginx active", "systemctl is-active nginx", L),
		("control", "reload", "โหลดค่าตั้งใหม่", "Reload", "sudo systemctl reload nginx", M),
		("control", "restart", "รีสตาร์ท", "Restart", "sudo systemctl restart nginx", M),
		("control", "stop", "หยุด Nginx", "Stop Nginx", "sudo systemctl stop nginx", H),
		("logs", "error", "error log 50 บรรทัด", "Error log, 50 lines", "sudo tail -n 50 /var/log/nginx/error.log", L),
		("logs", "access", "access log 50 บรรทัด", "Access log, 50 lines", "sudo tail -n 50 /var/log/nginx/access.log", L),
		("logs", "errorf", "ติดตาม error log", "Follow error log", "sudo tail -f /var/log/nginx/error.log", L),
		("test", "t", "ทดสอบค่าตั้ง", "Test configuration", "sudo nginx -t", L),
		("test", "treload", "ทดสอบแล้วโหลดใหม่ถ้าผ่าน", "Test, then reload if OK", "sudo nginx -t && sudo systemctl reload nginx", M),
		("config", "sites", "รายการไซต์ทั้งหมด", "Available sites", "ls -1 /etc/nginx/sites-available", L),
		("config", "enabled", "ไซต์ที่เปิดใช้", "Enabled sites", "ls -1 /etc/nginx/sites-enabled", L),
		("config", "editsite", "แก้ไขค่าตั้งไซต์", "Edit site config", "sudo nano /etc/nginx/sites-available/{site}", M),
		("config", "editmain", "แก้ไข nginx.conf", "Edit nginx.conf", "sudo nano /etc/nginx/nginx.conf", M),
		("config", "where", "ดูว่าค่าตั้งไซต์อยู่โฟลเดอร์ไหน (sites-available หรือ conf.d)", "Where site configs live (sites-available or conf.d)", "grep -n 'include' /etc/nginx/nginx.conf; ls -1 /etc/nginx", L),
		("config", "confdlist", "รายการไฟล์ใน conf.d", "Files in conf.d", "ls -1 /etc/nginx/conf.d", L),
		("config", "editconfd", "แก้ไขไฟล์ใน conf.d", "Edit file in conf.d", "sudo nano /etc/nginx/conf.d/{confd}", M),
		("tasks", "ensite", "เปิดใช้ไซต์", "Enable site", "sudo ln -s /etc/nginx/sites-available/{site} /etc/nginx/sites-enabled/", M),
		("tasks", "dissite", "ปิดใช้ไซต์", "Disable site", "sudo rm /etc/nginx/sites-enabled/{site}", H),
		("fix", "ports", "ตรวจว่าพอร์ต 80/443 ถูกใช้โดยอะไร", "What uses ports 80/443", "sudo ss -tlpn | grep -E ':(80|443) '", L),
		("fix", "local", "ทดสอบเรียกเว็บจากเครื่องเอง", "Request localhost", "curl -sI http://localhost | head -n 5", L),
	]),
	"apache": ("apache2", "Apache", "Apache", {
		"asite": ("ชื่อไซต์ Apache", "Apache site", "", "ls /etc/apache2/sites-available"),
		"module": ("ชื่อโมดูล", "Module name", "", None),
	}, [
		("check", "ver", "ดูเวอร์ชัน Apache", "Apache version", "apache2 -v", L),
		("status", "status", "ดูสถานะ Apache", "Apache status", "systemctl status apache2 --no-pager", L),
		("control", "reload", "โหลดค่าตั้งใหม่", "Reload", "sudo systemctl reload apache2", M),
		("control", "restart", "รีสตาร์ท", "Restart", "sudo systemctl restart apache2", M),
		("control", "stop", "หยุด Apache", "Stop Apache", "sudo systemctl stop apache2", H),
		("logs", "error", "error log 50 บรรทัด", "Error log, 50 lines", "sudo tail -n 50 /var/log/apache2/error.log", L),
		("logs", "access", "access log 50 บรรทัด", "Access log, 50 lines", "sudo tail -n 50 /var/log/apache2/access.log", L),
		("test", "t", "ทดสอบค่าตั้ง", "Test configuration", "sudo apache2ctl configtest", L),
		("config", "editsite", "แก้ไขค่าตั้งไซต์", "Edit site config", "sudo nano /etc/apache2/sites-available/{asite}", M),
		("config", "editmain", "แก้ไข apache2.conf", "Edit apache2.conf", "sudo nano /etc/apache2/apache2.conf", M),
		("tasks", "ensite", "เปิดใช้ไซต์", "Enable site", "sudo a2ensite {asite} && sudo systemctl reload apache2", M),
		("tasks", "dissite", "ปิดใช้ไซต์", "Disable site", "sudo a2dissite {asite} && sudo systemctl reload apache2", H),
		("tasks", "enmod", "เปิดใช้โมดูล", "Enable module", "sudo a2enmod {module} && sudo systemctl restart apache2", M),
		("tasks", "mods", "รายการโมดูลที่โหลดอยู่", "Loaded modules", "apache2ctl -M", L),
		("fix", "ports", "ตรวจพอร์ต 80/443", "Check ports 80/443", "sudo ss -tlpn | grep -E ':(80|443) '", L),
	]),
	"mysql": ("mysql", "MySQL / MariaDB", "MySQL / MariaDB", {
		"mysqldb": ("ฐานข้อมูล", "Database", "", "sudo mysql -N -e 'SHOW DATABASES'"),
		"dbuser": ("ผู้ใช้ฐานข้อมูล", "Database user", "", "sudo mysql -N -e 'SELECT DISTINCT user FROM mysql.user'"),
		"dbpass": ("รหัสผ่าน (จะอยู่ในประวัติคำสั่ง)", "Password (stays in shell history)", "", None),
	}, [
		("check", "ver", "ดูเวอร์ชัน", "Version", "mysql --version", L),
		("status", "status", "ดูสถานะบริการ", "Service status", "systemctl status mysql --no-pager || systemctl status mariadb --no-pager", L),
		("control", "restart", "รีสตาร์ท", "Restart", "sudo systemctl restart mysql || sudo systemctl restart mariadb", M),
		("logs", "error", "error log 50 บรรทัด", "Error log, 50 lines", "sudo tail -n 50 /var/log/mysql/error.log", L),
		("config", "edit", "แก้ไขค่าตั้งเซิร์ฟเวอร์", "Edit server config", "sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf", M),
		("tasks", "open", "เข้า MySQL ด้วย root", "Open MySQL as root", "sudo mysql", L),
		("tasks", "dbs", "รายการฐานข้อมูล", "List databases", "sudo mysql -N -e 'SHOW DATABASES'", L),
		("tasks", "tables", "รายการตารางในฐานข้อมูล", "List tables", "sudo mysql -N -e 'SHOW TABLES' {mysqldb}", L),
		("tasks", "size", "ขนาดของแต่ละฐานข้อมูล (MB)", "Database sizes (MB)", "sudo mysql -e 'SELECT table_schema AS db, ROUND(SUM(data_length+index_length)/1048576,1) AS MB FROM information_schema.tables GROUP BY table_schema'", L),
		("tasks", "users", "รายการผู้ใช้", "List users", "sudo mysql -e 'SELECT user, host FROM mysql.user'", L),
		("tasks", "create", "สร้างฐานข้อมูล (utf8mb4)", "Create database (utf8mb4)", "sudo mysql -e 'CREATE DATABASE {name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci'", M),
		("tasks", "mkuser", "สร้างผู้ใช้", "Create user", "sudo mysql -e \"CREATE USER '{dbuser}'@'localhost' IDENTIFIED BY '{dbpass}'\"", M),
		("tasks", "grant", "ให้สิทธิ์ผู้ใช้ทั้งฐานข้อมูล", "Grant all on database", "sudo mysql -e \"GRANT ALL PRIVILEGES ON {mysqldb}.* TO '{dbuser}'@'localhost'; FLUSH PRIVILEGES\"", M),
		("tasks", "dump", "สำรองฐานข้อมูล", "Back up database", "sudo mysqldump {mysqldb} > {mysqldb}-$(date +%Y%m%d).sql", L),
		("tasks", "restore", "นำเข้าไฟล์ SQL", "Restore SQL file", "sudo mysql {mysqldb} < {file}", H),
		("tasks", "drop", "ลบฐานข้อมูล", "Drop database", "sudo mysql -e 'DROP DATABASE {mysqldb}'", H),
		("fix", "port", "ตรวจพอร์ต 3306", "Check port 3306", "sudo ss -tlpn | grep ':3306 '", L),
	]),
	"postgres": ("psql", "PostgreSQL", "PostgreSQL", {
		"pgdb": ("ฐานข้อมูล", "Database", "", "sudo -u postgres psql -Atc 'SELECT datname FROM pg_database WHERE NOT datistemplate'"),
		"pguser": ("ผู้ใช้ฐานข้อมูล", "Database role", "", "sudo -u postgres psql -Atc 'SELECT rolname FROM pg_roles WHERE rolcanlogin'"),
	}, [
		("check", "ver", "ดูเวอร์ชัน", "Version", "psql --version", L),
		("status", "status", "ดูสถานะบริการ", "Service status", "systemctl status postgresql --no-pager", L),
		("status", "clusters", "ดูคลัสเตอร์ทั้งหมด", "List clusters", "pg_lsclusters", L),
		("control", "restart", "รีสตาร์ท", "Restart", "sudo systemctl restart postgresql", M),
		("control", "reload", "โหลดค่าตั้งใหม่", "Reload", "sudo systemctl reload postgresql", M),
		("logs", "log", "log 50 บรรทัด", "Log, 50 lines", "sudo sh -c 'tail -n 50 /var/log/postgresql/*.log'", L),
		("config", "conf", "แก้ไข postgresql.conf", "Edit postgresql.conf", "sudo sh -c 'nano /etc/postgresql/*/main/postgresql.conf'", M),
		("config", "hba", "แก้ไข pg_hba.conf (สิทธิ์การเชื่อมต่อ)", "Edit pg_hba.conf", "sudo sh -c 'nano /etc/postgresql/*/main/pg_hba.conf'", M),
		("tasks", "open", "เข้า psql", "Open psql", "sudo -u postgres psql", L),
		("tasks", "dbs", "รายการฐานข้อมูล", "List databases", "sudo -u postgres psql -Atc 'SELECT datname FROM pg_database WHERE NOT datistemplate'", L),
		("tasks", "size", "ขนาดของแต่ละฐานข้อมูล", "Database sizes", "sudo -u postgres psql -Atc \"SELECT datname, pg_size_pretty(pg_database_size(datname)) FROM pg_database\"", L),
		("tasks", "createdb", "สร้างฐานข้อมูล", "Create database", "sudo -u postgres createdb {name}", M),
		("tasks", "createuser", "สร้างผู้ใช้ (ถามรหัสผ่าน)", "Create role (asks password)", "sudo -u postgres createuser --pwprompt {name}", M),
		("tasks", "owner", "ให้ผู้ใช้เป็นเจ้าของฐานข้อมูล", "Make role owner of database", "sudo -u postgres psql -c 'ALTER DATABASE {pgdb} OWNER TO {pguser}'", M),
		("tasks", "dump", "สำรองฐานข้อมูล", "Back up database", "sudo -u postgres pg_dump {pgdb} > {pgdb}-$(date +%Y%m%d).sql", L),
		("tasks", "restore", "นำเข้าไฟล์ SQL", "Restore SQL file", "sudo -u postgres psql {pgdb} < {file}", H),
		("tasks", "drop", "ลบฐานข้อมูล", "Drop database", "sudo -u postgres dropdb {pgdb}", H),
		("fix", "port", "ตรวจพอร์ต 5432", "Check port 5432", "sudo ss -tlpn | grep ':5432 '", L),
	]),
	"php": ("php", "PHP / PHP-FPM", "PHP / PHP-FPM", {
		"phpver": ("เวอร์ชัน PHP (เช่น 8.3)", "PHP version (e.g. 8.3)", "", "ls /etc/php"),
		"ext": ("ชื่อส่วนขยาย (เช่น mbstring)", "Extension (e.g. mbstring)", "", None),
	}, [
		("check", "ver", "ดูเวอร์ชัน PHP", "PHP version", "php -v", L),
		("check", "mods", "ส่วนขยายที่ติดตั้ง", "Installed extensions", "php -m", L),
		("status", "status", "ดูสถานะ PHP-FPM", "PHP-FPM status", "systemctl status php{phpver}-fpm --no-pager", L),
		("control", "restart", "รีสตาร์ท PHP-FPM", "Restart PHP-FPM", "sudo systemctl restart php{phpver}-fpm", M),
		("control", "reload", "โหลดค่าตั้ง PHP-FPM ใหม่", "Reload PHP-FPM", "sudo systemctl reload php{phpver}-fpm", M),
		("logs", "log", "log ของ PHP-FPM", "PHP-FPM log", "sudo tail -n 50 /var/log/php{phpver}-fpm.log", L),
		("test", "t", "ทดสอบค่าตั้ง PHP-FPM", "Test PHP-FPM config", "sudo php-fpm{phpver} -t", L),
		("config", "ini", "แก้ไข php.ini ของ FPM", "Edit FPM php.ini", "sudo nano /etc/php/{phpver}/fpm/php.ini", M),
		("config", "where", "ดูว่าใช้ php.ini ไฟล์ไหน", "Which php.ini is loaded", "php --ini", L),
		("tasks", "setting", "ค้นหาค่าตั้งของ PHP", "Find a PHP setting", "php -i | grep -i '{text}'", L),
		("tasks", "install", "ติดตั้งส่วนขยาย", "Install extension", "sudo apt install -y php{phpver}-{ext}", M),
		("tasks", "composer", "ติดตั้งแพ็กเกจ Composer ของโปรเจกต์", "Composer install", "composer install --no-dev", M),
	]),
	"redis": ("redis-server", "Redis", "Redis", {}, [
		("check", "ver", "ดูเวอร์ชัน", "Version", "redis-server --version", L),
		("status", "status", "ดูสถานะบริการ", "Service status", "systemctl status redis-server --no-pager", L),
		("status", "ping", "ทดสอบการตอบสนอง", "Ping", "redis-cli ping", L),
		("control", "restart", "รีสตาร์ท", "Restart", "sudo systemctl restart redis-server", M),
		("logs", "log", "log 50 บรรทัด", "Log, 50 lines", "sudo tail -n 50 /var/log/redis/redis-server.log", L),
		("config", "edit", "แก้ไข redis.conf", "Edit redis.conf", "sudo nano /etc/redis/redis.conf", M),
		("tasks", "mem", "การใช้หน่วยความจำ", "Memory usage", "redis-cli info memory | grep -E 'used_memory_human|maxmemory_human'", L),
		("tasks", "size", "จำนวนคีย์", "Number of keys", "redis-cli dbsize", L),
		("tasks", "keys", "ค้นหาคีย์ตามคำขึ้นต้น", "Find keys by prefix", "redis-cli --scan --pattern '{text}*' | head -n 50", L),
		("tasks", "flush", "ลบข้อมูลทั้งหมด", "Flush all data", "redis-cli flushall", H),
	]),
	"certbot": ("certbot", "Certbot (SSL)", "Certbot (SSL)", {}, [
		("check", "ver", "ดูเวอร์ชัน", "Version", "certbot --version", L),
		("status", "certs", "ดูใบรับรองและวันหมดอายุ", "Certificates and expiry", "sudo certbot certificates", L),
		("status", "timer", "ตรวจการต่ออายุอัตโนมัติ", "Auto-renew timer", "systemctl list-timers --no-pager | grep -i certbot", L),
		("test", "dry", "ทดสอบการต่ออายุ (ไม่ต่อจริง)", "Renewal dry run", "sudo certbot renew --dry-run", L),
		("control", "renew", "ต่ออายุใบรับรอง", "Renew certificates", "sudo certbot renew", M),
		("logs", "log", "log ของ certbot", "Certbot log", "sudo tail -n 50 /var/log/letsencrypt/letsencrypt.log", L),
		("tasks", "nginx", "ขอใบรับรองสำหรับ Nginx", "New certificate for Nginx", "sudo certbot --nginx -d {domain}", M),
		("tasks", "apache", "ขอใบรับรองสำหรับ Apache", "New certificate for Apache", "sudo certbot --apache -d {domain}", M),
		("tasks", "expiry", "ดูวันหมดอายุของเว็บใด ๆ", "Expiry date of any site", "echo | openssl s_client -servername {domain} -connect {domain}:443 2>/dev/null | openssl x509 -noout -dates", L),
		("fix", "delete", "ลบใบรับรอง", "Delete certificate", "sudo certbot delete --cert-name {domain}", H),
	]),
	"git": ("git", "Git", "Git", {
		"branch": ("สาขา (branch)", "Branch", "", "git branch --format='%(refname:short)'"),
	}, [
		("check", "ver", "ดูเวอร์ชัน Git", "Git version", "git --version", L),
		("status", "status", "สถานะแบบย่อ", "Short status", "git status -sb", L),
		("status", "log", "10 commit ล่าสุด", "Last 10 commits", "git log --oneline -n 10", L),
		("status", "branches", "สาขาทั้งหมด", "All branches", "git branch -a", L),
		("status", "remote", "ดู remote", "Show remotes", "git remote -v", L),
		("status", "diffstat", "สรุปไฟล์ที่เปลี่ยน", "Changed files summary", "git diff --stat", L),
		("tasks", "pull", "ดึงโค้ดล่าสุด", "Pull", "git pull", M),
		("tasks", "fetch", "ดึงข้อมูล remote (ไม่รวม)", "Fetch all", "git fetch --all", L),
		("tasks", "checkout", "สลับสาขา", "Switch branch", "git switch {branch}", M),
		("tasks", "commit", "บันทึกทุกการเปลี่ยนแปลง", "Commit all changes", "git add -A && git commit -m '{text}'", M),
		("tasks", "push", "ส่งขึ้น remote", "Push", "git push", M),
		("tasks", "clone", "โคลนโปรเจกต์", "Clone repository", "git clone {url}", L),
		("tasks", "stash", "เก็บการเปลี่ยนแปลงชั่วคราว", "Stash changes", "git stash", M),
		("tasks", "pop", "นำการเปลี่ยนแปลงที่เก็บไว้กลับมา", "Pop stash", "git stash pop", M),
		("config", "name", "ตั้งชื่อผู้ commit", "Set commit author name", "git config --global user.name '{name}'", L),
		("fix", "discard", "ยกเลิกการแก้ไขไฟล์", "Discard changes to file", "git restore {file}", H),
		("fix", "hard", "ย้อนทุกอย่างกลับเป็น commit ล่าสุด", "Reset everything to last commit", "git reset --hard", H),
	]),
	"node": ("node", "Node.js / PM2", "Node.js / PM2", {
		"pm2app": ("แอปใน PM2", "PM2 app", "", "pm2 jlist 2>/dev/null | grep -o '\"name\":\"[^\"]*\"' | cut -d'\"' -f4 | sort -u"),
		"script": ("ชื่อสคริปต์ใน package.json", "package.json script", "", "node -e \"console.log(Object.keys(require('./package.json').scripts||{}).join('\\n'))\""),
	}, [
		("check", "ver", "ดูเวอร์ชัน Node และ npm", "Node and npm versions", "node -v; npm -v", L),
		("check", "pm2ver", "ดูเวอร์ชัน PM2", "PM2 version", "pm2 -v", L),
		("status", "ls", "แอปทั้งหมดใน PM2", "PM2 app list", "pm2 ls", L),
		("status", "describe", "รายละเอียดแอป", "App details", "pm2 describe {pm2app}", L),
		("control", "restart", "รีสตาร์ทแอป", "Restart app", "pm2 restart {pm2app}", M),
		("control", "reload", "รีโหลดแอปแบบไม่หยุดบริการ", "Zero-downtime reload", "pm2 reload {pm2app}", M),
		("control", "start", "เริ่มแอปใหม่ใน PM2", "Start new app in PM2", "pm2 start {file} --name {name}", M),
		("control", "stop", "หยุดแอป", "Stop app", "pm2 stop {pm2app}", H),
		("control", "save", "บันทึกรายการแอปให้เริ่มหลังรีบูต", "Save app list for reboot", "pm2 save", M),
		("logs", "logs", "log ของแอป 50 บรรทัด", "App log, 50 lines", "pm2 logs {pm2app} --lines 50 --nostream", L),
		("logs", "logsf", "ติดตาม log ของแอป", "Follow app log", "pm2 logs {pm2app}", L),
		("tasks", "install", "ติดตั้งแพ็กเกจของโปรเจกต์", "npm install", "npm install", M),
		("tasks", "ci", "ติดตั้งตาม lock file", "npm ci", "npm ci", M),
		("tasks", "run", "รันสคริปต์ npm", "Run npm script", "npm run {script}", M),
		("tasks", "outdated", "แพ็กเกจที่ล้าสมัย", "Outdated packages", "npm outdated", L),
	]),
	"python": ("python3", "Python / venv", "Python / venv", {}, [
		("check", "ver", "ดูเวอร์ชัน Python และ pip", "Python and pip versions", "python3 --version; python3 -m pip --version", L),
		("tasks", "venv", "สร้าง virtual environment (.venv)", "Create .venv", "python3 -m venv .venv", M),
		("tasks", "activate", "เปิดใช้ .venv", "Activate .venv", "source .venv/bin/activate", L),
		("tasks", "deactivate", "ออกจาก venv", "Deactivate venv", "deactivate", L),
		("tasks", "req", "ติดตั้งจาก requirements.txt", "Install requirements.txt", "pip install -r requirements.txt", M),
		("tasks", "install", "ติดตั้งแพ็กเกจ pip", "pip install package", "pip install {package}", M),
		("tasks", "list", "แพ็กเกจที่ติดตั้ง", "Installed packages", "pip list", L),
		("tasks", "freeze", "บันทึกรายการแพ็กเกจลง requirements.txt", "Freeze to requirements.txt", "pip freeze > requirements.txt", M),
		("tasks", "serve", "เปิดเว็บเซิร์ฟเวอร์ชั่วคราวในโฟลเดอร์นี้", "Quick web server here", "python3 -m http.server {port}", L),
		("fix", "which", "ดูว่าใช้ Python ตัวไหน", "Which Python is used", "which python3; python3 -c 'import sys; print(sys.prefix)'", L),
	]),
	"fail2ban": ("fail2ban-client", "Fail2ban", "Fail2ban", {
		"jail": ("ชื่อ jail", "Jail name", "sshd", "sudo fail2ban-client status | sed -n 's/.*Jail list:[[:space:]]*//p' | tr ',' '\\n'"),
	}, [
		("status", "status", "รายการ jail", "List jails", "sudo fail2ban-client status", L),
		("status", "jail", "IP ที่ถูกแบนใน jail", "Banned IPs in jail", "sudo fail2ban-client status {jail}", L),
		("control", "restart", "รีสตาร์ท fail2ban", "Restart fail2ban", "sudo systemctl restart fail2ban", M),
		("logs", "log", "log 50 บรรทัด", "Log, 50 lines", "sudo tail -n 50 /var/log/fail2ban.log", L),
		("test", "t", "ทดสอบค่าตั้ง", "Test configuration", "sudo fail2ban-client -t", L),
		("config", "edit", "แก้ไข jail.local", "Edit jail.local", "sudo nano /etc/fail2ban/jail.local", M),
		("tasks", "unban", "ปลดแบน IP", "Unban IP", "sudo fail2ban-client set {jail} unbanip {ip}", M),
		("tasks", "ban", "แบน IP", "Ban IP", "sudo fail2ban-client set {jail} banip {ip}", M),
	]),
	"samba": ("smbd", "Samba (แชร์ไฟล์)", "Samba (file sharing)", {}, [
		("check", "ver", "ดูเวอร์ชัน", "Version", "smbd --version", L),
		("status", "status", "ดูสถานะบริการ", "Service status", "systemctl status smbd --no-pager", L),
		("status", "shares", "รายการแชร์บนเครื่องนี้", "Shares on this host", "smbclient -L localhost -N", L),
		("control", "restart", "รีสตาร์ท", "Restart", "sudo systemctl restart smbd", M),
		("logs", "log", "log 50 บรรทัด", "Log, 50 lines", "sudo tail -n 50 /var/log/samba/log.smbd", L),
		("test", "t", "ทดสอบค่าตั้ง", "Test configuration", "testparm -s", L),
		("config", "edit", "แก้ไข smb.conf", "Edit smb.conf", "sudo nano /etc/samba/smb.conf", M),
		("tasks", "users", "รายการผู้ใช้ Samba", "Samba users", "sudo pdbedit -L", L),
		("tasks", "adduser", "เพิ่มผู้ใช้ Samba", "Add Samba user", "sudo smbpasswd -a {user}", M),
	]),
}


def main():
	os.makedirs(OUT, exist_ok=True)
	for f in os.listdir(OUT):
		if f.endswith(".json"):
			os.remove(os.path.join(OUT, f))
	total = 0
	for pid, (detect, th, en, params, cmds) in PACKS.items():
		cat = f"pack.{pid}"
		out = {
			"version": 1,
			"categories": [{"id": cat, "name": {"th": th, "en": en}, "detect": detect, "install": INSTALL[pid]}],
			"params": {},
			"commands": [],
		}
		for k, (pth, pen, d, src) in params.items():
			out["params"][k] = {"th": pth, "en": pen, "default": d}
			if src:
				out["params"][k]["source"] = src
		for row in cmds:
			g, key, cth, cen, tpl, risk = row[:6]
			d = {"id": f"{pid}.{key}", "cat": cat, "group": g, "name": {"th": cth, "en": cen},
				"keywords": [pid, en.lower()], "template": tpl, "risk": risk}
			out["commands"].append(d)
		total += len(cmds)
		with open(os.path.join(OUT, f"{pid}.json"), "w", encoding="utf-8") as f:
			json.dump(out, f, ensure_ascii=False, indent=1)
	print(len(PACKS), "packs,", total, "commands")


if __name__ == "__main__":
	main()
