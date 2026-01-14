const API_URL = "";

document.addEventListener('DOMContentLoaded', () => {
    fetchLeads();
    setupEventListeners();
});

function setupEventListeners() {
    document.getElementById('btn-simulate').addEventListener('click', async () => {
        const btn = document.getElementById('btn-simulate');
        btn.disabled = true;
        btn.textContent = "Injecting...";

        try {
            const names = ["Emily Chen", "Marcus Johnson", "Sarah Miller", "David Wu"];
            const companies = ["CloudScale AI", "NextGen Finance", "HealthPlus", "DataFlow Inc"];
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
                // Wait a moment for background task to process (simulated delay for UX)
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
    });
}

async function fetchLeads() {
    try {
        const response = await fetch(`${API_URL}/leads`);
        const leads = await response.json();

        updateMetrics(leads);
        renderReviewQueue(leads.filter(l => l.status === 'processed'));
    } catch (error) {
        console.error("Failed to fetch leads:", error);
    }
}

function updateMetrics(leads) {
    document.querySelector('#metrics .card:nth-child(1) .number').textContent = leads.length;
    document.querySelector('#metrics .card:nth-child(2) .number').textContent = leads.filter(l => l.status === 'sent').length;

    // Calculate simple stats
    const replies = leads.filter(l => l.status.includes('replied'));
    document.querySelector('#metrics .card:nth-child(3) .number').textContent =
        leads.length > 0 ? ((replies.length / leads.length) * 100).toFixed(1) + '%' : '0%';

    document.querySelector('#metrics .card:nth-child(4) .number').textContent =
        leads.filter(l => l.status === 'replied_interested').length;
}

function renderReviewQueue(pendingLeads) {
    const container = document.getElementById('review-queue');
    // Clear existing items but keep header (or restructure HTML to put header outside container)
    // Assuming container currently has H2 and items. Let's find the list wrapper.
    // Looking at index.html, #review-queue contains an H2 and divs.

    // Let's create a clearer wrapper in HTML or just append after H2.
    // The previous HTML didn't have a wrapper div for items.

    // Remove old lead-items
    document.querySelectorAll('.lead-item').forEach(e => e.remove());

    if (pendingLeads.length === 0) {
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
    div.innerHTML = `
        <div class="lead-info">
            <h4>${lead.name}</h4>
            <span class="company">${lead.company}</span>
        </div>
        <div class="email-preview">
            <strong>Subject:</strong> ${lead.subject}<br>
            <p>${lead.body ? lead.body.substring(0, 100) + '...' : 'No content generated'}</p>
        </div>
        <div class="actions">
            <button class="btn-approve" data-id="${lead.id}">Approve</button>
            <button class="btn-edit" data-id="${lead.id}">Edit</button>
            <button class="btn-reject" data-id="${lead.id}">Reject</button>
        </div>
    `;

    // Attach event listeners immediately
    div.querySelector('.btn-approve').addEventListener('click', () => approveLead(lead.id, div));

    return div;
}

async function approveLead(id, rowElement) {
    try {
        const btn = rowElement.querySelector('.btn-approve');
        btn.disabled = true;
        btn.textContent = "Sending...";

        const response = await fetch(`${API_URL}/leads/${id}/approve`, {
            method: 'POST'
        });

        if (response.ok) {
            rowElement.style.opacity = '0.5';
            btn.textContent = 'Approved';
            // Refresh counts after short delay or locally update
        } else {
            alert("Failed to approve");
            btn.disabled = false;
        }
    } catch (e) {
        console.error(e);
        alert("Error sending request");
    }
}
