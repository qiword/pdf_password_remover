import os
from pathlib import Path
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from gui.widgets import CheckableListWidget
from core.pdf_worker import PDFProcessingWorker

class PDFPasswordRemover(QMainWindow):
    def __init__(self):
        super().__init__()
        self.all_pdf_files = []
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        self.setWindowTitle("移除PDF密码工具")
        self.setGeometry(100, 100, 1000, 750)
        self.setStyleSheet(self.get_stylesheet())
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        title_label = QLabel("移除PDF密码工具")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        main_layout.addWidget(self.create_file_selection_group())
        main_layout.addWidget(self.create_file_list_group())
        main_layout.addWidget(self.create_settings_group())
        main_layout.addWidget(self.create_progress_group())
        main_layout.addLayout(self.create_control_buttons())
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
    
    def get_stylesheet(self):
        return """
            QMainWindow { background-color: #f5f7fa; }
            QGroupBox { 
                font-weight: bold; 
                border: 2px solid #d1d9e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }
            QPushButton {
                background-color: #4a6fa5;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #3a5a80; }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QPushButton#scan_btn {
                background-color: #27ae60;
            }
            QPushButton#scan_btn:hover {
                background-color: #219653;
            }
            QLineEdit, QListWidget {
                border: 1px solid #d1d9e6;
                border-radius: 4px;
                padding: 5px;
            }
            QProgressBar {
                border: 1px solid #d1d9e6;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """
    
    def create_file_selection_group(self):
        group = QGroupBox("1. 选择文件或文件夹")
        layout = QVBoxLayout(group)
        
        btn_layout = QHBoxLayout()
        self.select_files_btn = QPushButton("📄 选择文件")
        self.select_files_btn.setToolTip("选择单个或多个PDF文件")
        self.select_folder_btn = QPushButton("📁 选择文件夹")
        self.select_folder_btn.setToolTip("扫描文件夹及其子文件夹中的PDF文件")
        self.select_folder_btn.setObjectName("scan_btn")
        self.scan_subfolders_cb = QCheckBox("包含子文件夹")
        self.scan_subfolders_cb.setChecked(True)
        
        btn_layout.addWidget(self.select_files_btn)
        btn_layout.addWidget(self.select_folder_btn)
        btn_layout.addWidget(self.scan_subfolders_cb)
        btn_layout.addStretch()
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("当前路径:"))
        self.current_path_label = QLabel("未选择")
        self.current_path_label.setStyleSheet("color: #666; font-style: italic;")
        path_layout.addWidget(self.current_path_label)
        path_layout.addStretch()
        
        info_layout = QHBoxLayout()
        self.file_count_label = QLabel("已选择: 0 个文件")
        self.selected_count_label = QLabel("已勾选: 0 个文件")
        info_layout.addWidget(self.file_count_label)
        info_layout.addWidget(self.selected_count_label)
        info_layout.addStretch()
        
        layout.addLayout(btn_layout)
        layout.addLayout(path_layout)
        layout.addLayout(info_layout)
        return group
    
    def create_file_list_group(self):
        group = QGroupBox("2. 文件列表 (可勾选需要处理的文件)")
        layout = QVBoxLayout(group)
        
        control_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("✅ 全选")
        self.unselect_all_btn = QPushButton("❌ 全不选")
        self.invert_select_btn = QPushButton("🔄 反选")
        self.clear_list_btn = QPushButton("🗑️ 清空列表")
        
        control_layout.addWidget(self.select_all_btn)
        control_layout.addWidget(self.unselect_all_btn)
        control_layout.addWidget(self.invert_select_btn)
        control_layout.addWidget(self.clear_list_btn)
        control_layout.addStretch()
        
        self.file_list_widget = CheckableListWidget()
        self.file_list_widget.setAlternatingRowColors(True)
        
        layout.addLayout(control_layout)
        layout.addWidget(self.file_list_widget)
        return group
    
    def create_settings_group(self):
        group = QGroupBox("3. 设置")
        layout = QGridLayout(group)
        
        layout.addWidget(QLabel("密码类型:"), 0, 0)
        self.password_type_combo = QComboBox()
        self.password_type_combo.addItems(["打开密码", "只读密码锁（权限密码）", "两种密码都尝试"])
        layout.addWidget(self.password_type_combo, 0, 1, 1, 2)
        
        layout.addWidget(QLabel("密码:"), 1, 0)
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("请输入PDF密码")
        layout.addWidget(self.password_edit, 1, 1)
        
        self.show_password_cb = QCheckBox("显示密码")
        self.show_password_cb.stateChanged.connect(self.toggle_password_visibility)
        layout.addWidget(self.show_password_cb, 1, 2)
        
        layout.addWidget(QLabel("输出文件夹:"), 2, 0)
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setText(str(Path.home() / "Unlocked_PDFs"))
        layout.addWidget(self.output_path_edit, 2, 1)
        
        self.browse_output_btn = QPushButton("浏览")
        layout.addWidget(self.browse_output_btn, 2, 2)
        
        layout.addWidget(QLabel("文件名前缀:"), 3, 0)
        self.prefix_edit = QLineEdit()
        self.prefix_edit.setText("unlocked_")
        layout.addWidget(self.prefix_edit, 3, 1)
        
        self.skip_unencrypted_cb = QCheckBox("自动跳过无密码文件")
        self.skip_unencrypted_cb.setChecked(True)
        layout.addWidget(self.skip_unencrypted_cb, 4, 0, 1, 2)
        
        self.preserve_restrictions_cb = QCheckBox("保留原始权限设置")
        self.preserve_restrictions_cb.setChecked(False)
        self.preserve_restrictions_cb.setToolTip("移除密码后仍保留原有的打印、复制等限制")
        layout.addWidget(self.preserve_restrictions_cb, 4, 2)
        
        self.generate_summary_cb = QCheckBox("生成已解锁文件清单")
        self.generate_summary_cb.setChecked(True)
        self.generate_summary_cb.setToolTip("在处理完成后生成一个清单文件")
        layout.addWidget(self.generate_summary_cb, 5, 0, 1, 3)
        
        return group
    
    def create_progress_group(self):
        group = QGroupBox("4. 处理进度")
        layout = QVBoxLayout(group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(120)
        self.log_text.setStyleSheet("""
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 11px;
            background-color: #f8f9fa;
        """)
        layout.addWidget(self.log_text)
        
        return group
    
    def create_control_buttons(self):
        layout = QHBoxLayout()
        
        self.start_btn = QPushButton("▶️ 开始处理")
        self.start_btn.setMinimumHeight(45)
        self.start_btn.setStyleSheet("""
            font-size: 16px;
            background-color: #27ae60;
        """)
        
        self.stop_btn = QPushButton("⏹️ 停止")
        self.stop_btn.setMinimumHeight(45)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            font-size: 16px;
            background-color: #e74c3c;
        """)
        
        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)
        layout.addStretch()
        
        return layout
    
    def setup_connections(self):
        self.select_files_btn.clicked.connect(self.select_files)
        self.select_folder_btn.clicked.connect(self.select_folder)
        self.select_all_btn.clicked.connect(lambda: self.file_list_widget.select_all(True))
        self.unselect_all_btn.clicked.connect(lambda: self.file_list_widget.select_all(False))
        self.invert_select_btn.clicked.connect(self.file_list_widget.invert_selection)
        self.clear_list_btn.clicked.connect(self.clear_file_list)
        self.file_list_widget.itemChanged.connect(self.update_selection_count)
        self.browse_output_btn.clicked.connect(self.browse_output_path)
        self.start_btn.clicked.connect(self.start_processing)
        self.stop_btn.clicked.connect(self.stop_processing)
    
    def toggle_password_visibility(self, state):
        self.password_edit.setEchoMode(QLineEdit.Normal if state == Qt.Checked else QLineEdit.Password)
    
    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择PDF文件", str(Path.home()), 
            "PDF文件 (*.pdf);;所有文件 (*.*)"
        )
        if files:
            self.add_files_to_list(files)
            self.current_path_label.setText(f"已选择 {len(files)} 个文件")
    
    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹", str(Path.home()))
        if folder:
            self.current_path_label.setText(folder)
            output_path = Path(folder) / "Unlocked_PDFs"
            self.output_path_edit.setText(str(output_path))
            self.scan_pdf_files(folder)
    
    def scan_pdf_files(self, folder_path):
        include_subfolders = self.scan_subfolders_cb.isChecked()
        output_path = Path(folder_path) / "Unlocked_PDFs"
        self.log(f"开始扫描文件夹: {folder_path}")
        self.log(f"输出路径已自动设置为: {output_path}")
        
        try:
            pdf_files = []
            if include_subfolders:
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        if file.lower().endswith('.pdf'):
                            pdf_files.append(os.path.join(root, file))
            else:
                for file in os.listdir(folder_path):
                    if file.lower().endswith('.pdf'):
                        pdf_files.append(os.path.join(folder_path, file))
            
            if pdf_files:
                self.add_files_to_list(pdf_files)
                self.log(f"扫描完成，找到 {len(pdf_files)} 个PDF文件")
            else:
                self.log("未找到PDF文件")
                QMessageBox.information(self, "扫描结果", "该文件夹中未找到PDF文件")
                
        except Exception as e:
            self.log(f"扫描错误: {str(e)}")
            QMessageBox.critical(self, "扫描错误", f"扫描文件夹时出错:\n{str(e)}")
    
    def add_files_to_list(self, files):
        added_count = 0
        existing_files = self.get_all_files_in_list()
        
        for file_path in files:
            if file_path not in existing_files:
                file_name = os.path.basename(file_path)
                self.file_list_widget.add_checkable_item(f"📄 {file_name}", file_path)
                self.all_pdf_files.append(file_path)
                added_count += 1
        
        self.update_file_count()
        
        if added_count > 0:
            self.status_bar.showMessage(f"添加了 {added_count} 个新文件")
            self.log(f"添加了 {added_count} 个文件到列表")
    
    def get_all_files_in_list(self):
        files = []
        for i in range(self.file_list_widget.count()):
            item = self.file_list_widget.item(i)
            files.append(item.data(Qt.UserRole))
        return files
    
    def update_file_count(self):
        total = self.file_list_widget.count()
        checked = len(self.file_list_widget.get_checked_files())
        self.file_count_label.setText(f"已选择: {total} 个文件")
        self.selected_count_label.setText(f"已勾选: {checked} 个文件")
    
    def update_selection_count(self):
        checked = len(self.file_list_widget.get_checked_files())
        self.selected_count_label.setText(f"已勾选: {checked} 个文件")
    
    def clear_file_list(self):
        if self.file_list_widget.count() > 0:
            reply = QMessageBox.question(
                self, "确认清空", "确定要清空所有文件吗？", 
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.file_list_widget.clear()
                self.all_pdf_files.clear()
                self.update_file_count()
                self.current_path_label.setText("未选择")
                self.status_bar.showMessage("文件列表已清空")
                self.log("文件列表已清空")
    
    def browse_output_path(self):
        path = QFileDialog.getExistingDirectory(
            self, "选择输出文件夹", self.output_path_edit.text()
        )
        if path:
            self.output_path_edit.setText(path)
    
    def log(self, message):
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
        self.log_text.append(f"[{timestamp}] {message}")
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
    
    def validate_inputs(self):
        if not self.file_list_widget.get_checked_files():
            QMessageBox.warning(self, "警告", "请先勾选要处理的文件")
            return False
        if not self.password_edit.text().strip():
            QMessageBox.warning(self, "警告", "请输入PDF密码")
            return False
        return True
    
    def start_processing(self):
        if not self.validate_inputs():
            return
        
        output_path = Path(self.output_path_edit.text())
        try:
            output_path.mkdir(parents=True, exist_ok=True)
            self.log(f"输出目录: {output_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法创建输出目录:\n{str(e)}")
            return
        
        self.set_processing_state(True)
        files_to_process = self.file_list_widget.get_checked_files()
        
        self.worker = PDFProcessingWorker(
            files_to_process,
            self.password_edit.text(),
            self.output_path_edit.text(),
            self.prefix_edit.text(),
            self.skip_unencrypted_cb.isChecked(),
            self.password_type_combo.currentText(),
            self.preserve_restrictions_cb.isChecked(),
            self.generate_summary_cb.isChecked()
        )
        
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.file_processed.connect(self.file_processed)
        self.worker.processing_finished.connect(self.processing_finished)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.summary_generated.connect(self.on_summary_generated)
        self.worker.start()
    
    def set_processing_state(self, processing):
        self.select_files_btn.setEnabled(not processing)
        self.select_folder_btn.setEnabled(not processing)
        self.start_btn.setEnabled(not processing)
        self.stop_btn.setEnabled(processing)
        self.password_edit.setReadOnly(processing)
        if not processing:
            self.progress_bar.setValue(0)
    
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    
    def file_processed(self, filename, success, message):
        status_icon = "✓" if success else "✗"
        self.log(f"{status_icon} {filename} - {message}")
    
    def on_summary_generated(self, summary_file):
        if summary_file:
            self.log(f"📋 已生成文件清单: {summary_file}")
            self.status_bar.showMessage(f"清单已生成: {os.path.basename(summary_file)}")
    
    def processing_finished(self):
        self.set_processing_state(False)
        self.status_bar.showMessage("处理完成")
        self.log("=" * 50)
        self.log("所有文件处理完成！")
        
        output_path = Path(self.output_path_edit.text())
        summary_file = output_path / "已解锁文件清单.txt"
        
        message = f"PDF文件处理完成！\n输出目录: {self.output_path_edit.text()}"
        if summary_file.exists():
            message += f"\n\n已生成文件清单:\n{summary_file}"
        
        QMessageBox.information(self, "完成", message)
    
    def handle_error(self, error_msg):
        self.log(f"⚠️ 错误: {error_msg}")
        QMessageBox.critical(self, "处理错误", error_msg)
    
    def stop_processing(self):
        if hasattr(self, 'worker') and self.worker.isRunning():
            reply = QMessageBox.question(
                self, "确认停止", "确定要停止正在进行的处理吗？", 
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.worker.stop()
                self.set_processing_state(False)
                self.log("用户停止了处理")
                self.status_bar.showMessage("已停止")