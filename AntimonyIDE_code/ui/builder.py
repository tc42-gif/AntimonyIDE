import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, colorchooser
import json
import os
import subprocess
import sys
import glob
import time
import importlib
import inspect
import threading  # 添加threading用于后台运行脚本

# Import from our packages
from core.code_block import CodeBlock
from core.parser import PythonFileParser
from core.language_manager import LanguageManager
from ui.components import create_top_section, create_left_section, create_middle_section, create_right_section
from utils.block_loader import BlockLoader
from utils.file_handler import FileHandler


class ScratchPythonBuilder:
    def __init__(self, root):
        self.root = root
        self.lang = LanguageManager()  # Initialize language manager
        
        # Set app title with translation
        self.root.title(self.lang.get("app_title"))
        self.root.geometry("1400x800")
        
        self.project_name = self.lang.get("untitled_project")
        self.blocks = {}
        self.block_counter = 0
        self.selected_block_id = None
        self.dragging_block = None
        self.connecting_mode = False
        self.end_connecting_mode = False
        self.continue_connecting_mode = False
        self.start_connection_block = None
        self.current_category = self.lang.get("blocks_all")
        
        # Connection lines
        self.sequence_lines = []
        self.end_lines = []
        self.continue_lines = []
        
        # UI state variables
        self.dragging_from_list = False
        self.drag_block_type = None
        self.drag_block_text = None
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.scrolling = False
        self.scroll_start_x = 0
        self.scroll_start_y = 0
        
        # Current block data
        self.current_block_type = None
        self.current_block_text = None
        self.current_block_data = None
        
        # Initialize components
        self.parser = PythonFileParser()
        self.block_loader = BlockLoader()
        self.file_handler = FileHandler(self)
        
        # Setup UI
        self.setup_ui()
        self.setup_keybindings()
        self.setup_menu()
    
    def setup_menu(self):
        """Setup menu bar with language selection"""
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label=self.lang.get("new_project"), command=self.new_project)
        file_menu.add_command(label=self.lang.get("import_project"), command=self.import_project)
        file_menu.add_command(label=self.lang.get("save_project"), command=self.save_project)
        file_menu.add_separator()
        file_menu.add_command(label=self.lang.get("export_python"), command=self.export_python)
        file_menu.add_command(label=self.lang.get("load_python"), command=self.load_python_file)
        menubar.add_cascade(label=self.lang.get("project"), menu=file_menu)
        
        # Language menu
        lang_menu = tk.Menu(menubar, tearoff=0)
        for lang_code in self.lang.get_all_languages():
            lang_name = self.lang.get("english") if lang_code == 'en' else self.lang.get("chinese")
            lang_menu.add_command(label=lang_name, 
                                command=lambda lc=lang_code: self.change_language(lc))
        menubar.add_cascade(label=self.lang.get("select_language"), menu=lang_menu)
        
        self.root.config(menu=menubar)
    
    def change_language(self, lang_code):
        """Change application language"""
        if self.lang.set_language(lang_code):
            # Update window title
            self.root.title(self.lang.get("app_title"))
            
            # Update project name label if it's still default
            if self.project_name in ["Untitled Project", "未命名项目"]:
                self.project_name = self.lang.get("untitled_project")
                if hasattr(self, 'project_name_label'):
                    self.project_name_label.config(text=self.project_name)
            
            # Rebuild the UI to update all text
            self.rebuild_ui()
    
    def rebuild_ui(self):
        """Rebuild UI with new language"""
        # Destroy all children except menu
        for child in self.root.winfo_children():
            if not isinstance(child, tk.Menu):
                child.destroy()
        
        # Rebuild UI
        self.setup_ui()
        
        # Redraw blocks if any exist
        if self.blocks:
            self.draw_all_blocks()
            self.highlight_selected_block()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Configure grid weights
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(1, weight=3)
        self.root.grid_columnconfigure(2, weight=1, minsize=350)
        
        # Create UI sections
        create_top_section(self)
        create_left_section(self)
        create_middle_section(self)
        create_right_section(self)
    
    def setup_keybindings(self):
        """Setup keyboard shortcuts"""
        shortcuts = {
            "<Control-q>": self.delete_selected_block_no_confirm,  # Changed to no confirmation
            "<Control-s>": lambda e: self.save_project(),
            "<Control-e>": lambda e: self.export_python(),
            "<Control-n>": lambda e: self.new_project(),
            "<Control-o>": lambda e: self.import_project(),
            "<Control-l>": lambda e: self.load_python_file(),
            "<Control-h>": lambda e: self.show_help(),
            "<Control-a>": lambda e: self.start_connection(),
            "<Control-x>": lambda e: self.start_end_connection(),
            "<Control-w>": lambda e: self.start_continue_connection(),
            # Note: <Delete> binding is removed as requested
        }
        
        for key, func in shortcuts.items():
            self.root.bind(key, func)
    
    # ===== Canvas Drawing Methods =====
    
    def draw_grid(self):
        """Draw grid lines on the canvas"""
        self.canvas.delete("grid_line")
        
        # Get visible area
        bbox = self.canvas.bbox("all")
        if bbox is None:
            x1, y1, x2, y2 = 0, 0, 2000, 2000
        else:
            x1, y1, x2, y2 = bbox
        
        # Ensure we have valid coordinates
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = max(2000, x2), max(2000, y2)
        
        # Draw vertical lines every 20 pixels
        for i in range(int(x1) - int(x1) % 20, int(x2) + 20, 20):
            self.canvas.create_line([(i, y1), (i, y2)], tag="grid_line", fill="#e0e0e0")
            
        # Draw horizontal lines every 20 pixels
        for i in range(int(y1) - int(y1) % 20, int(y2) + 20, 20):
            self.canvas.create_line([(x1, i), (x2, i)], tag="grid_line", fill="#e0e0e0")
            
        # Draw thicker lines every 100 pixels
        for i in range(int(x1) - int(x1) % 100, int(x2) + 100, 100):
            self.canvas.create_line([(i, y1), (i, y2)], tag="grid_line", fill="#b0b0b0", width=2)
            
        for i in range(int(y1) - int(y1) % 100, int(y2) + 100, 100):
            self.canvas.create_line([(x1, i), (x2, i)], tag="grid_line", fill="#b0b0b0", width=2)
    
    def draw_block(self, block):
        """Draw a block on the canvas"""
        # Remove existing block items
        if block.canvas_ids[0]:
            self.canvas.delete(block.canvas_ids[0])
        if block.canvas_ids[1]:
            self.canvas.delete(block.canvas_ids[1])
        
        # Draw block rectangle
        rect_id = self.canvas.create_rectangle(
            block.x, block.y, 
            block.x + block.width, block.y + block.height,
            fill=block.color, outline="black", width=2,
            tags=("block", "block_rect", block.id)
        )
        
        # Draw block text
        text_id = self.canvas.create_text(
            block.x + block.width/2, block.y + block.height/2,
            text=block.text, fill="white", font=("Arial", 10, "bold"),
            tags=("block", "block_text", block.id)
        )
        
        # Store canvas IDs
        block.canvas_ids = (rect_id, text_id)
        
        # Bring to front if selected
        if self.selected_block_id == block.id:
            self.highlight_selected_block()
    
    def draw_all_blocks(self):
        """Draw all blocks on the canvas"""
        # Clear all block-related items
        self.canvas.delete("block")
        self.canvas.delete("block_text")
        self.canvas.delete("block_rect")
        self.canvas.delete("connection")
        self.canvas.delete("highlight")
        
        # Draw all blocks
        for block_id, block in self.blocks.items():
            self.draw_block(block)
        
        # Draw all connections
        self.draw_all_connections()
        
        # Update the canvas display
        self.canvas.update_idletasks()
    
    def draw_all_connections(self):
        """Draw all connection lines"""
        # Clear existing connections
        self.canvas.delete("connection")
        
        # Draw sequence lines (black)
        for start_id, end_id in self.sequence_lines:
            self.draw_connection(start_id, end_id, "black")
        
        # Draw end lines (red)
        for control_id, end_id in self.end_lines:
            self.draw_connection(control_id, end_id, "red")
        
        # Draw continue lines (blue)
        for start_id, end_id in self.continue_lines:
            self.draw_connection(start_id, end_id, "blue")
    
    def draw_connection(self, start_id, end_id, color="black"):
        """Draw a connection line between two blocks"""
        if start_id not in self.blocks or end_id not in self.blocks:
            return
        
        start_block = self.blocks[start_id]
        end_block = self.blocks[end_id]
        
        # Get connection points
        start_points = start_block.get_connector_points()
        end_points = end_block.get_connector_points()
        
        # Determine which sides to connect (simplified: start bottom to end top)
        start_point = start_points["bottom"]
        end_point = end_points["top"]
        
        # Draw line with arrow
        line_id = self.canvas.create_line(
            start_point[0], start_point[1],
            end_point[0], end_point[1],
            fill=color, width=2, arrow=tk.LAST,
            tags=("connection", f"conn_{start_id}_{end_id}")
        )
        
        return line_id
    
    # ===== Canvas Event Handlers =====

    def canvas_click(self, event):
        """Handle canvas click events"""
        # Convert to canvas coordinates
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        # Check if we're in connecting mode
        if self.connecting_mode:
            self.handle_connection_click(x, y)
            return

        if self.end_connecting_mode:
            self.handle_end_connection_click(x, y)
            return

        # Check if we're in continue connecting mode
        if self.continue_connecting_mode:
            self.handle_continue_click(x, y)
            return

        # Check if clicked on a block
        clicked_block_id = None
        for block_id, block in self.blocks.items():
            # Use a simple check for point containment
            if (block.x <= x <= block.x + block.width and
                    block.y <= y <= block.y + block.height):
                clicked_block_id = block_id
                break

        if clicked_block_id:
            # Select the block
            self.select_block(clicked_block_id)

            # Start dragging
            self.dragging_block = clicked_block_id
            block = self.blocks[clicked_block_id]
            self.drag_start_x = x - block.x
            self.drag_start_y = y - block.y
        else:
            # Deselect all
            self.deselect_all()
    
    def canvas_drag(self, event):
        """Handle canvas drag events"""
        # If we're not dragging a block, check for scrolling
        if not self.dragging_block:
            if self.scrolling:
                dx = event.x - self.scroll_start_x
                dy = event.y - self.scroll_start_y
                self.canvas.scan_dragto(dx, dy, gain=1)
                self.scroll_start_x = event.x
                self.scroll_start_y = event.y
                self.draw_grid()
            return
        
        # Convert to canvas coordinates
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # Calculate new position (snapped to grid)
        new_x = (x - self.drag_start_x) // 20 * 20
        new_y = (y - self.drag_start_y) // 20 * 20
        
        # Move the block
        block = self.blocks[self.dragging_block]
        
        # Only move if position changed
        if new_x != block.x or new_y != block.y:
            block.move(new_x - block.x, new_y - block.y)
            
            # Update block position directly on canvas
            rect_id, text_id = block.canvas_ids
            self.canvas.coords(rect_id, block.x, block.y, 
                              block.x + block.width, block.y + block.height)
            self.canvas.coords(text_id, block.x + block.width/2, 
                              block.y + block.height/2)
            
            # Redraw connections
            self.draw_all_connections()
            self.highlight_selected_block()
    
    def canvas_release(self, event):
        """Handle canvas release events"""
        if self.dragging_block:
            # Ensure block is properly snapped to grid
            block = self.blocks[self.dragging_block]
            block.x = (block.x // 20) * 20
            block.y = (block.y // 20) * 20
            
            # Update block position
            rect_id, text_id = block.canvas_ids
            self.canvas.coords(rect_id, block.x, block.y, 
                              block.x + block.width, block.y + block.height)
            self.canvas.coords(text_id, block.x + block.width/2, 
                              block.y + block.height/2)
        
        self.dragging_block = None
        self.scrolling = False
    
    def canvas_right_click(self, event):
        """Handle canvas right-click events"""
        # Convert to canvas coordinates
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # Check if clicked on a block
        clicked_block_id = None
        for block_id, block in self.blocks.items():
            if block.contains_point(x, y):
                clicked_block_id = block_id
                break
        
        if clicked_block_id:
            # Show context menu
            self.show_block_context_menu(clicked_block_id, event)
        else:
            # Start scrolling
            self.scroll_start(event)
    
    def scroll_start(self, event):
        """Start scrolling the canvas"""
        self.canvas.scan_mark(event.x, event.y)
        self.scrolling = True
        self.scroll_start_x = event.x
        self.scroll_start_y = event.y
    
    def scroll_move(self, event):
        """Scroll the canvas"""
        if self.scrolling:
            self.canvas.scan_dragto(event.x, event.y, gain=1)
            self.draw_grid()  # Redraw grid for new view
    
    # ===== Block Management Methods =====
    
    def select_block(self, block_id):
        """Select a block"""
        self.selected_block_id = block_id
        self.show_block_properties()
        self.highlight_selected_block()
    
    def deselect_all(self):
        """Deselect all blocks"""
        self.selected_block_id = None
        if hasattr(self, 'canvas'):
            self.canvas.delete("highlight")
        
        # Clear editor
        if hasattr(self, 'editor_frame'):
            for widget in self.editor_frame.winfo_children():
                widget.destroy()
            
            tk.Label(self.editor_frame, text=self.lang.get("select_block"), 
                    fg="gray").pack(expand=True)
    
    def highlight_selected_block(self):
        """Highlight the selected block"""
        if not hasattr(self, 'canvas'):
            return
            
        self.canvas.delete("highlight")
        
        if self.selected_block_id and self.selected_block_id in self.blocks:
            block = self.blocks[self.selected_block_id]
            
            # Draw highlight rectangle
            self.canvas.create_rectangle(
                block.x - 2, block.y - 2,
                block.x + block.width + 2, block.y + block.height + 2,
                outline="yellow", width=3, tags="highlight"
            )
            
            # Bring selected block to front
            rect_id, text_id = block.canvas_ids
            self.canvas.tag_raise(rect_id)
            self.canvas.tag_raise(text_id)
            self.canvas.tag_raise("highlight")
    
    # ===== Blocks List Methods =====

    def update_blocks_list(self, event=None):
        """Update the blocks list based on selected category"""
        if not hasattr(self, 'blocks_tree'):
            return

        # Clear treeview
        for item in self.blocks_tree.get_children():
            self.blocks_tree.delete(item)

        category = self.category_var.get()

        # Update category dropdown values if needed
        if hasattr(self, 'category_dropdown'):
            categories = [self.lang.get("blocks_all")]
            for cat in self.block_loader.available_blocks.keys():
                categories.append(cat)
            self.category_dropdown['values'] = categories

        if category == self.lang.get("blocks_all") or category == "All":
            # Add all blocks by category
            for cat_name, blocks in self.block_loader.available_blocks.items():
                parent = self.blocks_tree.insert("", "end", text=cat_name, open=True)
                for block in blocks:
                    self.blocks_tree.insert(parent, "end", text=block["text"], values=(block["type"],))
        else:
            # Add blocks from specific category
            if category in self.block_loader.available_blocks:
                parent = self.blocks_tree.insert("", "end", text=category, open=True)
                for block in self.block_loader.available_blocks.get(category, []):
                    self.blocks_tree.insert(parent, "end", text=block["text"], values=(block["type"],))
    
    def select_block_from_list(self, event):
        """When a block is selected from the list"""
        if not hasattr(self, 'blocks_tree'):
            return
            
        selection = self.blocks_tree.selection()
        if selection:
            item = self.blocks_tree.item(selection[0])
            # Check if it's a block (not a category)
            if item["values"]:  # Has type value
                self.current_block_type = item["values"][0]
                self.current_block_text = item["text"]
                # Find the block data
                for category, blocks in self.block_loader.available_blocks.items():
                    for block in blocks:
                        if block["text"] == self.current_block_text and block["type"] == self.current_block_type:
                            self.current_block_data = block
                            break
    
    def add_block_from_list(self, event):
        """Add a block from the list to the canvas on double-click"""
        if not hasattr(self, 'blocks_tree') or not hasattr(self, 'canvas'):
            return
        
        selection = self.blocks_tree.selection()
        if not selection:
            return
        
        item = self.blocks_tree.item(selection[0])
        # Check if it's a block (not a category)
        if not item["values"]:
            return
        
        # Find the block data
        block_text = item["text"]
        block_type = item["values"][0]
        
        for category, blocks in self.block_loader.available_blocks.items():
            for block in blocks:
                if block["text"] == block_text and block["type"] == block_type:
                    # Place at center of visible canvas
                    canvas_width = self.canvas.winfo_width()
                    canvas_height = self.canvas.winfo_height()
                    
                    if canvas_width > 1 and canvas_height > 1:
                        # Get center of visible area
                        x = self.canvas.canvasx(canvas_width // 2)
                        y = self.canvas.canvasy(canvas_height // 2)
                    else:
                        # Default position
                        x, y = 100, 100
                    
                    # Snap to grid
                    x = (x // 20) * 20
                    y = (y // 20) * 20
                    
                    # Create block ID
                    block_id = f"block_{self.block_counter}"
                    
                    # Create block
                    new_block = CodeBlock(
                        block_id,
                        block["type"],
                        x, y,
                        text=block["text"],
                        content=block["content"]
                    )
                    
                    # Add to blocks dictionary
                    self.blocks[block_id] = new_block
                    self.block_counter += 1
                    
                    # Draw block on canvas
                    self.draw_block(new_block)
                    
                    # Select the new block
                    self.select_block(block_id)
                    return
    
    def start_drag_from_list(self, event):
        """Start dragging from the blocks list"""
        if not hasattr(self, 'blocks_tree'):
            return
            
        selection = self.blocks_tree.selection()
        if not selection:
            return
        
        item = self.blocks_tree.item(selection[0])
        # Check if it's a block (not a category)
        if item["values"]:  # Has type value
            self.dragging_from_list = True
            self.drag_block_type = item["values"][0]
            self.drag_block_text = item["text"]
            self.drag_start_x = event.x
            self.drag_start_y = event.y
    
    def drag_from_list(self, event):
        """Drag from the blocks list"""
        if not hasattr(self, 'blocks_tree'):
            return
            
        if not self.dragging_from_list:
            return
        
        # Check if we've moved enough to consider it a drag
        if (abs(event.x - self.drag_start_x) > 5 or 
            abs(event.y - self.drag_start_y) > 5):
            # We're dragging, change cursor
            self.blocks_tree.config(cursor="hand2")
    
    def end_drag_from_list(self, event):
        """End dragging from the blocks list and place block on canvas"""
        if not hasattr(self, 'blocks_tree') or not hasattr(self, 'canvas'):
            return
            
        if not self.dragging_from_list:
            return
        
        self.dragging_from_list = False
        self.blocks_tree.config(cursor="")
        
        # Check if mouse is over canvas
        canvas_x = self.canvas.winfo_rootx()
        canvas_y = self.canvas.winfo_rooty()
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        mouse_x = self.root.winfo_pointerx()
        mouse_y = self.root.winfo_pointery()
        
        # Check if mouse is over canvas
        if (canvas_x <= mouse_x <= canvas_x + canvas_width and
            canvas_y <= mouse_y <= canvas_y + canvas_height):
            
            # Convert to canvas coordinates
            x = self.canvas.canvasx(mouse_x - canvas_x)
            y = self.canvas.canvasy(mouse_y - canvas_y)
            
            # Snap to grid
            x = (x // 20) * 20
            y = (y // 20) * 20
            
            # Find the block data
            for category, blocks in self.block_loader.available_blocks.items():
                for block in blocks:
                    if (block["text"] == self.drag_block_text and 
                        block["type"] == self.drag_block_type):
                        
                        # Create block ID
                        block_id = f"block_{self.block_counter}"
                        
                        # Create block
                        new_block = CodeBlock(
                            block_id,
                            block["type"],
                            x, y,
                            text=block["text"],
                            content=block["content"]
                        )
                        
                        # Add to blocks dictionary
                        self.blocks[block_id] = new_block
                        self.block_counter += 1
                        
                        # Draw block on canvas
                        self.draw_block(new_block)
                        
                        # Select the new block
                        self.select_block(block_id)
                        break
    
    # ===== Block Editor Methods =====
    
    def show_block_properties(self):
        """Show properties of the selected block"""
        if not self.selected_block_id or self.selected_block_id not in self.blocks:
            return
        
        # Clear editor frame
        if hasattr(self, 'editor_frame'):
            for widget in self.editor_frame.winfo_children():
                widget.destroy()
        
        block = self.blocks[self.selected_block_id]
        
        # Create scrollable editor
        editor_canvas = tk.Canvas(self.editor_frame, width=400)
        scrollbar = tk.Scrollbar(self.editor_frame, orient="vertical", command=editor_canvas.yview)
        editor_content = tk.Frame(editor_canvas)
        
        editor_content.bind(
            "<Configure>",
            lambda e: editor_canvas.configure(scrollregion=editor_canvas.bbox("all"))
        )
        
        editor_canvas.create_window((0, 0), window=editor_content, anchor="nw", width=380)
        editor_canvas.configure(yscrollcommand=scrollbar.set)
        
        editor_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Block type label
        tk.Label(editor_content, text=f"Block: {block.text}", 
                font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=10, sticky="w")
        
        # Block content editor
        tk.Label(editor_content, text=self.lang.get("content")).grid(row=1, column=0, sticky="w", pady=5)
        
        content_text = tk.Text(editor_content, height=8, width=45)
        content_text.insert("1.0", block.content)
        content_text.grid(row=2, column=0, columnspan=2, pady=5, sticky="ew")
        
        def update_content():
            block.content = content_text.get("1.0", tk.END).strip()
            # Update block text if it's a simple statement
            if "{" not in block.content and len(block.content) < 30:
                block.text = block.content
            # Redraw block
            self.draw_all_blocks()
            self.highlight_selected_block()
        
        tk.Button(editor_content, text=self.lang.get("update"), command=update_content).grid(row=3, column=0, columnspan=2, pady=10, sticky="ew")
        
        # Color editor
        tk.Label(editor_content, text=self.lang.get("color")).grid(row=4, column=0, sticky="w", pady=5)
        
        color_frame = tk.Frame(editor_content)
        color_frame.grid(row=4, column=1, pady=5, sticky="w")
        
        color_btn = tk.Button(color_frame, text=self.lang.get("choose"), width=10,
                             command=lambda: self.choose_block_color(block))
        color_btn.pack(side="left", padx=2)
        
        color_display = tk.Label(color_frame, text="     ", bg=block.color, relief="sunken")
        color_display.pack(side="left", padx=2)
        
        # Connection buttons
        tk.Label(editor_content, text=self.lang.get("connections"), 
                font=("Arial", 10, "bold")).grid(row=5, column=0, columnspan=2, pady=(20, 5), sticky="w")
        
        # Determine which connection buttons to show
        has_sequence = len(block.connections) > 0
        has_end = block.end_connection is not None
        has_continue = block.continue_connection is not None
        
        # Sequence connection button
        seq_text = self.lang.get("disconnect_sequence") if has_sequence else self.lang.get("connect_sequence")
        seq_btn = tk.Button(editor_content, text=seq_text,
                           command=lambda: self.toggle_sequence_connection())
        seq_btn.grid(row=6, column=0, columnspan=2, pady=5, sticky="ew")
        
        # End connection button for blocks that require indentation
        if block.requires_indentation():
            end_text = self.lang.get("disconnect_end") if has_end else self.lang.get("set_end_block")
            end_btn = tk.Button(editor_content, text=end_text,
                               command=lambda: self.toggle_end_connection())
            end_btn.grid(row=7, column=0, columnspan=2, pady=5, sticky="ew")
        
        # Continue connection button
        continue_text = self.lang.get("discontinue_line") if has_continue else self.lang.get("continue_line")
        continue_btn = tk.Button(editor_content, text=continue_text,
                                command=lambda: self.toggle_continue_connection())
        continue_btn.grid(row=8, column=0, columnspan=2, pady=5, sticky="ew")
        
        # Show current connections
        if block.connections or block.end_connection or block.continue_connection:
            tk.Label(editor_content, text=self.lang.get("current_connections")).grid(row=9, column=0, columnspan=2, pady=(20, 5), sticky="w")
            
            row = 10
            if block.connections:
                tk.Label(editor_content, text=self.lang.get("sequence_to")).grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 2))
                row += 1
                for i, conn_id in enumerate(block.connections):
                    if conn_id in self.blocks:
                        conn_block = self.blocks[conn_id]
                        tk.Label(editor_content, text=f"  • {conn_block.text}").grid(row=row, column=0, columnspan=2, sticky="w")
                        row += 1
            
            if block.end_connection:
                if block.end_connection in self.blocks:
                    conn_block = self.blocks[block.end_connection]
                    tk.Label(editor_content, text=f"{self.lang.get('end_block')}: {conn_block.text}").grid(row=row, column=0, columnspan=2, sticky="w")
                    row += 1
            
            if block.continue_connection:
                if block.continue_connection in self.blocks:
                    conn_block = self.blocks[block.continue_connection]
                    tk.Label(editor_content, text=f"{self.lang.get('continue_to')}: {conn_block.text}").grid(row=row, column=0, columnspan=2, sticky="w")
                    row += 1
        
        # Delete button
        delete_btn = tk.Button(editor_content, text=self.lang.get("delete_block"), bg="#ffcccc",
                              command=lambda: self.delete_block_without_confirm(block.id))
        delete_btn.grid(row=99, column=0, columnspan=2, pady=20, sticky="ew")
    
    def choose_block_color(self, block):
        """Change the color of a block"""
        color = colorchooser.askcolor(title="Choose block color")
        if color and color[1]:
            block.color = color[1]
            if hasattr(self, 'canvas'):
                self.draw_all_blocks()
                self.highlight_selected_block()
    
    # ===== Connection Methods =====
    
    def start_connection(self, start_block_id=None):
        """Start connecting blocks (sequence line)"""
        if start_block_id is None:
            if self.selected_block_id:
                start_block_id = self.selected_block_id
            else:
                return
        
        if start_block_id not in self.blocks:
            return
        
        # Check if block already has sequence connections
        block = self.blocks[start_block_id]
        if block.connections:
            # 改进3: 删除消息框，直接断开连接
            self.disconnect_sequence(start_block_id)
        
        self.connecting_mode = True
        self.start_connection_block = start_block_id
        self.canvas.config(cursor="cross")
        
        # Update status
        self.project_name_label.config(text="Connection Mode: Click another block to connect")
        
        # Bind escape key to cancel
        self.root.bind("<Escape>", self.cancel_connection)
    
    def start_end_connection(self, control_block_id=None):
        """Start connecting end block (for if/for/while/function)"""
        if control_block_id is None:
            if self.selected_block_id:
                control_block_id = self.selected_block_id
            else:
                return
        
        if control_block_id not in self.blocks:
            return
        
        block = self.blocks[control_block_id]
        if not block.requires_indentation():
            messagebox.showwarning("Invalid Block", 
                                 "This block type does not require an end connection.")
            return
        
        # Check if block already has an end connection
        if block.end_connection:
            # 改进3: 删除消息框，直接断开连接
            self.disconnect_end(control_block_id)
        
        self.end_connecting_mode = True
        self.start_connection_block = control_block_id
        self.canvas.config(cursor="cross")
        
        # Update status
        self.project_name_label.config(text="End Connection Mode: Click end block")
        
        # Bind escape key to cancel
        self.root.bind("<Escape>", self.cancel_connection)

    def start_continue_connection(self, block_id=None):
        """Start connecting continue line"""
        if block_id is None:
            if self.selected_block_id:
                block_id = self.selected_block_id
            else:
                return

        if block_id not in self.blocks:
            return

        # Check if block already has a continue connection
        block = self.blocks[block_id]
        if block.continue_connection:
            # 改进3: 删除消息框，直接断开连接
            self.disconnect_continue_line(block_id)

        self.continue_connecting_mode = True
        self.start_connection_block = block_id
        self.canvas.config(cursor="cross")

        # Update status
        if hasattr(self, 'project_name_label'):
            self.project_name_label.config(text="Continue Line Mode: Click another block to connect (same line)")

        # Bind escape key to cancel
        self.root.bind("<Escape>", self.cancel_continue_connection)

    def handle_connection_click(self, x, y):
        """Handle click when in connecting mode"""
        # Find clicked block
        clicked_block_id = None
        for block_id, block in self.blocks.items():
            if (block.x <= x <= block.x + block.width and
                    block.y <= y <= block.y + block.height):
                clicked_block_id = block_id
                break

        if clicked_block_id and clicked_block_id != self.start_connection_block:
            # Add connection
            start_block = self.blocks[self.start_connection_block]

            if clicked_block_id not in start_block.connections:
                start_block.connections.append(clicked_block_id)

                # Add to sequence lines
                if (self.start_connection_block, clicked_block_id) not in self.sequence_lines:
                    self.sequence_lines.append((self.start_connection_block, clicked_block_id))

                # Redraw connections
                self.draw_all_connections()

        # Reset connection mode
        self.cancel_connection()

    def handle_end_connection_click(self, x, y):
        """Handle click when in end connecting mode"""
        # Find clicked block
        clicked_block_id = None
        for block_id, block in self.blocks.items():
            if (block.x <= x <= block.x + block.width and
                    block.y <= y <= block.y + block.height):
                clicked_block_id = block_id
                break

        if clicked_block_id and clicked_block_id != self.start_connection_block:
            # Set end connection
            control_block = self.blocks[self.start_connection_block]
            control_block.end_connection = clicked_block_id

            # Add to end lines
            if (self.start_connection_block, clicked_block_id) not in self.end_lines:
                self.end_lines.append((self.start_connection_block, clicked_block_id))

            # Redraw connections
            self.draw_all_connections()

        # Reset end connection mode
        self.cancel_connection()

    def handle_continue_click(self, x, y):
        """Handle click when in continue connecting mode"""
        clicked_block_id = None
        for block_id, block in self.blocks.items():
            if (block.x <= x <= block.x + block.width and
                    block.y <= y <= block.y + block.height):
                clicked_block_id = block_id
                break

        if clicked_block_id and clicked_block_id != self.start_connection_block:
            # Check if start block already has a continue connection
            start_block = self.blocks[self.start_connection_block]
            if start_block.continue_connection:
                # Remove old connection
                old_end_id = start_block.continue_connection
                # Remove from continue lines
                self.continue_lines = [(s, e) for s, e in self.continue_lines if s != self.start_connection_block]

            # Add continue connection
            start_block.continue_connection = clicked_block_id

            # Add to continue lines
            if (self.start_connection_block, clicked_block_id) not in self.continue_lines:
                self.continue_lines.append((self.start_connection_block, clicked_block_id))

            # Update the end block to have a prev connection
            end_block = self.blocks[clicked_block_id]
            if self.start_connection_block not in end_block.prev_connections:
                end_block.prev_connections.append(self.start_connection_block)

            # Redraw everything
            self.draw_all_blocks()

            # Update the editor to show the new connection
            if self.selected_block_id:
                self.show_block_properties()

        # Reset connection mode
        self.cancel_continue_connection()
    
    def cancel_connection(self, event=None):
        """Cancel connection mode"""
        self.connecting_mode = False
        self.end_connecting_mode = False
        self.start_connection_block = None
        self.canvas.config(cursor="")
        self.project_name_label.config(text=self.project_name)
        self.root.unbind("<Escape>")

    def cancel_continue_connection(self, event=None):
        """Cancel continue connection mode"""
        self.continue_connecting_mode = False
        self.start_connection_block = None
        self.canvas.config(cursor="")
        if hasattr(self, 'project_name_label'):
            self.project_name_label.config(text=self.project_name)
        self.root.unbind("<Escape>")
    
    def toggle_sequence_connection(self, event=None):
        """Toggle sequence connection for selected block"""
        if self.selected_block_id:
            block = self.blocks[self.selected_block_id]
            has_sequence = len(block.connections) > 0
            if has_sequence:
                self.disconnect_sequence(self.selected_block_id)
            else:
                self.start_connection()
    
    def toggle_end_connection(self, event=None):
        """Toggle end connection for selected block"""
        if self.selected_block_id:
            block = self.blocks[self.selected_block_id]
            if block.requires_indentation():
                has_end = block.end_connection is not None
                if has_end:
                    self.disconnect_end(self.selected_block_id)
                else:
                    self.start_end_connection()
    
    def toggle_continue_connection(self, event=None):
        """Toggle continue connection for selected block"""
        if self.selected_block_id:
            block = self.blocks[self.selected_block_id]
            has_continue = block.continue_connection is not None
            if has_continue:
                self.disconnect_continue_line(self.selected_block_id)
            else:
                self.start_continue_connection()
    
    def disconnect_sequence(self, block_id):
        """Disconnect sequence line from block"""
        if block_id in self.blocks:
            block = self.blocks[block_id]
            # Remove all connections from this block
            for conn_id in block.connections[:]:
                self.sequence_lines = [(s, e) for s, e in self.sequence_lines if not (s == block_id and e == conn_id)]
                block.connections.remove(conn_id)
            self.draw_all_connections()
    
    def disconnect_end(self, block_id):
        """Disconnect end line from block"""
        if block_id in self.blocks:
            block = self.blocks[block_id]
            if block.end_connection:
                # Remove from end lines
                self.end_lines = [(c, e) for c, e in self.end_lines if c != block_id]
                block.end_connection = None
                self.draw_all_connections()
    
    def disconnect_continue_line(self, block_id):
        """Disconnect continue line from block"""
        if block_id in self.blocks:
            block = self.blocks[block_id]
            if block.continue_connection:
                # Remove from continue lines
                self.continue_lines = [(s, e) for s, e in self.continue_lines if s != block_id]
                block.continue_connection = None
                self.draw_all_connections()
    
    # ===== Block Operations =====
    
    def show_block_context_menu(self, block_id, event):
        """Show context menu for a block"""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Delete", command=lambda: self.delete_block(block_id))
        
        block = self.blocks[block_id]
        
        # Check current connection states
        has_sequence = len(block.connections) > 0
        has_end = block.end_connection is not None
        has_continue = block.continue_connection is not None
        
        # Sequence connection toggle
        seq_text = "Disconnect Sequence" if has_sequence else "Connect Sequence"
        menu.add_command(label=seq_text, 
                        command=lambda: self.start_connection(block_id))
        
        # End connection toggle for blocks that require indentation
        if block.requires_indentation():
            end_text = "Disconnect End" if has_end else "Connect End"
            menu.add_command(label=end_text, 
                           command=lambda: self.start_end_connection(block_id))
        
        # Continue connection toggle
        continue_text = "Disconnect Continue" if has_continue else "Continue Line"
        menu.add_command(label=continue_text, 
                        command=lambda: self.start_continue_connection(block_id))
        
        menu.add_separator()
        menu.add_command(label="Duplicate", command=lambda: self.duplicate_block(block_id))
        
        # Show the menu
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def delete_block(self, block_id):
        """Delete a block with confirmation (for UI button)"""
        if block_id not in self.blocks:
            return
        
        response = messagebox.askyesno("Delete Block", 
                                      f"Are you sure you want to delete block '{self.blocks[block_id].text}'?")
        if response:
            self._delete_block_impl(block_id)
    
    def delete_block_without_confirm(self, block_id):
        """Delete a block without confirmation (for keyboard shortcut)"""
        if block_id in self.blocks:
            self._delete_block_impl(block_id)
    
    def delete_selected_block(self, event=None):
        """Delete the selected block with confirmation (UI button)"""
        if self.selected_block_id:
            self.delete_block(self.selected_block_id)
    
    def delete_selected_block_no_confirm(self, event=None):
        """Delete the selected block without confirmation (keyboard shortcut)"""
        if self.selected_block_id:
            self.delete_block_without_confirm(self.selected_block_id)
    
    def _delete_block_impl(self, block_id):
        """Internal implementation of block deletion"""
        # Remove all connections involving this block
        self.sequence_lines = [(s, e) for s, e in self.sequence_lines if s != block_id and e != block_id]
        self.end_lines = [(c, e) for c, e in self.end_lines if c != block_id and e != block_id]
        self.continue_lines = [(s, e) for s, e in self.continue_lines if s != block_id and e != block_id]
        
        # Remove block from other blocks' connections
        for other_id, other_block in self.blocks.items():
            if block_id in other_block.connections:
                other_block.connections.remove(block_id)
            if other_block.end_connection == block_id:
                other_block.end_connection = None
            if other_block.continue_connection == block_id:
                other_block.continue_connection = None
        
        # Delete from canvas and dictionary
        if hasattr(self, 'canvas'):
            self.canvas.delete("block")
            self.canvas.delete("block_text")
        del self.blocks[block_id]
        
        # Redraw everything
        if hasattr(self, 'canvas'):
            self.draw_all_blocks()
        
        # Clear selection if this block was selected
        if self.selected_block_id == block_id:
            self.deselect_all()
    
    def duplicate_block(self, block_id):
        """Duplicate a block"""
        if block_id not in self.blocks:
            return
        
        original = self.blocks[block_id]
        
        # Create new block with offset
        new_id = f"block_{self.block_counter}"
        new_block = CodeBlock(
            new_id,
            original.type,
            original.x + 40, original.y + 40,
            original.width, original.height,
            original.text, original.content
        )
        new_block.color = original.color
        
        # Add to blocks
        self.blocks[new_id] = new_block
        self.block_counter += 1
        
        # Draw the new block
        if hasattr(self, 'canvas'):
            self.draw_block(new_block)
        
        # Select the new block
        self.select_block(new_id)
    
    # ===== File Operations =====
    
    def edit_project_name(self, event):
        """Edit the project name"""
        new_name = simpledialog.askstring(
            self.lang.get("edit_project_name"), 
            self.lang.get("enter_new_name"),
            initialvalue=self.project_name
        )
        if new_name:
            self.project_name = new_name
            if hasattr(self, 'project_name_label'):
                self.project_name_label.config(text=self.project_name)
    
    def new_project(self):
        """Create a new project"""
        if self.blocks:
            response = messagebox.askyesnocancel("New Project", 
                                                "Do you want to save the current project before clearing?")
            if response is None:  # Cancel
                return
            elif response:  # Yes - save
                self.save_project()
        
        # Clear everything
        self.blocks = {}
        self.block_counter = 0
        self.selected_block_id = None
        self.sequence_lines = []
        self.end_lines = []
        self.continue_lines = []
        
        # Reset project name
        self.project_name = self.lang.get("untitled_project")
        if hasattr(self, 'project_name_label'):
            self.project_name_label.config(text=self.project_name)
        
        # Clear canvas
        if hasattr(self, 'canvas'):
            self.canvas.delete("all")
            self.draw_grid()
        
        # Clear editor
        self.deselect_all()
    
    def save_project(self):
        """Save the project to a file"""
        self.file_handler.save_project()
    
    def import_project(self):
        """Import a saved project"""
        self.file_handler.import_project()
    
    def export_python(self):
        """Export the project as a Python .py file"""
        if not self.blocks:
            messagebox.showwarning("No Blocks", "There are no blocks to export.")
            return
        
        # Generate Python code with proper indentation
        python_code = self.generate_python_code_with_indentation()
        
        # Ask for filename
        filename = filedialog.asksaveasfilename(
            defaultextension=".py",
            filetypes=[("Python Files", "*.py"), ("All Files", "*.*")],
            initialfile=f"{self.project_name}.py"
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(python_code)
                messagebox.showinfo("Export Successful", f"Python code exported to {filename}")
                
                # 改进1: 询问是否运行脚本
                if messagebox.askyesno("Run Code", "Do you want to run the exported code?"):
                    # 在新线程中运行脚本，避免阻塞UI
                    threading.Thread(target=self.run_python_code, args=(filename,), daemon=True).start()
                    
            except Exception as e:
                messagebox.showerror("Export Error", f"Could not export file: {e}")
    
    def load_python_file(self):
        """Load a Python file"""
        # Ask for filename
        filename = filedialog.askopenfilename(
            defaultextension=".py",
            filetypes=[("Python Files", "*.py"), ("All Files", "*.*")]
        )
        
        if not filename:
            return
        
        try:
            # Parse the Python file
            result = self.parser.parse_gui_python_file(filename)
            
            if 'error' in result:
                messagebox.showerror("Parse Error", f"Could not parse Python file: {result['error']}")
                return
            
            # Clear current project
            self.new_project()
            
            # Update project name from file
            file_name = os.path.basename(filename)
            self.project_name = os.path.splitext(file_name)[0]
            if hasattr(self, 'project_name_label'):
                self.project_name_label.config(text=self.project_name)
            
            # Get metadata
            metadata = result.get('metadata', {})
            imports = result.get('imports', [])
            class_info = result.get('class_info', {})
            
            # Create blocks for imports
            x, y = 100, 100
            for imp in imports:
                block_id = f"block_{self.block_counter}"
                block = CodeBlock(
                    block_id,
                    "import",
                    x, y,
                    text="Import",
                    content=imp
                )
                self.blocks[block_id] = block
                self.block_counter += 1
                y += 80
            
            # Show success message
            messagebox.showinfo("Load Successful", 
                              f"Python file loaded successfully!")
            
        except Exception as e:
            messagebox.showerror("Load Error", f"Could not load Python file: {e}")
    
    def generate_python_code_with_indentation(self):
        """Generate Python code with proper indentation"""
        # Build connection maps
        next_map = {}
        for start_id, end_id in self.sequence_lines:
            if start_id not in next_map:
                next_map[start_id] = []
            next_map[start_id].append(end_id)
        
        # Build end block map
        end_map = {}
        for control_id, end_id in self.end_lines:
            end_map[control_id] = end_id
        
        # Build continue line map
        continue_map = {}
        for start_id, end_id in self.continue_lines:
            continue_map[start_id] = end_id
        
        # Find start blocks (blocks with no incoming connections)
        incoming = {}
        for start_id, end_id in self.sequence_lines:
            incoming[end_id] = incoming.get(end_id, 0) + 1
        
        start_blocks = []
        for block_id, block in self.blocks.items():
            if block_id not in incoming:
                # Check if it's not an end block
                is_end_block = False
                for control_id, end_id in self.end_lines:
                    if end_id == block_id:
                        is_end_block = True
                        break
                if not is_end_block:
                    start_blocks.append(block_id)
        
        # If no start blocks, use all non-end blocks
        if not start_blocks:
            for block_id, block in self.blocks.items():
                is_end_block = False
                for control_id, end_id in self.end_lines:
                    if end_id == block_id:
                        is_end_block = True
                        break
                if not is_end_block:
                    start_blocks.append(block_id)
        
        # Generate code
        code_lines = []
        code_lines.append(f"# Python code generated from ScratchPy project: {self.project_name}")
        code_lines.append("# Generated on: " + time.strftime("%Y-%m-%d %H:%M:%S"))
        code_lines.append("")
        
        # Track visited blocks and current indentation
        visited = set()
        
        # Stack to track nested control structures
        control_stack = []  # Each element is (control_block_id, indent_level_when_started)
        
        def process_block(block_id, current_indent, is_continue=False):
            """Process a block and return its lines"""
            if block_id in visited:
                return []
            
            visited.add(block_id)
            block = self.blocks[block_id]
            lines = []
            
            # Check if this is an end block for a control structure
            for i, (control_id, start_indent) in enumerate(control_stack):
                if end_map.get(control_id) == block_id:
                    # This is the end block for this control structure
                    # Remove this control from stack
                    control_stack.pop(i)
                    # End block should be at the control's starting indent level
                    current_indent = start_indent
                    break
            
            # Get the block's content with current indentation
            content_lines = block.content.split('\n')
            
            if is_continue:
                # For continue blocks, add to the last line
                if lines and content_lines:
                    lines[-1] = lines[-1].rstrip() + " " + content_lines[0].strip()
                    for line in content_lines[1:]:
                        if line.strip():  # Skip empty lines
                            indent_str = "    " * current_indent
                            lines.append(f"{indent_str}{line}")
                elif content_lines:
                    for line in content_lines:
                        if line.strip():
                            indent_str = "    " * current_indent
                            lines.append(f"{indent_str}{line}")
            else:
                # Normal block
                for line in content_lines:
                    if line.strip():  # Skip empty lines
                        indent_str = "    " * current_indent
                        lines.append(f"{indent_str}{line}")
            
            # Check if this block requires indentation (uses the new method)
            if block.requires_indentation() and block_id in end_map:
                # Push onto stack
                control_stack.append((block_id, current_indent))
                # Increase indent for next blocks
                next_indent = current_indent + 1
            else:
                next_indent = current_indent
            
            # Process continue connection first (same line)
            if block_id in continue_map:
                next_id = continue_map[block_id]
                continue_lines = process_block(next_id, current_indent, is_continue=True)
                if continue_lines:
                    # Merge with last line if possible
                    if lines and continue_lines:
                        lines[-1] = lines[-1].rstrip() + " " + continue_lines[0].strip()
                        lines.extend(continue_lines[1:])
                    else:
                        lines.extend(continue_lines)
            
            # Process connected blocks
            if block_id in next_map:
                for next_id in next_map[block_id]:
                    # Check if next block is already an end block for something in stack
                    is_end = False
                    for control_id, start_indent in control_stack:
                        if end_map.get(control_id) == next_id:
                            is_end = True
                            # Process end block at control's indent level
                            next_lines = process_block(next_id, start_indent)
                            lines.extend(next_lines)
                            break
                    
                    if not is_end:
                        next_lines = process_block(next_id, next_indent)
                        lines.extend(next_lines)
            
            return lines
        
        # Process all start blocks
        for start_id in start_blocks:
            result = process_block(start_id, 0)
            if result:
                code_lines.extend(result)
        
        # Add any unvisited blocks
        for block_id, block in self.blocks.items():
            if block_id not in visited:
                code_lines.append(block.content)
        
        return "\n".join(code_lines)
    
    def run_python_code(self, filename):
        """Run the exported Python code - 修复.exe环境下运行脚本的问题"""
        try:
            # 检查是否在.exe环境中运行
            if getattr(sys, 'frozen', False):
                # 在.exe环境中，sys.executable指向.exe文件本身
                # 我们需要找到系统的Python解释器
                import shutil
                
                # 尝试可能的Python解释器命令
                python_commands = ['python', 'python3', 'py']
                
                for cmd in python_commands:
                    if shutil.which(cmd):
                        # 使用找到的Python解释器运行脚本
                        result = subprocess.run([cmd, filename], 
                                              capture_output=True, text=True)
                        break
                else:
                    # 没有找到Python解释器
                    self.root.after(0, messagebox.showerror, 
                                   "Python Not Found",
                                   "Could not find Python interpreter on your system.\n"
                                   "Please make sure Python is installed and in your PATH.")
                    return
            else:
                # 在开发环境中，使用sys.executable
                result = subprocess.run([sys.executable, filename], 
                                      capture_output=True, text=True)
            
            # 在主线程中更新UI
            self.root.after(0, self._show_run_output, filename, result)
            
        except FileNotFoundError:
            self.root.after(0, messagebox.showerror, 
                           "Python Not Found",
                           "Could not find Python interpreter on your system.\n"
                           "Please make sure Python is installed and in your PATH.")
        except Exception as e:
            self.root.after(0, messagebox.showerror, "Run Error", f"Could not run Python code: {e}")

    def _show_run_output(self, filename, result):
        """在主线程中显示运行输出"""
        # Show output
        output_window = tk.Toplevel(self.root)
        output_window.title(f"Output: {os.path.basename(filename)}")
        output_window.geometry("600x400")
        
        # Create text widget for output
        text_widget = tk.Text(output_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add output
        text_widget.insert("1.0", f"Output:\n{result.stdout}")
        if result.stderr:
            text_widget.insert(tk.END, f"\n\nErrors:\n{result.stderr}")
        
        # Make text read-only
        text_widget.config(state=tk.DISABLED)
        
        # Add scrollbar
        scrollbar = tk.Scrollbar(text_widget)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=text_widget.yview)

    def import_package(self):
        """Import a package JSON file and add its blocks"""
        # Ask for JSON file
        filename = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            title="Select Package JSON File"
        )

        if not filename:
            return

        try:
            # Ask user for category name (default is filename without extension)
            default_category = os.path.basename(filename).replace('.json', '')
            category_name = simpledialog.askstring(
                "Package Category",
                f"Enter category name for this package:",
                initialvalue=default_category
            )

            if not category_name:  # User cancelled
                return

            # 改进2: 使用BlockLoader的新方法导入包
            added_count, actual_category = self.block_loader.add_custom_package(filename, category_name)

            if added_count > 0:
                # Update blocks list
                self.update_blocks_list()

                # Update category dropdown if it exists
                if hasattr(self, 'category_dropdown'):
                    # Refresh category list
                    categories = [self.lang.get("blocks_all")]
                    for category in self.block_loader.available_blocks.keys():
                        categories.append(category)
                    self.category_dropdown['values'] = categories

                    # Show success message
                    messagebox.showinfo(
                        "Package Imported",
                        f"Successfully imported {added_count} block(s).\n"
                        f"Added to category: '{actual_category}'"
                    )
                else:
                    messagebox.showinfo(
                        "No New Blocks",
                        "No new blocks were added. All blocks already exist."
                    )

        except Exception as e:
            messagebox.showerror(
                "Import Error",
                f"Could not import package:\n{str(e)}"
            )
    
    # ===== Help Methods =====
    
    def show_help(self):
        """Show improved help window with block information"""
        # Import here to avoid circular imports
        from ui.help_window import show_help_window
        show_help_window(self)
