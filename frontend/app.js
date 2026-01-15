const API_URL = "";

let currentLeads = [];
let selectedLeadIds = new Set();

document.addEventListener('DOMContentLoaded', () => {
    fetchLeads();
    setupEventListeners();
    setupBatchActions();
});

function setupEventListeners() {
    document.getElementById('btn-simulate').addEventListener('click', injectTestLead);
}

function setupBatchActions() {
    const batchBtn = document.getElementById('btn-batch-approve');
    batchBtn.addEventListener('click', async () => {
        if (selectedLeadIds.size === 0) return;

        batchBtn.disabled = true;
        batchBtn.textContent = "Processing...";

        try {
            // Collect overrides
            const overrides = {};
            selectedLeadIds.forEach(id => {
                const bodyEl = document.querySelector(`.body-edit[data-id="${id}"]`);
                if (bodyEl) {
                    overrides[id] = { body: bodyEl.value };
                }
            });

            const res = await fetch(`${API_URL}/leads/batch-approve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    lead_ids: Array.from(selectedLeadIds),
                    overrides: overrides
                })
            });

            if (res.ok) {
                const result = await res.json();
                console.log("Batch Result:", result);
                selectedLeadIds.clear(); // Reset selection
                updateBatchUI();
                await fetchLeads(); // Refresh list
            } else {
                alert("Batch processing failed");
            }
        } catch (e) {
            console.error(e);
            alert("Error sending batch request");
        } finally {
            batchBtn.disabled = false;
            batchBtn.textContent = "Approve Selected";
        }
    });
}

async function injectTestLead() {
    const btn = document.getElementById('btn-simulate');
    btn.disabled = true;
    btn.textContent = "Injecting...";

    try {
        const names = ["Emily Chen", "Marcus Johnson", "Sarah Miller", "David Wu", "Jessica Pearson"];
        const companies = ["CloudScale AI", "NextGen Finance", "HealthPlus", "DataFlow Inc", "Pearson Hardman"];
        const randomIdx = Math.floor(Math.random() * names.length);

        const payload = {
            name: names[randomIdx],
            company: companies[randomIdx],
            email: `contact@${companies[randomIdx].toLowerCase().replace(/\s/g, '')}.com`,
            source: "Web Simulation"
        };

        const res = await fetch(`${API_URL}/leads`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            setTimeout(() => {
                fetchLeads();
                btn.disabled = false;
                btn.textContent = "Inject Test Lead";
            }, 2000);
        }
    } catch (error) {
        console.error(error);
        btn.disabled = false;
    }
}

async function fetchLeads() {
    try {
        const [leadsRes, metricsRes] = await Promise.all([
            fetch(`${API_URL}/leads`),
            fetch(`${API_URL}/metrics`)
        ]);

        const leads = await leadsRes.json();
        const metrics = await metricsRes.json();

        currentLeads = leads;
        updateMetrics(leads, metrics);
        renderReviewQueue(leads.filter(l => l.status === 'processed'));
    } catch (error) {
        console.error("Failed to fetch data:", error);
    }
}

function updateMetrics(leads, metrics) {
    document.querySelector('#metrics .card:nth-child(1) .number').textContent = leads.length;
    document.querySelector('#metrics .card:nth-child(2) .number').textContent = metrics.sent;

    const rate = metrics.sent > 0 ? ((metrics.replied / metrics.sent) * 100).toFixed(1) : 0;
    document.querySelector('#metrics .card:nth-child(3) .number').textContent = `${rate}%`;

    document.querySelector('#metrics .card:nth-child(4) .number').textContent = metrics.positive;
}

function renderReviewQueue(pendingLeads) {
    const container = document.getElementById('queue-list');
    container.innerHTML = ''; // Clear

    // Hide batch UI if empty
    if (pendingLeads.length === 0) {
        document.querySelector('.batch-actions').style.display = 'none';
        const p = document.createElement('p');
        p.textContent = "No leads waiting for approval.";
        p.className = 'empty-state';
        container.appendChild(p);
        return;
    }

    pendingLeads.forEach(lead => {
        const el = createLeadElement(lead);
        container.appendChild(el);
    });
}

function createLeadElement(lead) {
    const div = document.createElement('div');
    div.className = 'lead-item';

    // Checkbox logic
    const isSelected = selectedLeadIds.has(lead.id);

    div.innerHTML = `
        <div class="selection-col">
            <input type="checkbox" class="lead-checkbox" data-id="${lead.id}" ${isSelected ? 'checked' : ''}>
        </div>
        <div class="lead-info">
            <h4>${lead.name}</h4>
            <span class="company">${lead.company}</span>
            <span class="view-logs" onclick="viewLogs('${lead.id}')">View Logs</span>
        </div>
        <div class="email-preview">
            <strong>Subject:</strong> ${lead.subject || ''}<br>
            <textarea class="body-edit" data-id="${lead.id}">${lead.body || ''}</textarea>
        </div>
        <div class="actions">
            <button class="btn-approve" data-id="${lead.id}">Approve</button>
            <button class="btn-reject" data-id="${lead.id}">Reject</button>
        </div>
    `;

    // Event listeners
    const checkbox = div.querySelector('.lead-checkbox');
    checkbox.addEventListener('change', (e) => {
        if (e.target.checked) selectedLeadIds.add(lead.id);
        else selectedLeadIds.delete(lead.id);
        updateBatchUI();
    });

    div.querySelector('.btn-approve').addEventListener('click', () => approveLead(lead.id, div));

    // "Simple" Edit - just auto-save or save on approve?
    // For MVP, allow editing the textarea, but update functionality needs explicit endpoint or update on "Approve". 
    // To keep it simple, we won't implement "Save Edit" separately yet, or just assume "What you see is what you send" if we passed body in approve (which we don't currently).
    // Let's rely on the Batch Approve or single Approve just taking the status.
    // *Optimization*: In a real app we'd PATCH the body.

    return div;
}

function updateBatchUI() {
    const bar = document.querySelector('.batch-actions');
    const countSpan = document.getElementById('selected-count');

    if (selectedLeadIds.size > 0) {
        bar.style.display = 'flex';
        countSpan.textContent = `${selectedLeadIds.size} selected`;
    } else {
        bar.style.display = 'none';
    }
}

async function approveLead(id, rowElement) {
    // Single approval
    try {
        const btn = rowElement.querySelector('.btn-approve');
        btn.disabled = true;
        btn.textContent = "Sending...";

        await fetch(`${API_URL}/leads/${id}/approve`, { method: 'POST' });

        // Remove from UI or fade
        rowElement.style.opacity = '0.5';
        btn.textContent = 'Approved';

        // Remove from selection if present
        if (selectedLeadIds.has(id)) {
            selectedLeadIds.delete(id);
            updateBatchUI();
        }

    } catch (e) {
        console.error(e);
        alert("Error sending request");
    }
}

async function viewLogs(id) {
    try {
        const res = await fetch(`${API_URL}/leads/${id}/logs`);
        const logs = await res.json();
        alert("Logs:\n" + logs.map(l => `[${l.time}] ${l.event}: ${l.details}`).join('\n'));
    } catch (e) {
        console.error(e);
    }
}
