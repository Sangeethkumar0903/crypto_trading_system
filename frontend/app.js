// API Configuration
const API_BASE_URL = 'http://localhost:8000';
const WS_BASE_URL = 'ws://localhost:8767'; // Use the port from your logs

// Global state
let state = {
    candles: {},
    ticks: {},
    positions: [],
    signals: [],
    trades: [],
    selectedSymbol: 'btcusdt',
    wsConnected: false,
    chart: null,
    candleSeries: null
};

// DOM Elements
const pages = document.querySelectorAll('.page');
const navItems = document.querySelectorAll('.nav-item');
const pageTitle = document.getElementById('pageTitle');
const symbolSelect = document.getElementById('symbolSelect');
const addSymbolBtn = document.getElementById('addSymbolBtn');
const addSymbolModal = document.getElementById('addSymbolModal');
const closeBtn = document.querySelector('.close');
const addSymbolForm = document.getElementById('addSymbolForm');
const toast = document.getElementById('toast');
const orderForm = document.getElementById('orderForm');
const orderType = document.getElementById('orderType');
const limitPriceGroup = document.getElementById('limitPriceGroup');
const wsStatus = document.getElementById('wsStatus');

// Initialize the application
async function init() {
    setupEventListeners();
    await fetchInitialData();
    initWebSocket();
    initChart();
    startDataPolling();
    updateSystemTime();
}

// Event Listeners
function setupEventListeners() {
    // Navigation
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const page = item.dataset.page;
            switchPage(page);
        });
    });

    // Symbol selector
    symbolSelect.addEventListener('change', (e) => {
        state.selectedSymbol = e.target.value;
        updateChartData();
        fetchCandles();
    });

    // Add symbol modal
    addSymbolBtn.addEventListener('click', () => {
        addSymbolModal.classList.add('active');
    });

    closeBtn.addEventListener('click', () => {
        addSymbolModal.classList.remove('active');
    });

    window.addEventListener('click', (e) => {
        if (e.target === addSymbolModal) {
            addSymbolModal.classList.remove('active');
        }
    });

    // Add symbol form
    addSymbolForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const symbol = document.getElementById('newSymbol').value.toLowerCase();
        await addSymbol(symbol);
    });

    // Order form
    orderType.addEventListener('change', (e) => {
        if (e.target.value === 'limit') {
            limitPriceGroup.style.display = 'flex';
        } else {
            limitPriceGroup.style.display = 'none';
        }
    });

    orderForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await placeOrder();
    });

    // Order side buttons
    document.querySelectorAll('.side-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.side-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // Signal filters
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const filter = this.dataset.filter;
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            filterSignals(filter);
        });
    });

    // Chart timeframe buttons
    document.querySelectorAll('.chart-controls .btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.chart-controls .btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            // Change timeframe logic here
        });
    });
}

