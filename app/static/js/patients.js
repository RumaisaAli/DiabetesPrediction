/**
 * Patient Records Portal Client Logic
 * Healthcare provider and administrator patient directory, search, filtering,
 * detailed clinical history modal, Chart.js longitudinal trends, and PDF downloads.
 */

let patientTrendChart = null;
let searchDebounceTimer = null;

document.addEventListener("DOMContentLoaded", () => {
    const user = Auth.initPage("Patient Records", ["provider", "admin"]);
    if (!user) return;

    loadPatientsList();

    // Setup debounced search input (300ms)
    const searchInput = document.getElementById("patient-search-input");
    if (searchInput) {
        searchInput.addEventListener("input", () => {
            clearTimeout(searchDebounceTimer);
            searchDebounceTimer = setTimeout(() => {
                loadPatientsList();
            }, 300);
        });
    }

    // Setup risk filter select
    const riskSelect = document.getElementById("risk-filter-select");
    if (riskSelect) {
        riskSelect.addEventListener("change", () => {
            loadPatientsList();
        });
    }

    // Clear filters button
    const clearBtn = document.getElementById("clear-filters-btn");
    if (clearBtn) {
        clearBtn.addEventListener("click", () => {
            if (searchInput) searchInput.value = "";
            if (riskSelect) riskSelect.value = "";
            loadPatientsList();
        });
    }

    // Modal backdrop click
    const modal = document.getElementById("patient-detail-modal");
    if (modal) {
        modal.addEventListener("click", (e) => {
            if (e.target === modal) {
                closePatientDetailModal();
            }
        });
    }
});

document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
        closePatientDetailModal();
    }
});

async function loadPatientsList() {
    const loadingEl = document.getElementById("patients-loading");
    const errorEl = document.getElementById("patients-error");
    const emptyEl = document.getElementById("patients-empty");
    const tableContainer = document.getElementById("patients-table-container");
    const tableBody = document.getElementById("patients-table-body");
    const searchInput = document.getElementById("patient-search-input");
    const riskSelect = document.getElementById("risk-filter-select");

    loadingEl.style.display = "block";
    errorEl.style.display = "none";
    emptyEl.style.display = "none";
    tableContainer.style.display = "none";
    tableBody.innerHTML = "";

    const queryParams = new URLSearchParams();
    if (searchInput && searchInput.value.trim()) {
        queryParams.set("search", searchInput.value.trim());
    }
    if (riskSelect && riskSelect.value) {
        queryParams.set("risk", riskSelect.value);
    }

    try {
        const url = `/api/patients?${queryParams.toString()}`;
        const res = await Auth.fetchWithAuth(url);
        loadingEl.style.display = "none";

        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            errorEl.textContent = errData.detail || "Failed to load patient records.";
            errorEl.style.display = "flex";
            return;
        }

        const patients = await res.json();
        if (!patients || patients.length === 0) {
            emptyEl.style.display = "block";
            return;
        }

        tableContainer.style.display = "block";
        renderPatientsTable(patients);
    } catch (err) {
        loadingEl.style.display = "none";
        errorEl.textContent = "Network error loading patient records.";
        errorEl.style.display = "flex";
    }
}

