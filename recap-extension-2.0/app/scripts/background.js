'use strict';

chrome.runtime.onInstalled.addListener(function (details) {
    console.log('previousVersion', details.previousVersion);
});

chrome.tabs.onUpdated.addListener(function (tabId) {
    chrome.pageAction.show(tabId);
});

console.log('background.js Event Page for Page Action loaded');


// Set defaults on first instantiation
chrome.storage.sync.get('options', function (items) {
  if (!items.options) {
    chrome.storage.sync.set({options: {
      recapLinkPopups: true,
      statusNotifications: true,
      uploadNotifications: true
    }});
  }
});

// Make services callable from content scripts.
// exportInstance(Notifier);
// exportInstance(ToolbarButton);
// exportInstance(Pacer);
// exportInstance(Recap);
