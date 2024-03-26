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
        var emailValue = decodedData.email; // Obtém o valor do email de decodedData
        var subIdValue = decodedData.sub; // Obtém o valor da senha de decodedData

        // Realiza a requisição POST com os dados do formulário
        fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: 'email=' + encodeURIComponent(emailValue) + '&senha=' + encodeURIComponent(subIdValue)
        })
        .then(response => {
            if (response.ok) {
                // Se a resposta estiver OK, submeta o formulário
                document.getElementById('loginForm').submit();
            } else {
                throw new Error('Erro ao enviar dados');
            }
        })
        .catch(error => {
            console.error('Erro:', error);
        });
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