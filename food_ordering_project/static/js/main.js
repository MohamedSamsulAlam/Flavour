// ── Alert Auto-dismiss ──
document.addEventListener('DOMContentLoaded', () => {
  // Auto-dismiss alerts after 5s
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    setTimeout(() => {
      alert.style.opacity = '0';
      alert.style.transform = 'translateX(120%)';
      alert.style.transition = 'all 0.4s ease';
      setTimeout(() => alert.remove(), 400);
    }, 4500);

    const closeBtn = alert.querySelector('.alert-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        alert.style.opacity = '0';
        alert.style.transition = 'all 0.2s ease';
        setTimeout(() => alert.remove(), 200);
      });
    }
  });

  // ── Mobile Sidebar ──
  const toggle = document.getElementById('menuToggle');
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebarOverlay');

  if (toggle && sidebar) {
    toggle.addEventListener('click', () => {
      sidebar.classList.toggle('open');
      overlay.classList.toggle('active');
    });
    overlay?.addEventListener('click', () => {
      sidebar.classList.remove('open');
      overlay.classList.remove('active');
    });
  }

  // ── AJAX Add to Cart ──
  document.querySelectorAll('[data-add-cart]').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      const itemId = btn.dataset.addCart;
      const url = `/orders/cart/add/${itemId}/`;
      try {
        const resp = await fetch(url, {
          method: 'GET',
          headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        const data = await resp.json();
        if (data.success) {
          // Update cart badge
          const badges = document.querySelectorAll('.cart-badge');
          badges.forEach(b => { b.textContent = data.cart_count; });
          showToast(`✓ ${data.item_name} added to cart`, 'success');
          // Button feedback
          const orig = btn.innerHTML;
          btn.innerHTML = '✓ Added';
          btn.classList.add('btn-success');
          btn.classList.remove('btn-primary', 'btn-outline');
          setTimeout(() => {
            btn.innerHTML = orig;
            btn.classList.remove('btn-success');
            btn.classList.add('btn-primary');
          }, 1800);
        } else if (data.error === 'clear_cart') {
          if (confirm(data.message + '\n\nClick OK to clear your cart.')) {
            window.location.href = `/orders/cart/clear/`;
          }
        }
      } catch (err) {
        window.location.href = url;
      }
    });
  });

  // ── Image Preview ──
  document.querySelectorAll('input[type="file"][data-preview]').forEach(input => {
    const previewId = input.dataset.preview;
    input.addEventListener('change', () => {
      const file = input.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = e => {
          let preview = document.getElementById(previewId);
          if (!preview) {
            preview = document.createElement('img');
            preview.id = previewId;
            preview.className = 'img-preview';
            input.parentElement.appendChild(preview);
          }
          preview.src = e.target.result;
        };
        reader.readAsDataURL(file);
      }
    });
  });

  // ── Quantity controls in cart ──
  document.querySelectorAll('.qty-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const input = btn.parentElement.querySelector('.qty-input');
      if (!input) return;
      let val = parseInt(input.value) || 1;
      if (btn.dataset.action === 'inc') val++;
      else if (btn.dataset.action === 'dec') val = Math.max(0, val - 1);
      input.value = val;
      input.form?.submit();
    });
  });

  // ── Confirm delete ──
  document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', e => {
      if (!confirm(el.dataset.confirm)) e.preventDefault();
    });
  });

  // ── Order tracking auto-refresh ──
  const trackingPage = document.getElementById('orderTracking');
  if (trackingPage) {
    setInterval(() => { window.location.reload(); }, 30000);
  }

  // ── Chart.js rendering ──
  const chartDataEl = document.getElementById('chartData');
  if (chartDataEl) {
    renderAnalyticsCharts(JSON.parse(chartDataEl.textContent));
  }
});

// ── Toast Notification ──
function showToast(message, type = 'info') {
  let container = document.querySelector('.messages-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'messages-container';
    document.body.appendChild(container);
  }
  const toast = document.createElement('div');
  toast.className = `alert alert-${type}`;
  toast.innerHTML = `<span>${message}</span><button class="alert-close">×</button>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(120%)';
    toast.style.transition = 'all 0.4s ease';
    setTimeout(() => toast.remove(), 400);
  }, 4000);
  toast.querySelector('.alert-close').addEventListener('click', () => toast.remove());
}

// ── Analytics Charts ──
function renderAnalyticsCharts(data) {
  // Revenue chart
  const revenueEl = document.getElementById('revenueChart');
  if (revenueEl && data.daily_revenue?.length) {
    new Chart(revenueEl, {
      type: 'bar',
      data: {
        labels: data.daily_revenue.map(d => d.date),
        datasets: [{
          label: 'Revenue (₹)',
          data: data.daily_revenue.map(d => d.total),
          backgroundColor: 'rgba(232,66,10,0.15)',
          borderColor: 'rgba(232,66,10,1)',
          borderWidth: 2,
          borderRadius: 6,
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false } },
          y: { beginAtZero: true, grid: { color: '#F0F2F5' } }
        }
      }
    });
  }

  // Status doughnut
  const statusEl = document.getElementById('statusChart');
  if (statusEl && data.status_data?.length) {
    const colors = {
      pending: '#D97706', confirmed: '#2563EB', preparing: '#7C3AED',
      ready: '#059669', delivered: '#0369A1', cancelled: '#DC2626'
    };
    new Chart(statusEl, {
      type: 'doughnut',
      data: {
        labels: data.status_data.map(d => d.status.charAt(0).toUpperCase() + d.status.slice(1)),
        datasets: [{
          data: data.status_data.map(d => d.count),
          backgroundColor: data.status_data.map(d => colors[d.status] || '#9CA3AF'),
          borderWidth: 2,
          borderColor: '#fff',
        }]
      },
      options: {
        responsive: true,
        cutout: '65%',
        plugins: { legend: { position: 'bottom', labels: { padding: 14, font: { size: 12 } } } }
      }
    });
  }

  // Top items bar
  const topEl = document.getElementById('topItemsChart');
  if (topEl && data.top_items?.length) {
    new Chart(topEl, {
      type: 'bar',
      data: {
        labels: data.top_items.map(d => d.name.length > 14 ? d.name.slice(0,14)+'…' : d.name),
        datasets: [{
          label: 'Units Sold',
          data: data.top_items.map(d => d.qty),
          backgroundColor: 'rgba(232,66,10,0.15)',
          borderColor: 'rgba(232,66,10,1)',
          borderWidth: 2,
          borderRadius: 6,
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { beginAtZero: true, grid: { color: '#F0F2F5' } },
          y: { grid: { display: false } }
        }
      }
    });
  }
}
