/* eslint-env browser */
/* globals Components */

function PrefListener(branchName, func) {
    "use strict";
    var prefService = Components
      .classes["@mozilla.org/preferences-service;1"]
      .getService(Components.interfaces.nsIPrefService);

    var branch = prefService.getBranch(branchName);
    branch.QueryInterface(Components.interfaces.nsIPrefBranch2);

    this.register = function() {
        branch.addObserver("", this, false);
        branch.getChildList("", { })
              .forEach(function (name) { func(branch, name); });
    };

    this.unregister = function unregister() {
        if (branch)
            branch.removeObserver("", this);
    };

    this.observe = function(subject, topic, data) {
        if (topic == "nsPref:changed")
            func(branch, data);
    };
}