// Switch between pages
function switchPage(page) {
    // Update navigation
    navItems.forEach(item => {
        if (item.dataset.page === page) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    // Update page title
    pageTitle.textContent = page.charAt(0).toUpperCase() + page.slice(1);

    // Show selected page
    pages.forEach(p => {
        p.classList.remove('active');
    });
    document.getElementById(`${page}-page`).classList.add('active');

    // Load page-specific data
    if (page === 'positions') {
        fetchPositions();
    } else if (page === 'signals') {
        fetchAllSignals();
    } else if (page === 'history') {
        fetchTradeHistory();
    }
}

// Initialize WebSocket connection
function initWebSocket() {
    try {
        const ws = new WebSocket(WS_BASE_URL);
        
        ws.onopen = () => {
            state.wsConnected = true;
            wsStatus.innerHTML = '<i class="fas fa-plug"></i> WebSocket: Connected';
            wsStatus.style.color = 'var(--success)';
            
            // Subscribe to default symbol
            ws.send(JSON.stringify({
                type: 'subscribe',
                symbol: state.selectedSymbol
            }));
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'candle_update') {
                handleCandleUpdate(data.data);
            }
        };

        ws.onclose = () => {
            state.wsConnected = false;
            wsStatus.innerHTML = '<i class="fas fa-plug"></i> WebSocket: Disconnected';
            wsStatus.style.color = 'var(--danger)';
            
            // Attempt to reconnect after 5 seconds
            setTimeout(initWebSocket, 5000);
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            state.wsConnected = false;
        };

        state.ws = ws;
    } catch (error) {
        console.error('Failed to connect WebSocket:', error);
        setTimeout(initWebSocket, 5000);
    }
}

// Handle candle updates from WebSocket
function handleCandleUpdate(candle) {
    if (candle.symbol === state.selectedSymbol) {
        updateChart(candle);
    }
    
    if (candle.is_finalized) {
        showToast('New candle finalized', 'info');
    }
}

// Initialize candlestick chart
function initChart() {
    const chartContainer = document.getElementById('candlestick-chart');
    chartContainer.innerHTML = '';
    
    state.chart = LightweightCharts.createChart(chartContainer, {
        width: chartContainer.clientWidth,
        height: 500,
        layout: {
            backgroundColor: '#ffffff',
            textColor: '#1a1e24',
        },
        grid: {
            vertLines: {
                color: '#e1e5eb',
            },
            horzLines: {
                color: '#e1e5eb',
            },
        },
        timeScale: {
            timeVisible: true,
            secondsVisible: false,
        },
    });

    state.candleSeries = state.chart.addCandlestickSeries({
        upColor: '#00c853',
        downColor: '#ff3d00',
        borderDownColor: '#ff3d00',
        borderUpColor: '#00c853',
        wickDownColor: '#ff3d00',
        wickUpColor: '#00c853',
    });

    // Handle window resize
    window.addEventListener('resize', () => {
        state.chart.resize(chartContainer.clientWidth, 500);
    });
}

// Update chart with new data
function updateChart(candle) {
    if (!state.candleSeries) return;
    
    state.candleSeries.update({
        time: new Date(candle.close_time).getTime() / 1000,
        open: candle.open,
        high: candle.high,
        low: candle.low,
        close: candle.close,
    });
}

// Update chart with historical data
async function updateChartData() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/candles/${state.selectedSymbol}?limit=100`);
        const candles = await response.json();
        
        if (candles && candles.length > 0) {
            const chartData = candles.map(c => ({
                time: new Date(c.close_time).getTime() / 1000,
                open: c.open,
                high: c.high,
                low: c.low,
                close: c.close,
            }));
            
            state.candleSeries.setData(chartData);
        }
    } catch (error) {
        console.error('Failed to fetch candles:', error);
    }
}

// Fetch candles for selected symbol
async function fetchCandles() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/candles/${state.selectedSymbol}?limit=20`);
        const candles = await response.json();
        state.candles[state.selectedSymbol] = candles;
        updateCandlesTable(candles);
    } catch (error) {
        console.error('Failed to fetch candles:', error);
    }
}

// Fetch initial data
async function fetchInitialData() {
    await Promise.all([
        fetchTicks(),
        fetchPositions(),
        fetchRecentSignals(),
        fetchTradeHistory()
    ]);
}

