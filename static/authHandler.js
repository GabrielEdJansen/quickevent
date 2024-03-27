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
        console.log(decodedData);
        var emailValue = decodedData.email;
        var subIdValue = decodedData.sub;
        var nomeValue = decodedData.given_name; // Adicionando o campo nome
        var sobrenomeValue = decodedData.family_name; // Adicionando o campo sobrenome

        // Definindo os valores dos campos no formulário HTML
        document.getElementById('inputEmail').value = emailValue;
        document.getElementById('subId').value = subIdValue;
        document.getElementById('nomecad').value = nomeValue; // Alimentando o campo nomecad
        document.getElementById('sobrenomecad').value = sobrenomeValue; // Alimentando o campo sobrenomecad

        // Submetendo o formulário
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