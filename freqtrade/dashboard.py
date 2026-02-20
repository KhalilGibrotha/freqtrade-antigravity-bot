import time
import requests
import sys
from datetime import datetime
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich import box

# Configuration
API_URL = "http://localhost:8080/api/v1"
AUTH = ("freqtrader", "SuperSecurePassword123!")
REFRESH_RATE = 2  # Seconds

console = Console()

def fetch_data(endpoint):
    try:
        response = requests.get(f"{API_URL}/{endpoint}", auth=AUTH, timeout=2)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException:
        pass
    return None

def make_header():
    grid = Table.grid(expand=True)
    grid.add_column(justify="left")
    grid.add_column(justify="center")
    grid.add_column(justify="right")
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    grid.add_row(
        "Freqtrade Antigravity Bot",
        "[bold magenta]GLACIAL ECLIPSE DASHBOARD[/bold magenta]",
        timestamp
    )
    return Panel(grid, style="white on blue")

def make_heartbeat(ping_data):
    if ping_data and ping_data.get("status") == "pong":
        return Panel(Align.center("[bold green]● ONLINE[/bold green]\nSystem Functional"), title="Heartbeat", border_style="green")
    else:
        return Panel(Align.center("[bold red]○ OFFLINE[/bold red]\nConnection Lost"), title="Heartbeat", border_style="red")

def make_profit_summary(profit_data):
    if not profit_data:
        return Panel(Align.center("No Data"), title="Profit Summary")
    
    # Extract metrics
    profit_closed_coin = profit_data.get("profit_closed_coin", 0)
    profit_all_coin = profit_data.get("profit_all_coin", 0)
    winrate = profit_data.get("winrate", 0) * 100
    count = profit_data.get("trade_count", 0)
    
    table = Table.grid(expand=True)
    table.add_column(justify="left")
    table.add_column(justify="right")
    
    color = "green" if profit_all_coin >= 0 else "red"
    
    table.add_row("Total Profit:", f"[{color}]{profit_all_coin:.2f} USDT[/{color}]")
    table.add_row("Win Rate:", f"{winrate:.1f}%")
    table.add_row("Trade Count:", str(count))
    
    return Panel(table, title="Performance", border_style="cyan")

def make_trades_table(trades_data):
    table = Table(title="Active Trades", expand=True, box=box.SIMPLE_HEAD)
    table.add_column("Pair")
    table.add_column("Open Date")
    table.add_column("Profit %", justify="right")
    table.add_column("Amount", justify="right")
    
    trades = trades_data.get("trades", []) if trades_data else []
    
    if not trades:
        table.add_row("-", "-", "-", "-")
    else:
        for trade in trades:
            profit = trade['profit_ratio'] * 100
            color = "green" if profit >= 0 else "red"
            pair = trade['pair']
            open_date = trade['open_date_human']
            amount = trade['amount']
            
            table.add_row(
                pair,
                open_date,
                f"[{color}]{profit:.2f}%[/{color}]",
                f"{amount:.4f}"
            )
            
    return Panel(table, border_style="yellow")

def make_balance_info(balance_data):
    if not balance_data:
        return Panel("No Data", title="Balance")
        
    currencies = balance_data.get("currencies", [])
    total_usdt = balance_data.get("total", 0)
    
    table = Table.grid(expand=True)
    table.add_column("Coin")
    table.add_column("Balance", justify="right")
    
    for coin in currencies:
        if coin['balance'] > 0:
            table.add_row(coin['currency'], f"{coin['balance']:.4f}")
            
    table.add_row("---", "---")
    table.add_row("Est. USDT", f"{total_usdt:.2f}")

    return Panel(table, title="Wallet Risk/Exposure", border_style="magenta")

def generate_layout():
    layout = Layout()
    layout.split(
        Layout(name="header", size=3),
        Layout(name="main", ratio=1)
    )
    
    layout["main"].split_row(
        Layout(name="left", ratio=1),
        Layout(name="right", ratio=2)
    )
    
    layout["left"].split(
        Layout(name="heartbeat", size=4),
        Layout(name="profit", size=6),
        Layout(name="balance", ratio=1)
    )
    
    return layout

def update_dashboard(layout):
    # Fetch Data
    ping = fetch_data("ping")
    profit = fetch_data("profit")
    trades = fetch_data("status")
    balance = fetch_data("balance")
    
    # Update Components
    layout["header"].update(make_header())
    layout["heartbeat"].update(make_heartbeat(ping))
    layout["profit"].update(make_profit_summary(profit))
    layout["balance"].update(make_balance_info(balance))
    layout["right"].update(make_trades_table(trades))

if __name__ == "__main__":
    layout = generate_layout()
    
    console.clear()
    console.print("[yellow]Connecting to Freqtrade Bot...[/yellow]")
    
    try:
        with Live(layout, refresh_per_second=1, screen=True):
            while True:
                update_dashboard(layout)
                time.sleep(REFRESH_RATE)
    except KeyboardInterrupt:
        print("\nDashboard closed.")
