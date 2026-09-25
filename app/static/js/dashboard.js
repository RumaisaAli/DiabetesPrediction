/**
 * Dashboard & Result Visualization Logic
 * Renders SVG risk gauge, Chart.js factor chart, personalized recommendations,
 * historical health trend line chart, and triggers server-side PDF downloads.
 */

let factorsChart = null;
let trendChart = null;

document.addEventListener("DOMContentLoaded", async () => {
    const user = Auth.initPage("Patient Health Dashboard", ["patient", "provider", "admin"]);
    if (!user) return;

    // Personalized greeting
    const greetingEl = document.getElementById("patient-greeting");
    if (greetingEl) {
        const hour = new Date().getHours();
        const timeOfDay = hour < 12 ? "morning" : (hour < 18 ? "afternoon" : "evening");
        greetingEl.textContent = `Good ${timeOfDay}, ${user.username}`;
    }

    // Load active system model
    loadActiveModelInfo();

    // Load Records and Predictions
    await loadDashboardData();

    // Setup Feedback Modal
    setupFeedbackModal();
});

async function loadActiveModelInfo() {
    try {
        const res = await fetch("/api/active-model");
        if (res.ok) {
            const data = await res.json();
            const el = document.getElementById("active-system-model-name");
            if (el) el.textContent = `${data.active_model} (v${data.version || '1.0.0'})`;
        }
    } catch (e) {
        console.error("Failed to load active model info", e);
    }
}

async function loadDashboardData() {
    try {
        const res = await Auth.fetchWithAuth("/api/records");
        const history = await res.json();

        if (!res.ok || !history || history.length === 0) {
            showEmptyState();
            return;
        }

        // Show dashboard content
        document.getElementById("empty-state").style.display = "none";
        document.getElementById("dashboard-content").style.display = "block";

        // Check if a specific prediction ID was passed via query param
        const urlParams = new URLSearchParams(window.location.search);
        const predId = urlParams.get("id");

        let activeItem = history[0]; // latest by default
        if (predId) {
            const found = history.find(h => h.id == predId);
            if (found) activeItem = found;
        }

        // Check if we have detailed latest_prediction in sessionStorage
        let detailedPrediction = null;
        const stored = sessionStorage.getItem("latest_prediction");
        if (stored) {
            try {
                const parsed = JSON.parse(stored);
                if (parsed.id === activeItem.id) {
                    detailedPrediction = parsed;
                }
            } catch (e) {}
        }

        renderRiskAssessment(activeItem, detailedPrediction);
        renderHistoryTable(history);
        renderTrendChart(history);
    } catch (err) {
        console.error("Failed to load dashboard data", err);
        showEmptyState();
    }
}

function showEmptyState() {
    document.getElementById("empty-state").style.display = "block";
    document.getElementById("dashboard-content").style.display = "none";
}

function renderRiskAssessment(item, detail) {
    const isHigh = item.risk_level === "High";
    const riskBadge = document.getElementById("risk-level-badge");
    const riskVal = document.getElementById("risk-confidence-val");
    const modelUsedEl = document.getElementById("model-used-display");
    const assessTimeEl = document.getElementById("assessment-time-display");
    const downloadBtn = document.getElementById("download-pdf-btn");

    if (riskBadge) {
        riskBadge.textContent = `${item.risk_level.toUpperCase()} RISK`;
        riskBadge.className = isHigh ? "badge badge-high-risk" : "badge badge-low-risk";
    }

    if (riskVal) riskVal.textContent = `${item.confidence.toFixed(1)}%`;
    if (modelUsedEl) modelUsedEl.textContent = item.model_used;
    if (assessTimeEl) assessTimeEl.textContent = new Date(item.date).toLocaleDateString(undefined, {
        month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit'
    });

    // Update Circular SVG Gauge
    const circleFill = document.getElementById("gauge-fill-circle");
    if (circleFill) {
        const circumference = 552.9; // 2 * PI * 88
        const offset = circumference - (item.confidence / 100) * circumference;
        circleFill.style.strokeDashoffset = offset;
        circleFill.style.stroke = isHigh ? "var(--error)" : "var(--primary)";
    }

    // PDF Download Button
    if (downloadBtn) {
        downloadBtn.onclick = () => {
            window.location.href = `/api/report/${item.id}/pdf`;
        };
    }

    // Render Factors Chart
    const topFactors = detail ? detail.top_factors : [
        { label: "Blood Glucose Level", impact: 42.0, status: item.glucose > 100 ? "Elevated" : "Optimal" },
        { label: "Body Mass Index", impact: 28.0, status: item.bmi > 25 ? "High" : "Optimal" },
        { label: "Patient Age", impact: 18.0, status: "Optimal" },
        { label: "Blood Pressure", impact: 12.0, status: "Optimal" }
    ];
    renderFactorsChart(topFactors);

    // Render Recommendations
    const recs = detail ? detail.recommendations : (
        isHigh ? [
            "Consult an Endocrinologist promptly for comprehensive HbA1c screening and clinical evaluation.",
            "Adopt a low-glycemic, Mediterranean-style diet; eliminate refined sugars and sweetened drinks.",
            "Engage in at least 150 minutes of moderate-intensity exercise per week (brisk walking, swimming).",
            "Monitor fasting blood glucose levels daily and maintain a detailed journal for physician review."
        ] : [
            "Maintain an active lifestyle with regular cardiovascular exercise to preserve insulin sensitivity.",
            "Follow a balanced, nutrient-dense diet emphasizing vegetables, healthy fats, and controlled portion sizes.",
            "Schedule an annual routine physical exam and routine metabolic blood panel."
        ]
    );
    renderRecommendations(recs, isHigh);
}

