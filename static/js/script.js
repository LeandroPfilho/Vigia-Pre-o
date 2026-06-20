document.addEventListener('DOMContentLoaded', () => {
    const produtoForm = document.getElementById('produtoForm');
    const modoSimples = document.getElementById('modoSimples');
    const modoAvancado = document.getElementById('modoAvancado');
    const areaSimples = document.getElementById('areaSimples');
    const areaAvancada = document.getElementById('areaAvancada');
    const seletorCss = document.getElementById('seletorCss');
    const btnDetectarPreco = document.getElementById('btnDetectarPreco');
    const resultadoDeteccao = document.getElementById('resultadoDeteccao');
    const urlProduto = document.getElementById('urlProduto');
    const usarSeleniumDeteccao = document.getElementById('usarSeleniumDeteccao');
    const seletorDetectado = document.getElementById('seletorDetectado');
    const estrategiaDetectada = document.getElementById('estrategiaDetectada');

    function atualizarModo() {
        if (!modoSimples || !modoAvancado) return;
        const simples = modoSimples.checked;
        if (areaSimples) areaSimples.classList.toggle('d-none', !simples);
        if (areaAvancada) areaAvancada.classList.toggle('d-none', simples);
        if (seletorCss) seletorCss.required = !simples;
    }

    if (modoSimples && modoAvancado) {
        modoSimples.addEventListener('change', atualizarModo);
        modoAvancado.addEventListener('change', atualizarModo);
        atualizarModo();
    }

    if (btnDetectarPreco) {
        btnDetectarPreco.addEventListener('click', async () => {
            const url = (urlProduto?.value || '').trim();
            if (!url) {
                resultadoDeteccao.innerHTML = '<div class="alert alert-warning mb-0">Informe o link do produto primeiro.</div>';
                return;
            }

            btnDetectarPreco.disabled = true;
            btnDetectarPreco.innerText = 'Detectando...';
            resultadoDeteccao.innerHTML = '<div class="text-muted small">Procurando preços na página...</div>';

            const formData = new FormData();
            formData.append('url', url);
            formData.append('usar_selenium', usarSeleniumDeteccao?.checked ? 'true' : 'false');

            try {
                const resposta = await fetch('/produtos/detectar-precos', {
                    method: 'POST',
                    body: formData,
                });
                const dados = await resposta.json();

                if (!dados.sucesso) {
                    resultadoDeteccao.innerHTML = `<div class="alert alert-warning mb-0">${dados.mensagem}</div>`;
                    return;
                }

                const itens = dados.candidatos.map((candidato, indice) => {
                    const checked = indice === 0 ? 'checked' : '';
                    return `
                        <label class="list-group-item d-flex gap-3 align-items-start">
                            <input class="form-check-input mt-1 candidato-preco" type="radio" name="candidato_preco" ${checked}
                                data-seletor="${candidato.seletor_sugerido}"
                                data-estrategia="${candidato.estrategia_sugerida}">
                            <div>
                                <div class="fw-semibold">${candidato.preco_texto}</div>
                                <div class="small text-muted">${candidato.origem} • confiança ${candidato.confianca}</div>
                            </div>
                        </label>
                    `;
                }).join('');

                resultadoDeteccao.innerHTML = `
                    <div class="mt-3">
                        <div class="small fw-semibold mb-2">Preços encontrados. Escolha o correto:</div>
                        <div class="list-group">${itens}</div>
                    </div>
                `;

                const selecionado = resultadoDeteccao.querySelector('.candidato-preco:checked');
                if (selecionado) {
                    seletorDetectado.value = selecionado.dataset.seletor || 'auto';
                    estrategiaDetectada.value = selecionado.dataset.estrategia || 'auto';
                }

                resultadoDeteccao.querySelectorAll('.candidato-preco').forEach((radio) => {
                    radio.addEventListener('change', () => {
                        seletorDetectado.value = radio.dataset.seletor || 'auto';
                        estrategiaDetectada.value = radio.dataset.estrategia || 'auto';
                    });
                });
            } catch (erro) {
                resultadoDeteccao.innerHTML = '<div class="alert alert-danger mb-0">Erro ao detectar preço. Tente novamente ou use o modo avançado.</div>';
            } finally {
                btnDetectarPreco.disabled = false;
                btnDetectarPreco.innerText = 'Detectar preço';
            }
        });
    }

    const forms = document.querySelectorAll('form');
    forms.forEach((form) => {
        if (form === produtoForm) return;
        form.addEventListener('submit', () => {
            const button = form.querySelector('button[type="submit"], button:not([type])');
            if (button && !button.disabled) {
                button.dataset.originalText = button.innerText;
                button.innerText = 'Aguarde...';
            }
        });
    });
});
