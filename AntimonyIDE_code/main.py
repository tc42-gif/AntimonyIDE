import tkinter as tk
from ui import ScratchPythonBuilder

def main():
    root = tk.Tk()
    app = ScratchPythonBuilder(root)
    root.mainloop()

if __name__ == "__main__":
    main()