function renderPatientsTable(patients) {
    const tableBody = document.getElementById("patients-table-body");
    tableBody.innerHTML = "";

    patients.forEach(patient => {
        const row = document.createElement("tr");

        // 1. Patient Name
        const nameCell = document.createElement("td");
        nameCell.style.fontWeight = "600";
        nameCell.style.color = "var(--text-main)";
        nameCell.textContent = patient.username;
        row.appendChild(nameCell);

        // 2. Email Address
        const emailCell = document.createElement("td");
        emailCell.style.color = "var(--text-muted)";
        emailCell.textContent = patient.email;
        row.appendChild(emailCell);

        // 3. Age
        const ageCell = document.createElement("td");
        ageCell.textContent = patient.latest_age !== null && patient.latest_age !== undefined
            ? Math.round(patient.latest_age)
            : "--";
        row.appendChild(ageCell);

        // 4. Total Assessments
        const totalCell = document.createElement("td");
        const totalBadge = document.createElement("span");
        totalBadge.style.cssText = "display: inline-block; padding: 2px 8px; border-radius: var(--radius-full); background: var(--surface-low); border: 1px solid var(--border); font-size: 12px; font-weight: 600;";
        totalBadge.textContent = patient.total_assessments;
        totalCell.appendChild(totalBadge);
        row.appendChild(totalCell);

        // 5. Latest Risk Badge
        const riskCell = document.createElement("td");
        const riskBadge = document.createElement("span");
        riskBadge.className = "badge";
        if (patient.latest_risk_level === "High") {
            riskBadge.classList.add("badge-high-risk");
            riskBadge.textContent = "High Risk";
        } else if (patient.latest_risk_level === "Low") {
            riskBadge.classList.add("badge-low-risk");
            riskBadge.textContent = "Low Risk";
        } else {
            riskBadge.style.backgroundColor = "var(--surface-low)";
            riskBadge.style.color = "var(--text-muted)";
            riskBadge.textContent = "No data";
        }
        riskCell.appendChild(riskBadge);
        row.appendChild(riskCell);

        // 6. Confidence %
        const confCell = document.createElement("td");
        confCell.textContent = patient.latest_confidence !== null && patient.latest_confidence !== undefined
            ? `${patient.latest_confidence.toFixed(1)}%`
            : "--";
        row.appendChild(confCell);

        // 7. Last Assessment Date
        const dateCell = document.createElement("td");
        dateCell.style.color = "var(--text-muted)";
        dateCell.style.fontSize = "13px";
        if (patient.last_assessment_date) {
            const d = new Date(patient.last_assessment_date);
            dateCell.textContent = d.toLocaleDateString(undefined, {
                year: "numeric",
                month: "short",
                day: "numeric"
            });
        } else {
            dateCell.textContent = "Never";
        }
        row.appendChild(dateCell);

        // 8. Actions ("View Record" Button)
        const actionCell = document.createElement("td");
        actionCell.style.textAlign = "right";

        const viewBtn = document.createElement("button");
        viewBtn.className = "btn btn-secondary btn-sm";
        viewBtn.style.display = "inline-flex";
        viewBtn.style.alignItems = "center";
        viewBtn.style.gap = "4px";

        const viewIcon = document.createElement("span");
        viewIcon.className = "material-symbols-outlined";
        viewIcon.style.fontSize = "16px";
        viewIcon.textContent = "visibility";
        viewBtn.appendChild(viewIcon);

        const viewText = document.createElement("span");
        viewText.textContent = "View Record";
        viewBtn.appendChild(viewText);

        viewBtn.onclick = () => openPatientDetailModal(patient.id);
        actionCell.appendChild(viewBtn);
        row.appendChild(actionCell);

        tableBody.appendChild(row);
    });
}

async function openPatientDetailModal(patientId) {
    const modal = document.getElementById("patient-detail-modal");
    if (!modal) return;

    // Reset modal fields while loading
    document.getElementById("modal-patient-name").textContent = "Loading Patient Profile...";
    document.getElementById("modal-patient-email").textContent = "";
    document.getElementById("modal-latest-risk-badge").textContent = "--";
    document.getElementById("modal-latest-risk-badge").className = "badge";
    document.getElementById("modal-latest-confidence").textContent = "";
    document.getElementById("modal-vitals-container").innerHTML = "<div style='grid-column: span 4; text-align: center; color: var(--text-muted); padding: 12px;'>Loading vitals...</div>";
    document.getElementById("modal-history-table-body").innerHTML = "";

    modal.classList.add("show");

    try {
        const res = await Auth.fetchWithAuth(`/api/patients/${patientId}`);
        if (!res.ok) {
            UI.showToast("Failed to retrieve patient clinical profile", "error");
            closePatientDetailModal();
            return;
        }

        const patient = await res.json();
        renderPatientDetail(patient);
    } catch (err) {
        UI.showToast("Network error retrieving patient record", "error");
        closePatientDetailModal();
    }
}

