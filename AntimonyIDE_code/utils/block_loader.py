import json
import os
import glob


class BlockLoader:
    def __init__(self):
        self.available_blocks = self.load_default_blocks()
        self.custom_blocks_file = "custom_blocks.json"
        self.custom_package_paths = []  # 存储包路径
        self.load_custom_blocks()

    def load_default_blocks(self):
        """Load default code blocks with corrected types"""
        blocks = {
            "Statements": [
                {"type": "statement", "text": "Print", "content": "print({value})", "template": "print({value})",
                 "description": "Output text to console."},
                {"type": "statement", "text": "Assign", "content": "{var} = {value}", "template": "{var} = {value}",
                 "description": "Assign a value to a variable."},
                {"type": "statement", "text": "Return", "content": "return {value}", "template": "return {value}",
                 "description": "Return a value from a function."},
                {"type": "statement", "text": "Pass", "content": "pass", "template": "pass",
                 "description": "Do nothing. Used as a placeholder."},
                {"type": "statement", "text": "Break", "content": "break", "template": "break",
                 "description": "Exit a loop immediately."},
                {"type": "statement", "text": "Continue", "content": "continue", "template": "continue",
                 "description": "Skip to the next iteration of a loop."},
            ],
            "Control Flow": [
                {"type": "control", "text": "If", "content": "if {condition}:", "template": "if {condition}:",
                 "description": "Conditional statement. Executes code if condition is True."},
                {"type": "control", "text": "Else", "content": "else:", "template": "else:",
                 "description": "Optional part of if statement. Executes when if condition is False."},
                {"type": "control", "text": "Elif", "content": "elif {condition}:", "template": "elif {condition}:",
                 "description": "Else-if statement. Checks another condition if previous if/elif was False."},
            ],
            "Loops": [
                {"type": "loop", "text": "For Loop", "content": "for {item} in {iterable}:",
                 "template": "for {item} in {iterable}:",
                 "description": "Loop through items in a sequence."},
                {"type": "loop", "text": "While Loop", "content": "while {condition}:",
                 "template": "while {condition}:",
                 "description": "Loop while condition is True."},
            ],
            "Functions": [
                # CHANGED: "Define Function" is now type "defining" instead of "function"
                {"type": "defining", "text": "Define Function", "content": "def {name}({params}):",
                 "template": "def {name}({params}):",
                 "description": "Define a new function. Set an End Block for the function body."},
                # These remain type "function" and don't need indentation
                {"type": "function", "text": "Call Function", "content": "{name}({args})", "template": "{name}({args})",
                 "description": "Call (execute) a function."},
                {"type": "function", "text": "Lambda", "content": "lambda {params}: {expression}",
                 "template": "lambda {params}: {expression}",
                 "description": "Create a small anonymous function."},
            ],
            "I/O": [
                {"type": "io", "text": "Input", "content": "input({prompt})", "template": "input({prompt})",
                 "description": "Get user input from keyboard."},
                {"type": "io", "text": "Open File", "content": "open({filename}, {mode})",
                 "template": "open({filename}, {mode})",
                 "description": "Open a file. Modes: 'r' (read), 'w' (write), 'a' (append)."},
            ],
            "Variables": [
                {"type": "variable", "text": "Integer", "content": "int({value})", "template": "int({value})",
                 "description": "Convert value to integer."},
                {"type": "variable", "text": "Float", "content": "float({value})", "template": "float({value})",
                 "description": "Convert value to floating-point number."},
                {"type": "variable", "text": "String", "content": "str({value})", "template": "str({value})",
                 "description": "Convert value to string."},
                {"type": "variable", "text": "List", "content": "list({iterable})", "template": "list({iterable})",
                 "description": "Create a list from an iterable."},
                {"type": "variable", "text": "Dict", "content": "dict({mapping})", "template": "dict({mapping})",
                 "description": "Create a dictionary."},
            ],
            "Operators": [
                {"type": "operator", "text": "Add (+)", "content": "{a} + {b}", "template": "{a} + {b}",
                 "description": "Add two values."},
                {"type": "operator", "text": "Subtract (-)", "content": "{a} - {b}", "template": "{a} - {b}",
                 "description": "Subtract b from a."},
                {"type": "operator", "text": "Multiply (*)", "content": "{a} * {b}", "template": "{a} * {b}",
                 "description": "Multiply two values."},
                {"type": "operator", "text": "Divide (/)", "content": "{a} / {b}", "template": "{a} / {b}",
                 "description": "Divide a by b."},
                {"type": "operator", "text": "Equal (==)", "content": "{a} == {b}", "template": "{a} == {b}",
                 "description": "Check if two values are equal."},
            ],
            "Imports": [
                {"type": "import", "text": "Import", "content": "import {module}", "template": "import {module}",
                 "description": "Import an entire module."},
                {"type": "import", "text": "From Import", "content": "from {module} import {name}",
                 "template": "from {module} import {name}",
                 "description": "Import specific names from a module."},
            ],
            "GUI Components": [
                {"type": "gui", "text": "Tkinter Window",
                 "content": "root = tk.Tk()\nroot.title(\"{title}\")\nroot.geometry(\"{size}\")",
                 "template": "root = tk.Tk()",
                 "description": "Create main Tkinter window."},
                {"type": "class", "text": "Define Class",
                 "content": "class {ClassName}:\n    def __init__(self, root):\n        self.root = root",
                 "template": "class {ClassName}:",
                 "description": "Define a new class. Set an End Block for class body."},
                {"type": "method", "text": "Define Method", "content": "def {method_name}(self{params}):\n    {body}",
                 "template": "def {method_name}(self):",
                 "description": "Define a method in a class. Set an End Block for method body."},
            ]
        }
        return blocks

    def load_package_file(self, file_path, category_name=None):
        """Load a single package JSON file"""
        try:
            with open(file_path, 'r') as f:
                package_data = json.load(f)

            # If category_name not provided, use filename
            if not category_name:
                category_name = os.path.basename(file_path).replace('.json', '')

            # Process the package data
            added_count = 0

            # Package JSON can have different structures:
            # Option 1: Direct list of blocks
            # Option 2: Dictionary with category as key
            if isinstance(package_data, dict):
                # If it's a dict, each key is a category
                for category, blocks in package_data.items():
                    if isinstance(blocks, list):
                        # Use the provided category name or the dict key
                        use_category = category_name if category == list(package_data.keys())[0] else category

                        # Add to available blocks
                        if use_category not in self.available_blocks:
                            self.available_blocks[use_category] = []

                        # Check for duplicates
                        existing_block_texts = [b["text"] for b in self.available_blocks[use_category]]
                        for block in blocks:
                            if block.get("text") not in existing_block_texts:
                                self.available_blocks[use_category].append(block)
                                added_count += 1
            elif isinstance(package_data, list):
                # If it's a list, use the provided category name
                if category_name not in self.available_blocks:
                    self.available_blocks[category_name] = []

                # Check for duplicates
                existing_block_texts = [b["text"] for b in self.available_blocks[category_name]]
                for block in package_data:
                    if block.get("text") not in existing_block_texts:
                        self.available_blocks[category_name].append(block)
                        added_count += 1

            return added_count, category_name

        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            raise Exception(f"Error loading package: {str(e)}")

    def load_all_packages(self, packages_dir="packages"):
        """Load all package files from a directory (for backward compatibility)"""
        total_added = 0
        if os.path.exists(packages_dir):
            for package_file in glob.glob(os.path.join(packages_dir, "*.json")):
                try:
                    added, _ = self.load_package_file(package_file)
                    total_added += added
                    print(f"Loaded package: {os.path.basename(package_file)}")
                except Exception as e:
                    print(f"Error loading package {package_file}: {e}")
        return total_added

    def load_custom_blocks(self):
        """Load custom blocks from file - 改进2: 只保存包路径"""
        if os.path.exists(self.custom_blocks_file):
            try:
                with open(self.custom_blocks_file, 'r') as f:
                    saved_data = json.load(f)
                
                # 检查是新格式(只包含路径)还是旧格式(包含完整块数据)
                if isinstance(saved_data, dict) and "package_paths" in saved_data:
                    # 新格式: 只包含包路径
                    self.custom_package_paths = saved_data.get("package_paths", [])
                    
                    # 加载每个包
                    for package_path in self.custom_package_paths:
                        if os.path.exists(package_path):
                            try:
                                self.load_package_file(package_path)
                            except Exception as e:
                                print(f"Error loading custom package {package_path}: {e}")
                        else:
                            print(f"Custom package not found: {package_path}")
                else:
                    # 旧格式: 包含完整块数据，转换为新格式
                    print("Converting old custom blocks format to new format...")
                    # 这里可以添加转换逻辑，但为了简单起见，我们只清空旧数据
                    self.custom_package_paths = []
                    
            except Exception as e:
                print(f"Error loading custom blocks: {e}")
                self.custom_package_paths = []

    def save_custom_blocks(self):
        """Save custom blocks to file - 改进2: 只保存包路径"""
        try:
            # 只保存包路径，而不是完整的块数据
            save_data = {
                "package_paths": self.custom_package_paths,
                "version": "1.0"  # 添加版本标识
            }
            
            with open(self.custom_blocks_file, 'w') as f:
                json.dump(save_data, f, indent=2)
        except Exception as e:
            print(f"Error saving custom blocks: {e}")

    def add_custom_package(self, file_path, category_name=None):
        """添加自定义包并保存路径"""
        # 检查路径是否已存在
        if file_path in self.custom_package_paths:
            # 包已存在，重新加载
            print(f"Package already exists: {file_path}, reloading...")
            # 可以先移除旧的，然后重新加载
            self.custom_package_paths.remove(file_path)
        
        # 加载包
        added_count, actual_category = self.load_package_file(file_path, category_name)
        
        if added_count > 0:
            # 添加路径到列表
            self.custom_package_paths.append(file_path)
            # 保存更新后的路径列表
            self.save_custom_blocks()
        
        return added_count, actual_category
