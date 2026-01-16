class CodeBlock:
    def __init__(self, block_id, block_type, x, y, width=120, height=60, text="", content=""):
        self.id = block_id
        self.type = block_type
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.content = content
        self.color = self.get_default_color()
        self.connections = []  # List of block IDs this block connects to (sequence)
        self.end_connection = None  # Block ID for end connection (for if/for/while)
        self.continue_connection = None  # Block ID for continue connection (for same-line connections)
        self.prev_connections = []  # List of block IDs that connect to this block
        self.next_block = None  # Direct next block in sequence
        self.canvas_ids = (None, None)  # Store canvas IDs for rectangle and text
        
    def get_default_color(self):
        """Return default color based on block type"""
        color_map = {
            "statement": "#4CAF50",  # Green
            "function": "#2196F3",   # Blue
            "control": "#FF9800",    # Orange
            "loop": "#9C27B0",       # Purple
            "io": "#F44336",         # Red
            "variable": "#009688",   # Teal
            "operator": "#FFC107",   # Amber
            "import": "#607D8B",     # Blue Grey
            "gui": "#FF5722",        # Deep Orange
            "class": "#673AB7",      # Deep Purple
            "method": "#3F51B5",     # Indigo
            "defining": "#FF4081",   # Pink - New color for defining blocks
        }
        return color_map.get(self.type, "#757575")  # Default Grey
    
    def get_connector_points(self):
        """Return connection points for the block"""
        top = (self.x + self.width/2, self.y)
        bottom = (self.x + self.width/2, self.y + self.height)
        left = (self.x, self.y + self.height/2)
        right = (self.x + self.width, self.y + self.height/2)
        
        return {
            "top": top,
            "bottom": bottom,
            "left": left,
            "right": right
        }
    
    def contains_point(self, x, y):
        """Check if point (x,y) is inside the block"""
        return (self.x <= x <= self.x + self.width and 
                self.y <= y <= self.y + self.height)
    
    def requires_indentation(self):
        """Check if this block type requires indentation and end block"""
        # Only defining, control, loop, class, and method blocks need indentation
        # Function calls (type "function") do NOT need indentation
        return self.type in ["control", "loop", "defining", "class", "method"]
    
    def move(self, dx, dy):
        """Move the block by dx, dy"""
        self.x += dx
        self.y += dy
    
    def to_dict(self):
        """Convert block to dictionary for serialization"""
        return {
            "id": self.id,
            "type": self.type,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "text": self.text,
            "content": self.content,
            "color": self.color,
            "connections": self.connections,
            "end_connection": self.end_connection,
            "continue_connection": self.continue_connection,
            "prev_connections": self.prev_connections
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create block from dictionary"""
        block = cls(
            data["id"],
            data["type"],
            data["x"],
            data["y"],
            data["width"],
            data["height"],
            data["text"],
            data["content"]
        )
        block.color = data.get("color", block.color)
        block.connections = data.get("connections", [])
        block.end_connection = data.get("end_connection")
        block.continue_connection = data.get("continue_connection")
        block.prev_connections = data.get("prev_connections", [])
        return block