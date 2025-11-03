// Sample data from JSON
const sampleData = {
  header: {
    syllabus: "Compiler Design (CS401)",
    total_marks: 100,
    time_minutes: 180
  },
  questions: [
    { number: 1, text: "Define compiler and interpreter. Differentiate between them.", marks: 10, difficulty: "EASY", crispness: "CRISP" },
    { number: 2, text: "Explain the phases of compiler design with a neat diagram.", marks: 10, difficulty: "MEDIUM", crispness: "CRISP" },
    { number: 3, text: "Construct a DFA for the regular expression (a|b)*abb.", marks: 12, difficulty: "HARD", crispness: "CRISP" },
    { number: 4, text: "Describe top-down and bottom-up parsing techniques.", marks: 10, difficulty: "MEDIUM", crispness: "CRISP" },
    { number: 5, text: "List the different types of tokens in lexical analysis.", marks: 8, difficulty: "EASY", crispness: "CRISP" },
    { number: 6, text: "Design and implement a complete compiler for a simple programming language that supports variable declarations, arithmetic operations, conditional statements, loops, and function calls with proper error handling and optimization.", marks: 15, difficulty: "HARD", crispness: "VERBOSE" },
    { number: 7, text: "Explain syntax-directed translation with examples.", marks: 10, difficulty: "MEDIUM", crispness: "CRISP" },
    { number: 8, text: "State the properties of context-free grammars.", marks: 5, difficulty: "EASY", crispness: "CRISP" },
    { number: 9, text: "Discuss code optimization techniques in detail.", marks: 10, difficulty: "MEDIUM", crispness: "CRISP" },
    { number: 10, text: "Illustrate the process of intermediate code generation.", marks: 10, difficulty: "MEDIUM", crispness: "CRISP" }
  ],
  analysis: {
    marks_validation: {
      status: "FAIL",
      calculated_total: 100,
      declared_total: 100,
      message: "Marks sum matches but Question 3 should be 10 marks, not 12"
    },
    time_estimation: {
      status: "WARN",
      estimated_time: 195,
      declared_time: 180,
      difference: 15
    },
    difficulty_distribution: {
      status: "PASS",
      easy_count: 3,
      medium_count: 5,
      hard_count: 2,
      easy_percentage: 30.0,
      medium_percentage: 50.0,
      hard_percentage: 20.0
    },
    crispness_analysis: {
      status: "WARN",
      crisp_count: 9,
      verbose_count: 1,
      ambiguous_count: 0,
      crispness_percentage: 90.0
    }
  },
  warnings: [
    "Time allocation mismatch: 15 minutes over estimated time",
    "Question 6 is too verbose (>100 words)"
  ],
  suggestions: [
    "Consider reducing Question 6 complexity or splitting into parts",
    "Reduce Question 3 marks from 12 to 10 for better balance",
    "Add more diverse topics to improve syllabus coverage"
  ],
  quality_score: 78
};

const parseTree = {
  root: {
    type: "paper",
    children: [
      {
        type: "header",
        data: { syllabus: "Compiler Design", marks: 100, time: "180 min" }
      },
      {
        type: "questions",
        children: [
          { q: 1, marks: 10, diff: "EASY" },
          { q: 2, marks: 10, diff: "MEDIUM" },
          { q: 3, marks: 12, diff: "HARD" },
          { q: 4, marks: 10, diff: "MEDIUM" },
          { q: 5, marks: 8, diff: "EASY" },
          { q: 6, marks: 15, diff: "HARD" },
          { q: 7, marks: 10, diff: "MEDIUM" },
          { q: 8, marks: 5, diff: "EASY" },
          { q: 9, marks: 10, diff: "MEDIUM" },
          { q: 10, marks: 10, diff: "MEDIUM" }
        ]
      }
    ]
  }
};

// State management
let analysisComplete = false;
let currentFile = null;

// Navigation
function navigateTo(page) {
  // Update active page
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById(`page-${page}`).classList.add('active');

  // Update active nav link
  document.querySelectorAll('.nav-link').forEach(link => {
    link.classList.remove('active');
    if (link.dataset.page === page) {
      link.classList.add('active');
    }
  });

  // Scroll to top
  window.scrollTo(0, 0);

  // Initialize charts if navigating to dashboard
  if (page === 'dashboard' && analysisComplete) {
    setTimeout(() => initCharts(), 100);
  }

  // Initialize tree if navigating to tree page
  if (page === 'tree' && analysisComplete) {
    setTimeout(() => initTree(), 100);
  }
}

// Setup navigation listeners
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const page = link.dataset.page;
      if (!link.classList.contains('disabled')) {
        navigateTo(page);
      }
    });
  });

  setupFileUpload();
  setupTabs();
});