// Fetch latest ticks
async function fetchTicks() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/ticks`);
        const ticks = await response.json();
        
        ticks.forEach(tick => {
            state.ticks[tick.symbol] = tick;
            
            if (tick.symbol === 'btcusdt') {
                updateKPICard('btc', tick.price);
            } else if (tick.symbol === 'ethusdt') {
                updateKPICard('eth', tick.price);
            }
        });
    } catch (error) {
        console.error('Failed to fetch ticks:', error);
    }
}

// Update KPI cards with price data
function updateKPICard(symbol, price) {
    const priceElement = document.getElementById(`${symbol}Price`);
    const changeElement = document.getElementById(`${symbol}Change`);
    
    if (priceElement) {
        priceElement.textContent = `$${formatNumber(price)}`;
    }
    
    if (changeElement) {
        // Calculate random change for demo
        const change = (Math.random() * 2 - 1).toFixed(2);
        changeElement.textContent = `${change}%`;
        changeElement.className = `kpi-change ${parseFloat(change) >= 0 ? 'positive' : 'negative'}`;
    }
}

// Fetch active positions
async function fetchPositions() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/positions`);
        const positions = await response.json();
        state.positions = positions;
        updatePositionsTable(positions);
        updateStrategyCards(positions);
        updateTotalPnL(positions);
    } catch (error) {
        console.error('Failed to fetch positions:', error);
    }
}

// Update positions table
function updatePositionsTable(positions) {
    const tbody = document.querySelector('#positionsTable tbody');
    
    if (!positions || positions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="11" class="loading">No active positions</td></tr>';
        return;
    }
    
    tbody.innerHTML = positions.map(pos => {
        const pnl = ((pos.current_price - pos.entry_price) * pos.quantity).toFixed(2);
        const pnlPercent = ((pos.current_price - pos.entry_price) / pos.entry_price * 100).toFixed(2);
        
        return `
            <tr>
                <td>${pos.id.slice(0, 8)}...</td>
                <td>${pos.symbol.toUpperCase()}</td>
                <td><span class="badge-${pos.side.toLowerCase()}">${pos.side}</span></td>
                <td>$${formatNumber(pos.entry_price)}</td>
                <td>$${formatNumber(pos.current_price)}</td>
                <td>${pos.quantity}</td>
                <td class="${parseFloat(pnl) >= 0 ? 'positive' : 'negative'}">$${pnl}</td>
                <td class="${parseFloat(pnlPercent) >= 0 ? 'positive' : 'negative'}">${pnlPercent}%</td>
                <td>$${formatNumber(pos.sl_price)}</td>
                <td><span class="badge" style="background: ${pos.variant === 'A' ? 'var(--variant-a)' : 'var(--variant-b)'}">Variant ${pos.variant}</span></td>
                <td>
                    <button class="btn btn-sm btn-secondary" onclick="closePosition('${pos.id}')">
                        <i class="fas fa-times"></i> Close
                    </button>
                </td>
            </tr>
        `;
    }).join('');
    
    document.getElementById('activePositions').textContent = positions.length;
}

// Update strategy cards with position data
function updateStrategyCards(positions) {
    const variantAPos = positions.find(p => p.variant === 'A');
    const variantBPos = positions.find(p => p.variant === 'B');
    
    // Variant A
    if (variantAPos) {
        document.getElementById('variantAPosition').textContent = variantAPos.side;
        document.getElementById('variantAEntry').textContent = `$${formatNumber(variantAPos.entry_price)}`;
        const pnl = ((variantAPos.current_price - variantAPos.entry_price) * variantAPos.quantity).toFixed(2);
        document.getElementById('variantAPnl').textContent = `$${pnl}`;
    } else {
        document.getElementById('variantAPosition').textContent = 'None';
        document.getElementById('variantAEntry').textContent = '$0.00';
        document.getElementById('variantAPnl').textContent = '$0.00';
    }
    
    // Variant B
    if (variantBPos) {
        document.getElementById('variantBPosition').textContent = variantBPos.side;
        document.getElementById('variantBEntry').textContent = `$${formatNumber(variantBPos.entry_price)}`;
        const pnl = ((variantBPos.current_price - variantBPos.entry_price) * variantBPos.quantity).toFixed(2);
        document.getElementById('variantBPnl').textContent = `$${pnl}`;
    } else {
        document.getElementById('variantBPosition').textContent = 'None';
        document.getElementById('variantBEntry').textContent = '$0.00';
        document.getElementById('variantBPnl').textContent = '$0.00';
    }
}

