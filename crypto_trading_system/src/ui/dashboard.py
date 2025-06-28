"""
Dashboard UI module for the Cryptocurrency Trading System.

This module provides a web-based dashboard with a futuristic 3D/neon UI
for visualizing cryptocurrency analysis and trading data.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

from ..config import settings
from ..utils.helpers import setup_logging
from ..models.data_models import TradingSignal

# Set up logging
logger = setup_logging("dashboard")

# Initialize the Dash app with a dark theme
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.CYBORG],  # Dark theme with neon accents
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ],
)

# Set the title
app.title = "Crypto Trading System - Futuristic Dashboard"

# Define neon colors for the UI
NEON_COLORS = {
    "blue": "#00f3ff",
    "pink": "#ff00ff",
    "green": "#00ff9f",
    "yellow": "#ffff00",
    "orange": "#ff9900",
    "purple": "#9900ff",
    "red": "#ff0033",
    "white": "#ffffff",
}

# Define signal colors
SIGNAL_COLORS = {
    TradingSignal.STRONG_BUY.value: NEON_COLORS["green"],
    TradingSignal.BUY.value: NEON_COLORS["blue"],
    TradingSignal.NEUTRAL.value: NEON_COLORS["white"],
    TradingSignal.SELL.value: NEON_COLORS["orange"],
    TradingSignal.STRONG_SELL.value: NEON_COLORS["red"],
}

# Define the app layout with a futuristic theme
app.layout = dbc.Container(
    fluid=True,
    className="dashboard-container",
    style={
        "backgroundColor": "#000000",
        "color": NEON_COLORS["white"],
        "fontFamily": "'Orbitron', sans-serif",
        "minHeight": "100vh",
        "padding": "20px",
        "backgroundImage": "radial-gradient(circle, #0a0a0a 0%, #000000 100%)",
    },
    children=[
        # Custom CSS for futuristic styling
        html.Link(
            href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;700&display=swap",
            rel="stylesheet",
        ),
        
        # Header with glowing title
        html.Div(
            className="header",
            style={
                "textAlign": "center",
                "marginBottom": "30px",
                "borderBottom": f"1px solid {NEON_COLORS['blue']}",
                "paddingBottom": "20px",
            },
            children=[
                html.H1(
                    "CRYPTOCURRENCY TRADING SYSTEM",
                    className="glow-text",
                    style={
                        "color": "#FFFFFF",  # Changed to white for better contrast
                        "backgroundColor": "#000000",  # Added black background
                        "textShadow": f"0 0 10px {NEON_COLORS['blue']}, 0 0 20px {NEON_COLORS['blue']}",
                        "letterSpacing": "3px",
                        "fontWeight": "bold",
                        "padding": "10px",
                        "borderRadius": "5px",
                    },
                ),
                html.H3(
                    "ADVANCED ANALYSIS & AUTOMATED TRADING",
                    style={
                        "color": "#FFFFFF",  # Changed to white for better contrast
                        "backgroundColor": "#000000",  # Added black background
                        "textShadow": f"0 0 5px {NEON_COLORS['pink']}",
                        "letterSpacing": "2px",
                        "fontWeight": "bold",  # Added bold
                        "padding": "5px",
                        "borderRadius": "5px",
                    },
                ),
                html.Div(
                    id="live-clock",
                    style={
                        "color": NEON_COLORS["green"],
                        "fontSize": "1.2rem",
                        "marginTop": "10px",
                    },
                ),
                dcc.Interval(
                    id="interval-component",
                    interval=1000,  # in milliseconds
                    n_intervals=0,
                ),
            ],
        ),
        
        # Main content area
        dbc.Row(
            [
                # Left sidebar with controls
                dbc.Col(
                    width=3,
                    className="sidebar",
                    style={
                        "backgroundColor": "#0a0a0a",
                        "borderRight": f"1px solid {NEON_COLORS['blue']}",
                        "padding": "20px",
                        "boxShadow": f"0 0 10px {NEON_COLORS['blue']}",
                        "borderRadius": "10px",
                        "marginRight": "20px",
                    },
                    children=[
                        html.H4(
                            "CONTROL PANEL",
                            style={
                                "color": NEON_COLORS["yellow"],
                                "textAlign": "center",
                                "marginBottom": "20px",
                                "textShadow": f"0 0 5px {NEON_COLORS['yellow']}",
                            },
                        ),
                        
                        # Symbol selection
                        html.Div(
                            [
                                html.Label(
                                    "SELECT CRYPTOCURRENCY",
                                    style={
                                        "color": "#FFFFFF",  # Changed to white for better contrast
                                        "backgroundColor": "#0a0a0a",  # Dark background
                                        "padding": "5px",
                                        "fontWeight": "bold",  # Added bold
                                        "borderRadius": "3px",
                                        "border": f"1px solid {NEON_COLORS['green']}",
                                    },
                                ),
                                dcc.Dropdown(
                                    id="symbol-dropdown",
                                    options=[
                                        {"label": "Bitcoin (BTC-USD)", "value": "BTC-USD"},
                                        {"label": "Ethereum (ETH-USD)", "value": "ETH-USD"},
                                        {"label": "Cardano (ADA-USD)", "value": "ADA-USD"},
                                        {"label": "Solana (SOL-USD)", "value": "SOL-USD"},
                                        {"label": "Ripple (XRP-USD)", "value": "XRP-USD"},
                                    ],
                                    value="BTC-USD",
                                    className="futuristic-dropdown",
                                    style={
                                        "backgroundColor": "#0a0a0a",
                                        "color": "#FFFFFF",  # Changed to white for better contrast
                                        "border": f"1px solid {NEON_COLORS['green']}",
                                        "borderRadius": "5px",
                                        "fontWeight": "bold",  # Added bold
                                    },
                                ),
                            ],
                            style={"marginBottom": "20px"},
                        ),
                        
                        # Time range selection
                        html.Div(
                            [
                                html.Label(
                                    "SELECT TIME RANGE",
                                    style={
                                        "color": "#FFFFFF",  # Changed to white for better contrast
                                        "backgroundColor": "#0a0a0a",  # Dark background
                                        "padding": "5px",
                                        "fontWeight": "bold",  # Added bold
                                        "borderRadius": "3px",
                                        "border": f"1px solid {NEON_COLORS['green']}",
                                    },
                                ),
                                dcc.RadioItems(
                                    id="timerange-radio",
                                    options=[
                                        {"label": "1 Hour", "value": "1h"},  # Added 1 hour timeframe
                                        {"label": "24 Hours", "value": "1d"},
                                        {"label": "7 Days", "value": "7d"},
                                        {"label": "30 Days", "value": "30d"},
                                        {"label": "90 Days", "value": "90d"},
                                    ],
                                    value="1h",  # Default to 1 hour for rapid trading
                                    className="futuristic-radio",
                                    style={
                                        "color": "#FFFFFF",  # Changed to white for better contrast
                                        "marginTop": "10px",
                                        "fontWeight": "bold",  # Added bold
                                    },
                                    labelStyle={
                                        "display": "block",
                                        "marginBottom": "10px",
                                        "padding": "10px",
                                        "border": f"1px solid {NEON_COLORS['blue']}",
                                        "borderRadius": "5px",
                                        "transition": "all 0.3s ease",
                                        "backgroundColor": "#0a0a0a",  # Dark background for contrast
                                    },
                                ),
                            ],
                            style={"marginBottom": "20px"},
                        ),
                        
                        # Analysis type selection
                        html.Div(
                            [
                                html.Label(
                                    "ANALYSIS TYPE",
                                    style={
                                        "color": "#FFFFFF",  # Changed to white for better contrast
                                        "backgroundColor": "#0a0a0a",  # Dark background
                                        "padding": "5px",
                                        "fontWeight": "bold",  # Added bold
                                        "borderRadius": "3px",
                                        "border": f"1px solid {NEON_COLORS['green']}",
                                    },
                                ),
                                dcc.Checklist(
                                    id="analysis-checklist",
                                    options=[
                                        {"label": "Technical", "value": "technical"},
                                        {"label": "Sentiment", "value": "sentiment"},
                                        {"label": "Market Data", "value": "market"},
                                        {"label": "Project Fundamentals", "value": "project"},
                                    ],
                                    value=["technical", "sentiment", "market"],
                                    className="futuristic-checklist",
                                    style={
                                        "color": "#FFFFFF",  # Changed to white for better contrast
                                        "marginTop": "10px",
                                        "fontWeight": "bold",  # Added bold
                                    },
                                    labelStyle={
                                        "display": "block",
                                        "marginBottom": "10px",
                                        "padding": "10px",
                                        "border": f"1px solid {NEON_COLORS['purple']}",
                                        "borderRadius": "5px",
                                        "transition": "all 0.3s ease",
                                        "backgroundColor": "#0a0a0a",  # Dark background for contrast
                                    },
                                ),
                            ],
                            style={"marginBottom": "20px"},
                        ),
                        
                        # Action buttons
                        html.Div(
                            [
                                dbc.Button(
                                    "ANALYZE NOW",
                                    id="analyze-button",
                                    color="success",
                                    className="me-2 futuristic-button",
                                    style={
                                        "backgroundColor": "#000000",  # Black background for contrast
                                        "color": "#FFFFFF",  # White text for better contrast
                                        "border": f"2px solid {NEON_COLORS['green']}",
                                        "boxShadow": f"0 0 10px {NEON_COLORS['green']}",
                                        "marginRight": "10px",
                                        "width": "48%",
                                        "fontWeight": "bold",  # Added bold
                                        "fontSize": "1.1rem",  # Larger text
                                    },
                                ),
                                dbc.Button(
                                    "EXECUTE TRADE",
                                    id="trade-button",
                                    color="warning",
                                    className="futuristic-button",
                                    style={
                                        "backgroundColor": "#000000",  # Black background for contrast
                                        "color": "#FFFFFF",  # White text for better contrast
                                        "border": f"2px solid {NEON_COLORS['orange']}",
                                        "boxShadow": f"0 0 10px {NEON_COLORS['orange']}",
                                        "width": "48%",
                                        "fontWeight": "bold",  # Added bold
                                        "fontSize": "1.1rem",  # Larger text
                                    },
                                ),
                            ],
                            style={"display": "flex", "justifyContent": "space-between", "marginBottom": "20px"},
                        ),
                        
                        # Portfolio summary
                        html.Div(
                            [
                                html.H5(
                                    "PORTFOLIO SUMMARY",
                                    style={
                                        "color": "#FFFFFF",  # Changed to white for better contrast
                                        "backgroundColor": "#0a0a0a",  # Dark background
                                        "textAlign": "center",
                                        "marginBottom": "15px",
                                        "textShadow": f"0 0 5px {NEON_COLORS['yellow']}",
                                        "padding": "5px",
                                        "fontWeight": "bold",  # Added bold
                                        "borderRadius": "3px",
                                        "border": f"1px solid {NEON_COLORS['yellow']}",
                                    },
                                ),
                                html.Div(
                                    id="portfolio-summary",
                                    className="portfolio-card",
                                    style={
                                        "backgroundColor": "#0a0a0a",
                                        "border": f"1px solid {NEON_COLORS['blue']}",
                                        "borderRadius": "10px",
                                        "padding": "15px",
                                        "boxShadow": f"0 0 5px {NEON_COLORS['blue']}",
                                    },
                                    children=[
                                        html.P(
                                            [
                                                html.Span(
                                                    "Total Value: ",
                                                    style={"color": "#FFFFFF", "fontWeight": "bold"},  # Improved contrast
                                                ),
                                                html.Span(
                                                    "$10,000.00",
                                                    style={"color": "#00FF00", "fontWeight": "bold"},  # Brighter green
                                                ),
                                            ]
                                        ),
                                        html.P(
                                            [
                                                html.Span(
                                                    "Cash Balance: ",
                                                    style={"color": "#FFFFFF", "fontWeight": "bold"},  # Improved contrast
                                                ),
                                                html.Span(
                                                    "$5,000.00",
                                                    style={"color": "#00FFFF", "fontWeight": "bold"},  # Brighter blue
                                                ),
                                            ]
                                        ),
                                        html.P(
                                            [
                                                html.Span(
                                                    "Invested: ",
                                                    style={"color": "#FFFFFF", "fontWeight": "bold"},  # Improved contrast
                                                ),
                                                html.Span(
                                                    "$5,000.00",
                                                    style={"color": "#FF00FF", "fontWeight": "bold"},  # Brighter purple
                                                ),
                                            ]
                                        ),
                                        html.P(
                                            [
                                                html.Span(
                                                    "Profit/Loss: ",
                                                    style={"color": "#FFFFFF", "fontWeight": "bold"},  # Improved contrast
                                                ),
                                                html.Span(
                                                    "+$500.00 (5%)",
                                                    style={"color": "#00FF00", "fontWeight": "bold"},  # Brighter green
                                                ),
                                            ]
                                        ),
                                    ],
                                ),
                            ],
                            style={"marginBottom": "20px"},
                        ),
                    ],
                ),
                
                # Main content area
                dbc.Col(
                    width=9,
                    children=[
                        # Top row with key metrics
                        dbc.Row(
                            [
                                # Current price card
                                dbc.Col(
                                    width=4,
                                    children=[
                                        html.Div(
                                            className="metric-card",
                                            style={
                                                "backgroundColor": "#0a0a0a",
                                                "border": f"1px solid {NEON_COLORS['green']}",
                                                "borderRadius": "10px",
                                                "padding": "15px",
                                                "boxShadow": f"0 0 10px {NEON_COLORS['green']}",
                                                "height": "100%",
                                            },
                                            children=[
                                                html.H5(
                                                    "CURRENT PRICE",
                                                    style={
                                                        "color": NEON_COLORS["green"],
                                                        "textAlign": "center",
                                                        "marginBottom": "10px",
                                                    },
                                                ),
                                                html.Div(
                                                    id="current-price",
                                                    style={
                                                        "fontSize": "2rem",
                                                        "fontWeight": "bold",
                                                        "textAlign": "center",
                                                        "color": NEON_COLORS["white"],
                                                    },
                                                    children="$107,414.83",
                                                ),
                                                html.Div(
                                                    id="price-change",
                                                    style={
                                                        "fontSize": "1.2rem",
                                                        "textAlign": "center",
                                                        "color": NEON_COLORS["green"],
                                                    },
                                                    children="+2.5%",
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                                
                                # Trading signal card
                                dbc.Col(
                                    width=4,
                                    children=[
                                        html.Div(
                                            className="metric-card",
                                            style={
                                                "backgroundColor": "#0a0a0a",
                                                "border": f"1px solid {NEON_COLORS['blue']}",
                                                "borderRadius": "10px",
                                                "padding": "15px",
                                                "boxShadow": f"0 0 10px {NEON_COLORS['blue']}",
                                                "height": "100%",
                                            },
                                            children=[
                                                html.H5(
                                                    "TRADING SIGNAL",
                                                    style={
                                                        "color": NEON_COLORS["blue"],
                                                        "textAlign": "center",
                                                        "marginBottom": "10px",
                                                    },
                                                ),
                                                html.Div(
                                                    id="trading-signal",
                                                    style={
                                                        "fontSize": "2rem",
                                                        "fontWeight": "bold",
                                                        "textAlign": "center",
                                                        "color": NEON_COLORS["green"],
                                                    },
                                                    children="BUY",
                                                ),
                                                html.Div(
                                                    id="signal-confidence",
                                                    style={
                                                        "fontSize": "1.2rem",
                                                        "textAlign": "center",
                                                        "color": NEON_COLORS["white"],
                                                    },
                                                    children="Confidence: 85%",
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                                
                                # Sentiment card
                                dbc.Col(
                                    width=4,
                                    children=[
                                        html.Div(
                                            className="metric-card",
                                            style={
                                                "backgroundColor": "#0a0a0a",
                                                "border": f"1px solid {NEON_COLORS['yellow']}",
                                                "borderRadius": "10px",
                                                "padding": "15px",
                                                "boxShadow": f"0 0 10px {NEON_COLORS['yellow']}",
                                                "height": "100%",
                                            },
                                            children=[
                                                html.H5(
                                                    "MARKET SENTIMENT",
                                                    style={
                                                        "color": NEON_COLORS["yellow"],
                                                        "textAlign": "center",
                                                        "marginBottom": "10px",
                                                    },
                                                ),
                                                html.Div(
                                                    id="sentiment-value",
                                                    style={
                                                        "fontSize": "2rem",
                                                        "fontWeight": "bold",
                                                        "textAlign": "center",
                                                        "color": NEON_COLORS["green"],
                                                    },
                                                    children="65",
                                                ),
                                                html.Div(
                                                    id="sentiment-label",
                                                    style={
                                                        "fontSize": "1.2rem",
                                                        "textAlign": "center",
                                                        "color": NEON_COLORS["green"],
                                                    },
                                                    children="Greed",
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                            className="mb-4",
                        ),
                        
                        # Middle row with price chart
                        dbc.Row(
                            [
                                dbc.Col(
                                    width=12,
                                    children=[
                                        html.Div(
                                            className="chart-container",
                                            style={
                                                "backgroundColor": "#0a0a0a",
                                                "border": f"1px solid {NEON_COLORS['blue']}",
                                                "borderRadius": "10px",
                                                "padding": "15px",
                                                "boxShadow": f"0 0 10px {NEON_COLORS['blue']}",
                                                "marginBottom": "20px",
                                            },
                                            children=[
                                                html.H5(
                                                    "PRICE CHART",
                                                    style={
                                                        "color": NEON_COLORS["blue"],
                                                        "textAlign": "center",
                                                        "marginBottom": "10px",
                                                    },
                                                ),
                                                dcc.Graph(
                                                    id="price-chart",
                                                    config={"displayModeBar": False},
                                                    style={"height": "400px"},
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        
                        # Bottom row with analysis components
                        dbc.Row(
                            [
                                # Technical indicators
                                dbc.Col(
                                    width=6,
                                    children=[
                                        html.Div(
                                            className="analysis-container",
                                            style={
                                                "backgroundColor": "#0a0a0a",
                                                "border": f"1px solid {NEON_COLORS['purple']}",
                                                "borderRadius": "10px",
                                                "padding": "15px",
                                                "boxShadow": f"0 0 10px {NEON_COLORS['purple']}",
                                                "height": "100%",
                                            },
                                            children=[
                                                html.H5(
                                                    "TECHNICAL INDICATORS",
                                                    style={
                                                        "color": NEON_COLORS["purple"],
                                                        "textAlign": "center",
                                                        "marginBottom": "10px",
                                                    },
                                                ),
                                                dcc.Graph(
                                                    id="technical-indicators-chart",
                                                    config={"displayModeBar": False},
                                                    style={"height": "300px"},
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                                
                                # Score breakdown
                                dbc.Col(
                                    width=6,
                                    children=[
                                        html.Div(
                                            className="analysis-container",
                                            style={
                                                "backgroundColor": "#0a0a0a",
                                                "border": f"1px solid {NEON_COLORS['pink']}",
                                                "borderRadius": "10px",
                                                "padding": "15px",
                                                "boxShadow": f"0 0 10px {NEON_COLORS['pink']}",
                                                "height": "100%",
                                            },
                                            children=[
                                                html.H5(
                                                    "SCORE BREAKDOWN",
                                                    style={
                                                        "color": NEON_COLORS["pink"],
                                                        "textAlign": "center",
                                                        "marginBottom": "10px",
                                                    },
                                                ),
                                                dcc.Graph(
                                                    id="score-breakdown-chart",
                                                    config={"displayModeBar": False},
                                                    style={"height": "300px"},
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
        
        # Footer
        html.Div(
            className="footer",
            style={
                "textAlign": "center",
                "marginTop": "30px",
                "borderTop": f"1px solid {NEON_COLORS['blue']}",
                "paddingTop": "20px",
            },
            children=[
                html.P(
                    "CRYPTO TRADING SYSTEM © 2025",
                    style={
                        "color": NEON_COLORS["blue"],
                        "textShadow": f"0 0 5px {NEON_COLORS['blue']}",
                    },
                ),
                html.P(
                    "POWERED BY ADVANCED AI ANALYTICS",
                    style={
                        "color": NEON_COLORS["green"],
                        "fontSize": "0.8rem",
                    },
                ),
            ],
        ),
        
        # Store for holding data
        dcc.Store(id="analysis-data-store"),
    ],
)

# Callback to update the clock
@app.callback(
    Output("live-clock", "children"),
    Input("interval-component", "n_intervals"),
)
def update_clock(n):
    """Update the live clock."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Callback to generate the price chart
