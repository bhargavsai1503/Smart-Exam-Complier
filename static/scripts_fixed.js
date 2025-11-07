// Dashboard: Tab selector
function showTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(function(el) {
        el.classList.add('hidden');
    });
    document.getElementById(tabName).classList.remove('hidden');
}
document.addEventListener("DOMContentLoaded", function() {
    let tabs = document.querySelectorAll('.tab-btn');
    if (tabs.length > 0) tabs[0].click();
});

// Chart.js demo: expects global stats object from Flask via Jinja
function renderCharts(report) {
    // Difficulty Pie Chart
    const difficultyCtx = document.getElementById('difficultyChart').getContext('2d');
    new Chart(difficultyCtx, {
        type: 'pie',
        data: {
            labels: ['Easy', 'Medium', 'Hard'],
            datasets: [{
                data: [
                    report.statistics.difficulty_distribution.easy,
                    report.statistics.difficulty_distribution.medium,
                    report.statistics.difficulty_distribution.hard
                ],
                backgroundColor: ['#4ade80', '#facc15', '#f87171']
            }]
        }
    });

    // Marks Distribution Bar Chart (aggregated by mark value)
    const marksDist = report.statistics.marks_distribution || {};
    const marksLabels = Object.keys(marksDist);
    const marksData = Object.values(marksDist);
    const marksCtx = document.getElementById('marksChart').getContext('2d');
    new Chart(marksCtx, {
        type: 'bar',
        data: {
            labels: marksLabels.map(m => m + ' marks'),
            datasets: [{
                label: 'Number of Questions',
                data: marksData,
                backgroundColor: '#60a5fa'
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });

    // Time Line Chart
    const timeCtx = document.getElementById('timeChart').getContext('2d');
    new Chart(timeCtx, {
        type: 'line',
        data: {
            labels: ['Estimated', 'Declared'],
            datasets: [{
                label: 'Time (minutes)',
                data: [
                    report.statistics.time_comparison.estimated,
                    report.statistics.time_comparison.declared
                ],
                fill: false,
                borderColor: '#34d399'
            }]
        }
    });
}

// Parse tree (tree.html): pretty JSON view or D3 rendering
document.addEventListener("DOMContentLoaded", function(){
    if (document.getElementById("tree") && typeof astData !== "undefined") {
        d3.select("#tree").append("pre").text(JSON.stringify(astData, null, 2));
        // To upgrade: use D3.hierarchy for tree rendering.
    }
});
