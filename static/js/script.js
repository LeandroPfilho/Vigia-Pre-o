document.addEventListener('DOMContentLoaded', () => {
    const forms = document.querySelectorAll('form');
    forms.forEach((form) => {
        form.addEventListener('submit', () => {
            const button = form.querySelector('button[type="submit"], button:not([type])');
            if (button && !button.disabled) {
                button.dataset.originalText = button.innerText;
                button.innerText = 'Aguarde...';
            }
        });
    });
});