function renderFactorsChart(factors) {
    const ctx = document.getElementById("factorsChart");
    if (!ctx) return;

    if (factorsChart) factorsChart.destroy();

    const labels = factors.slice(0, 5).map(f => f.label || f.feature);
    const data = factors.slice(0, 5).map(f => f.impact);

    factorsChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Relative Impact (%)",
                data: data,
                backgroundColor: [
                    "#35607f",
                    "#4f7999",
                    "#615e57",
                    "#8b6f5b",
                    "#a1cbef"
                ],
                borderRadius: 8
            }]
        },
        options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (ctx) => `Contribution: ${ctx.parsed.x.toFixed(1)}%`
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    max: 100,
                    grid: { color: "#efeeeb" }
                },
                y: {
                    grid: { display: false }
                }
            }
        }
    });
}

function renderRecommendations(recs, isHigh) {
    const container = document.getElementById("recommendations-list");
    if (!container) return;

    container.innerHTML = "";
    recs.forEach((rec, idx) => {
        const item = document.createElement("li");
        item.className = `recommendation-item ${isHigh && idx === 0 ? "high-priority" : ""}`;
        item.innerHTML = `
            <span class="material-symbols-outlined" style="color: ${isHigh ? 'var(--error)' : 'var(--primary)'}">
                ${idx === 0 ? 'medical_services' : 'check_circle'}
            </span>
            <span>${rec}</span>
        `;
        container.appendChild(item);
    });
}

function renderTrendChart(history) {
    const ctx = document.getElementById("trendChart");
    if (!ctx) return;

    if (trendChart) trendChart.destroy();

    // Sort chronologically ascending for line trend
    const sorted = [...history].sort((a, b) => new Date(a.date) - new Date(b.date));

    const labels = sorted.map(h => new Date(h.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }));
    const glucoseData = sorted.map(h => h.glucose);
    const bmiData = sorted.map(h => h.bmi);

    trendChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Blood Glucose (mg/dL)",
                    data: glucoseData,
                    borderColor: "#ba1a1a",
                    backgroundColor: "rgba(186, 26, 26, 0.1)",
                    borderWidth: 2,
                    tension: 0.3,
                    fill: false
                },
                {
                    label: "BMI",
                    data: bmiData,
                    borderColor: "#35607f",
                    backgroundColor: "rgba(53, 96, 127, 0.1)",
                    borderWidth: 2,
                    tension: 0.3,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: "index",
                intersect: false,
            },
            plugins: {
                legend: { position: "top" }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    grid: { color: "#efeeeb" }
                },
                x: {
                    grid: { display: false }
                }
            }
        }
    });
}

function renderHistoryTable(history) {
    const tbody = document.getElementById("history-table-body");
    if (!tbody) return;

    tbody.innerHTML = "";
    history.forEach(item => {
        const isHigh = item.risk_level === "High";
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><b>${new Date(item.date).toLocaleDateString()}</b></td>
            <td><span class="badge ${isHigh ? 'badge-high-risk' : 'badge-low-risk'}">${item.risk_level}</span></td>
            <td>${item.confidence.toFixed(1)}%</td>
            <td>${item.glucose.toFixed(1)} mg/dL</td>
            <td>${item.bmi.toFixed(1)}</td>
            <td><small class="text-muted">${item.model_used}</small></td>
            <td>
                <button class="btn btn-secondary btn-sm" onclick="window.location.href='/api/report/${item.id}/pdf'">
                    <span class="material-symbols-outlined" style="font-size: 16px;">download</span> PDF
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function setupFeedbackModal() {
    const btn = document.getElementById("feedback-modal-btn");
    const modal = document.getElementById("feedback-modal");
    const form = document.getElementById("feedback-form");
    const closeBtn = document.getElementById("close-feedback-btn");
    const statusMsg = document.getElementById("feedback-status");

    if (!btn || !modal) return;

    btn.onclick = () => { modal.style.display = "flex"; };
    if (closeBtn) closeBtn.onclick = () => { modal.style.display = "none"; };

    if (form) {
        form.onsubmit = async (e) => {
            e.preventDefault();
            const message = document.getElementById("feedback-text").value.trim();
            if (!message) return;

            statusMsg.textContent = "Submitting feedback...";
            statusMsg.style.display = "block";

            try {
                const res = await Auth.fetchWithAuth("/api/feedback", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ message })
                });

                if (res.ok) {
                    statusMsg.className = "alert alert-success";
                    statusMsg.textContent = "Thank you! Your feedback has been sent to our clinical team.";
                    setTimeout(() => {
                        modal.style.display = "none";
                        document.getElementById("feedback-text").value = "";
                        statusMsg.style.display = "none";
                    }, 1800);
                } else {
                    statusMsg.className = "alert alert-error";
                    statusMsg.textContent = "Failed to submit feedback.";
                }
            } catch (err) {
                statusMsg.className = "alert alert-error";
                statusMsg.textContent = "Network error submitting feedback.";
            }
        };
    }
}
