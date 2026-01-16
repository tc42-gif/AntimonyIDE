import json
import os
from tkinter import filedialog, messagebox
from core.code_block import CodeBlock

class FileHandler:
    def __init__(self, app):
        self.app = app
    
    def save_project(self):
        """Save the project to a file"""
        project_dir = "projects"
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)
        
        save_data = {
            "project_name": self.app.project_name,
            "blocks": {bid: block.to_dict() for bid, block in self.app.blocks.items()},
            "block_counter": self.app.block_counter,
            "sequence_lines": self.app.sequence_lines,
            "end_lines": self.app.end_lines,
            "continue_lines": self.app.continue_lines
        }
        
        filename = filedialog.asksaveasfilename(
            initialdir=project_dir,
            defaultextension=".aide",
            filetypes=[("AIDEproject", "*.aide"), ("All Files", "*.*")],
            initialfile=f"{self.app.project_name}.aide"
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(save_data, f, indent=2)
                messagebox.showinfo("Save Successful", f"Project saved to {filename}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Could not save project: {e}")
    
    def import_project(self):
        """Import a saved project"""
        project_dir = "projects"
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)
        
        filename = filedialog.askopenfilename(
            initialdir=project_dir,
            defaultextension=".aide",
            filetypes=[("AIDEproject", "*.aide"), ("All Files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    load_data = json.load(f)
                
                # Clear current project
                self.app.blocks = {}
                self.app.sequence_lines = []
                self.app.end_lines = []
                self.app.continue_lines = []
                
                # Load data
                self.app.project_name = load_data["project_name"]
                self.app.project_name_label.config(text=self.app.project_name)
                
                # Load blocks
                for bid, block_data in load_data["blocks"].items():
                    self.app.blocks[bid] = CodeBlock.from_dict(block_data)
                
                self.app.block_counter = load_data.get("block_counter", 0)
                self.app.sequence_lines = load_data.get("sequence_lines", [])
                self.app.end_lines = load_data.get("end_lines", [])
                self.app.continue_lines = load_data.get("continue_lines", [])
                
                # Redraw everything
                self.app.canvas.delete("all")
                self.app.draw_grid()
                self.app.draw_all_blocks()
                
                # Clear editor
                self.app.deselect_all()
                
                messagebox.showinfo("Import Successful", f"Project imported from {filename}")
                
            except Exception as e:
                messagebox.showerror("Import Error", f"Could not import project: {e}")