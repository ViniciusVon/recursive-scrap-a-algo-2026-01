/**
 * Percorre o DOM, identifica nós de texto visíveis contendo valores numéricos
 * (como preços, percentuais, datas, horários e outros números monitoráveis)
 * e retorna uma lista no formato:
 *
 * [{ text, xpath }, ...]
 *
 * Utilizado por src/value_selector.py via driver.execute_script()
 * para localizar valores disponíveis na página e permitir sua seleção
 * para monitoramento.
 */

function getXPath(el) {
    if (el === document.body) return '/html/body';
    var ix = 0;
    var siblings = el.parentNode ? el.parentNode.childNodes : [];
    for (var i = 0; i < siblings.length; i++) {
        var sib = siblings[i];
        if (sib === el) {
            return getXPath(el.parentNode) + '/' +
                el.tagName.toLowerCase() + '[' + (ix + 1) + ']';
        }
        if (sib.nodeType === 1 && sib.tagName === el.tagName) ix++;
    }
    return '';
}

function isVisible(el) {
    try {
        var rect = el.getBoundingClientRect();
        if (rect.width === 0 && rect.height === 0) return false;
        var style = window.getComputedStyle(el);
        if (
            style.display === 'none' ||
            style.visibility === 'hidden' ||
            style.opacity === '0'
        ) return false;
        return true;
    } catch(e) {
        return false;
    }
}

function listarValores() {
    var resultados = [];
    var vistos = new Set();

    var regexPreco = /\d{1,3}(\.\d{3})+(,\d+)?|\d+(,\d{2,})|\d{1,2}:\d{2}(:\d{2})?|\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}/;

    var tagsIgnorar = new Set(['script', 'style', 'noscript', 'meta', 'link']);

    var walker = document.createTreeWalker(
        document.body,
        NodeFilter.SHOW_TEXT,
        {
            acceptNode: function(node) {
                var texto = node.nodeValue.trim();
                if (!texto) return NodeFilter.FILTER_REJECT;
                var pai = node.parentElement;
                if (!pai) return NodeFilter.FILTER_REJECT;
                if (tagsIgnorar.has(pai.tagName.toLowerCase())) return NodeFilter.FILTER_REJECT;
                return NodeFilter.FILTER_ACCEPT;
            }
        }
    );

    var node;
    while ((node = walker.nextNode())) {
        var texto = node.nodeValue.trim();
        var pai = node.parentElement;

        if (!isVisible(pai)) continue;
        if (!regexPreco.test(texto)) continue;
        if (texto.length < 4 || texto.length > 80) continue;
        if (texto.includes('%.@.') || texto.includes('null,')) continue;

        var chave = "text:" + texto;
        if (vistos.has(chave)) continue;
        vistos.add(chave);

        resultados.push({
            tipo: "texto",
            text: texto,
            xpath: getXPath(pai)
        });
    }

    return resultados;
}

return listarValores();