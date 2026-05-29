"""
GUI Interface using tkinter
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import threading


class PackageMonitorUI:
    """Main GUI Application"""
    
    def __init__(self, scanner_manager, storage, report_generator, config):
        self.scanner_manager = scanner_manager
        self.storage = storage
        self.report_generator = report_generator
        self.config = config
        self.is_scanning = False
        self.next_scan_job = None
        
        self.root = tk.Tk()
        self.root.title("Package Monitor - 包安装监控")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Set macOS style colors
        self.colors = {
            'bg': '#f5f5f7',
            'card': '#ffffff',
            'accent': '#007AFF',
            'text': '#1d1d1f',
            'text_secondary': '#86868b',
            'border': '#e5e5ea',
            'success': '#34C759',
            'warning': '#FF9500'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # Current selected date
        self.selected_date = datetime.now().strftime("%Y-%m-%d")
        
        # Setup UI
        self._setup_styles()
        self._create_widgets()
        self._load_data()

        if self.config.get("auto_scan_on_startup"):
            self.root.after(100, lambda: self._start_scan(reason="startup"))
        else:
            self._schedule_next_scan()
    
    def _setup_styles(self):
        """Configure ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('Card.TFrame', background=self.colors['card'])
        style.configure('Main.TFrame', background=self.colors['bg'])
        style.configure('Title.TLabel', 
                        font=('SF Pro Display', 24, 'bold'),
                        foreground=self.colors['text'],
                        background=self.colors['card'])
        style.configure('Subtitle.TLabel',
                        font=('SF Pro Text', 12),
                        foreground=self.colors['text_secondary'],
                        background=self.colors['card'])
        style.configure('Treeview',
                        font=('SF Pro Text', 12),
                        rowheight=35,
                        background=self.colors['card'],
                        fieldbackground=self.colors['card'])
        style.configure('Treeview.Heading',
                        font=('SF Pro Text', 12, 'bold'),
                        background=self.colors['bg'])
        style.configure('Accent.TButton',
                        font=('SF Pro Text', 12),
                        background=self.colors['accent'])
    
    def _create_widgets(self):
        """Create all UI widgets"""
        # Main container
        main_frame = ttk.Frame(self.root, style='Main.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Header
        header_frame = ttk.Frame(main_frame, style='Card.TFrame')
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        header_inner = ttk.Frame(header_frame, style='Card.TFrame')
        header_inner.pack(padx=20, pady=15)
        
        title_label = ttk.Label(header_inner, text="📦 包安装监控", style='Title.TLabel')
        title_label.pack(side=tk.LEFT)
        
        # Buttons in header
        btn_frame = ttk.Frame(header_inner, style='Card.TFrame')
        btn_frame.pack(side=tk.RIGHT)
        
        scan_btn = ttk.Button(btn_frame, text="🔄 立即扫描", command=self._start_scan)
        scan_btn.pack(side=tk.LEFT, padx=5)
        
        report_btn = ttk.Button(btn_frame, text="📊 生成报告", command=self._generate_report)
        report_btn.pack(side=tk.LEFT, padx=5)
        
        # Content area
        content_frame = ttk.Frame(main_frame, style='Main.TFrame')
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left sidebar - dates
        sidebar_frame = ttk.Frame(content_frame, style='Card.TFrame', width=200)
        sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        sidebar_frame.pack_propagate(False)
        
        sidebar_label = ttk.Label(sidebar_frame, text="📅 日期", style='Subtitle.TLabel')
        sidebar_label.pack(padx=15, pady=(15, 10), anchor=tk.W)
        
        # Date listbox
        self.date_listbox = tk.Listbox(sidebar_frame,
                                        font=('SF Pro Text', 12),
                                        selectbackground=self.colors['accent'],
                                        selectforeground='white',
                                        borderwidth=0,
                                        highlightthickness=0)
        self.date_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.date_listbox.bind('<<ListboxSelect>>', self._on_date_select)
        
        # Right content - packages
        right_frame = ttk.Frame(content_frame, style='Main.TFrame')
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Search bar
        search_frame = ttk.Frame(right_frame, style='Card.TFrame')
        search_frame.pack(fill=tk.X, pady=(0, 15))
        
        search_inner = ttk.Frame(search_frame, style='Card.TFrame')
        search_inner.pack(padx=15, pady=10)
        
        search_label = ttk.Label(search_inner, text="🔍", style='Subtitle.TLabel')
        search_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self._on_search)
        search_entry = ttk.Entry(search_inner, textvariable=self.search_var, font=('SF Pro Text', 12))
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Package table
        table_frame = ttk.Frame(right_frame, style='Card.TFrame')
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview
        columns = ('manager', 'name', 'version', 'time')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', style='Treeview')
        
        self.tree.heading('manager', text='包管理器')
        self.tree.heading('name', text='包名')
        self.tree.heading('version', text='版本')
        self.tree.heading('time', text='安装时间')
        
        self.tree.column('manager', width=100, anchor=tk.CENTER)
        self.tree.column('name', width=300, anchor=tk.W)
        self.tree.column('version', width=150, anchor=tk.CENTER)
        self.tree.column('time', width=150, anchor=tk.CENTER)
        
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        # Status bar
        status_frame = ttk.Frame(main_frame, style='Card.TFrame')
        status_frame.pack(fill=tk.X, pady=(15, 0))
        
        self.status_label = ttk.Label(status_frame, 
                                       text="就绪 | 上次扫描: 从未",
                                       style='Subtitle.TLabel')
        self.status_label.pack(padx=15, pady=10)
    
    def _load_data(self):
        """Load initial data"""
        # Load dates
        dates = self.storage.get_recent_dates(30)
        if not dates:
            dates = [self.selected_date]
        
        self.date_listbox.delete(0, tk.END)
        for date in dates:
            self.date_listbox.insert(tk.END, date)
        
        # Select first date
        if dates:
            self.date_listbox.select_set(0)
            self.selected_date = dates[0]
        
        # Load packages for selected date
        self._refresh_package_list()
        
        # Update status
        total = self.storage.get_total_count()
        last_scan_at = self.storage.get_last_scan_at() or "从未"
        self.status_label.config(text=f"就绪 | 新增安装记录: {total} | 上次扫描: {last_scan_at}")
    
    def _on_date_select(self, event):
        """Handle date selection"""
        selection = self.date_listbox.curselection()
        if selection:
            self.selected_date = self.date_listbox.get(selection[0])
            self._refresh_package_list()
    
    def _on_search(self, *args):
        """Handle search input"""
        self._refresh_package_list()
    
    def _refresh_package_list(self):
        """Refresh the package list"""
        # Clear current items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get packages
        query = self.search_var.get()
        if query:
            packages = self.storage.search_packages(query, self.selected_date)
        else:
            packages = self.storage.get_packages(self.selected_date)
        
        # Insert packages
        for pkg in packages:
            self.tree.insert('', tk.END, values=(
                pkg['manager'],
                pkg['name'],
                pkg['version'],
                pkg.get('time', '')
            ))
    
    def _get_scan_interval_ms(self):
        """Get scan interval in milliseconds, with a one-hour minimum."""
        try:
            hours = float(self.config.get("scan_interval_hours", 24))
        except (TypeError, ValueError):
            hours = 24

        if hours < 1:
            hours = 1

        return int(hours * 60 * 60 * 1000)

    def _schedule_next_scan(self):
        """Schedule the next periodic scan."""
        if self.next_scan_job is not None:
            self.root.after_cancel(self.next_scan_job)

        self.next_scan_job = self.root.after(
            self._get_scan_interval_ms(),
            self._run_scheduled_scan
        )

    def _run_scheduled_scan(self):
        """Run a scheduled scan or defer it if a scan is already active."""
        self.next_scan_job = None
        if self.is_scanning:
            self._schedule_next_scan()
            return

        self._start_scan(reason="scheduled")

    def _should_show_notifications(self):
        """Return whether completion message boxes should be shown."""
        return bool(self.config.get("show_notifications", True))

    def _start_scan(self, reason="manual"):
        """Start scanning packages in background"""
        if self.is_scanning:
            self.status_label.config(text="扫描已在进行中...")
            return

        self.is_scanning = True
        self.status_label.config(text="扫描中...")

        def scan_thread():
            try:
                packages = self.scanner_manager.scan_all()
                now = datetime.now()
                result = self.storage.record_scan(
                    now.strftime("%Y-%m-%d"),
                    packages,
                    now.strftime("%Y-%m-%d %H:%M")
                )
                self.root.after(0, self._on_scan_complete, result)
            except Exception as e:
                self.root.after(0, self._on_scan_error, e)
        
        thread = threading.Thread(target=scan_thread, daemon=True)
        thread.start()
    
    def _on_scan_complete(self, result):
        """Called when scan is complete"""
        self.is_scanning = False
        self._load_data()
        now = result.get("scanned_at", datetime.now().strftime("%Y-%m-%d %H:%M"))
        total = self.storage.get_total_count()
        count = result.get("new_count", 0)

        if result.get("is_initial_scan"):
            message = f"首次扫描已建立基线 | 已扫描: {result.get('scanned_count', 0)} 个包 | 时间: {now}"
            dialog_message = "首次扫描已建立基线，后续扫描将记录新增安装包"
        else:
            message = f"扫描完成 | 新增: {count} 个安装包 | 总计: {total} | 时间: {now}"
            dialog_message = f"发现 {count} 个新增安装包"

        self.status_label.config(text=message)
        if self._should_show_notifications():
            messagebox.showinfo("扫描完成", dialog_message)

        self._schedule_next_scan()

    def _on_scan_error(self, error):
        """Called when a scan fails."""
        self.is_scanning = False
        self.status_label.config(text=f"扫描失败: {error}")
        if self._should_show_notifications():
            messagebox.showerror("扫描失败", str(error))
        self._schedule_next_scan()
    
    def _generate_report(self):
        """Generate HTML report"""
        packages = self.storage.get_packages(self.selected_date)
        total_unique = self.storage.get_total_count()
        
        filepath = self.report_generator.generate(
            self.selected_date,
            packages,
            total_unique
        )
        
        # Open in browser
        import webbrowser
        webbrowser.open(f"file://{filepath}")
        
        self.status_label.config(text=f"报告已生成: {filepath}")
        if self._should_show_notifications():
            messagebox.showinfo("报告已生成", f"报告已保存到:\n{filepath}")
    
    def run(self):
        """Run the application"""
        self.root.mainloop()
