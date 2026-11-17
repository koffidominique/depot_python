from nicegui import ui

def apply_theme():
    ui.colors(
        primary='#2563eb',
        secondary='#1e40af',
        accent='#3b82f6',
        positive='#10b981',
        negative='#ef4444',
        warning='#f59e0b',
        info='#06b6d4'
    )
    ui.query('body').classes('bg-slate-50 text-slate-900')