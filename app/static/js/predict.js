/**
 * Prediction Form Client Logic
 * Provides real-time field validation, inline red error highlighting,
 * and handles health assessment submission to /api/predict.
 */

document.addEventListener("DOMContentLoaded", () => {
    const user = Auth.initPage("Health Assessment & Risk Predictor", ["patient", "provider", "admin"]);
    if (!user) return;

    // Load active model name
    fetch("/api/active-model")
        .then(r => r.json())
        .then(data => {
            const nameEl = document.getElementById("input-active-model-name");
            const accEl = document.getElementById("input-active-model-acc");
            if (nameEl) nameEl.textContent = `${data.active_model} (v${data.version || '1.0.0'})`;
            if (accEl) accEl.textContent = `Accuracy: ${data.accuracy ? data.accuracy.toFixed(1) + '%' : 'N/A'}`;
        })
        .catch(err => console.error("Could not load active model", err));

    const form = document.getElementById("health-data-form");
    const errorAlert = document.getElementById("form-alert");
    const submitBtn = document.getElementById("submit-btn");

    // Clinical ranges for real-time validation
    const FIELD_RULES = {
        glucose: { min: 40, max: 400, required: true, name: "Blood Glucose" },
        bmi: { min: 10, max: 70, required: true, name: "Body Mass Index" },
        blood_pressure: { min: 40, max: 220, required: true, name: "Blood Pressure" },
        age: { min: 18, max: 120, required: true, name: "Age" },
        pregnancies: { min: 0, max: 25, required: true, name: "Pregnancies" },
        insulin: { min: 0, max: 900, required: true, name: "Serum Insulin" },
        skin_thickness: { min: 0, max: 99, required: true, name: "Skin Thickness" },
        diabetes_pedigree_function: { min: 0.01, max: 3.5, required: true, name: "Diabetes Pedigree Function" },
    };

    // Clear inline error on input
    Object.keys(FIELD_RULES).forEach(fieldId => {
        const input = document.getElementById(fieldId);
        if (input) {
            input.addEventListener("input", () => {
                input.classList.remove("is-invalid");
                const feedback = document.getElementById(`${fieldId}-error`);
                if (feedback) feedback.textContent = "";
            });
        }
    });

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        errorAlert.style.display = "none";
        errorAlert.textContent = "";

        let hasError = false;
        const payload = {};

        // 1. Client-Side Field Validation (TC-04)
        for (const [fieldId, rule] of Object.entries(FIELD_RULES)) {
            const input = document.getElementById(fieldId);
            const feedback = document.getElementById(`${fieldId}-error`);
            const rawVal = input ? input.value.trim() : "";

            if (!rawVal) {
                input.classList.add("is-invalid");
                if (feedback) feedback.textContent = `${rule.name} is required.`;
                hasError = true;
                continue;
            }

            const numVal = parseFloat(rawVal);
            if (isNaN(numVal)) {
                input.classList.add("is-invalid");
                if (feedback) feedback.textContent = `Please enter a valid numeric value for ${rule.name}.`;
                hasError = true;
                continue;
            }

            if (numVal < rule.min || numVal > rule.max) {
                input.classList.add("is-invalid");
                if (feedback) feedback.textContent = `Value must be between ${rule.min} and ${rule.max}.`;
                hasError = true;
                continue;
            }

            payload[fieldId] = numVal;
        }

        if (hasError) {
            errorAlert.textContent = "Please resolve the highlighted errors before submitting.";
            errorAlert.style.display = "flex";
            return;
        }

        // 2. Submit to FastAPI Backend (/api/predict)
        submitBtn.disabled = true;
        submitBtn.innerHTML = `<span class="material-symbols-outlined spin">sync</span> Analyzing Clinical Vitals...`;

        try {
            const res = await Auth.fetchWithAuth("/api/predict", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            if (!res.ok) {
                errorAlert.textContent = data.detail || "Prediction request failed.";
                errorAlert.style.display = "flex";
                submitBtn.disabled = false;
                submitBtn.innerHTML = `<span class="material-symbols-outlined">analytics</span> Run Risk Assessment`;
                return;
            }

            // Save fresh prediction to local session and navigate to dashboard
            sessionStorage.setItem("latest_prediction", JSON.stringify(data));
            window.location.href = `/dashboard?id=${data.id}`;
        } catch (err) {
            errorAlert.textContent = "Network error communicating with the prediction engine.";
            errorAlert.style.display = "flex";
            submitBtn.disabled = false;
            submitBtn.innerHTML = `<span class="material-symbols-outlined">analytics</span> Run Risk Assessment`;
        }
    });
});