function renderPatientDetail(patient) {
    // Header Info
    document.getElementById("modal-patient-name").textContent = patient.username;
    document.getElementById("modal-patient-email").textContent = patient.email;

    // "Add Assessment for this Patient" Button
    const addLink = document.getElementById("modal-add-assessment-link");
    if (addLink) {
        addLink.href = `/input?patient_id=${patient.id}`;
    }

    // Latest Risk Badge & Confidence
    const riskBadge = document.getElementById("modal-latest-risk-badge");
    riskBadge.className = "badge";
    if (patient.latest_risk_level === "High") {
        riskBadge.classList.add("badge-high-risk");
        riskBadge.textContent = "High Risk";
    } else if (patient.latest_risk_level === "Low") {
        riskBadge.classList.add("badge-low-risk");
        riskBadge.textContent = "Low Risk";
    } else {
        riskBadge.style.backgroundColor = "var(--surface-low)";
        riskBadge.style.color = "var(--text-muted)";
        riskBadge.textContent = "No Assessments";
    }

    const confEl = document.getElementById("modal-latest-confidence");
    if (patient.latest_confidence) {
        confEl.textContent = `(${patient.latest_confidence.toFixed(1)}% confidence)`;
    } else {
        confEl.textContent = "";
    }

    // Render Latest Vitals
    renderModalVitals(patient.latest_vitals);

    // Render Longitudinal Trend Chart
    renderPatientTrendChart(patient.history);

    // Render History Table
    renderModalHistoryTable(patient.history);
}

function renderModalVitals(vitals) {
    const container = document.getElementById("modal-vitals-container");
    container.innerHTML = "";

    if (!vitals) {
        const emptyMsg = document.createElement("div");
        emptyMsg.style.gridColumn = "span 4";
        emptyMsg.style.textAlign = "center";
        emptyMsg.style.color = "var(--text-muted)";
        emptyMsg.style.padding = "16px";
        emptyMsg.style.background = "var(--surface-low)";
        emptyMsg.style.borderRadius = "var(--radius-md)";
        emptyMsg.textContent = "No clinical vitals recorded yet for this patient.";
        container.appendChild(emptyMsg);
        return;
    }

    const indicators = [
        { label: "Blood Glucose", value: `${vitals.glucose} mg/dL`, icon: "bloodtype" },
        { label: "Body Mass Index", value: `${vitals.bmi} kg/m²`, icon: "monitor_weight" },
        { label: "Blood Pressure", value: `${vitals.blood_pressure} mm Hg`, icon: "speed" },
        { label: "Serum Insulin", value: `${vitals.insulin} mu U/ml`, icon: "vaccines" },
        { label: "Skin Thickness", value: `${vitals.skin_thickness} mm`, icon: "straighten" },
        { label: "Pregnancies", value: `${vitals.pregnancies}`, icon: "family_restroom" },
        { label: "Pedigree Function", value: `${vitals.diabetes_pedigree_function}`, icon: "dna" },
        { label: "Age", value: `${Math.round(vitals.age)} years`, icon: "calendar_today" },
    ];

    indicators.forEach(item => {
        const card = document.createElement("div");
        card.style.cssText = "background: var(--surface-low); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 12px 14px;";

        const topRow = document.createElement("div");
        topRow.style.cssText = "display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;";

        const label = document.createElement("span");
        label.style.cssText = "font-size: 11px; font-weight: 600; color: var(--text-muted); text-transform: uppercase;";
        label.textContent = item.label;
        topRow.appendChild(label);

        const icon = document.createElement("span");
        icon.className = "material-symbols-outlined";
        icon.style.cssText = "font-size: 16px; color: var(--primary);";
        icon.textContent = item.icon;
        topRow.appendChild(icon);

        const val = document.createElement("div");
        val.style.cssText = "font-size: 15px; font-weight: 700; color: var(--text-main);";
        val.textContent = item.value;

        card.appendChild(topRow);
        card.appendChild(val);
        container.appendChild(card);
    });
}

function renderPatientTrendChart(history) {
    const ctx = document.getElementById("patientTrendChart");
    if (!ctx) return;

    if (patientTrendChart) {
        patientTrendChart.destroy();
        patientTrendChart = null;
    }

    if (!history || history.length === 0) {
        return;
    }

    // Reverse history to display chronological progression left-to-right
    const chronological = [...history].reverse();
    const labels = chronological.map(h => {
        const d = new Date(h.date);
        return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
    });

    const glucoseData = chronological.map(h => h.glucose);
    const bmiData = chronological.map(h => h.bmi);
    const bpData = chronological.map(h => h.blood_pressure);

    patientTrendChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Glucose (mg/dL)",
                    data: glucoseData,
                    borderColor: "#35607f",
                    backgroundColor: "rgba(53, 96, 127, 0.1)",
                    borderWidth: 2,
                    tension: 0.3,
                    pointRadius: 4,
                    fill: false
                },
                {
                    label: "BMI (kg/m²)",
                    data: bmiData,
                    borderColor: "#b78103",
                    backgroundColor: "rgba(183, 129, 3, 0.1)",
                    borderWidth: 2,
                    tension: 0.3,
                    pointRadius: 4,
                    fill: false
                },
                {
                    label: "Blood Pressure (mm Hg)",
                    data: bpData,
                    borderColor: "#615e57",
                    backgroundColor: "rgba(97, 94, 87, 0.1)",
                    borderWidth: 2,
                    tension: 0.3,
                    pointRadius: 4,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: "index",
                intersect: false
            },
            plugins: {
                legend: {
                    position: "top",
                    labels: {
                        boxWidth: 12,
                        font: { family: "Inter", size: 12 }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { font: { family: "Inter", size: 11 } }
                },
                y: {
                    grid: { color: "#efeeeb" },
                    ticks: { font: { family: "Inter", size: 11 } }
                }
            }
        }
    });
}

