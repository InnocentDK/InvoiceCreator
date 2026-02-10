const api = {
  get: (url) => fetch(url).then(async (r) => {
    if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || `HTTP ${r.status}`);
    return r.json();
  }),
  post: (url, payload) => fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }).then(async (r) => {
    if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || `HTTP ${r.status}`);
    return r.json();
  }),
};

const formatMoney = (v) => Number(v).toLocaleString('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

async function initIndexPage() {
  const tbody = document.querySelector('#invoices-table tbody');
  if (!tbody) return;
  const invoices = await api.get('/api/invoices');
  tbody.innerHTML = '';
  invoices.forEach((inv) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${inv.number}</td>
      <td>${inv.date}</td>
      <td>${inv.organization}</td>
      <td>${inv.contractor}</td>
      <td>${formatMoney(inv.total)} ₽</td>
      <td>
        <div class="actions">
          <a class="btn" href="/api/invoices/${inv.id}" target="_blank">View</a>
          <a class="btn" href="${inv.docx_url}">DOCX</a>
          <a class="btn" href="${inv.pdf_url}">PDF</a>
        </div>
      </td>`;
    tbody.appendChild(tr);
  });
}

async function initCreatePage() {
  const form = document.querySelector('#invoice-form');
  if (!form) return;

  const [organizations, services] = await Promise.all([
    api.get('/api/organizations'),
    api.get('/api/services'),
  ]);

  const serviceMap = new Map(services.map((s) => [s.name, s]));
  const orgSelect = document.querySelector('#organization');
  organizations.forEach((org) => {
    const option = document.createElement('option');
    option.value = org.id;
    option.textContent = `${org.name} (ИНН ${org.inn})`;
    orgSelect.appendChild(option);
  });

  const servicesContainer = document.querySelector('#services-container');
  const rowTemplate = document.querySelector('#service-row-template');
  const totalEl = document.querySelector('#total');

  const recomputeTotal = () => {
    let total = 0;
    servicesContainer.querySelectorAll('.service-row').forEach((row) => {
      const qty = Number(row.querySelector('.service-qty').value || 0);
      const price = Number(row.querySelector('.service-price').value || 0);
      total += qty * price;
    });
    totalEl.textContent = total.toFixed(2);
  };

  const renderNotesFields = (row, serviceName) => {
    const notesContainer = row.querySelector('.notes-container');
    notesContainer.innerHTML = '';
    const config = serviceMap.get(serviceName);
    if (!config) return;
    config.notes.forEach((note) => {
      const label = document.createElement('label');
      label.textContent = note.label;
      let input;
      if (note.type === 'select') {
        input = document.createElement('select');
        note.options.forEach((opt) => {
          const op = document.createElement('option');
          op.value = opt;
          op.textContent = opt;
          input.appendChild(op);
        });
      } else {
        input = document.createElement('input');
        input.type = 'text';
      }
      input.dataset.noteKey = note.key;
      input.required = true;
      label.appendChild(input);
      notesContainer.appendChild(label);
    });
  };

  const addServiceRow = () => {
    const node = rowTemplate.content.cloneNode(true);
    const row = node.querySelector('.service-row');
    const selectEl = row.querySelector('.service-select');
    services.forEach((s) => {
      const opt = document.createElement('option');
      opt.value = s.name;
      opt.textContent = `${s.name} [${s.template}]`;
      selectEl.appendChild(opt);
    });

    row.querySelector('.service-price').addEventListener('input', recomputeTotal);
    row.querySelector('.service-qty').addEventListener('input', recomputeTotal);
    row.querySelector('.remove-service').addEventListener('click', () => {
      row.remove();
      recomputeTotal();
    });
    selectEl.addEventListener('change', () => renderNotesFields(row, selectEl.value));

    renderNotesFields(row, selectEl.value);
    servicesContainer.appendChild(row);
    recomputeTotal();
  };

  document.querySelector('#add-service').addEventListener('click', addServiceRow);
  addServiceRow();

  document.querySelector('#search-contractor').addEventListener('click', async () => {
    const inn = document.querySelector('#contractor-inn').value.trim();
    if (!inn) return;
    try {
      const ctr = await api.get(`/api/contractors/search?inn=${encodeURIComponent(inn)}`);
      document.querySelector('#contractor-name').value = ctr.name;
      document.querySelector('#contractor-kpp').value = ctr.kpp;
      document.querySelector('#contractor-address').value = ctr.address;
    } catch (err) {
      alert(`Контрагент не найден: ${err.message}`);
    }
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const items = [...servicesContainer.querySelectorAll('.service-row')].map((row) => {
      const serviceName = row.querySelector('.service-select').value;
      const notes = {};
      row.querySelectorAll('[data-note-key]').forEach((input) => {
        notes[input.dataset.noteKey] = input.value;
      });
      return {
        service_name: serviceName,
        description: row.querySelector('.service-description').value || serviceName,
        qty: Number(row.querySelector('.service-qty').value),
        price: Number(row.querySelector('.service-price').value),
        notes,
      };
    });

    const payload = {
      organization_id: Number(orgSelect.value),
      contractor: {
        name: document.querySelector('#contractor-name').value,
        inn: document.querySelector('#contractor-inn').value,
        kpp: document.querySelector('#contractor-kpp').value,
        address: document.querySelector('#contractor-address').value,
      },
      items,
    };

    try {
      const created = await api.post('/api/invoices', payload);
      alert(`Счет ${created.number} успешно создан`);
      window.location.href = '/';
    } catch (err) {
      alert(`Ошибка: ${err.message}`);
    }
  });
}

initIndexPage().catch((err) => console.error(err));
initCreatePage().catch((err) => console.error(err));