@app.callback(
    Output("price-chart", "figure"),
    [Input("symbol-dropdown", "value"), Input("timerange-radio", "value")],
)
def update_price_chart(symbol, timerange):
    """Generate the price chart for the selected symbol and timerange."""
    # In a real implementation, this would fetch data from the backend
    # For now, we'll generate some sample data
    
    # Generate sample dates
    if timerange == "1d":
        n_points = 24
        date_range = pd.date_range(end=datetime.now(), periods=n_points, freq="H")
    elif timerange == "7d":
        n_points = 7
        date_range = pd.date_range(end=datetime.now(), periods=n_points, freq="D")
    elif timerange == "30d":
        n_points = 30
        date_range = pd.date_range(end=datetime.now(), periods=n_points, freq="D")
    else:  # 90d
        n_points = 90
        date_range = pd.date_range(end=datetime.now(), periods=n_points, freq="D")
    
    # Generate sample prices
    if symbol == "BTC-USD":
        base_price = 107000
    elif symbol == "ETH-USD":
        base_price = 3500
    elif symbol == "ADA-USD":
        base_price = 0.5
    elif symbol == "SOL-USD":
        base_price = 150
    else:  # XRP-USD
        base_price = 0.7
    
    # Add some randomness to the prices
    np.random.seed(42)  # For reproducibility
    price_changes = np.cumsum(np.random.normal(0, base_price * 0.01, n_points))
    prices = base_price + price_changes
    
    # Create a DataFrame
    df = pd.DataFrame({
        "date": date_range,
        "price": prices,
    })
    
    # Create the figure
    fig = go.Figure()
    
    # Add the price line
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["price"],
            mode="lines",
            name=symbol,
            line=dict(color=NEON_COLORS["blue"], width=3),
            fill="tozeroy",
            fillcolor=f"rgba(0, 243, 255, 0.1)",
        )
    )
    
    # Add buy/sell markers (sample data)
    buy_dates = df["date"][::5]  # Every 5th point
    buy_prices = df["price"][::5]
    
    sell_dates = df["date"][2::5]  # Every 5th point, offset by 2
    sell_prices = df["price"][2::5]
    
    fig.add_trace(
        go.Scatter(
            x=buy_dates,
            y=buy_prices,
            mode="markers",
            name="Buy Signal",
            marker=dict(
                color=NEON_COLORS["green"],
                size=12,
                symbol="triangle-up",
                line=dict(color=NEON_COLORS["green"], width=2),
            ),
        )
    )
    
    fig.add_trace(
        go.Scatter(
            x=sell_dates,
            y=sell_prices,
            mode="markers",
            name="Sell Signal",
            marker=dict(
                color=NEON_COLORS["red"],
                size=12,
                symbol="triangle-down",
                line=dict(color=NEON_COLORS["red"], width=2),
            ),
        )
    )
    
    # Update the layout
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color=NEON_COLORS["white"]),
        ),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=True,
            linecolor=NEON_COLORS["blue"],
            linewidth=2,
            showticklabels=True,
            tickfont=dict(color=NEON_COLORS["white"]),
            title=dict(text="", font=dict(color=NEON_COLORS["white"])),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(0, 243, 255, 0.1)",
            zeroline=False,
            showline=True,
            linecolor=NEON_COLORS["blue"],
            linewidth=2,
            showticklabels=True,
            tickfont=dict(color=NEON_COLORS["white"]),
            title=dict(text="", font=dict(color=NEON_COLORS["white"])),
        ),
        hovermode="x unified",
    )
    
    return fig

