import json
import os
import sys

class LanguageManager:
    def __init__(self, default_lang='en'):
        self.languages = {}
        self.current_lang = default_lang
        
        # 获取应用运行路径（处理打包后路径）
        if getattr(sys, 'frozen', False):
            # 如果是打包后的exe
            self.base_path = sys._MEIPASS
        else:
            # 如果是开发环境
            self.base_path = os.path.dirname(os.path.abspath(__file__))
            
        self.load_languages()
    
    def load_languages(self):
        """加载所有语言文件"""
        # 首先尝试从当前目录查找
        lang_dirs = [
            os.path.join(self.base_path, "language"),  # 打包后的路径
            os.path.join(os.getcwd(), "language"),     # 当前工作目录
            "language",                                # 相对路径
        ]
        
        lang_dir = None
        for dir_path in lang_dirs:
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                lang_dir = dir_path
                break
        
        if not lang_dir:
            # 创建语言目录
            lang_dir = "language"
            if not os.path.exists(lang_dir):
                os.makedirs(lang_dir)
            # 创建示例语言文件
            self.create_example_languages()
            lang_dir = "language"
        
        for file in os.listdir(lang_dir):
            if file.endswith('.json'):
                lang_code = file.replace('.json', '')
                try:
                    with open(os.path.join(lang_dir, file), 'r', encoding='utf-8') as f:
                        self.languages[lang_code] = json.load(f)
                except Exception as e:
                    print(f"Error loading language {lang_code}: {e}")
    
    def create_example_languages(self):
        """Create example English and Chinese language files"""
        en_translations = {
            "app_title": "Antimony IDE",
            "project": "Project",
            "new_project": "New Project",
            "import": "Import",
            "save": "Save",
            "export": "Export",
            "load_python": "Load Python",
            "help": "Help",
            "gui_builder": "GUI Builder",
            "code_blocks": "Code Blocks",
            "category": "Category:",
            "import_package": "Import Package",
            "drag_to_canvas": "Double-click or drag to canvas",
            "workspace": "Workspace",
            "block_editor": "Block Editor",
            "select_block": "Select a block to edit",
            "content": "Content:",
            "update": "Update",
            "color": "Color:",
            "choose": "Choose",
            "connections": "Connections:",
            "connect_sequence": "Connect Sequence (Ctrl+A)",
            "disconnect_sequence": "Disconnect Sequence (Ctrl+A)",
            "set_end_block": "Set End Block (Ctrl+X)",
            "disconnect_end": "Disconnect End (Ctrl+X)",
            "continue_line": "Continue Line (Ctrl+W)",
            "discontinue_line": "Discontinue Line (Ctrl+W)",
            "current_connections": "Current Connections:",
            "delete_block": "Delete Block",
            "sequence_to": "Sequence to:",
            "end_block": "End Block:",
            "continue_to": "Continue to:",
            "edit_project_name": "Edit Project Name",
            "enter_new_name": "Enter new project name:",
            "save_project": "Save Project",
            "import_project": "Import Project",
            "export_python": "Export Python",
            "run_code": "Run Code",
            "select_language": "Select Language",
            "english": "English",
            "chinese": "Chinese",
            "blocks_all": "All",
            "blocks_statements": "Statements",
            "blocks_control": "Control Flow",
            "blocks_loops": "Loops",
            "blocks_functions": "Functions",
            "blocks_io": "I/O",
            "blocks_variables": "Variables",
            "blocks_operators": "Operators",
            "blocks_imports": "Imports",
            "blocks_gui": "GUI Components",
            "untitled_project": "Untitled Project"
        }
        
        zh_translations = {
            "app_title": "Antimony 集成开发环境",
            "project": "项目",
            "new_project": "新建项目",
            "import": "导入",
            "save": "保存",
            "export": "导出",
            "load_python": "加载Python",
            "help": "帮助",
            "gui_builder": "GUI构建器",
            "code_blocks": "代码块",
            "category": "类别：",
            "import_package": "导入包",
            "drag_to_canvas": "双击或拖动到画布",
            "workspace": "工作区",
            "block_editor": "块编辑器",
            "select_block": "选择一个块进行编辑",
            "content": "内容：",
            "update": "更新",
            "color": "颜色：",
            "choose": "选择",
            "connections": "连接：",
            "connect_sequence": "连接序列 (Ctrl+A)",
            "disconnect_sequence": "断开序列连接 (Ctrl+A)",
            "set_end_block": "设置结束块 (Ctrl+X)",
            "disconnect_end": "断开结束连接 (Ctrl+X)",
            "continue_line": "继续行 (Ctrl+W)",
            "discontinue_line": "断开继续连接 (Ctrl+W)",
            "current_connections": "当前连接：",
            "delete_block": "删除块",
            "sequence_to": "序列到：",
            "end_block": "结束块：",
            "continue_to": "继续到：",
            "edit_project_name": "编辑项目名称",
            "enter_new_name": "输入新项目名称：",
            "save_project": "保存项目",
            "import_project": "导入项目",
            "export_python": "导出Python",
            "run_code": "运行代码",
            "select_language": "选择语言",
            "english": "英文",
            "chinese": "中文",
            "blocks_all": "全部",
            "blocks_statements": "语句",
            "blocks_control": "控制流程",
            "blocks_loops": "循环",
            "blocks_functions": "函数",
            "blocks_io": "输入/输出",
            "blocks_variables": "变量",
            "blocks_operators": "运算符",
            "blocks_imports": "导入",
            "blocks_gui": "GUI组件",
            "untitled_project": "未命名项目"
        }
        
        # Save language files
        lang_dir = "language"
        with open(os.path.join(lang_dir, 'en.json'), 'w', encoding='utf-8') as f:
            json.dump(en_translations, f, ensure_ascii=False, indent=2)
        with open(os.path.join(lang_dir, 'zh.json'), 'w', encoding='utf-8') as f:
            json.dump(zh_translations, f, ensure_ascii=False, indent=2)
    
    def set_language(self, lang_code):
        """Change current language"""
        if lang_code in self.languages:
            self.current_lang = lang_code
            return True
        return False
    
    def get(self, key, default=None):
        """Get translation for key"""
        if self.current_lang in self.languages:
            return self.languages[self.current_lang].get(key, default or key)
        return default or key
    
    def get_all_languages(self):
        """Return list of available language codes"""
        return list(self.languages.keys())
