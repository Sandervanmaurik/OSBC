#!/usr/bin/env python3
"""
Test script to verify sidebar toggle width changes correctly.
"""
import customtkinter as ctk

def main():
    root = ctk.CTk()
    root.geometry('1000x700')
    root.title('Sidebar Toggle Test')
    
    # Grid layout - same as OSBC.py
    root.grid_columnconfigure(0, weight=0, minsize=180)  # Sidebar
    root.grid_columnconfigure(1, weight=1)  # Middle
    root.grid_columnconfigure(2, weight=0, minsize=280)  # Stats
    root.grid_rowconfigure(0, weight=1)
    
    # Sidebar frame
    sidebar = ctk.CTkFrame(root, fg_color="#242424", width=180, corner_radius=0)
    sidebar.grid(row=0, column=0, sticky="nswe", padx=0, pady=0)
    sidebar.grid_propagate(False)  # KEY: Don't let children control size
    
    # Add some buttons with padding (like the real sidebar)
    toggle_btn = ctk.CTkButton(
        sidebar, 
        text="☰", 
        width=160, 
        height=40,
        fg_color="#2E2E2E"
    )
    toggle_btn.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
    
    script_btn1 = ctk.CTkButton(
        sidebar, 
        text="🎣 Fishing", 
        width=160, 
        height=40,
        fg_color="#2E2E2E"
    )
    script_btn1.grid(row=1, column=0, padx=10, pady=3, sticky="ew")
    
    script_btn2 = ctk.CTkButton(
        sidebar, 
        text="🪓 Woodcutting", 
        width=160, 
        height=40,
        fg_color="#2E2E2E"
    )
    script_btn2.grid(row=2, column=0, padx=10, pady=3, sticky="ew")
    
    # Middle panel
    middle = ctk.CTkFrame(root, fg_color="transparent")
    middle.grid(row=0, column=1, sticky="nswe")
    
    middle_label = ctk.CTkLabel(
        middle, 
        text="Middle Panel\n(Should expand when sidebar collapses)",
        font=("Roboto", 20)
    )
    middle_label.pack(expand=True)
    
    # Stats panel
    stats = ctk.CTkFrame(root, fg_color="#1A1A1A", width=280)
    stats.grid(row=0, column=2, sticky="nswe")
    stats_label = ctk.CTkLabel(stats, text="Stats Panel\n(280px fixed)")
    stats_label.pack(pady=20)
    
    # Toggle function
    is_collapsed = [False]  # Use list to modify in closure
    
    def toggle_sidebar():
        is_collapsed[0] = not is_collapsed[0]
        
        if is_collapsed[0]:
            print("Collapsing sidebar to 50px...")
            sidebar.configure(width=50)
            sidebar.grid_configure(sticky="ns")  # Only vertical stretch
            root.grid_columnconfigure(0, minsize=0)  # Remove minsize
            
            # Update buttons
            toggle_btn.configure(text="☰", width=40)
            script_btn1.configure(text="🎣", width=40)
            script_btn2.configure(text="🪓", width=40)
        else:
            print("Expanding sidebar to 180px...")
            sidebar.configure(width=180)
            sidebar.grid_configure(sticky="nswe")  # Fill column
            root.grid_columnconfigure(0, minsize=180)
            
            # Update buttons
            toggle_btn.configure(text="☰", width=160)
            script_btn1.configure(text="🎣 Fishing", width=160)
            script_btn2.configure(text="🪓 Woodcutting", width=160)
        
        # Force layout update
        root.update_idletasks()
        actual_width = sidebar.winfo_width()
        print(f"Sidebar actual width: {actual_width}px")
        print(f"Expected: {'50px' if is_collapsed[0] else '180px'}")
        print(f"Success: {actual_width == (50 if is_collapsed[0] else 180)}\n")
    
    toggle_btn.configure(command=toggle_sidebar)
    
    # Add a control panel button too
    control_btn = ctk.CTkButton(
        middle, 
        text="Toggle Sidebar (Click here or button in sidebar)",
        command=toggle_sidebar,
        font=("Roboto", 16),
        height=50
    )
    control_btn.pack(pady=20)
    
    # Show initial width
    root.after(100, lambda: print(f"Initial sidebar width: {sidebar.winfo_width()}px\n"))
    
    root.mainloop()

if __name__ == "__main__":
    main()
