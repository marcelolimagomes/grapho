
// Funcionalidades JavaScript customizadas

document.addEventListener('DOMContentLoaded', function() {
    // Adiciona tooltips para elementos truncados
    const truncatedElements = document.querySelectorAll('.truncate');
    truncatedElements.forEach(el => {
        if (el.scrollWidth > el.clientWidth) {
            el.title = el.textContent;
        }
    });
    
    // Adiciona efeitos de hover suaves
    const cards = document.querySelectorAll('.bg-white');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    // Adiciona funcionalidade de busca rápida
    addQuickSearch();
});

function addQuickSearch() {
    // Adiciona campo de busca se houver listas
    const lists = document.querySelectorAll('.space-y-2');
    lists.forEach(list => {
        if (list.children.length > 5) {
            const searchInput = document.createElement('input');
            searchInput.type = 'text';
            searchInput.placeholder = 'Buscar...';
            searchInput.className = 'w-full px-3 py-2 border border-gray-300 rounded-md text-sm mb-4';
            
            searchInput.addEventListener('input', function() {
                const query = this.value.toLowerCase();
                Array.from(list.children).forEach(item => {
                    const text = item.textContent.toLowerCase();
                    item.style.display = text.includes(query) ? 'block' : 'none';
                });
            });
            
            list.parentNode.insertBefore(searchInput, list);
        }
    });
}

// Utilitários de navegação
function goBack() {
    window.history.back();
}

function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// Adiciona botão de voltar ao topo
window.addEventListener('scroll', function() {
    const scrollBtn = document.getElementById('scroll-top-btn');
    if (!scrollBtn) {
        const btn = document.createElement('button');
        btn.id = 'scroll-top-btn';
        btn.innerHTML = '↑';
        btn.className = 'fixed bottom-4 right-4 bg-primary text-white p-3 rounded-full shadow-lg hover:bg-blue-600 transition-all duration-200 opacity-0';
        btn.onclick = scrollToTop;
        document.body.appendChild(btn);
    }
    
    const btn = document.getElementById('scroll-top-btn');
    if (window.pageYOffset > 300) {
        btn.style.opacity = '1';
        btn.style.pointerEvents = 'auto';
    } else {
        btn.style.opacity = '0';
        btn.style.pointerEvents = 'none';
    }
});
