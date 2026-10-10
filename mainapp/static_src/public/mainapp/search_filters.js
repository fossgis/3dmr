const MAX_SUGGESTIONS = 50;

const panel = document.getElementById('advSearch');
const form = document.getElementById('searchForm');

if (panel && form) {
	setUpFilterPanel();
}

function setUpFilterPanel() {
	const options = {
		category: readJson('all-categories').map(String),
		tag: readJson('all-tags').map(String),
	};

	const fields = Array.from(panel.querySelectorAll('.filter-dropdown')).map(setUpField);

	if (fields.some(f => f.selected.size > 0)) {
		panel.classList.add('show');
		const trigger = document.querySelector('[data-bs-target="#advSearch"]');
		if (trigger) trigger.setAttribute('aria-expanded', 'true');
	}

	document.addEventListener('click', e => {
		for (const f of fields) {
			if (!f.root.contains(e.target)) f.close();
		}
	});

	document.getElementById('clearFilters').addEventListener('click', () => {
		for (const f of fields) {
			f.selected.clear();
			f.update();
		}
	});

	function setUpField(root) {
		const name = root.dataset.filter;
		const label = root.dataset.label;
		const search = root.querySelector('.filter-search');
		const menu = root.querySelector('.filter-menu');
		const list = root.querySelector('.filter-list');
		const status = root.querySelector('.filter-status');
		const chips = root.querySelector('.filter-chips');

		const selected = new Set(readJson(name === 'category' ? 'selected-categories' : 'selected-tags').map(String));

		const api = { root, selected, render, update, close, setStatus };

		search.addEventListener('focus', render);
		search.addEventListener('input', render);
		search.addEventListener('keydown', e => {
			if (e.key === 'Escape') {
				close();
			} else if (e.key === 'Enter') {
				e.preventDefault();
				const first = list.querySelector('input[type="checkbox"]');
				if (first) {
					first.checked = !first.checked;
					first.dispatchEvent(new Event('change', { bubbles: true }));
				} else {
					form.requestSubmit();
				}
			}
		});

		list.addEventListener('change', e => {
			if (e.target.type !== 'checkbox') return;
			if (e.target.checked) selected.add(e.target.value);
			else selected.delete(e.target.value);
			update();
			search.focus();
		});

		chips.addEventListener('click', e => {
			const btn = e.target.closest('[data-remove]');
			if (!btn) return;
			selected.delete(btn.dataset.remove);
			update();
		});

		update();
		return api;

		function update() {
			if (menu.classList.contains('show')) render();
			renderChips();
			syncHiddenInputs();
		}

		function open() {
			menu.classList.add('show');
			search.setAttribute('aria-expanded', 'true');
		}

		function close() {
			menu.classList.remove('show');
			search.setAttribute('aria-expanded', 'false');
		}

		function render() {
			list.replaceChildren();

			const q = search.value.trim().toLowerCase();
			if (!q) {
				close();
				return;
			}

			open();

			const all = options[name];
			const matches = all.filter(v => v.toLowerCase().includes(q));
			const shown = matches.slice(0, MAX_SUGGESTIONS);

			const frag = document.createDocumentFragment();
			shown.forEach((value, i) => {
				const id = name + '-opt-' + i;
				const row = document.createElement('div');
				row.className = 'form-check';

				const input = document.createElement('input');
				input.className = 'form-check-input';
				input.type = 'checkbox';
				input.id = id;
				input.value = value;
				input.checked = selected.has(value);

				const lbl = document.createElement('label');
				lbl.className = 'form-check-label text-truncate d-block';
				lbl.htmlFor = id;
				lbl.textContent = value;
				lbl.title = value;

				row.append(input, lbl);
				frag.append(row);
			});
			list.append(frag);

			if (all.length === 0) setStatus('No ' + label.toLowerCase() + ' available.');
			else if (matches.length === 0) setStatus('No matches.');
			else if (matches.length > shown.length) setStatus(shown.length + ' of ' + matches.length);
			else setStatus(matches.length + ' match' + (matches.length === 1 ? '' : 'es'));
		}

		function renderChips() {
			chips.replaceChildren();
			for (const value of selected) {
				const chip = document.createElement('span');
				chip.className = 'badge text-bg-secondary d-inline-flex align-items-center gap-1 fw-normal mw-100 mt-2';

				const text = document.createElement('span');
				text.className = 'text-truncate';
				text.textContent = value;

				const remove = document.createElement('button');
				remove.type = 'button';
				remove.className = 'btn-close btn-close-white';
				remove.setAttribute('aria-label', 'Remove ' + value);
				remove.dataset.remove = value;

				chip.append(text, remove);
				chips.append(chip);
			}
		}

		function syncHiddenInputs() {
			form.querySelectorAll('input[type="hidden"][name="' + name + '"]').forEach(el => el.remove());
			for (const value of selected) {
				const input = document.createElement('input');
				input.type = 'hidden';
				input.name = name;
				input.value = value;
				form.append(input);
			}
		}

		function setStatus(text) {
			status.textContent = text;
		}
	}
}

function readJson(id) {
	const el = document.getElementById(id);
	if (!el) return [];
	try {
		const value = JSON.parse(el.textContent);
		return Array.isArray(value) ? value : [];
	} catch (e) {
		return [];
	}
}
