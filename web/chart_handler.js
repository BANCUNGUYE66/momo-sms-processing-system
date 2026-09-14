document.addEventListener('DOMContentLoaded', () => {
    let rawTransactions = [];
    let categoryChartInstance = null;
    let volumeChartInstance = null;

    const btnReload = document.getElementById('btn-run-etl');
    const searchInput = document.getElementById('search-input');
    const tableBody = document.getElementById('table-body');

    const totalVolumeElem = document.getElementById('val-total-volume');
    const totalCountElem = document.getElementById('val-total-count');

    // Fetch dashboard data
    async function loadDashboardData() {
        try {
            // Attempt to fetch from processed json
            const response = await fetch('data/processed/dashboard.json');
            if (!response.ok) throw new Error('Data file not found');
            rawTransactions = await response.json();
            renderDashboard(rawTransactions);
        } catch (err) {
            console.warn('Fallback: loading sample transaction dataset');
            rawTransactions = getFallbackData();
            renderDashboard(rawTransactions);
        }
    }

    function renderDashboard(data) {
        // Calculate Metrics
        const totalTx = data.length;
        const totalVol = data.reduce((sum, tx) => sum + (tx.amount || 0), 0);

        totalCountElem.textContent = totalTx;
        totalVolumeElem.textContent = `RWF ${totalVol.toLocaleString()}`;

        // Populate Table
        renderTable(data);

        // Render Charts
        renderCharts(data);
    }

    function renderTable(data) {
        if (!data || data.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="5" class="empty-state">No transactions found.</td></tr>`;
            return;
        }

        tableBody.innerHTML = data.map(tx => `
            <tr>
                <td>${formatDate(tx.timestamp)}</td>
                <td><strong>${tx.sender || 'Unknown'}</strong></td>
                <td>${tx.amount ? `RWF ${tx.amount.toLocaleString()}` : '-'}</td>
                <td><span class="badge-cat ${tx.category}">${tx.category}</span></td>
                <td><small style="color: #94a3b8">${escapeHtml(tx.raw_text)}</small></td>
            </tr>
        `).join('');
    }

    function renderCharts(data) {
        // Categorization counts
        const categories = {};
        const volumePerCategory = {};

        data.forEach(tx => {
            const cat = tx.category || 'OTHER';
            categories[cat] = (categories[cat] || 0) + 1;
            volumePerCategory[cat] = (volumePerCategory[cat] || 0) + (tx.amount || 0);
        });

        const catLabels = Object.keys(categories);
        const catCounts = Object.values(categories);
        const volAmounts = catLabels.map(l => volumePerCategory[l]);

        // Category Doughnut Chart
        const ctxCat = document.getElementById('categoryChart').getContext('2d');
        if (categoryChartInstance) categoryChartInstance.destroy();
        categoryChartInstance = new Chart(ctxCat, {
            type: 'doughnut',
            data: {
                labels: catLabels,
                datasets: [{
                    data: catCounts,
                    backgroundColor: ['#6366f1', '#10b981', '#0ea5e9', '#f59e0b', '#f43f5e', '#94a3b8']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#f8fafc' } }
                }
            }
        });

        // Volume Bar Chart
        const ctxVol = document.getElementById('volumeChart').getContext('2d');
        if (volumeChartInstance) volumeChartInstance.destroy();
        volumeChartInstance = new Chart(ctxVol, {
            type: 'bar',
            data: {
                labels: catLabels,
                datasets: [{
                    label: 'Volume (RWF)',
                    data: volAmounts,
                    backgroundColor: '#6366f1',
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#f8fafc' } }
                },
                scales: {
                    x: { ticks: { color: '#94a3b8' } },
                    y: { ticks: { color: '#94a3b8' } }
                }
            }
        });
    }

    // Search filter
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        const filtered = rawTransactions.filter(tx => 
            (tx.sender && tx.sender.toLowerCase().includes(query)) ||
            (tx.raw_text && tx.raw_text.toLowerCase().includes(query)) ||
            (tx.category && tx.category.toLowerCase().includes(query))
        );
        renderTable(filtered);
    });

    btnReload.addEventListener('click', () => {
        loadDashboardData();
    });

    function formatDate(isoStr) {
        if (!isoStr) return '-';
        try {
            const date = new Date(isoStr);
            return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        } catch {
            return isoStr;
        }
    }

    function escapeHtml(str) {
        if (!str) return '';
        return str.replace(/[&<>"']/g, function(m) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[m];
        });
    }

    function getFallbackData() {
        return [
            { sender: "+250788111222", timestamp: "2023-09-01T10:00:00", amount: 50000, category: "RECEIVE", raw_text: "You have received 50000 RWF from JOHN DOE." },
            { sender: "+250788333444", timestamp: "2023-09-02T14:00:00", amount: 12000, category: "TRANSFER", raw_text: "Transferred 12000 RWF to JANE SMITH." },
            { sender: "+250788555666", timestamp: "2023-09-03T16:00:00", amount: 3500, category: "PAYMENT", raw_text: "Payment of 3500 RWF to KIGALI SUPERMARKET." },
            { sender: "+250788777888", timestamp: "2023-09-04T18:00:00", amount: 2000, category: "AIRTIME", raw_text: "You have purchased airtime worth 2000 RWF." },
            { sender: "+250788999000", timestamp: "2023-09-05T20:00:00", amount: 5000, category: "CASH_OUT", raw_text: "Cash Power token 1234-5678-9012 for 5000 RWF." }
        ];
    }

    loadDashboardData();
});
