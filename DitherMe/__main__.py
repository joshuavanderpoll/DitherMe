# pylint: disable=missing-module-docstring
import sys
import tkinter as tk
from app import DitherMe

if __name__ == "__main__":
    file_path = sys.argv[1] if len(sys.argv) > 1 else None
    root = tk.Tk()
    DitherMe(root, file_path)
    root.mainloop()
