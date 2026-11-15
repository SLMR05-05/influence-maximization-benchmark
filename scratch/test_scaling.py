import customtkinter as ctk

app = ctk.CTk()
lbl = ctk.CTkLabel(app, text="Hello World", font=("Segoe UI", 11))
lbl.pack()
print("Initial scaling:", ctk.ScalingTracker.get_widget_scaling(lbl))

ctk.set_widget_scaling(1.2)
print("Updated scaling:", ctk.ScalingTracker.get_widget_scaling(lbl))
app.destroy()
print("Scaling test passed!")
