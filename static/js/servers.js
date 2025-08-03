function toggleForm(formId, btn) {
    const form = document.getElementById(formId);
    form.classList.toggle('active');
    btn.textContent = form.classList.contains('active') ? 'Fechar' : 'Enviar Mensagem';
}