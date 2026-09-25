/**
 * Admin Panel Client Logic
 * Handles model monitoring, retraining pipeline, dataset imports, and feedback oversight.
 * Enforces admin-only access (TC-20).
 */

document.addEventListener("DOMContentLoaded", async () => {
    // Role Gate: Only Admin Allowed (TC-20)
    const user = Auth.initPage("Admin Operations & Model Management", ["admin"]);
    if (!user) return;

    await loadPerformanceStats();
    await loadModelsTable();
    await loadDatasetsTable();
    await loadFeedbackTable();

    setupDatasetUpload();
    setupRetraining();
});

async function loadPerformanceStats() {
    try {
        const res = await Auth.fetchWithAuth("/api/admin/performance");
        if (!res.ok) return;
        const data = await res.json();

        document.getElementById("stat-active-model").textContent = data.active_model;
        document.getElementById("stat-predictions").textContent = data.total_predictions.toLocaleString();
        document.getElementById("stat-patients").textContent = data.total_patients.toLocaleString();
        document.getElementById("stat-latency").textContent = `${data.avg_latency_ms.toFixed(1)}ms`;
    } catch (e) {
        console.error("Failed to fetch performance stats", e);
    }
}

async function loadModelsTable() {
    try {
        const res = await Auth.fetchWithAuth("/api/admin/models");
        if (!res.ok) return;
        const models = await res.json();

        const tbody = document.getElementById("models-table-body");
        tbody.innerHTML = "";

        models.forEach(m => {
            const isActive = m.status === "active";
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><b>${m.name}</b> <small class="text-muted">v${m.version}</small></td>
                <td><span class="badge ${isActive ? 'badge-active' : 'badge-trained'}">${m.status.toUpperCase()}</span></td>
                <td><b>${m.accuracy.toFixed(2)}%</b></td>
                <td>${m.f1_score.toFixed(3)}</td>
                <td>${m.precision.toFixed(3)}</td>
                <td>${m.recall.toFixed(3)}</td>
                <td>${new Date(m.trained_at).toLocaleDateString()}</td>
                <td>
                    ${isActive 
                        ? '<span class="text-muted" style="font-size:12px;">Active Model</span>' 
                        : `<button class="btn btn-outline btn-sm" onclick="activateModel(${m.id})">Set Active</button>`
                    }
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Failed to load models table", e);
    }
}

async function activateModel(modelId) {
    try {
        const res = await Auth.fetchWithAuth(`/api/admin/models/${modelId}/activate`, { method: "POST" });
        if (res.ok) {
            UI.showToast("Model promoted to active successfully!", "success");
            await loadModelsTable();
            await loadPerformanceStats();
        } else {
            UI.showToast("Failed to activate model.", "error");
        }
    } catch (e) {
        UI.showToast("Network error activating model.", "error");
    }
}

async function loadDatasetsTable() {
    try {
        const res = await Auth.fetchWithAuth("/api/admin/datasets");
        if (!res.ok) return;
        const datasets = await res.json();

        const tbody = document.getElementById("datasets-table-body");
        tbody.innerHTML = "";

        if (datasets.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">No uploaded datasets yet. Upload a CSV below.</td></tr>`;
            return;
        }

        datasets.forEach(d => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><b>${d.filename}</b></td>
                <td>${d.row_count.toLocaleString()}</td>
                <td>${new Date(d.uploaded_at).toLocaleDateString()}</td>
                <td><span class="badge badge-low-risk">Validated</span></td>
                <td>
                    <button class="btn btn-primary btn-sm" onclick="triggerRetrainWithDataset(${d.id})">
                        <span class="material-symbols-outlined" style="font-size: 16px;">model_training</span> Retrain
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Failed to load datasets", e);
    }
}

async function loadFeedbackTable() {
    try {
        const res = await Auth.fetchWithAuth("/api/admin/feedback");
        if (!res.ok) return;
        const feedbacks = await res.json();

        const tbody = document.getElementById("feedback-table-body");
        tbody.innerHTML = "";

        if (feedbacks.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" class="text-center text-muted">No user feedback submitted yet.</td></tr>`;
            return;
        }

        feedbacks.forEach(f => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><b>${f.username}</b></td>
                <td>${f.message}</td>
                <td>${new Date(f.submitted_at).toLocaleDateString()}</td>
                <td><span class="badge badge-trained">Reviewed</span></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Failed to load feedback", e);
    }
}

function setupDatasetUpload() {
    const fileInput = document.getElementById("dataset-file-input");
    const uploadBtn = document.getElementById("upload-dataset-btn");
    const alertBox = document.getElementById("upload-alert");

    if (!uploadBtn) return;

    uploadBtn.onclick = async () => {
        alertBox.style.display = "none";
        const file = fileInput.files[0];

        // Client side validation (TC-08)
        if (!file) {
            alertBox.className = "alert alert-error";
            alertBox.textContent = "Please select a file to upload.";
            alertBox.style.display = "flex";
            return;
        }

        if (!file.name.toLowerCase().endsWith(".csv")) {
            alertBox.className = "alert alert-error";
            alertBox.textContent = "Invalid file type. Only CSV (.csv) datasets are accepted for training.";
            alertBox.style.display = "flex";
            return;
        }

        const formData = new FormData();
        formData.append("file", file);

        uploadBtn.disabled = true;
        uploadBtn.innerHTML = `<span class="material-symbols-outlined spin">sync</span> Uploading & Validating...`;

        try {
            const res = await Auth.fetchWithAuth("/api/admin/datasets", {
                method: "POST",
                body: formData
            });

            const data = await res.json();
            if (res.ok) {
                alertBox.className = "alert alert-success";
                alertBox.textContent = `Dataset '${data.filename}' (${data.row_count} rows) successfully imported and verified.`;
                alertBox.style.display = "flex";
                fileInput.value = "";
                await loadDatasetsTable();
            } else {
                alertBox.className = "alert alert-error";
                alertBox.textContent = data.detail || "Upload rejected.";
                alertBox.style.display = "flex";
            }
        } catch (e) {
            alertBox.className = "alert alert-error";
            alertBox.textContent = "Network error uploading dataset.";
            alertBox.style.display = "flex";
        } finally {
            uploadBtn.disabled = false;
            uploadBtn.innerHTML = `<span class="material-symbols-outlined">upload_file</span> Upload Dataset`;
        }
    };
}

function setupRetraining() {
    const retrainBtn = document.getElementById("retrain-all-btn");
    const resultBox = document.getElementById("retrain-result-box");

    if (!retrainBtn) return;

    retrainBtn.onclick = async () => {
        await triggerRetrainWithDataset(null);
    };
}

async function triggerRetrainWithDataset(datasetId) {
    const retrainBtn = document.getElementById("retrain-all-btn");
    const resultBox = document.getElementById("retrain-result-box");

    retrainBtn.disabled = true;
    retrainBtn.innerHTML = `<span class="material-symbols-outlined spin">sync</span> Training All 4 Models...`;
    resultBox.style.display = "none";

    try {
        const payload = datasetId ? { dataset_id: datasetId } : {};
        const res = await Auth.fetchWithAuth("/api/admin/train", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (res.ok) {
            resultBox.className = "alert alert-success";
            resultBox.innerHTML = `
                <div>
                    <b>Training Pipeline Complete!</b><br/>
                    ${data.message}<br/>
                    <small>Auto-selected active model: <b>${data.active_model}</b> (${data.best_accuracy}%)</small>
                </div>
            `;
            resultBox.style.display = "flex";

            await loadModelsTable();
            await loadPerformanceStats();
        } else {
            resultBox.className = "alert alert-error";
            resultBox.textContent = data.detail || "Retraining failed.";
            resultBox.style.display = "flex";
        }
    } catch (e) {
        resultBox.className = "alert alert-error";
        resultBox.textContent = "Network error during model retraining pipeline.";
        resultBox.style.display = "flex";
    } finally {
        retrainBtn.disabled = false;
        retrainBtn.innerHTML = `<span class="material-symbols-outlined">restart_alt</span> Retrain All Models`;
    }
}
