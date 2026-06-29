document.addEventListener('DOMContentLoaded', function() {
    updateProgress();
    
    // Task Search
    const searchInput = document.getElementById('taskSearch');
    searchInput.addEventListener('input', filterTasks);

    // Category Filter
    const filterBtns = document.querySelectorAll('.filter-btn');
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            filterTasks();
        });
    });

    // Add Task Form submission
    document.getElementById('addTaskForm').addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(this);
        
        fetch('/planner/add', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert(data.error || 'Something went wrong');
            }
        });
    });

    // Edit Task Form submission
    document.getElementById('editTaskForm').addEventListener('submit', function(e) {
        e.preventDefault();
        const taskId = document.getElementById('editTaskId').value;
        const formData = new FormData(this);
        
        fetch(`/planner/edit/${taskId}`, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert(data.error || 'Something went wrong');
            }
        });
    });
});

function filterTasks() {
    const searchTerm = document.getElementById('taskSearch').value.toLowerCase();
    const activeCategory = document.querySelector('.filter-btn.active').dataset.category;
    const cards = document.querySelectorAll('.task-card');

    cards.forEach(card => {
        const title = card.dataset.title.toLowerCase();
        const category = card.dataset.category;
        
        const matchesSearch = title.includes(searchTerm);
        const matchesCategory = activeCategory === 'All' || category === activeCategory;

        if (matchesSearch && matchesCategory) {
            card.style.display = 'flex';
        } else {
            card.style.display = 'none';
        }
    });
}

function updateProgress() {
    const cards = document.querySelectorAll('.task-card');
    const completed = document.querySelectorAll('.task-card.completed');
    
    if (cards.length === 0) return;

    const percent = Math.round((completed.length / cards.length) * 100);
    const fill = document.getElementById('progress-fill');
    const text = document.getElementById('progress-percent');
    
    if (fill && text) {
        fill.style.width = percent + '%';
        text.innerText = percent + '%';
    }
}

function openModal(type) {
    document.getElementById(type + 'Modal').style.display = 'flex';
}

function closeModal(type) {
    document.getElementById(type + 'Modal').style.display = 'none';
}

function openEditModal(id, title, desc, priority, category, dueDate) {
    document.getElementById('editTaskId').value = id;
    document.getElementById('editTitle').value = title;
    document.getElementById('editDescription').value = desc;
    document.getElementById('editPriority').value = priority;
    document.getElementById('editCategory').value = category;
    document.getElementById('editDateDue').value = dueDate;
    openModal('edit');
}

function toggleTask(id) {
    fetch(`/planner/toggle/${id}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const card = document.querySelector(`.task-card[data-id="${id}"]`);
            const icon = card.querySelector('.complete-btn i');
            
            if (data.completed) {
                card.classList.add('completed');
                icon.className = 'fas fa-check-circle';
            } else {
                card.classList.remove('completed');
                icon.className = 'fas fa-circle';
            }
            updateProgress();
        }
    });
}

function deleteTask(id) {
    if (confirm('Are you sure you want to delete this task?')) {
        fetch(`/planner/delete/${id}`, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const card = document.querySelector(`.task-card[data-id="${id}"]`);
                card.style.transform = 'scale(0.8)';
                card.style.opacity = '0';
                setTimeout(() => {
                    card.remove();
                    updateProgress();
                }, 300);
            }
        });
    }
}

// Close modal when clicking outside
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
}
