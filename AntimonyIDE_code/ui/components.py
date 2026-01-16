import tkinter as tk
from tkinter import ttk

def create_top_section(app):
    """Create the top section with project name and buttons"""
    top_frame = tk.Frame(app.root, bg="#f0f0f0", height=60)
    top_frame.grid(row=0, column=0, columnspan=3, sticky="ew")
    top_frame.grid_propagate(False)
    
    # Configure grid columns
    top_frame.grid_columnconfigure(1, weight=1)
    
    # Project name (clickable to edit)
    app.project_name_label = tk.Label(
        top_frame, 
        text=app.project_name, 
        font=("Arial", 14, "bold"),
        bg="#f0f0f0",
        cursor="hand2"
    )
    app.project_name_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
    app.project_name_label.bind("<Button-1>", app.edit_project_name)
    
    # Buttons frame
    buttons_frame = tk.Frame(top_frame, bg="#f0f0f0")
    buttons_frame.grid(row=0, column=2, padx=10, pady=10, sticky="e")
    
    # Create buttons
    tk.Button(buttons_frame, text=app.lang.get("new_project"), 
              command=app.new_project, width=12).grid(row=0, column=0, padx=2)
    tk.Button(buttons_frame, text=app.lang.get("import"), 
              command=app.import_project, width=12).grid(row=0, column=1, padx=2)
    tk.Button(buttons_frame, text=app.lang.get("save"), 
              command=app.save_project, width=12).grid(row=0, column=2, padx=2)
    tk.Button(buttons_frame, text=app.lang.get("export"), 
              command=app.export_python, width=12).grid(row=0, column=3, padx=2)
    
    # New button: Load Python File
    tk.Button(buttons_frame, text=app.lang.get("load_python"), 
              command=app.load_python_file, width=12, 
              bg="#FF5722", fg="white").grid(row=0, column=4, padx=2)
    
    # Help button
    tk.Button(buttons_frame, text=app.lang.get("help"), 
              command=app.show_help, width=12, 
              bg="#4CAF50", fg="white").grid(row=0, column=5, padx=2)


def create_left_section(app):
    """Create the left section with blocks list"""
    left_frame = tk.LabelFrame(app.root, text=app.lang.get("code_blocks"), padx=10, pady=10)
    left_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

    # Category selection
    category_frame = tk.Frame(left_frame)
    category_frame.pack(fill="x", pady=(0, 5))

    tk.Label(category_frame, text=app.lang.get("category")).pack(side="left", padx=(0, 5))

    app.category_var = tk.StringVar(value=app.lang.get("blocks_all"))

    # Get categories from available blocks
    categories = [app.lang.get("blocks_all")]
    for category in app.block_loader.available_blocks.keys():
        # Use the category name directly for now
        categories.append(category)

    app.category_dropdown = ttk.Combobox(category_frame, textvariable=app.category_var,
                                         values=categories, state="readonly", width=15)
    app.category_dropdown.pack(side="left")
    app.category_dropdown.bind("<<ComboboxSelected>>", lambda e: app.update_blocks_list())

    # Import package button
    tk.Button(category_frame, text=app.lang.get("import_package"),
              command=app.import_package, width=12).pack(side="right", padx=(5, 0))

    # ... rest of the code remains the same ...
    
    # Blocks list with scrollbar
    list_frame = tk.Frame(left_frame)
    list_frame.pack(fill="both", expand=True)
    
    # Create treeview for blocks
    app.blocks_tree = ttk.Treeview(list_frame, height=20)
    app.blocks_tree.pack(side="left", fill="both", expand=True)

    # Configure treeview
    app.blocks_tree["columns"] = ("type",)
    app.blocks_tree.column("#0", width=150, minwidth=150)
    app.blocks_tree.column("type", width=80, minwidth=80)

    app.blocks_tree.heading("#0", text="Block")
    app.blocks_tree.heading("type", text="Type")

    # Add scrollbar
    scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=app.blocks_tree.yview)
    scrollbar.pack(side="right", fill="y")
    app.blocks_tree.configure(yscrollcommand=scrollbar.set)

    # Bind selection event
    app.blocks_tree.bind("<<TreeviewSelect>>", app.select_block_from_list)
    app.blocks_tree.bind("<Double-1>", app.add_block_from_list)

    # Bind drag events for treeview
    app.blocks_tree.bind("<ButtonPress-1>", app.start_drag_from_list)
    app.blocks_tree.bind("<B1-Motion>", app.drag_from_list)
    app.blocks_tree.bind("<ButtonRelease-1>", app.end_drag_from_list)

    # Update blocks list
    app.update_blocks_list()

    # Instructions
    tk.Label(left_frame, text=app.lang.get("drag_to_canvas"),
             fg="gray", justify="center").pack(pady=5)

def create_middle_section(app):
    """Create the middle section with design canvas"""
    middle_frame = tk.LabelFrame(app.root, text=app.lang.get("workspace"), padx=10, pady=10)
    middle_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
    
    # Canvas with scrollbars
    canvas_frame = tk.Frame(middle_frame)
    canvas_frame.pack(fill="both", expand=True)
    
    # Canvas for blocks and connections
    app.canvas = tk.Canvas(canvas_frame, bg="white", scrollregion=(0, 0, 2000, 2000))
    
    # Scrollbars
    v_scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=app.canvas.yview)
    h_scrollbar = tk.Scrollbar(canvas_frame, orient="horizontal", command=app.canvas.xview)
    app.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
    
    # Grid layout
    v_scrollbar.pack(side="right", fill="y")
    h_scrollbar.pack(side="bottom", fill="x")
    app.canvas.pack(side="left", fill="both", expand=True)
    
    # Draw grid
    app.draw_grid()
    
    # Initialize drag variables
    app.drag_start_x = 0
    app.drag_start_y = 0
    app.scrolling = False
    
    # Bind canvas events
    app.canvas.bind("<Button-1>", app.canvas_click)
    app.canvas.bind("<B1-Motion>", app.canvas_drag)
    app.canvas.bind("<ButtonRelease-1>", app.canvas_release)
    app.canvas.bind("<Button-3>", app.canvas_right_click)
    
    # Allow drag to scroll
    app.canvas.bind("<ButtonPress-2>", app.scroll_start)
    app.canvas.bind("<B2-Motion>", app.scroll_move)
    app.canvas.bind("<ButtonPress-3>", app.scroll_start)
    app.canvas.bind("<B3-Motion>", app.scroll_move)

def create_right_section(app):
    """Create the right section with block editor"""
    app.right_frame = tk.LabelFrame(app.root, text=app.lang.get("block_editor"), padx=10, pady=10)
    app.right_frame.grid(row=1, column=2, sticky="nsew", padx=5, pady=5)
    
    # Initially empty - will be populated when block is selected
    app.editor_frame = tk.Frame(app.right_frame)
    app.editor_frame.pack(fill="both", expand=True)
    
    tk.Label(app.editor_frame, text=app.lang.get("select_block"), 
            fg="gray").pack(expand=True)