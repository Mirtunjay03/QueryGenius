const form = document.getElementById('query-form');
const resultBox = document.getElementById('result-box');
const errorBox = document.getElementById('error-box');
const sqlOutput = document.getElementById('sql-output');
const metricName = document.getElementById('metric-name');
const securityStatus = document.getElementById('security-status');
const rowCount = document.getElementById('row-count');
const lineageList = document.getElementById('lineage-list');
const resultTableHead = document.querySelector('#result-table thead');
const resultTableBody = document.querySelector('#result-table tbody');

form.addEventListener('submit', async (event) => {
    event.preventDefault();
    errorBox.classList.add('hidden');
    resultBox.classList.add('hidden');

    const question = document.getElementById('question').value.trim();
    if (!question) {
        errorBox.textContent = 'Please provide a business question.';
        errorBox.classList.remove('hidden');
        return;
    }

    try {
        const response = await fetch('/api/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
            },
            body: JSON.stringify({ question })
        });

        const payload = await response.json();
        if (!response.ok) {
            errorBox.textContent = payload.error || 'Query generation failed.';
            errorBox.classList.remove('hidden');
            return;
        }

        sqlOutput.textContent = payload.sql;
        metricName.textContent = payload.metric || 'N/A';
        securityStatus.textContent = payload.security.status || 'approved';
        rowCount.textContent = payload.rows.length || 0;

        const lineage = payload.lineage || {};
        lineageList.innerHTML = '';
        const items = [
            `Question: ${payload.question}`,
            `Tables: ${lineage.tables ? lineage.tables.join(', ') : 'n/a'}`,
            `Columns: ${lineage.columns ? lineage.columns.join(', ') : 'n/a'}`,
            `Filters: ${lineage.filters && lineage.filters.length ? lineage.filters.join(' | ') : 'none'}`,
            `Explanation: ${lineage.explanation || 'The query was validated and executed safely.'}`
        ];

        for (const item of items) {
            const li = document.createElement('li');
            li.textContent = item;
            lineageList.appendChild(li);
        }

        const columns = payload.columns || [];
        resultTableHead.replaceChildren();
        if (columns.length) {
            const headerRow = document.createElement('tr');
            for (const column of columns) {
                const th = document.createElement('th');
                th.textContent = column;
                headerRow.appendChild(th);
            }
            resultTableHead.appendChild(headerRow);
        }
        resultTableBody.innerHTML = '';

        for (const row of payload.rows || []) {
            const tr = document.createElement('tr');
            for (const column of columns) {
                const td = document.createElement('td');
                td.textContent = row[column] ?? '';
                tr.appendChild(td);
            }
            resultTableBody.appendChild(tr);
        }

        resultBox.classList.remove('hidden');
    } catch (error) {
        errorBox.textContent = 'Failed to contact the QueryGenius service.';
        errorBox.classList.remove('hidden');
    }
});
