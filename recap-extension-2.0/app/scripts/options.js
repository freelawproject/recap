'use strict';

console.log('Options page js loaded.');

var inputs = document.getElementsByTagName('input');

function loadOptions() {
    chrome.storage.sync.get('options', function (items) {
        for (var i = 0; i < inputs.length; i++) {
            inputs[i].checked = items.options[inputs[i].id];
        }
    });
}

function saveOptions() {
    var options = {};
    for (var i = 0; i < inputs.length; i++) {
        options[inputs[i].id] = inputs[i].checked;
    }
    chrome.storage.sync.set({options: options});
}

loadOptions();
for (var i = 0; i < inputs.length; i++) {
    inputs[i].addEventListener('change', saveOptions);
}
