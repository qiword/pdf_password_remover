import os
import shutil
from pathlib import Path
from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal
import pikepdf

class PDFProcessingWorker(QThread):
    progress_updated = pyqtSignal(int)
    file_processed = pyqtSignal(str, bool, str)
    processing_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    summary_generated = pyqtSignal(str)
    
    def __init__(self, file_paths, password, output_dir, prefix, 
                 skip_unencrypted=True, password_type="打开密码", 
                 preserve_restrictions=False, generate_summary=True):
        super().__init__()
        self.file_paths = file_paths
        self.password = password
        self.output_dir = Path(output_dir)
        self.prefix = prefix
        self.skip_unencrypted = skip_unencrypted
        self.password_type = password_type
        self.preserve_restrictions = preserve_restrictions
        self.generate_summary = generate_summary
        self.processing_results = []
        self._is_running = True
    
    def run(self):
        total_files = len(self.file_paths)
        
        for i, file_path in enumerate(self.file_paths):
            if not self._is_running:
                break
                
            filename = os.path.basename(file_path)
            success, message, output_file = self.process_file(file_path, filename)
            
            result = {
                'original_file': filename,
                'output_file': output_file,
                'success': success,
                'message': message,
                'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.processing_results.append(result)
            
            self.file_processed.emit(filename, success, message)
            self.progress_updated.emit(int((i + 1) / total_files * 100))
            self.msleep(50)
        
        if self.generate_summary and self.processing_results:
            summary_file = self.generate_summary_file()
            if summary_file:
                self.summary_generated.emit(summary_file)
        
        self.processing_finished.emit()
    
    def process_file(self, file_path, filename):
        try:
            if not self.is_encrypted(file_path):
                return self.process_unencrypted(file_path, filename)
            else:
                return self.process_encrypted(file_path, filename)
        except Exception as e:
            self.error_occurred.emit(f"处理 {filename} 时出错: {str(e)}")
            return False, f"处理错误: {str(e)}", "未生成"
    
    def is_encrypted(self, file_path):
        try:
            with pikepdf.open(file_path, allow_overwriting_input=False) as pdf:
                return hasattr(pdf, 'trailer') and '/Encrypt' in pdf.trailer
        except pikepdf.PasswordError:
            return True
        except Exception:
            return False
    
    def process_unencrypted(self, file_path, filename):
        if self.skip_unencrypted:
            return True, "文件未加密，已跳过", "未生成"
        
        output_filename = f"{self.prefix}{filename}"
        output_path = self.output_dir / output_filename
        try:
            shutil.copy2(file_path, output_path)
            return True, "文件未加密，已复制", output_filename
        except Exception as e:
            return False, f"复制失败: {str(e)}", "未生成"
    
    def process_encrypted(self, file_path, filename):
        password_types = self.get_password_types()
        
        for pwd_type in password_types:
            try:
                pdf = pikepdf.open(file_path, password=self.password, 
                                  allow_overwriting_input=False)
                
                output_filename = f"{self.prefix}{filename}"
                output_path = self.output_dir / output_filename
                pdf.save(output_path)
                pdf.close()
                
                message_type = "打开密码" if pwd_type == "user" else "权限密码"
                return True, f"{message_type}已移除", output_filename
                
            except pikepdf.PasswordError:
                continue
            except Exception as e:
                return False, f"处理错误: {str(e)}", "未生成"
        
        return self.get_failure_message()
    
    def get_password_types(self):
        if self.password_type == "打开密码":
            return ["user"]
        elif self.password_type == "只读密码锁（权限密码）":
            return ["owner"]
        return ["user", "owner"]
    
    def get_failure_message(self):
        if self.password_type == "打开密码":
            return False, "打开密码错误", "未生成"
        elif self.password_type == "只读密码锁（权限密码）":
            return False, "权限密码错误", "未生成"
        return False, "打开密码和权限密码都错误", "未生成"
    
    def generate_summary_file(self):
        try:
            summary_path = self.output_dir / "已解锁文件清单.txt"
            
            with open(summary_path, 'w', encoding='utf-8') as f:
                self.write_summary_header(f)
                self.write_statistics(f)
                self.write_file_details(f)
                self.write_failed_files(f)
                f.write("=" * 60 + "\n")
                f.write("处理完成！\n")
                f.write("=" * 60 + "\n")
            
            return str(summary_path)
        except Exception as e:
            self.error_occurred.emit(f"生成清单文件时出错: {str(e)}")
            return None
    
    def write_summary_header(self, file):
        file.write("=" * 60 + "\n")
        file.write("移除PDF密码工具 - 处理结果清单\n")
        file.write("=" * 60 + "\n\n")
        file.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        file.write(f"输出目录: {self.output_dir}\n")
        file.write(f"处理文件总数: {len(self.processing_results)}\n")
        file.write(f"密码类型: {self.password_type}\n\n")
    
    def write_statistics(self, file):
        successful = sum(1 for r in self.processing_results if r['success'])
        failed = len(self.processing_results) - successful
        skipped = sum(1 for r in self.processing_results if "已跳过" in r['message'])
        
        file.write("📊 处理统计:\n")
        file.write(f"  成功处理: {successful} 个文件\n")
        file.write(f"  处理失败: {failed} 个文件\n")
        file.write(f"  跳过文件: {skipped} 个文件\n")
        file.write("-" * 60 + "\n\n")
    
    def write_file_details(self, file):
        file.write("📁 文件处理详情:\n\n")
        
        for i, result in enumerate(self.processing_results, 1):
            status = self.get_status_icon(result)
            file.write(f"{i}. {result['original_file']}\n")
            file.write(f"   状态: {status}\n")
            file.write(f"   结果: {result['message']}\n")
            if result['output_file'] != "未生成":
                file.write(f"   输出文件: {result['output_file']}\n")
            file.write(f"   文件大小: {self.format_file_size(result['file_size'])}\n")
            file.write(f"   处理时间: {result['timestamp']}\n\n")
    
    def get_status_icon(self, result):
        if "已跳过" in result['message']:
            return "⏭️ 跳过"
        return "✅ 成功" if result['success'] else "❌ 失败"
    
    def write_failed_files(self, file):
        failed_files = [
            r for r in self.processing_results 
            if not r['success'] and "已跳过" not in r['message']
        ]
        
        if failed_files:
            file.write("⚠️ 失败文件列表:\n")
            for fail in failed_files:
                file.write(f"   - {fail['original_file']}: {fail['message']}\n")
            file.write("\n")
    
    def format_file_size(self, size_bytes):
        if size_bytes == 0:
            return "0 B"
        
        size_names = ("B", "KB", "MB", "GB")
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024
            i += 1
        return f"{size_bytes:.2f} {size_names[i]}"
    
    def stop(self):
        self._is_running = False