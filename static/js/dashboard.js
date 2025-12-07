// AI Trading Bot Dashboard JavaScript - Enhanced Version

class TradingDashboard {
    constructor() {
        this.marketChart = null;
        this.performanceChart = null;
        this.updateInterval = null;
        this.isTradingActive = false;
        this.currentSymbol = 'SPY';
        this.chartTimeframe = '1D';
        this.lastMarketData = {};

        this.init();
        this.setupEventListeners();
        this.startDataUpdates();
    }

    init() {
        this.initMarketChart();
        this.initPerformanceChart();
        this.updateStatus();
        this.updateLastUpdate();
        // Load symbols immediately
        this.loadSymbols();
    }

    initMarketChart() {
        const ctx = document.getElementById('market-chart').getContext('2d');

        // Create gradient
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, 'rgba(0, 212, 255, 0.3)');
        gradient.addColorStop(1, 'rgba(0, 212, 255, 0.05)');

        this.marketChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Price',
                    data: [],
                    borderColor: '#00d4ff',
                    backgroundColor: gradient,
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#00d4ff',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2
                }, {
                    label: 'EMA 20',
                    data: [],
                    borderColor: '#00ff88',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.4,
                    pointRadius: 0,
                    hidden: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        display: true,
                        labels: {
                            color: '#b8c5d6',
                            usePointStyle: true,
                            pointStyle: 'line'
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(26, 26, 36, 0.95)',
                        titleColor: '#ffffff',
                        bodyColor: '#b8c5d6',
                        borderColor: '#2a2a35',
                        borderWidth: 1,
                        cornerRadius: 8,
                        displayColors: true,
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: $${context.parsed.y.toFixed(2)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            displayFormats: {
                                hour: 'HH:mm',
                                day: 'MMM dd'
                            }
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#6c7b95'
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#6c7b95',
                            callback: function(value) {
                                return '$' + value.toFixed(2);
                            }
                        }
                    }
                },
                elements: {
                    point: {
                        hoverBorderWidth: 3
                    }
                },
                animation: {
                    duration: 1000,
                    easing: 'easeInOutQuart'
                }
            }
        });
    }

    initPerformanceChart() {
        const ctx = document.getElementById('performance-chart').getContext('2d');

        this.performanceChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Wins', 'Losses', 'Pending'],
                datasets: [{
                    data: [0, 0, 0],
                    backgroundColor: [
                        '#00ff88',
                        '#ff4757',
                        '#ffa502'
                    ],
                    borderWidth: 0,
                    hoverOffset: 10
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#b8c5d6',
                            padding: 20,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(26, 26, 36, 0.95)',
                        titleColor: '#ffffff',
                        bodyColor: '#b8c5d6',
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? ((context.parsed / total) * 100).toFixed(1) : 0;
                                return `${context.label}: ${context.parsed} (${percentage}%)`;
                            }
                        }
                    }
                },
                cutout: '70%'
            }
        });
    }

    setupEventListeners() {
        // Trading control buttons
        document.getElementById('start-btn').addEventListener('click', () => this.startTrading());
        document.getElementById('stop-btn').addEventListener('click', () => this.stopTrading());
        document.getElementById('cycle-btn').addEventListener('click', () => this.runCycle());

        // Settings
        document.getElementById('update-settings').addEventListener('click', () => this.updateSettings());

        // Risk level slider
        document.getElementById('risk-level').addEventListener('input', (e) => {
            document.getElementById('risk-value').textContent = e.target.value;
        });

        // Symbol selection
        document.getElementById('chart-symbol').addEventListener('change', (e) => {
            this.currentSymbol = e.target.value;
            // Reload symbols in case positions changed, then update data
            this.loadSymbols().then(() => {
                this.updateMarketData();
            });
        });

        // Manual symbol input
        document.getElementById('manual-symbol').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const symbol = e.target.value.trim();
                if (symbol) {
                    this.addManualSymbol(symbol);
                }
            }
        });

        document.getElementById('add-symbol-btn').addEventListener('click', () => {
            const symbolInput = document.getElementById('manual-symbol');
            const symbol = symbolInput.value.trim();
            if (symbol) {
                this.addManualSymbol(symbol);
            }
        });

        // Timeframe buttons
        document.querySelectorAll('[data-timeframe]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('[data-timeframe]').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.chartTimeframe = e.target.dataset.timeframe;
                this.updateChartTimeframe(this.chartTimeframe);
            });
        });
    }

    async startTrading() {
        try {
            const response = await fetch('/api/start_trading');
            const data = await response.json();

            if (data.status === 'started') {
                this.isTradingActive = true;
                this.updateStatus();
                this.showNotification('Trading started successfully!', 'success');
            }
        } catch (error) {
            console.error('Error starting trading:', error);
            this.showNotification('Failed to start trading', 'error');
        }
    }

    async stopTrading() {
        try {
            const response = await fetch('/api/stop_trading');
            const data = await response.json();

            if (data.status === 'stopped') {
                this.isTradingActive = false;
                this.updateStatus();
                this.showNotification('Trading stopped successfully!', 'warning');
            }
        } catch (error) {
            console.error('Error stopping trading:', error);
            this.showNotification('Failed to stop trading', 'error');
        }
    }

    async runCycle() {
        const btn = document.getElementById('cycle-btn');
        const originalText = btn.innerHTML;

        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Running...';
        btn.disabled = true;

        try {
            const response = await fetch('/api/run_cycle');
            const data = await response.json();

            if (data.status === 'success') {
                this.showNotification('Trading cycle completed!', 'success');
                this.updateAllData();
            } else {
                this.showNotification('Trading cycle failed', 'error');
            }
        } catch (error) {
            console.error('Error running cycle:', error);
            this.showNotification('Failed to run trading cycle', 'error');
        } finally {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    }

    async updateSettings() {
        const mode = document.getElementById('trading-mode').value;
        const risk = document.getElementById('risk-level').value;

        // For now, just show a notification
        this.showNotification(`Settings updated: ${mode} mode, risk level ${risk}`, 'info');
    }

    updateLastUpdate() {
        const now = new Date();
        const timeString = now.toLocaleTimeString();
        document.getElementById('last-update').textContent = timeString;
    }

    updateStatus() {
        const statusIndicator = document.getElementById('status-indicator');
        const startBtn = document.getElementById('start-btn');
        const stopBtn = document.getElementById('stop-btn');

        if (this.isTradingActive) {
            statusIndicator.innerHTML = '<i class="fas fa-circle text-success"></i> ACTIVE';
            statusIndicator.className = 'badge bg-success me-3';
            startBtn.disabled = true;
            stopBtn.disabled = false;
        } else {
            statusIndicator.innerHTML = '<i class="fas fa-circle text-danger"></i> STOPPED';
            statusIndicator.className = 'badge bg-danger me-3';
            startBtn.disabled = false;
            stopBtn.disabled = true;
        }
    }

    updatePerformanceChart() {
        // Mock performance data - in real implementation, this would come from API
        const wins = Math.floor(Math.random() * 10) + 5;
        const losses = Math.floor(Math.random() * 5) + 1;
        const pending = Math.floor(Math.random() * 3);

        this.performanceChart.data.datasets[0].data = [wins, losses, pending];
        this.performanceChart.update();

        // Update win rate display
        const total = wins + losses;
        const winRate = total > 0 ? (wins / total) * 100 : 0;
        document.getElementById('win-rate').textContent = `${winRate.toFixed(1)}%`;

        // Update total trades
        document.getElementById('total-trades').textContent = total;
    }

    startDataUpdates() {
        // Update data every 30 seconds
        this.updateInterval = setInterval(() => {
            this.updateAllData();
        }, 30000);

        // Initial data load
        this.updateAllData();
    }

    async updateAllData() {
        await Promise.all([
            this.updateMarketData(),
            this.updatePortfolio(),
            this.updateTradingDecisions(),
            this.updateNews(),
            this.updateTechnicalIndicators(),
            this.updateTradingStatus(),
            this.updatePerformanceChart()
        ]);

        this.updateLastUpdate();
    }

    async updateMarketData() {
        try {
            // First load symbols from positions
            await this.loadSymbols();

            // Then load market data for current symbol
            const response = await fetch(`/api/market_data?symbol=${this.currentSymbol}`);
            const data = await response.json();

            if (data.status === 'success' && data.data) {
                this.lastMarketData = data.data;
                this.updateChart(data.data);
                this.updateMarketStats(data.data);
            }
        } catch (error) {
            console.error('Error updating market data:', error);
        }
    }

    async loadSymbols() {
        try {
            const response = await fetch('/api/symbols');
            const data = await response.json();

            if (data.status === 'success' && data.symbols) {
                // Get manually added symbols from localStorage
                const manualSymbols = this.getManualSymbols();
                
                // Combine API symbols with manual symbols
                const allSymbols = [...new Set([...data.symbols, ...manualSymbols])];
                
                this.updateSymbolDropdownFromSymbols(allSymbols, data.position_symbols || [], data.order_symbols || []);
            }
        } catch (error) {
            console.error('Error loading symbols:', error);
            // Fallback to empty symbols
            this.updateSymbolDropdownFromSymbols([], [], []);
        }
    }

    getManualSymbols() {
        try {
            const stored = localStorage.getItem('manualSymbols');
            return stored ? JSON.parse(stored) : [];
        } catch (error) {
            return [];
        }
    }

    addManualSymbol(symbol) {
        if (!symbol || symbol.trim() === '') return;
        
        symbol = symbol.toUpperCase().trim();
        const manualSymbols = this.getManualSymbols();
        
        if (!manualSymbols.includes(symbol)) {
            manualSymbols.push(symbol);
            localStorage.setItem('manualSymbols', JSON.stringify(manualSymbols));
            
            // Reload symbols to update dropdown
            this.loadSymbols().then(() => {
                // Set the newly added symbol as selected
                document.getElementById('chart-symbol').value = symbol;
                this.currentSymbol = symbol;
                this.updateMarketData();
            });
        }
        
        // Clear the input
        document.getElementById('manual-symbol').value = '';
    }

    updateSymbolDropdownFromSymbols(symbols, positionSymbols = [], orderSymbols = []) {
        const symbolSelect = document.getElementById('chart-symbol');

        // Clear existing options
        symbolSelect.innerHTML = '';

        if (symbols.length > 0) {
            // Add options for each symbol
            symbols.forEach(symbol => {
                const option = document.createElement('option');
                option.value = symbol;
                option.textContent = symbol;
                
                // Mark position symbols with a special indicator
                if (positionSymbols.includes(symbol)) {
                    option.textContent += ' 📊'; // Position indicator
                } else if (orderSymbols.includes(symbol)) {
                    option.textContent += ' 📋'; // Order indicator
                }
                
                symbolSelect.appendChild(option);
            });

            // Set current symbol to first position symbol if available, otherwise first symbol
            if (!symbols.includes(this.currentSymbol)) {
                this.currentSymbol = positionSymbols.length > 0 ? positionSymbols[0] : symbols[0];
            }
            symbolSelect.value = this.currentSymbol;
        } else {
            // No symbols available
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'No symbols';
            option.disabled = true;
            symbolSelect.appendChild(option);
        }
    }

    updateChart(data) {
        // Clear existing data
        this.marketChart.data.labels = [];
        this.marketChart.data.datasets.forEach(dataset => {
            dataset.data = [];
        });

        if (Object.keys(data).length > 0) {
            const symbol = this.currentSymbol in data ? this.currentSymbol : Object.keys(data)[0];
            const symbolData = data[symbol];

            if (symbolData && symbolData.price) {
                // Fetch real historical data instead of generating mock data
                this.loadHistoricalData(symbol);
            }
        } else {
            // No data available - show empty chart
            this.marketChart.update('active');
        }
    }

    async loadHistoricalData(symbol) {
        try {
            // Determine appropriate timeframe and hours back based on selected timeframe
            let timeframe, hoursBack;
            switch (this.chartTimeframe) {
                case '1H':
                    timeframe = '5Min';
                    hoursBack = 48; // Get 48 hours of data to ensure we have points (will show last ~14 hours)
                    break;
                case '4H':
                    timeframe = '5Min';
                    hoursBack = 96; // Get 96 hours of data for 4H view
                    break;
                case '1D':
                    timeframe = '1H';
                    hoursBack = 168; // Get 7 days of 1H bars for 1D view
                    break;
                case '1W':
                    timeframe = '1H';
                    hoursBack = 720; // Get 30 days of 1H bars for 1W view
                    break;
                default:
                    timeframe = '5Min';
                    hoursBack = 168; // Default to 7 days
            }

            console.log(`Fetching ${timeframe} data for ${hoursBack} hours for ${symbol}`);

            const response = await fetch(`/api/historical_data/${symbol}?timeframe=${timeframe}&hours=${hoursBack}`);
            const histData = await response.json();

            if (histData.status === 'success' && histData.data && histData.data.length > 0) {
                console.log(`Got ${histData.data.length} data points for ${symbol}`);
                this.renderHistoricalChart(histData.data);
            } else {
                console.log(`No ${timeframe} data for ${hoursBack} hours, trying fallback...`);

                // Try fallback timeframes based on the view
                let fallbackSuccessful = false;

                if (this.chartTimeframe === '1H' || this.chartTimeframe === '4H') {
                    // For short timeframes, try 15Min data first, then 1H data
                    const fallbackTimeframes = ['15Min', '1H'];

                    for (const fallbackTimeframe of fallbackTimeframes) {
                        console.log(`Trying fallback timeframe: ${fallbackTimeframe} for ${hoursBack} hours`);
                        try {
                            const fallbackResponse = await fetch(`/api/historical_data/${symbol}?timeframe=${fallbackTimeframe}&hours=${hoursBack}`);
                            const fallbackData = await fallbackResponse.json();

                            if (fallbackData.status === 'success' && fallbackData.data && fallbackData.data.length > 0) {
                                console.log(`Using ${fallbackTimeframe} data: ${fallbackData.data.length} points`);
                                this.renderHistoricalChart(fallbackData.data);
                                fallbackSuccessful = true;
                                break;
                            }
                        } catch (e) {
                            console.log(`Failed to fetch ${fallbackTimeframe} data:`, e);
                        }
                    }
                }

                if (!fallbackSuccessful) {
                    // Try with daily data for longer timeframes
                    if (this.chartTimeframe === '1W') {
                        const dailyResponse = await fetch(`/api/historical_data/${symbol}?timeframe=1D&hours=720`); // 30 days
                        const dailyData = await dailyResponse.json();
                        if (dailyData.status === 'success' && dailyData.data && dailyData.data.length > 0) {
                            console.log(`Using daily data: ${dailyData.data.length} points`);
                            this.renderHistoricalChart(dailyData.data);
                            fallbackSuccessful = true;
                        }
                    }
                }

                if (!fallbackSuccessful) {
                    console.log('All data fetching attempts failed, using fallback chart');
                    this.generateFallbackChart(symbol);
                }
            }
        } catch (error) {
            console.error('Error loading historical data:', error);
            // Fallback to generated data
            this.generateFallbackChart(symbol);
        }
    }

    generateFallbackChart(symbol) {
        const currentData = this.lastMarketData[symbol];
        if (currentData && currentData.price) {
            this.generateHistoricalData(currentData.price);
        } else {
            // No data available
            this.marketChart.data.labels = [];
            this.marketChart.data.datasets.forEach(dataset => {
                dataset.data = [];
            });
            this.marketChart.update('active');
        }
    }

    renderHistoricalChart(historicalData) {
        const labels = [];
        const prices = [];
        const emaData = [];

        historicalData.forEach(point => {
            // Parse timestamp - handle different formats
            let timestamp;
            if (point.timestamp.includes('+')) {
                timestamp = new Date(point.timestamp);
            } else {
                timestamp = new Date(point.timestamp + (point.timestamp.includes('Z') ? '' : 'Z'));
            }
            labels.push(timestamp);
            prices.push(point.close);

            // Calculate EMA
            if (emaData.length === 0) {
                emaData.push(point.close);
            } else {
                const multiplier = 2 / (20 + 1);
                emaData.push((point.close * multiplier) + (emaData[emaData.length - 1] * (1 - multiplier)));
            }
        });

        this.marketChart.data.labels = labels;
        this.marketChart.data.datasets[0].data = prices;
        this.marketChart.data.datasets[1].data = emaData;
        this.marketChart.update('active');

        console.log(`Chart updated with ${historicalData.length} data points`);
        console.log(`Price range: $${Math.min(...prices).toFixed(2)} - $${Math.max(...prices).toFixed(2)}`);
    }

    generateHistoricalData(currentPrice) {
        const labels = [];
        const prices = [];
        const emaData = [];
        const now = new Date();

        // Generate data points for the selected timeframe
        let points, interval;
        switch (this.chartTimeframe) {
            case '1H':
                points = 60;
                interval = 1 * 60 * 1000; // 1 minute
                break;
            case '4H':
                points = 48;
                interval = 5 * 60 * 1000; // 5 minutes
                break;
            case '1D':
                points = 78;
                interval = 20 * 60 * 1000; // 20 minutes
                break;
            case '1W':
                points = 35;
                interval = 6 * 60 * 60 * 1000; // 6 hours
                break;
            default:
                points = 50;
                interval = 1 * 60 * 1000;
        }

        // Generate price data with realistic volatility
        let price = currentPrice * 0.98; // Start slightly lower
        const volatility = 0.002; // 0.2% volatility per point

        for (let i = points - 1; i >= 0; i--) {
            const timestamp = new Date(now.getTime() - (i * interval));
            labels.push(timestamp);

            // Add random walk with mean reversion
            const randomChange = (Math.random() - 0.5) * 2 * volatility;
            const meanReversion = (currentPrice - price) * 0.001; // Slight pull toward current price
            price += price * (randomChange + meanReversion);

            prices.push(price);

            // Simple EMA calculation
            if (emaData.length === 0) {
                emaData.push(price);
            } else {
                const multiplier = 2 / (20 + 1);
                emaData.push((price * multiplier) + (emaData[emaData.length - 1] * (1 - multiplier)));
            }
        }

        this.marketChart.data.labels = labels;
        this.marketChart.data.datasets[0].data = prices;
        this.marketChart.data.datasets[1].data = emaData;
    }

    generateMockData() {
        const labels = [];
        const prices = [];
        const emaData = [];
        const now = new Date();

        for (let i = 49; i >= 0; i--) {
            labels.push(new Date(now.getTime() - (i * 60 * 1000)));
            const price = 150 + Math.sin(i * 0.1) * 5 + Math.random() * 2;
            prices.push(price);

            if (emaData.length === 0) {
                emaData.push(price);
            } else {
                const multiplier = 2 / (20 + 1);
                emaData.push((price * multiplier) + (emaData[emaData.length - 1] * (1 - multiplier)));
            }
        }

        this.marketChart.data.labels = labels;
        this.marketChart.data.datasets[0].data = prices;
        this.marketChart.data.datasets[1].data = emaData;
    }

    updateMarketStats(data) {
        if (Object.keys(data).length > 0) {
            const symbol = this.currentSymbol in data ? this.currentSymbol : Object.keys(data)[0];
            const symbolData = data[symbol];

            if (symbolData) {
                // Update current price
                let priceText = `$${symbolData.price.toFixed(2)}`;
                if (symbolData.subscription_limited) {
                    priceText += ' <i class="fas fa-exclamation-triangle text-warning" title="Limited data - upgrade subscription for real-time prices"></i>';
                }
                document.getElementById('current-price').innerHTML = priceText;

                // Update volume
                let volumeText = symbolData.volume ? symbolData.volume.toLocaleString() : '--';
                if (symbolData.subscription_limited) {
                    volumeText += ' <small class="text-muted">(delayed)</small>';
                }
                document.getElementById('volume').innerHTML = volumeText;

                // Calculate real 24h change from historical data
                this.calculate24hChange(symbol);
            }
        } else {
            // No data available
            document.getElementById('current-price').textContent = '$--.--';
            document.getElementById('price-change').textContent = '+--.-- (--.--%)';
            document.getElementById('price-change').className = '';
            document.getElementById('volume').textContent = '--';
        }

        // Update market status
        this.updateMarketStatus();
    }

    updateMarketStatus() {
        const now = new Date();
        const estTime = new Date(now.toLocaleString("en-US", {timeZone: "America/New_York"}));
        const day = estTime.getDay(); // 0 = Sunday, 6 = Saturday
        const hour = estTime.getHours();
        const minute = estTime.getMinutes();
        const currentTime = hour * 60 + minute;

        // Market hours: 9:30 AM - 4:00 PM EST, Monday-Friday
        const marketOpen = 9 * 60 + 30; // 9:30 AM
        const marketClose = 16 * 60; // 4:00 PM
        const isWeekday = day >= 1 && day <= 5;
        const isMarketHours = isWeekday && currentTime >= marketOpen && currentTime < marketClose;

        const statusElement = document.getElementById('market-status');
        const badge = statusElement.querySelector('.badge');

        if (isMarketHours) {
            badge.textContent = 'OPEN';
            badge.className = 'badge bg-success market-status-badge';
        } else if (isWeekday && currentTime < marketOpen) {
            badge.textContent = 'PRE-MARKET';
            badge.className = 'badge bg-warning market-status-badge';
        } else if (isWeekday && currentTime >= marketClose) {
            badge.textContent = 'AFTER HOURS';
            badge.className = 'badge bg-info market-status-badge';
        } else {
            badge.textContent = 'CLOSED';
            badge.className = 'badge bg-secondary market-status-badge';
        }
    }

    async calculate24hChange(symbol) {
        try {
            // Get 24 hours of 1H bars to calculate change
            const response = await fetch(`/api/historical_data/${symbol}?timeframe=1H&hours=24`);
            const histData = await response.json();

            if (histData.status === 'success' && histData.data && histData.data.length >= 2) {
                const currentPrice = histData.data[histData.data.length - 1].close;
                const previousPrice = histData.data[0].close; // 24 hours ago
                const change = currentPrice - previousPrice;
                const changePercent = (change / previousPrice) * 100;

                const changeElement = document.getElementById('price-change');
                changeElement.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)} (${changePercent >= 0 ? '+' : ''}${changePercent.toFixed(2)}%)`;
                changeElement.className = change >= 0 ? 'price-positive' : 'price-negative';
            } else {
                // Fallback: use position data for change calculation
                await this.calculateChangeFromPosition(symbol);
            }
        } catch (error) {
            console.error('Error calculating 24h change:', error);
            // Fallback: use position data
            await this.calculateChangeFromPosition(symbol);
        }
    }

    async calculateChangeFromPosition(symbol) {
        try {
            // Get position data to calculate change
            const response = await fetch('/api/portfolio');
            const data = await response.json();

            if (data.status === 'success' && data.data && data.data.positions) {
                const position = data.data.positions.find(pos => pos.symbol === symbol);
                if (position) {
                    const currentPrice = parseFloat(position.current_price || 0);
                    const entryPrice = parseFloat(position.avg_entry_price || 0);

                    if (currentPrice > 0 && entryPrice > 0) {
                        const change = currentPrice - entryPrice;
                        const changePercent = (change / entryPrice) * 100;

                        const changeElement = document.getElementById('price-change');
                        changeElement.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)} (${changePercent >= 0 ? '+' : ''}${changePercent.toFixed(2)}%)`;
                        changeElement.className = change >= 0 ? 'price-positive' : 'price-negative';
                        return;
                    }
                }
            }

            // If no position data, show neutral
            const changeElement = document.getElementById('price-change');
            changeElement.textContent = '-- (--)';
            changeElement.className = '';
        } catch (error) {
            console.error('Error calculating change from position:', error);
            const changeElement = document.getElementById('price-change');
            changeElement.textContent = '-- (--)';
            changeElement.className = '';
        }
    }

    updateChartTimeframe(timeframe) {
        this.chartTimeframe = timeframe;
        this.updateMarketData();
    }

    async updatePortfolio() {
        try {
            const response = await fetch('/api/portfolio');
            const data = await response.json();

            if (data.status === 'success' && data.data) {
                this.renderPortfolio(data.data);
            }
        } catch (error) {
            console.error('Error updating portfolio:', error);
        }
    }

    renderPortfolio(data) {
        const summaryContainer = document.getElementById('portfolio-timestamp');
        const totalValueEl = document.getElementById('total-market-value');
        const totalPnLEl = document.getElementById('total-unrealized-pl');
        const totalPnLPcEl = document.getElementById('total-unrealized-plpc');
        const tableBody = document.getElementById('positions-table-body');
        const noPositionsMsg = document.getElementById('no-positions-message');

        if (!data || (!data.positions && !data.account)) {
            tableBody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-muted">No portfolio data available</td></tr>';
            noPositionsMsg.classList.remove('d-none');
            return;
        }

        // Update timestamp
        if (data.timestamp) {
            const timestamp = new Date(data.timestamp);
            summaryContainer.textContent = timestamp.toLocaleTimeString();
        }

        // Update portfolio summary
        if (data.summary) {
            const totalValue = parseFloat(data.summary.total_market_value || 0);
            const totalPnL = parseFloat(data.summary.total_unrealized_pl || 0);
            const totalPnLPc = parseFloat(data.summary.total_unrealized_plpc || 0);

            totalValueEl.textContent = `$${totalValue.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;

            const pnlClass = totalPnL >= 0 ? 'text-success' : 'text-danger';
            const pnlSign = totalPnL >= 0 ? '+' : '';
            totalPnLEl.innerHTML = `<span class="${pnlClass}">${pnlSign}$${totalPnL.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>`;
            totalPnLPcEl.innerHTML = `<span class="${pnlClass}">(${pnlSign}${totalPnLPc.toFixed(2)}%)</span>`;
        }

        // Render positions table
        let tableHtml = '';

        if (data.positions && Array.isArray(data.positions) && data.positions.length > 0) {
            data.positions.forEach(position => {
                const symbol = position.symbol || position.asset_id || 'Unknown';
                const qty = parseFloat(position.qty || 0);
                const avgEntryPrice = parseFloat(position.avg_entry_price || 0);
                const currentPrice = parseFloat(position.current_price || position.market_value / qty || avgEntryPrice);
                const marketValue = parseFloat(position.market_value || 0);
                const costBasis = parseFloat(position.cost_basis || 0);
                const unrealizedPl = parseFloat(position.unrealized_pl || 0);
                const unrealizedPlPc = parseFloat(position.unrealized_plpc || 0);

                const side = position.side || 'long';
                const sideIcon = side === 'long' ? '📈' : '📉';
                const sideClass = side === 'long' ? 'text-success' : 'text-danger';

                const pnlClass = unrealizedPl >= 0 ? 'text-success' : 'text-danger';
                const pnlIcon = unrealizedPl >= 0 ? '▲' : '▼';
                const pnlSign = unrealizedPl >= 0 ? '+' : '';

                tableHtml += `
                    <tr class="position-row">
                        <td>
                            <div class="d-flex align-items-center">
                                <span class="me-2">${sideIcon}</span>
                                <div>
                                    <div class="fw-bold">${symbol}</div>
                                    <small class="text-muted text-capitalize">${side}</small>
                                </div>
                            </div>
                        </td>
                        <td class="text-end">
                            <span class="fw-semibold">${qty.toLocaleString('en-US', {maximumFractionDigits: 0})}</span>
                        </td>
                        <td class="text-end">
                            <span>$${avgEntryPrice.toFixed(2)}</span>
                        </td>
                        <td class="text-end">
                            <span>$${currentPrice.toFixed(2)}</span>
                        </td>
                        <td class="text-end">
                            <span class="fw-semibold">$${marketValue.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
                        </td>
                        <td class="text-end">
                            <div class="${pnlClass} fw-semibold">
                                ${pnlIcon} $${unrealizedPl.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                                <br><small>(${pnlSign}${unrealizedPlPc.toFixed(2)}%)</small>
                            </div>
                        </td>
                    </tr>
                `;
            });

            noPositionsMsg.classList.add('d-none');
        } else {
            tableHtml = '<tr><td colspan="6" class="text-center py-4 text-muted">No open positions</td></tr>';
            noPositionsMsg.classList.remove('d-none');
        }

        tableBody.innerHTML = tableHtml;

        // Update global stats
        const positionCount = data.summary ? data.summary.position_count || 0 : 0;
        document.getElementById('active-positions').textContent = positionCount;

        // Update total P&L in header stats
        if (data.summary) {
            const totalPnL = parseFloat(data.summary.total_unrealized_pl || 0);
            const totalPnLPc = parseFloat(data.summary.total_unrealized_plpc || 0);

            document.getElementById('total-pnl').textContent = `$${totalPnL.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
            document.getElementById('pnl-change').textContent = `${totalPnL >= 0 ? '+' : ''}${totalPnLPc.toFixed(2)}%`;
            document.getElementById('pnl-change').className = `badge ${totalPnL >= 0 ? 'bg-success' : 'bg-danger'}`;
        }
    }

    async updateTradingDecisions() {
        try {
            // Try to get decisions from the last trading cycle
            const response = await fetch('/api/trading_status');
            const data = await response.json();

            if (data.last_data && data.last_data.decisions) {
                this.renderTradingDecisions(data.last_data);
            } else {
                // Fallback to mock data
                this.renderMockDecisions();
            }
        } catch (error) {
            console.error('Error updating trading decisions:', error);
            this.renderMockDecisions();
        }
    }

    renderTradingDecisions(tradingData) {
        const container = document.getElementById('trading-decisions');
        let html = '';

        if (tradingData.decisions) {
            Object.keys(tradingData.decisions).forEach(symbol => {
                const decision = tradingData.decisions[symbol];
                const analysis = tradingData.analysis_results?.[symbol];

                html += `
                    <div class="decision-card ${decision.toLowerCase()}">
                        <div class="decision-symbol">${symbol}</div>
                        <div class="decision-action">${decision}</div>
                        <div class="decision-details">
                            ${analysis ? this.formatAnalysis(analysis) : 'Analysis not available'}
                        </div>
                    </div>
                `;
            });
        }

        if (!html) {
            html = '<div class="text-center text-muted"><i class="fas fa-robot fa-2x mb-3"></i><p>No recent decisions</p></div>';
        }

        container.innerHTML = html;
    }

    formatAnalysis(analysis) {
        if (!analysis || !analysis.indicators) return 'No analysis data';

        const indicators = analysis.indicators;
        let details = [];

        if (indicators.close !== undefined) details.push(`Price: $${indicators.close.toFixed(2)}`);
        if (indicators.rsi !== undefined) details.push(`RSI: ${indicators.rsi.toFixed(2)}`);
        if (indicators.ema !== undefined) details.push(`EMA: ${indicators.ema.toFixed(3)}`);
        if (indicators.atr !== undefined) details.push(`ATR: ${indicators.atr.toFixed(3)}`);

        return details.join(' | ');
    }

    renderMockDecisions() {
        const container = document.getElementById('trading-decisions');
        const mockDecisions = [
            {
                symbol: 'NFGC',
                action: 'HOLD',
                price: 3.14,
                pnl: 0.05,
                indicators: 'RSI: 54.55, EMA: 3.13'
            }
        ];

        let html = '';

        mockDecisions.forEach(decision => {
            const actionClass = decision.action.toLowerCase();
            html += `
                <div class="decision-card ${actionClass}">
                    <div class="decision-symbol">${decision.symbol}</div>
                    <div class="decision-action">${decision.action}</div>
                    <div class="decision-details">
                        Price: $${decision.price} | P&L: ${decision.pnl >= 0 ? '+' : ''}$${decision.pnl}<br>
                        ${decision.indicators}
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
    }

    async updateNews() {
        try {
            const response = await fetch('/api/news');
            const data = await response.json();

            if (data.status === 'success' && data.data) {
                this.renderNews(data.data);
            } else {
                // Fallback to mock data if no real news
                this.renderMockNews();
            }
        } catch (error) {
            console.error('Error updating news:', error);
            this.renderMockNews();
        }
    }

    renderNews(newsData) {
        const container = document.getElementById('news-feed');
        let html = '';

        // newsData should be in the format {symbol: [news_items]}
        Object.keys(newsData).forEach(symbol => {
            const newsItems = newsData[symbol];
            if (Array.isArray(newsItems)) {
                newsItems.slice(0, 5).forEach(item => {
                    const title = item.title || 'No title';
                    const summary = item.summary || 'No summary';
                    const sentiment = item.sentiment || 'neutral';

                    html += `
                        <div class="news-item ${sentiment}">
                            <div class="news-title">${title}</div>
                            <div class="news-summary">${summary.length > 100 ? summary.substring(0, 100) + '...' : summary}</div>
                        </div>
                    `;
                });
            }
        });

        if (!html) {
            html = '<div class="text-center text-muted">No news available</div>';
        }

        container.innerHTML = html;
    }

    renderMockNews() {
        const container = document.getElementById('news-feed');
        const mockNews = [
            {
                title: 'New Found Gold closes Queensway acquisition',
                summary: 'New Found Gold completes acquisition expanding project by 31%',
                sentiment: 'positive'
            },
            {
                title: 'Market volatility increases amid economic uncertainty',
                summary: 'Investors react to latest economic indicators',
                sentiment: 'neutral'
            }
        ];

        let html = '';
        mockNews.forEach(item => {
            html += `
                <div class="news-item ${item.sentiment}">
                    <div class="news-title">${item.title}</div>
                    <div class="news-summary">${item.summary}</div>
                </div>
            `;
        });

        container.innerHTML = html;
    }

    async updateTechnicalIndicators() {
        try {
            // Try to get indicators from the last trading cycle
            const response = await fetch('/api/trading_status');
            const data = await response.json();

            if (data.last_data && data.last_data.analysis_results) {
                this.renderTechnicalIndicators(data.last_data.analysis_results);
            } else {
                // Fallback to mock data
                this.renderMockIndicators();
            }
        } catch (error) {
            console.error('Error updating technical indicators:', error);
            this.renderMockIndicators();
        }
    }

    renderTechnicalIndicators(analysisResults) {
        // Get the first symbol's analysis for display
        const symbols = Object.keys(analysisResults);
        if (symbols.length > 0) {
            const analysis = analysisResults[symbols[0]];
            if (analysis && analysis.indicators) {
                const indicators = analysis.indicators;

                this.updateIndicator('rsi', indicators.rsi, 'RSI');
                this.updateIndicator('macd', indicators.atr, 'MACD'); // Using ATR value for MACD display
                this.updateIndicator('ema', indicators.ema, 'EMA');
                this.updateIndicator('volatility', indicators.volatility_score, 'Volatility');

                return;
            }
        }

        // Fallback if no real data
        this.renderMockIndicators();
    }

    updateIndicator(elementId, value, name) {
        const valueElement = document.getElementById(`${elementId}-value`);
        const statusElement = document.getElementById(`${elementId}-status`);

        if (value !== undefined && value !== null) {
            // Format the value
            let displayValue = value;
            if (typeof value === 'number') {
                if (elementId === 'rsi') {
                    displayValue = value.toFixed(2);
                } else if (elementId === 'volatility') {
                    displayValue = value.toFixed(3);
                } else {
                    displayValue = value.toFixed(3);
                }
            }

            valueElement.textContent = displayValue;

            // Determine status and styling
            let statusText = '';
            let statusClass = '';

            switch(elementId) {
                case 'rsi':
                    if (value < 30) {
                        statusText = 'Oversold (Buy)';
                        statusClass = 'status-oversold';
                    } else if (value > 70) {
                        statusText = 'Overbought (Sell)';
                        statusClass = 'status-overbought';
                    } else {
                        statusText = 'Neutral (30-70)';
                        statusClass = 'status-neutral';
                    }
                    break;
                case 'ema':
                    statusText = 'Trend Indicator';
                    statusClass = 'status-neutral';
                    break;
                case 'macd':
                    if (value < -0.5) {
                        statusText = 'Bearish Signal';
                        statusClass = 'status-overbought';
                    } else if (value > 0.5) {
                        statusText = 'Bullish Signal';
                        statusClass = 'status-oversold';
                    } else {
                        statusText = 'Neutral Signal';
                        statusClass = 'status-neutral';
                    }
                    break;
                case 'volatility':
                    if (value < 2) {
                        statusText = 'Low risk';
                        statusClass = 'status-low';
                    } else if (value < 5) {
                        statusText = 'Medium risk';
                        statusClass = 'status-medium';
                    } else {
                        statusText = 'High risk';
                        statusClass = 'status-high';
                    }
                    break;
            }

            statusElement.textContent = statusText;
            statusElement.className = `indicator-status ${statusClass}`;
        } else {
            valueElement.textContent = '--';
            statusElement.textContent = 'Loading...';
            statusElement.className = 'indicator-status';
        }
    }

    renderMockIndicators() {
        // Mock technical indicators for demonstration
        const indicators = {
            rsi: { value: 54.55, status: 'neutral', label: 'Neutral (30-70)' },
            macd: { value: 0.025, status: 'neutral', label: 'Signal Line' },
            ema: { value: 3.125, status: 'neutral', label: 'Trend Indicator' },
            volatility: { value: 0.796, status: 'low', label: 'Low risk' }
        };

        Object.keys(indicators).forEach(key => {
            const indicator = indicators[key];
            document.getElementById(`${key}-value`).textContent = key === 'rsi' || key === 'volatility' ?
                indicator.value.toFixed(2) : indicator.value.toFixed(3);
            document.getElementById(`${key}-status`).textContent = indicator.label;
            document.getElementById(`${key}-status`).className = `indicator-status status-${indicator.status}`;
        });
    }

    async updateTradingStatus() {
        try {
            const response = await fetch('/api/trading_status');
            const data = await response.json();

            this.isTradingActive = data.is_active;
            this.updateStatus();
        } catch (error) {
            console.error('Error updating trading status:', error);
        }
    }

    showNotification(message, type) {
        const toastContainer = document.getElementById('notification-toast');
        const toast = new bootstrap.Toast(toastContainer);

        const toastTitle = document.getElementById('toast-title');
        const toastMessage = document.getElementById('toast-message');

        toastTitle.textContent = type.charAt(0).toUpperCase() + type.slice(1);
        toastMessage.textContent = message;

        // Update toast classes based on type
        const headerIcon = toastContainer.querySelector('.toast-header i');
        switch(type) {
            case 'success':
                headerIcon.className = 'fas fa-check-circle me-2 text-success';
                break;
            case 'error':
                headerIcon.className = 'fas fa-exclamation-triangle me-2 text-danger';
                break;
            case 'warning':
                headerIcon.className = 'fas fa-exclamation-circle me-2 text-warning';
                break;
            default:
                headerIcon.className = 'fas fa-info-circle me-2 text-info';
        }

        toast.show();
    }
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    new TradingDashboard();
});