# Callback to generate the technical indicators chart
@app.callback(
    Output("technical-indicators-chart", "figure"),
    [Input("symbol-dropdown", "value")],
)
def update_technical_indicators_chart(symbol):
    """Generate the technical indicators chart for the selected symbol."""
    # In a real implementation, this would fetch data from the backend
    # For now, we'll generate some sample data
    
    # Define the indicators
    indicators = ["RSI", "MACD", "SMA", "EMA", "Bollinger"]
    
    # Generate sample scores
    np.random.seed(hash(symbol) % 100)  # Different seed for each symbol
    scores = np.random.uniform(-1, 1, len(indicators))
    
    # Define colors based on scores
    colors = []
    for score in scores:
        if score > 0.5:
            colors.append(NEON_COLORS["green"])
        elif score > 0:
            colors.append(NEON_COLORS["blue"])
        elif score > -0.5:
            colors.append(NEON_COLORS["orange"])
        else:
            colors.append(NEON_COLORS["red"])
    
    # Create the figure
    fig = go.Figure()
    
    # Add the bars
    fig.add_trace(
        go.Bar(
            x=indicators,
            y=scores,
            marker_color=colors,
            text=[f"{score:.2f}" for score in scores],
            textposition="auto",
        )
    )
    
    # Update the layout
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=True,
            linecolor=NEON_COLORS["purple"],
            linewidth=2,
            showticklabels=True,
            tickfont=dict(color=NEON_COLORS["white"]),
            title=dict(text="", font=dict(color=NEON_COLORS["white"])),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(153, 0, 255, 0.1)",
            zeroline=True,
            zerolinecolor=NEON_COLORS["white"],
            zerolinewidth=2,
            showline=True,
            linecolor=NEON_COLORS["purple"],
            linewidth=2,
            showticklabels=True,
            tickfont=dict(color=NEON_COLORS["white"]),
            title=dict(text="", font=dict(color=NEON_COLORS["white"])),
            range=[-1, 1],
        ),
    )
    
    return fig

