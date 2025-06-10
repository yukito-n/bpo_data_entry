let token = null;

async function api(path, method = 'GET', body = null) {
    const opts = {method, headers: {}};
    if (token) opts.headers['Authorization'] = 'Bearer ' + token;
    if (body) {
        opts.headers['Content-Type'] = 'application/json';
        opts.body = JSON.stringify(body);
    }
    const resp = await fetch(path, opts);
    if (!resp.ok) throw new Error(await resp.text());
    return resp.json();
}

function showTab(name) {
    document.querySelectorAll('.tabs li').forEach(li => {
        li.classList.toggle('is-active', li.querySelector('a').dataset.tab === name);
    });
    document.querySelectorAll('.tab-content').forEach(div => {
        div.classList.toggle('is-hidden', div.id !== name);
    });
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.tabs a').forEach(a => {
        a.addEventListener('click', e => {
            e.preventDefault();
            showTab(a.dataset.tab);
        });
    });

    document.getElementById('loginForm').addEventListener('submit', async e => {
        e.preventDefault();
        const fd = new FormData(e.target);
        try {
            const res = await fetch('/token', {method: 'POST', body: fd});
            if (!res.ok) throw new Error('Login failed');
            const data = await res.json();
            token = data.access_token;
            document.getElementById('login-view').classList.add('is-hidden');
            document.getElementById('app-view').classList.remove('is-hidden');
            loadProjects();
            loadBatches();
        } catch (err) {
            alert(err);
        }
    });

    document.getElementById('projectForm').addEventListener('submit', async e => {
        e.preventDefault();
        const body = {name: e.target.name.value, client_name: e.target.client.value};
        try {
            await api('/projects', 'POST', body);
            e.target.reset();
            loadProjects();
        } catch (err) { alert(err); }
    });

    document.getElementById('batchForm').addEventListener('submit', async e => {
        e.preventDefault();
        const body = {
            project_id: parseInt(e.target.project_id.value),
            reception_date: new Date(e.target.reception_date.value).toISOString(),
            due_date: new Date(e.target.due_date.value).toISOString(),
            initial_volume: parseInt(e.target.volume.value)
        };
        try {
            await api('/batches', 'POST', body);
            e.target.reset();
            loadBatches();
        } catch (err) { alert(err); }
    });
});

async function loadProjects() {
    try {
        const projects = await api('/projects');
        const tbody = document.querySelector('#projectTable tbody');
        tbody.innerHTML = '';
        projects.forEach(p => {
            const tr = document.createElement('tr');
            tr.innerHTML = `<td>${p.id}</td><td>${p.name}</td><td>${p.client_name}</td>`;
            tbody.appendChild(tr);
        });
    } catch (err) { console.error(err); }
}

async function loadBatches() {
    try {
        const batches = await api('/batches');
        const tbody = document.querySelector('#batchTable tbody');
        tbody.innerHTML = '';
        batches.forEach(b => {
            const tr = document.createElement('tr');
            tr.innerHTML = `<td>${b.id}</td><td>${b.project_id}</td><td>${b.status}</td><td>${b.due_date.slice(0,10)}</td>`;
            tbody.appendChild(tr);
        });
    } catch (err) { console.error(err); }
}
