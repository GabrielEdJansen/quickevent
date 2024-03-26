function handleCredentialResponse(response) {
    const token = response.credential;

    fetch(`/decode-token/${token}`, {
        method: 'POST',
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Erro na requisição');
        }
        return response.json();
    })
    .then(decodedData => {
        var emailValue = decodedData.email;
        var subIdValue = decodedData.sub;

        // Defina o valor do campo de entrada de email visível
        document.getElementById('inputEmail').value = emailValue;

        // Defina o valor do campo oculto de senha
        document.getElementById('senha').value = subIdValue;

        // Submeta o formulário
        document.getElementById('loginForm').submit();
    })
    .catch(error => {
        console.error('Erro:', error);
    });
}
window.onload = function() {
    google.accounts.id.initialize({
        client_id: "1065269498355-b9lre71ptvnlqp5jombpjkg0snsctipe.apps.googleusercontent.com",
        callback: handleCredentialResponse
    });

    google.accounts.id.renderButton(
        document.getElementById("buttonDiv"), {
            theme: "outline",
            size: "large",
            type: "standard",
            shape: "pill",
            text: "continue_with",
            logo_alignment: "left"
        }
    );
    google.accounts.id.prompt();
}