# Callback to generate the score breakdown chart
@app.callback(
    Output("score-breakdown-chart", "figure"),
    [Input("symbol-dropdown", "value")],
)
def update_score_breakdown_chart(symbol):
    """Generate the score breakdown chart for the selected symbol."""
    # In a real implementation, this would fetch data from the backend
    # For now, we'll generate some sample data
    
    # Define the categories
    categories = ["Technical", "Sentiment", "Market", "Project", "Overall"]
    
    # Generate sample scores
    np.random.seed(hash(symbol) % 100)  # Different seed for each symbol
    scores = np.random.uniform(-1, 1, len(categories))
    
    # Define colors based on scores
    colors = []
    for score in scores:
        if score > 0.5:
            colors.append(NEON_COLORS["green"])
        elif score > 0:
            colors.append(NEON_COLORS["blue"])
        elif score > -0.5:
            colors.append(NEON_COLORS["orange"])
        else:
            colors.append(NEON_COLORS["red"])
    
    # Create the figure
    fig = go.Figure()
    
    # Add the radar chart
    fig.add_trace(
        go.Scatterpolar(
            r=[score + 1 for score in scores],  # Shift to 0-2 range for better visualization
            theta=categories,
            fill="toself",
            fillcolor="rgba(255, 0, 255, 0.2)",
            line=dict(color=NEON_COLORS["pink"], width=3),
            name=symbol,
        )
    )
    
    # Update the layout
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=10, b=10),
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 2],
                showticklabels=False,
                gridcolor="rgba(255, 0, 255, 0.1)",
            ),
            angularaxis=dict(
                showticklabels=True,
                tickfont=dict(color=NEON_COLORS["white"]),
                gridcolor=NEON_COLORS["pink"],
            ),
            bgcolor="rgba(0,0,0,0)",
        ),
        showlegend=False,
    )
    
    return fig