// File upload
function setupFileUpload() {
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('fileInput');
  const filePreview = document.getElementById('filePreview');

  // Drag and drop
  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('drag-over');
  });

  dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('drag-over');
  });

  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('drag-over');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFile(files[0]);
    }
  });

  // File input
  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      handleFile(e.target.files[0]);
    }
  });
}

function handleFile(file) {
  currentFile = file;
  const fileName = document.getElementById('fileName');
  const fileSize = document.getElementById('fileSize');
  const dropzone = document.getElementById('dropzone');
  const filePreview = document.getElementById('filePreview');

  fileName.textContent = file.name;
  fileSize.textContent = formatFileSize(file.size);

  dropzone.style.display = 'none';
  filePreview.style.display = 'block';
}

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// Analysis simulation
function analyzeFile() {
  const progressSection = document.getElementById('progressSection');
  const filePreview = document.getElementById('filePreview');

  filePreview.style.display = 'none';
  progressSection.style.display = 'block';

  simulateProgress();
}

function simulateProgress() {
  const stages = [
    { stage: 1, message: 'Extracting text from document...', duration: 1000 },
    { stage: 2, message: 'Tokenizing with Lex...', duration: 1500 },
    { stage: 3, message: 'Parsing with Yacc...', duration: 2000 },
    { stage: 4, message: 'Performing semantic analysis...', duration: 1500 },
    { stage: 5, message: 'Generating enhancement suggestions...', duration: 1000 }
  ];

  let currentStage = 0;
  const progressFill = document.getElementById('progressFill');
  const progressStatus = document.getElementById('progressStatus');

  function runStage() {
    if (currentStage >= stages.length) {
      completeAnalysis();
      return;
    }

    const stage = stages[currentStage];
    progressStatus.textContent = stage.message;
    progressFill.style.width = ((currentStage + 1) / stages.length * 100) + '%';

    // Mark stage as active
    document.querySelectorAll('.progress-stage').forEach((el, idx) => {
      el.classList.remove('active');
      if (idx < currentStage) {
        el.classList.add('completed');
      }
      if (idx === currentStage) {
        el.classList.add('active');
      }
    });

    currentStage++;
    setTimeout(runStage, stage.duration);
  }

  runStage();
}

function completeAnalysis() {
  analysisComplete = true;
  showToast('Analysis completed successfully!');

  // Enable navigation links
  document.getElementById('nav-dashboard').classList.remove('disabled');
  document.getElementById('nav-tree').classList.remove('disabled');
  document.getElementById('nav-enhanced').classList.remove('disabled');

  // Navigate to dashboard
  setTimeout(() => {
    navigateTo('dashboard');
  }, 1000);
}

// Toast notification
function showToast(message) {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.classList.add('show');
  setTimeout(() => {
    toast.classList.remove('show');
  }, 3000);
}

// Tabs
function setupTabs() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const tab = btn.dataset.tab;

      // Update active tab button
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      // Update active tab content
      document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
      });
      document.getElementById(`tab-${tab}`).classList.add('active');

      // Initialize charts if charts tab
      if (tab === 'charts') {
        setTimeout(() => initCharts(), 100);
      }
    });
  });
}

// Charts initialization
let chartsInitialized = false;

