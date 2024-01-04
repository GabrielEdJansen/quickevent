 function handleCredentialResponse(response) {
            const token = response.credential;

            return fetch(`/decode-token/${token}`, {
                method: 'POST',
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Erro na requisição');
                }
                return response.json();
            })
            .then(decodedData => {
                var given_name = document.getElementById('nomecad');
                var family_name = document.getElementById('sobrenomecad');
                var email = document.getElementById('emailcad');
                var subId = document.getElementById('subId');

                given_name.textContent = decodedData.given_name
                family_name.textContent = decodedData.family_name
                email.textContent = decodedData.email
                subId.textContent = decodedData.sub

                given_name.value = decodedData.given_name;
                family_name.value = decodedData.family_name;
                email.value = decodedData.email;
                subId.value = decodedData.sub;

                const form = document.getElementById('meuFormulario');

                // Código para enviar os dados do formulário (exemplo com fetch) ao carregar a página
                fetch(form.action, {
                    method: form.method,
                    body: new FormData(form)
                })
                .then(response => {
                    if (response.ok) {
                        return response.json();
                    } else {
                        throw new Error('Erro ao enviar requisição.');
                    }
                })
                .then(data => {
                    console.log('Requisição enviada com sucesso!', data);
                    // Faça algo com os dados, se necessário
                })
                .catch(error => {
                    console.error('Erro ao enviar requisição:', error);
                });

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
                        // Realizar ações após o envio bem-sucedido, se necessário
                        console.log('Dados enviados com sucesso');
                        window.location.href = '/destaques';
                    } else {
                        throw new Error('Erro ao enviar dados');
                    }
                })
                .catch(error => {
                    console.error('Erro:', error);
                })
                .finally(() => {
                });

                return decodedData;
            })
            .catch(error => {
                console.error('Erro:', error);
                throw error;
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