# utils/chart_helper.py
# Helper untuk membuat grafik matplotlib yang di-embed ke CustomTkinter

"""
Utility untuk membuat dan embed grafik matplotlib ke dalam
frame CustomTkinter menggunakan FigureCanvasTkAgg.

Digunakan oleh Dashboard Admin Kota untuk analitik.
"""

import matplotlib
matplotlib.use("TkAgg")  # Backend untuk Tkinter

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import customtkinter as ctk


# Konfigurasi style matplotlib untuk dark mode
def configure_chart_style(dark_mode: bool = True):
    """Set style matplotlib sesuai tema aplikasi."""
    if dark_mode:
        plt.style.use("dark_background")
        plt.rcParams.update({
            "figure.facecolor": "#2B2B2B",
            "axes.facecolor": "#2B2B2B",
            "text.color": "#FFFFFF",
            "axes.labelcolor": "#FFFFFF",
            "xtick.color": "#CCCCCC",
            "ytick.color": "#CCCCCC",
        })
    else:
        plt.style.use("default")


def create_pie_chart(parent: ctk.CTkFrame, labels: list, values: list,
                     title: str = "", colors: list = None) -> FigureCanvasTkAgg:
    """
    Buat pie chart dan embed ke frame CTk.
    Returns: FigureCanvasTkAgg object.
    """
    fig = Figure(figsize=(5, 4), dpi=100)
    ax = fig.add_subplot(111)
    
    if colors is None:
        colors = ["#3498DB", "#2ECC71", "#E74C3C", "#F39C12",
                  "#9B59B6", "#1ABC9C", "#E67E22", "#95A5A6"]
    
    ax.pie(values, labels=labels, colors=colors[:len(labels)],
           autopct='%1.1f%%', startangle=90)
    ax.set_title(title, fontsize=14, fontweight="bold", pad=20)
    
    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    return canvas


def create_bar_chart(parent: ctk.CTkFrame, labels: list, values: list,
                     title: str = "", xlabel: str = "",
                     ylabel: str = "", color: str = "#3498DB") -> FigureCanvasTkAgg:
    """
    Buat bar chart dan embed ke frame CTk.
    Returns: FigureCanvasTkAgg object.
    """
    fig = Figure(figsize=(6, 4), dpi=100)
    ax = fig.add_subplot(111)
    
    bars = ax.bar(labels, values, color=color, edgecolor="white", linewidth=0.5)
    ax.set_title(title, fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    
    # Rotasi label x jika terlalu panjang
    if any(len(str(l)) > 8 for l in labels):
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    
    fig.tight_layout()
    
    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    return canvas


def create_line_chart(parent: ctk.CTkFrame, x_data: list, y_data: list,
                      title: str = "", xlabel: str = "",
                      ylabel: str = "", color: str = "#2ECC71") -> FigureCanvasTkAgg:
    """
    Buat line chart dan embed ke frame CTk.
    Returns: FigureCanvasTkAgg object.
    """
    fig = Figure(figsize=(6, 4), dpi=100)
    ax = fig.add_subplot(111)
    
    ax.plot(x_data, y_data, color=color, marker="o", linewidth=2, markersize=6)
    ax.fill_between(x_data, y_data, alpha=0.1, color=color)
    ax.set_title(title, fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.3)
    
    fig.tight_layout()
    
    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    return canvas