# Callback for the analyze button
@app.callback(
    [
        Output("current-price", "children"),
        Output("price-change", "children"),
        Output("price-change", "style"),
        Output("trading-signal", "children"),
        Output("trading-signal", "style"),
        Output("signal-confidence", "children"),
        Output("sentiment-value", "children"),
        Output("sentiment-label", "children"),
        Output("sentiment-label", "style"),
    ],
    [Input("analyze-button", "n_clicks")],
    [State("symbol-dropdown", "value")],
)
def analyze_crypto(n_clicks, symbol):
    """Analyze the selected cryptocurrency."""
    if n_clicks is None:
        # Default values
        return (
            "$107,414.83",
            "+2.5%",
            {"fontSize": "1.2rem", "textAlign": "center", "color": NEON_COLORS["green"]},
            "BUY",
            {"fontSize": "2rem", "fontWeight": "bold", "textAlign": "center", "color": NEON_COLORS["green"]},
            "Confidence: 85%",
            "65",
            "Greed",
            {"fontSize": "1.2rem", "textAlign": "center", "color": NEON_COLORS["green"]},
        )
    
    # In a real implementation, this would fetch data from the backend
    # For now, we'll generate some sample data based on the symbol
    
    # Generate price and change
    if symbol == "BTC-USD":
        price = "$107,414.83"
        change_pct = 2.5
    elif symbol == "ETH-USD":
        price = "$3,521.67"
        change_pct = 1.8
    elif symbol == "ADA-USD":
        price = "$0.52"
        change_pct = -0.7
    elif symbol == "SOL-USD":
        price = "$152.34"
        change_pct = 3.2
    else:  # XRP-USD
        price = "$0.73"
        change_pct = -1.5
    
    # Format the change
    change_text = f"{'+' if change_pct > 0 else ''}{change_pct}%"
    change_style = {
        "fontSize": "1.2rem",
        "textAlign": "center",
        "color": NEON_COLORS["green"] if change_pct > 0 else NEON_COLORS["red"],
    }
    
    # Generate trading signal
    np.random.seed(hash(symbol) % 100)  # Different seed for each symbol
    signal_value = np.random.uniform(-1, 1)
    
    if signal_value > 0.5:
        signal = "STRONG BUY"
        signal_color = NEON_COLORS["green"]
    elif signal_value > 0:
        signal = "BUY"
        signal_color = NEON_COLORS["blue"]
    elif signal_value > -0.5:
        signal = "NEUTRAL"
        signal_color = NEON_COLORS["white"]
    elif signal_value > -0.8:
        signal = "SELL"
        signal_color = NEON_COLORS["orange"]
    else:
        signal = "STRONG SELL"
        signal_color = NEON_COLORS["red"]
    
    signal_style = {
        "fontSize": "2rem",
        "fontWeight": "bold",
        "textAlign": "center",
        "color": signal_color,
    }
    
    # Generate confidence
    confidence = int(abs(signal_value) * 100)
    confidence_text = f"Confidence: {confidence}%"
    
    # Generate sentiment
    sentiment_value = np.random.randint(0, 100)
    
    if sentiment_value >= 75:
        sentiment_label = "Extreme Greed"
        sentiment_color = NEON_COLORS["green"]
    elif sentiment_value >= 60:
        sentiment_label = "Greed"
        sentiment_color = NEON_COLORS["green"]
    elif sentiment_value >= 40:
        sentiment_label = "Neutral"
        sentiment_color = NEON_COLORS["white"]
    elif sentiment_value >= 25:
        sentiment_label = "Fear"
        sentiment_color = NEON_COLORS["orange"]
    else:
        sentiment_label = "Extreme Fear"
        sentiment_color = NEON_COLORS["red"]
    
    sentiment_style = {
        "fontSize": "1.2rem",
        "textAlign": "center",
        "color": sentiment_color,
    }
    
    return (
        price,
        change_text,
        change_style,
        signal,
        signal_style,
        confidence_text,
        str(sentiment_value),
        sentiment_label,
        sentiment_style,
    )

