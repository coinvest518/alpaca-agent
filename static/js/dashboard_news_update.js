// Add this method to the TradingDashboard class to replace the existing renderNews method

renderNews(newsData) {
    const container = document.getElementById('news-feed');
    let html = '';

    Object.keys(newsData).forEach(symbol => {
        const newsItems = newsData[symbol];
        if (Array.isArray(newsItems)) {
            newsItems.slice(0, 5).forEach(item => {
                const title = item.title || 'No title';
                const summary = item.summary || 'No summary';
                const sentiment = item.sentiment || 'neutral';
                const url = item.url || '#';
                const source = item.source || 'Market Data';

                if (symbol === 'MARKET_INTELLIGENCE') {
                    html += `
                        <a href="${url}" target="_blank" class="news-item market-intelligence ${sentiment} text-decoration-none">
                            <div class="news-title"><i class="fas fa-chart-line me-2"></i>${title}</div>
                            <div class="news-summary">${summary.length > 150 ? summary.substring(0, 150) + '...' : summary}</div>
                            <div class="news-meta"><small>${source}</small></div>
                        </a>
                    `;
                } else {
                    html += `
                        <a href="${url}" target="_blank" class="news-item ${sentiment} text-decoration-none">
                            <div class="news-title">${symbol}: ${title}</div>
                            <div class="news-summary">${summary.length > 100 ? summary.substring(0, 100) + '...' : summary}</div>
                            <div class="news-meta"><small>${source}</small></div>
                        </a>
                    `;
                }
            });
        }
    });

    if (!html) {
        html = '<div class="text-center text-muted"><i class="fas fa-search fa-2x mb-3 opacity-50"></i><p>Scanning for market news...</p><small class="text-muted">Real-time news and analysis</small></div>';
    }

    container.innerHTML = html;
}