// Update total P&L
function updateTotalPnL(positions) {
    const totalPnl = positions.reduce((sum, pos) => {
        return sum + ((pos.current_price - pos.entry_price) * pos.quantity);
    }, 0);
    
    const totalInvestment = positions.reduce((sum, pos) => {
        return sum + (pos.entry_price * pos.quantity);
    }, 0);
    
    const pnlPercent = totalInvestment > 0 ? (totalPnl / totalInvestment * 100) : 0;
    
    document.getElementById('totalPnl').textContent = `$${totalPnl.toFixed(2)}`;
    document.getElementById('pnlPercent').textContent = `${pnlPercent.toFixed(2)}%`;
    document.getElementById('pnlPercent').className = `kpi-change ${totalPnl >= 0 ? 'positive' : 'negative'}`;
}

// Fetch recent signals
async function fetchRecentSignals() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/signals?limit=5`);
        const signals = await response.json();
        state.signals = signals;
        updateRecentSignalsTable(signals);
    } catch (error) {
        console.error('Failed to fetch signals:', error);
    }
}

// Update recent signals table
function updateRecentSignalsTable(signals) {
    const tbody = document.querySelector('#recentSignalsTable tbody');
    
    if (!signals || signals.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="loading">Waiting for signals...</td></tr>';
        return;
    }
    
    tbody.innerHTML = signals.map(signal => {
        const time = new Date(signal.timestamp).toLocaleTimeString();
        
        return `
            <tr>
                <td>${time}</td>
                <td>${signal.symbol.toUpperCase()}</td>
                <td><span class="badge-${signal.action.toLowerCase()}">${signal.action}</span></td>
                <td>$${formatNumber(signal.price)}</td>
                <td><span class="badge" style="background: ${signal.variant === 'A' ? 'var(--variant-a)' : 'var(--variant-b)'}">Variant ${signal.variant}</span></td>
                <td><span class="badge" style="background: ${signal.strength === 'STRONG' ? 'var(--success)' : 'var(--warning)'}">${signal.strength}</span></td>
            </tr>
        `;
    }).join('');
}

// Fetch all signals
async function fetchAllSignals() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/signals?limit=50`);
        const signals = await response.json();
        updateAllSignalsTable(signals);
    } catch (error) {
        console.error('Failed to fetch signals:', error);
    }
}

// Update all signals table
function updateAllSignalsTable(signals) {
    const tbody = document.querySelector('#allSignalsTable tbody');
    
    if (!signals || signals.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="loading">No signals found</td></tr>';
        return;
    }
    
    tbody.innerHTML = signals.map(signal => {
        const time = new Date(signal.timestamp).toLocaleString();
        
        return `
            <tr>
                <td>${time}</td>
                <td>${signal.symbol.toUpperCase()}</td>
                <td><span class="badge-${signal.action.toLowerCase()}">${signal.action}</span></td>
                <td>$${formatNumber(signal.price)}</td>
                <td><span class="badge" style="background: ${signal.variant === 'A' ? 'var(--variant-a)' : 'var(--variant-b)'}">Variant ${signal.variant}</span></td>
                <td><span class="badge" style="background: ${signal.strength === 'STRONG' ? 'var(--success)' : 'var(--warning)'}">${signal.strength}</span></td>
                <td>${signal.reason || '-'}</td>
            </tr>
        `;
    }).join('');
}

// Filter signals
function filterSignals(filter) {
    let filtered = state.signals;
    
    if (filter !== 'all') {
        filtered = state.signals.filter(s => 
            s.variant === filter || s.action === filter
        );
    }
    
    updateAllSignalsTable(filtered);
}

