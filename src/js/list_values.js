/**
 * Percorre o DOM identificando elementos folha (sem filhos) cujo texto
 * contém dígitos, e devolve uma lista [{text, xpath}, ...].
 *
 * Usado por src/value_selector.py via driver.execute_script().
 */

function getXPath(el) {
    if (el === document.body) return '/html/body';
    var ix = 0;
    var siblings = el.parentNode ? el.parentNode.childNodes : [];
    for (var i = 0; i < siblings.length; i++) {
        var sib = siblings[i];
        if (sib === el) {
            return getXPath(el.parentNode) + '/' + el.tagName.toLowerCase() + '[' + (ix + 1) + ']';
        }
        if (sib.nodeType === 1 && sib.tagName === el.tagName) ix++;
    }
    return '';
}

function listarValores() {
    var resultados = [];
    var todos = document.body.getElementsByTagName('*');
    var regex = /\d/;
    for (var i = 0; i < todos.length; i++) {
        var el = todos[i];
        if (el.children.length > 0) continue;
        var tag = el.tagName.toLowerCase();
        if (tag === 'script' || tag === 'style' || tag === 'noscript') continue;
        var texto = (el.innerText || el.textContent || '').trim();
        if (!texto || !regex.test(texto)) continue;
        if (texto.length > 200) continue;
        resultados.push({text: texto, xpath: getXPath(el)});
    }
    return resultados;
}

return listarValores();
