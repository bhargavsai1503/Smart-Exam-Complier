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
<<<<<<< HEAD
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
=======
    try {
        if (!report || typeof report !== 'object') {
            console.warn('renderCharts: invalid report object', report);
            return;
        }

        // Difficulty Pie Chart: try multiple report shapes
        const difficultyEl = document.getElementById('difficultyChart');
        if (difficultyEl && difficultyEl.getContext) {
            const difficultyCtx = difficultyEl.getContext('2d');
            // Try several places for counts
            let easy = 0, medium = 0, hard = 0;
            // 1) report.checks.difficulty_distribution (primary location)
            if (report?.checks?.difficulty_distribution) {
                easy = report.checks.difficulty_distribution.easy_count || report.checks.difficulty_distribution.easy || easy;
                medium = report.checks.difficulty_distribution.medium_count || report.checks.difficulty_distribution.medium || medium;
                hard = report.checks.difficulty_distribution.hard_count || report.checks.difficulty_distribution.hard || hard;
            }
            // 2) report.statistics.difficulty_distribution (fallback)
            if (report?.statistics?.difficulty_distribution) {
                easy = easy || report.statistics.difficulty_distribution.easy ?? report.statistics.difficulty_distribution.easy_count ?? report.statistics.difficulty_easy_count ?? easy;
                medium = medium || report.statistics.difficulty_distribution.medium ?? report.statistics.difficulty_distribution.medium_count ?? report.statistics.difficulty_medium_count ?? medium;
                hard = hard || report.statistics.difficulty_distribution.hard ?? report.statistics.difficulty_distribution.hard_count ?? report.statistics.difficulty_hard_count ?? hard;
            }
            // 3) report.statistics direct counts
            easy = easy || report?.statistics?.difficulty_easy_count || 0;
            medium = medium || report?.statistics?.difficulty_medium_count || 0;
            hard = hard || report?.statistics?.difficulty_hard_count || 0;
            // 4) derive from questions array if still zero
            if ((!easy && !medium && !hard) && Array.isArray(report?.questions)) {
                report.questions.forEach(q => {
                    const diff = (q.difficulty || '').toLowerCase();
                    if (diff.includes('easy')) easy++;
                    else if (diff.includes('hard')) hard++;
                    else medium++;
                });
            }
            if (typeof Chart !== 'undefined') {
                new Chart(difficultyCtx, {
                    type: 'pie',
                    data: {
                        labels: ['Easy', 'Medium', 'Hard'],
                        datasets: [{
                            data: [easy, medium, hard],
                            backgroundColor: ['#4ade80', '#facc15', '#f87171']
                        }]
                    }
                });
            }
        }

        // Marks Distribution Bar Chart (aggregated by mark value)
        const marksEl = document.getElementById('marksChart');
        if (marksEl && marksEl.getContext) {
            // Try to build marks distribution from various shapes
            let marksLabels = [];
            let marksData = [];
            const marksDist = report?.statistics?.marks_distribution || report?.statistics?.marks_distribution || report?.marks_distribution || null;
            if (marksDist && typeof marksDist === 'object' && Object.keys(marksDist).length > 0) {
                marksLabels = Object.keys(marksDist);
                marksData = Object.values(marksDist);
            } else if (Array.isArray(report?.questions)) {
                // Aggregate number of questions per marks value
                const agg = {};
                report.questions.forEach(q => {
                    const m = q.marks ?? q.mark ?? 0;
                    agg[m] = (agg[m] || 0) + 1;
                });
                marksLabels = Object.keys(agg).sort((a,b)=>Number(a)-Number(b));
                marksData = marksLabels.map(k => agg[k]);
            }
            if (typeof Chart !== 'undefined') {
                const marksCtx = marksEl.getContext('2d');
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
            }
        }

        // Time Line Chart
        const timeEl = document.getElementById('timeChart');
        if (timeEl && timeEl.getContext) {
            const est = report?.statistics?.time_comparison?.estimated ?? report?.statistics?.estimated_time_minutes ?? 0;
            const dec = report?.statistics?.time_comparison?.declared ?? report?.statistics?.declared_time_minutes ?? 0;
            if (typeof Chart !== 'undefined') {
                const timeCtx = timeEl.getContext('2d');
                new Chart(timeCtx, {
                    type: 'line',
                    data: {
                        labels: ['Estimated', 'Declared'],
                        datasets: [{
                            label: 'Time (minutes)',
                            data: [est, dec],
                            fill: false,
                            borderColor: '#34d399'
                        }]
                    }
                });
            }
        }
    } catch (err) {
        console.error('renderCharts error:', err);
        const chartsContainer = document.getElementById('charts');
        if (chartsContainer) chartsContainer.innerHTML = '<div class="p-4 text-red-600">Failed to render charts. See console for details.</div>';
    }
}

// Initialize charts when charts tab is shown
// Note: dashboard template defines its own showTab and handles initial tab activation.
>>>>>>> final_version