// Fetch trade history
async function fetchTradeHistory() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/trades?limit=50`);
        const trades = await response.json();
        state.trades = trades;
        updateHistoryTable(trades);
    } catch (error) {
        console.error('Failed to fetch trades:', error);
    }
}

// Update history table
function updateHistoryTable(trades) {
    const tbody = document.querySelector('#historyTable tbody');
    
    if (!trades || trades.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="loading">No trade history</td></tr>';
        return;
    }
    
    tbody.innerHTML = trades.map(trade => {
        const time = new Date(trade.timestamp).toLocaleString();
        const total = trade.price * trade.quantity;
        
        return `
            <tr>
                <td>${time}</td>
                <td>${trade.symbol.toUpperCase()}</td>
                <td><span class="badge-${trade.side.toLowerCase()}">${trade.side}</span></td>
                <td>$${formatNumber(trade.price)}</td>
                <td>${trade.quantity}</td>
                <td>$${total.toFixed(2)}</td>
                <td><span class="badge" style="background: ${trade.variant === 'A' ? 'var(--variant-a)' : 'var(--variant-b)'}">Variant ${trade.variant}</span></td>
                <td>${trade.order_id ? trade.order_id.slice(0, 8) + '...' : '-'}</td>
            </tr>
        `;
    }).join('');
}

// Add new symbol
async function addSymbol(symbol) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/symbols/add`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ symbol }),
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            showToast(`Symbol ${symbol} added successfully`, 'success');
            
            // Add to dropdown
            const option = document.createElement('option');
            option.value = symbol;
            option.textContent = symbol.toUpperCase() + '/USDT';
            symbolSelect.appendChild(option);
            
            // Close modal
            addSymbolModal.classList.remove('active');
            addSymbolForm.reset();
        } else if (data.status === 'already_exists') {
            showToast(`Symbol ${symbol} already exists`, 'warning');
        }
    } catch (error) {
        console.error('Failed to add symbol:', error);
        showToast('Failed to add symbol', 'error');
    }
}

// Place order
async function placeOrder() {
    const symbol = document.getElementById('orderSymbol').value;
    const side = document.querySelector('.side-btn.active').textContent;
    const quantity = parseFloat(document.getElementById('orderQuantity').value);
    const orderType = document.getElementById('orderType').value;
    const limitPrice = parseFloat(document.getElementById('limitPrice').value);
    const variant = document.getElementById('orderVariant').value;
    
    // This would connect to your API endpoint for placing orders
    showToast(`Order placed: ${side} ${quantity} ${symbol}`, 'success');
    orderForm.reset();
}

// Close position
async function closePosition(positionId) {
    showToast(`Closing position ${positionId}...`, 'warning');
    // This would connect to your API endpoint for closing positions
}

// Show toast notification
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastIcon = toast.querySelector('.toast-icon');
    const toastMessage = toast.querySelector('.toast-message');
    
    toast.className = 'toast active ' + type;
    toastMessage.textContent = message;
    
    if (type === 'success') {
        toastIcon.className = 'toast-icon fas fa-check-circle';
    } else if (type === 'error') {
        toastIcon.className = 'toast-icon fas fa-exclamation-circle';
    } else if (type === 'warning') {
        toastIcon.className = 'toast-icon fas fa-exclamation-triangle';
    } else {
        toastIcon.className = 'toast-icon fas fa-info-circle';
    }
    
    setTimeout(() => {
        toast.classList.remove('active');
    }, 3000);
}

// Update system time
function updateSystemTime() {
    const timeElement = document.getElementById('systemTime');
    
    setInterval(() => {
        const now = new Date();
        timeElement.textContent = now.toLocaleString();
    }, 1000);
}

// Start data polling
function startDataPolling() {
    // Poll ticks every 2 seconds
    setInterval(fetchTicks, 2000);
    
    // Poll positions every 5 seconds
    setInterval(fetchPositions, 5000);
    
    // Poll signals every 10 seconds
    setInterval(fetchRecentSignals, 10000);
}

// Format number with commas
function formatNumber(num) {
    return num.toLocaleString(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

// Update candles table
function updateCandlesTable(candles) {
    // Implement if needed
}

// Initialize the application
document.addEventListener('DOMContentLoaded', init);