function initCharts() {
  if (chartsInitialized) return;
  chartsInitialized = true;

  // Marks distribution chart
  const marksCtx = document.getElementById('marksChart');
  if (marksCtx) {
    new Chart(marksCtx, {
      type: 'bar',
      data: {
        labels: ['Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'Q6', 'Q7', 'Q8', 'Q9', 'Q10'],
        datasets: [{
          label: 'Marks',
          data: [10, 10, 12, 10, 8, 15, 10, 5, 10, 10],
          backgroundColor: '#32B8C6',
          borderColor: '#32B8C6',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: {
            labels: { color: '#e2e8f0' }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: { color: '#a0aec0' },
            grid: { color: 'rgba(255, 255, 255, 0.1)' }
          },
          x: {
            ticks: { color: '#a0aec0' },
            grid: { color: 'rgba(255, 255, 255, 0.1)' }
          }
        }
      }
    });
  }

  // Difficulty distribution chart
  const diffCtx = document.getElementById('difficultyChart');
  if (diffCtx) {
    new Chart(diffCtx, {
      type: 'pie',
      data: {
        labels: ['Easy', 'Medium', 'Hard'],
        datasets: [{
          data: [30, 50, 20],
          backgroundColor: ['#32B8C6', '#E68161', '#FF5459'],
          borderColor: '#2d3748',
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: {
            labels: { color: '#e2e8f0' }
          }
        }
      }
    });
  }

  // Time analysis chart
  const timeCtx = document.getElementById('timeChart');
  if (timeCtx) {
    new Chart(timeCtx, {
      type: 'line',
      data: {
        labels: ['Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'Q6', 'Q7', 'Q8', 'Q9', 'Q10'],
        datasets: [
          {
            label: 'Estimated Time (min)',
            data: [15, 18, 25, 18, 12, 35, 18, 10, 20, 24],
            borderColor: '#32B8C6',
            backgroundColor: 'rgba(50, 184, 198, 0.1)',
            tension: 0.4,
            fill: true
          },
          {
            label: 'Allotted Time (min)',
            data: [18, 18, 18, 18, 18, 18, 18, 18, 18, 18],
            borderColor: '#E68161',
            backgroundColor: 'rgba(230, 129, 97, 0.1)',
            borderDash: [5, 5],
            tension: 0.4,
            fill: false
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: {
            labels: { color: '#e2e8f0' }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: { color: '#a0aec0' },
            grid: { color: 'rgba(255, 255, 255, 0.1)' }
          },
          x: {
            ticks: { color: '#a0aec0' },
            grid: { color: 'rgba(255, 255, 255, 0.1)' }
          }
        }
      }
    });
  }
}

// Parse Tree Visualization
let treeInitialized = false;

function initTree() {
  if (treeInitialized) return;
  treeInitialized = true;

  const container = document.getElementById('treeContainer');
  const width = container.offsetWidth || 1000;
  const height = 600;

  const svg = d3.select('#treeContainer')
    .append('svg')
    .attr('width', width)
    .attr('height', height);

  const g = svg.append('g')
    .attr('transform', 'translate(50, 50)');

  // Create tree data
  const treeData = {
    name: 'Question Paper',
    children: [
      {
        name: 'Header',
        children: [
          { name: 'Syllabus: CS401' },
          { name: 'Marks: 100' },
          { name: 'Time: 180 min' }
        ]
      },
      {
        name: 'Questions',
        children: [
          { name: 'Q1 (10) - EASY' },
          { name: 'Q2 (10) - MEDIUM' },
          { name: 'Q3 (12) - HARD' },
          { name: 'Q4 (10) - MEDIUM' },
          { name: 'Q5 (8) - EASY' },
          { name: 'Q6 (15) - HARD' },
          { name: 'Q7 (10) - MEDIUM' },
          { name: 'Q8 (5) - EASY' },
          { name: 'Q9 (10) - MEDIUM' },
          { name: 'Q10 (10) - MEDIUM' }
        ]
      }
    ]
  };

  const root = d3.hierarchy(treeData);
  const treeLayout = d3.tree().size([height - 100, width - 200]);
  treeLayout(root);

  // Links
  g.selectAll('.link')
    .data(root.links())
    .enter()
    .append('path')
    .attr('class', 'link')
    .attr('d', d3.linkHorizontal()
      .x(d => d.y)
      .y(d => d.x));

  // Nodes
  const node = g.selectAll('.node')
    .data(root.descendants())
    .enter()
    .append('g')
    .attr('class', 'node')
    .attr('transform', d => `translate(${d.y},${d.x})`);

  node.append('circle')
    .attr('r', 5);

  node.append('text')
    .attr('dy', -10)
    .attr('text-anchor', 'middle')
    .text(d => d.data.name);
}

function expandAllNodes() {
  showToast('All nodes expanded');
}

function collapseAllNodes() {
  showToast('All nodes collapsed');
}

function downloadTree() {
  showToast('Tree downloaded as image');
}

// Download functions
function downloadEnhanced() {
  const content = `ENHANCED QUESTION PAPER\n\nCompiler Design (CS401)\nTotal Marks: 100 | Time: 180 minutes\n\n${sampleData.questions.map((q, idx) => {
    if (q.number === 3) {
      return `Q${q.number}. ${q.text} (10) [Changed from 12]`;
    } else if (q.number === 6) {
      return `Q${q.number}.\n  a) Design a compiler architecture for a simple language. (8)\n  b) Implement lexical and syntax analysis phases. (7) [Split from original]`;
    }
    return `Q${q.number}. ${q.text} (${q.marks})`;
  }).join('\n\n')}`;

  const blob = new Blob([content], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'enhanced_paper.txt';
  a.click();
  URL.revokeObjectURL(url);

  showToast('Enhanced paper downloaded');
}

function downloadReport() {
  showToast('PDF report generation in progress...');
  setTimeout(() => {
    showToast('PDF report downloaded');
  }, 2000);
}