# Callback for the trade button
@app.callback(
    Output("portfolio-summary", "children"),
    [Input("trade-button", "n_clicks")],
    [
        State("symbol-dropdown", "value"),
        State("trading-signal", "children"),
    ],
)
def execute_trade(n_clicks, symbol, signal):
    """Execute a trade based on the trading signal."""
    if n_clicks is None:
        # Default portfolio
        return [
            html.P(
                [
                    "Total Value: ",
                    html.Span(
                        "$10,000.00",
                        style={"color": NEON_COLORS["green"], "fontWeight": "bold"},
                    ),
                ]
            ),
            html.P(
                [
                    "Cash Balance: ",
                    html.Span(
                        "$5,000.00",
                        style={"color": NEON_COLORS["blue"], "fontWeight": "bold"},
                    ),
                ]
            ),
            html.P(
                [
                    "Invested: ",
                    html.Span(
                        "$5,000.00",
                        style={"color": NEON_COLORS["purple"], "fontWeight": "bold"},
                    ),
                ]
            ),
            html.P(
                [
                    "Profit/Loss: ",
                    html.Span(
                        "+$500.00 (5%)",
                        style={"color": NEON_COLORS["green"], "fontWeight": "bold"},
                    ),
                ]
            ),
        ]
    
    # In a real implementation, this would execute a trade via the backend
    # For now, we'll just update the portfolio summary with some sample data
    
    # Generate new portfolio values based on the signal
    if signal in ["BUY", "STRONG BUY"]:
        total_value = 10500.00
        cash_balance = 3000.00
        invested = 7500.00
        profit_loss = 500.00
        profit_pct = 5.0
        profit_color = NEON_COLORS["green"]
    elif signal == "NEUTRAL":
        total_value = 10000.00
        cash_balance = 5000.00
        invested = 5000.00
        profit_loss = 0.00
        profit_pct = 0.0
        profit_color = NEON_COLORS["white"]
    else:  # SELL or STRONG SELL
        total_value = 9800.00
        cash_balance = 8000.00
        invested = 1800.00
        profit_loss = -200.00
        profit_pct = -2.0
        profit_color = NEON_COLORS["red"]
    
    # Format the profit/loss
    profit_text = f"{'+' if profit_loss > 0 else ''}{profit_loss:.2f} ({'+' if profit_pct > 0 else ''}{profit_pct:.1f}%)"
    
    # Create the updated portfolio summary
    return [
        html.P(
            [
                "Total Value: ",
                html.Span(
                    f"${total_value:.2f}",
                    style={"color": NEON_COLORS["green"], "fontWeight": "bold"},
                ),
            ]
        ),
        html.P(
            [
                "Cash Balance: ",
                html.Span(
                    f"${cash_balance:.2f}",
                    style={"color": NEON_COLORS["blue"], "fontWeight": "bold"},
                ),
            ]
        ),
        html.P(
            [
                "Invested: ",
                html.Span(
                    f"${invested:.2f}",
                    style={"color": NEON_COLORS["purple"], "fontWeight": "bold"},
                ),
            ]
        ),
        html.P(
            [
                "Profit/Loss: ",
                html.Span(
                    profit_text,
                    style={"color": profit_color, "fontWeight": "bold"},
                ),
            ]
        ),
        html.P(
            [
                "Last Trade: ",
                html.Span(
                    f"{signal} {symbol}",
                    style={"color": NEON_COLORS["yellow"], "fontWeight": "bold"},
                ),
            ]
        ),
    ]

def run_dashboard(host="0.0.0.0", port=8050, debug=False):
    """Run the dashboard."""
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    run_dashboard(debug=True)
