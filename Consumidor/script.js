document.addEventListener("DOMContentLoaded", function() {
    // Função para buscar as mensagens do servidor
    function fetchMessages() {
        fetch('/mensagens') 
            .then(response => response.json()) 
            .then(data => {
                const mensagensContainer = document.querySelector('#mensagens-lista');
                
                mensagensContainer.innerHTML = '';

                data.forEach(mensagem => {
                    const listItem = document.createElement('li');
                    listItem.textContent = mensagem;
                    mensagensContainer.appendChild(listItem);
                });
            })
            .catch(error => console.error('Erro ao buscar mensagens:', error));
    }

    fetchMessages();

    setInterval(fetchMessages, 5000);
});