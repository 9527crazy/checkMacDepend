"""
GUI Interface using tkinter
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
from typing import List, Dict, Callable
import threading


class PackageMonitorUI:
    """Main GUI Application"""
    
    def __init__(self, scanner_manager, storage, report_generator, config):
        self.scanner_manager = scanner_manager
        self.storage = storage
        self.report_generator = report_generator
        self.config = config
        
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
        self.status_label.config(text=f"就绪 | 总包数: {total} | 上次扫描: 从未")
    
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
    
    def _start_scan(self):
        """Start scanning packages in background"""
        def scan_thread():
            self.status_label.config(text="扫描中...")
            
            packages = self.scanner_manager.scan_all()
            
            if packages:
                self.storage.add_packages(self.selected_date, packages)
            
            # Update UI in main thread
            self.root.after(0, self._on_scan_complete, len(packages))
        
        thread = threading.Thread(target=scan_thread, daemon=True)
        thread.start()
    
    def _on_scan_complete(self, count):
        """Called when scan is complete"""
        self._load_data()
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        total = self.storage.get_total_count()
        self.status_label.config(text=f"扫描完成 | 本次: {count} 个包 | 总计: {total} | 时间: {now}")
        messagebox.showinfo("扫描完成", f"发现 {count} 个已安装的包")
    
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
        
        messagebox.showinfo("报告已生成", f"报告已保存到:\n{filepath}")
    
    def run(self):
        """Run the application"""
        self.root.mainloop()
