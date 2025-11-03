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
                    report.statistics.difficulty_easy_count,
                    report.statistics.difficulty_medium_count,
                    report.statistics.difficulty_hard_count
                ],
                backgroundColor: ['#4ade80', '#facc15', '#f87171']
            }]
        }
    });

    // Marks Bar Chart
    const marks = (report.questions || []).map(q => q.marks);
    const labels = (report.questions || []).map((q, i) => 'Q' + (i+1));
    const marksCtx = document.getElementById('marksChart').getContext('2d');
    new Chart(marksCtx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Marks per Question',
                data: marks,
                backgroundColor: '#60a5fa'
            }]
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
                    report.statistics.estimated_time_minutes,
                    report.statistics.declared_time_minutes
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