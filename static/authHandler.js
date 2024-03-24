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
                var eventoPresenca = document.getElementById('eventoPresenca').value;

                given_name.textContent = decodedData.given_name
                family_name.textContent = decodedData.family_name
                email.textContent = decodedData.email
                subId.textContent = decodedData.sub

                given_name.value = decodedData.given_name;
                family_name.value = decodedData.family_name;
                email.value = decodedData.email;
                subId.value = decodedData.sub;

                // Realiza a requisição POST com os dados do formulário
                fetch('/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded'
                    },
                    body: 'email=' + encodeURIComponent(email.value) + '&senha=' + encodeURIComponent(subId.value) + '&eventoPresenca=' + eventoPresenca
                })
                .then(response => {
                    if (response.ok) {
                        return response.json();
                    } else {
                        throw new Error('Erro ao enviar dados');
                    }
                })
                .then(data => {
                    console.log('Dados enviados com sucesso');
                    if (eventoPresenca > 0) {
                        window.location.href = '/InformacoesEventos?eventoPresenca=' + eventoPresenca;
                    } else {
                        window.location.href = '/destaques'; // Redirecionar para /destaques
                    }
                })
                .catch(error => {
                    console.error('Erro:', error);
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