function renderModalHistoryTable(history) {
    const tableBody = document.getElementById("modal-history-table-body");
    tableBody.innerHTML = "";

    if (!history || history.length === 0) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");
        cell.colSpan = 8;
        cell.style.textAlign = "center";
        cell.style.color = "var(--text-muted)";
        cell.style.padding = "20px";
        cell.textContent = "No assessment history available for this patient.";
        row.appendChild(cell);
        tableBody.appendChild(row);
        return;
    }

    history.forEach(item => {
        const row = document.createElement("tr");

        // Date
        const dateCell = document.createElement("td");
        dateCell.style.fontSize = "13px";
        const d = new Date(item.date);
        dateCell.textContent = d.toLocaleDateString(undefined, {
            year: "numeric",
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit"
        });
        row.appendChild(dateCell);

        // Risk Level
        const riskCell = document.createElement("td");
        const badge = document.createElement("span");
        badge.className = "badge";
        if (item.risk_level === "High") {
            badge.classList.add("badge-high-risk");
            badge.textContent = "High";
        } else {
            badge.classList.add("badge-low-risk");
            badge.textContent = "Low";
        }
        riskCell.appendChild(badge);
        row.appendChild(riskCell);

        // Confidence
        const confCell = document.createElement("td");
        confCell.textContent = `${item.confidence.toFixed(1)}%`;
        row.appendChild(confCell);

        // Glucose
        const gluCell = document.createElement("td");
        gluCell.textContent = item.glucose;
        row.appendChild(gluCell);

        // BMI
        const bmiCell = document.createElement("td");
        bmiCell.textContent = item.bmi;
        row.appendChild(bmiCell);

        // Blood Pressure
        const bpCell = document.createElement("td");
        bpCell.textContent = item.blood_pressure;
        row.appendChild(bpCell);

        // Model Used
        const modelCell = document.createElement("td");
        modelCell.style.fontSize = "12px";
        modelCell.style.color = "var(--text-muted)";
        modelCell.textContent = item.model_used;
        row.appendChild(modelCell);

        // Actions: Download PDF
        const actionCell = document.createElement("td");
        actionCell.style.textAlign = "right";

        const pdfBtn = document.createElement("a");
        pdfBtn.className = "btn btn-outline btn-sm";
        pdfBtn.style.display = "inline-flex";
        pdfBtn.style.alignItems = "center";
        pdfBtn.style.gap = "4px";
        pdfBtn.style.padding = "4px 8px";
        pdfBtn.style.fontSize = "11px";
        pdfBtn.href = `/api/report/${item.id}/pdf`;
        pdfBtn.target = "_blank";
        pdfBtn.title = "Download Clinical Assessment PDF";

        const pdfIcon = document.createElement("span");
        pdfIcon.className = "material-symbols-outlined";
        pdfIcon.style.fontSize = "14px";
        pdfIcon.textContent = "download";
        pdfBtn.appendChild(pdfIcon);

        const pdfLabel = document.createElement("span");
        pdfLabel.textContent = "PDF";
        pdfBtn.appendChild(pdfLabel);

        actionCell.appendChild(pdfBtn);
        row.appendChild(actionCell);

        tableBody.appendChild(row);
    });
}

function closePatientDetailModal() {
    const modal = document.getElementById("patient-detail-modal");
    if (modal) {
        modal.classList.remove("show");
    }
    if (patientTrendChart) {
        patientTrendChart.destroy();
        patientTrendChart = null;
    }
}

