'use strict';

var $ = require('jquery');
var ko = require('knockout');
var bootbox = require('bootbox');
var Raven = require('raven-js');
var oop = require('js/oop');

var $osf = require('js/osfHelpers');

var USE_CHARON = true;

var ConnectedProject = function(data) {
    var self = this;
    self.title = data.title;
    self.id = data.id;
    self.urls = data.urls;
};

var ExternalAccount = oop.defclass({
    constructor: function(data) {
        var self = this;
        self.name = data.display_name;
        self.id = data.id;
        self.profileUrl = data.profile_url;
        self.providerName = data.provider_name;

        self.connectedNodes = ko.observableArray();

        ko.utils.arrayMap(data.nodes, function(item) {
            self.connectedNodes.push(new ConnectedProject(item));
        });
    },
    _deauthorizeNodeConfirm: function(node) {
        var self = this;
        var url = node.urls.deauthorize;
        var request = $osf.ajaxJSON(
            'DELETE',
            url,
            {
                isCors: true,
            }
        )
            .done(function(data) {
                self.connectedNodes.remove(node);
            })
            .fail(function(xhr, status, error) {
                Raven.captureMessage('Error deauthorizing node: ' + node.id, {
                    extra: {
                        url: url,
                        status: status,
                        error: error
                    }
                });
            });
    },
    deauthorizeNode: function(node) {
        var self = this;
        bootbox.confirm({
            title: 'Remove addon?',
            message: 'Are you sure you want to remove the ' + $osf.htmlEscape(self.providerName) + ' authorization from this project?',
            callback: function(confirm) {
                if (confirm) {
                    self._deauthorizeNodeConfirm(node);
                }
            },
            buttons:{
                confirm:{
                    label:'Remove',
                    className:'btn-danger'
                }
            }
        });
    }
});

var OAuthAddonSettingsViewModel = oop.defclass({
    constructor: function(name, displayName) {
        var self = this;
        self.name = name;
        self.properName = displayName;
        self.accounts = ko.observableArray();
        self.message = ko.observable('');
        self.messageClass = ko.observable('');
        window.addEventListener(
            'message',
            function(event) {
                console.error('$$$ ogtta msg');
                if (event.origin !== "http://localhost:8011") {
                    return;
                }
                if (event.data['addon'] === 'box') {
                    console.debug('heard back from the meowmeow boys about box');
                }
                else {
                    console.debug('heard back, but ignored');
                }
            },
            false,
        );

    },
    setMessage: function(msg, cls) {
        var self = this;
        self.message(msg);
        self.messageClass(cls || 'text-info');
    },
    connectAccount: function() {
        var self = this;
        window.oauthComplete = function() {
            self.setMessage('');
            var accountCount = self.accounts().length;
            self.updateAccounts().done( function() {
                if (self.accounts().length > 0 && self.accounts().length >= accountCount) {  // If there's more than 1 and the count stays the same, probably reauthorizing
                    if (self.name === 'dropbox') {
                        self.setMessage('Add-on successfully authorized. If you wish to link a different account, log out of dropbox.com before attempting to connect to a second Dropbox account on the OSF. This will clear the credentials stored in your browser.', 'text-success');
                    } else if (self.name === 'bitbucket') {
                        self.setMessage('Add-on successfully authorized. If you wish to link a different account, log out of bitbucket.org before attempting to connect to a second Bitbucket account on the OSF. This will clear the credentials stored in your browser.', 'text-success');
                    } else if (self.name === 'onedrive') {
                        self.setMessage('Add-on successfully authorized. If you wish to link a different account, log out of Personal OneDrive at login.live.com and OneDrive for School or Business at login.microsoftonline.com before attempting to connect to a second OneDrive account on the OSF. This will clear the credentials stored in your browser.', 'text-success');
                    } else {
                        self.setMessage('Add-on successfully authorized. To link this add-on to an OSF project, go to the settings page of the project, enable ' + self.properName + ', and choose content to connect.', 'text-success');
                    }
                } else {
                    self.setMessage('Error while authorizing add-on. Please log in to your ' + self.properName + ' account and grant access to the OSF to enable this add-on.', 'text-danger');
                }
            });
        };
        console.error('$$$ decision time!');
        if (USE_CHARON && self.name === 'box') {
            console.error('$$$   -- CORRECT!');
            window.open('http://localhost:8011/charon/box/connect', 'charon-land');
        } else {
            console.error('$$$    --- FAIL SO HARD!!');
            window.open('/oauth/connect/' + self.name + '/');
        }
    },
    askDisconnect: function(account) {
        var self = this;
        bootbox.confirm({
            title: 'Disconnect Account?',
            message: '<p class="overflow">' +
                'Are you sure you want to disconnect the ' + $osf.htmlEscape(self.properName) + ' account <strong>' +
                $osf.htmlEscape(account.name) + '</strong>? This will revoke access to ' + $osf.htmlEscape(self.properName) + ' for all projects you have authorized.' +
                '</p>',
            callback: function(confirm) {
                if (confirm) {
                    self.disconnectAccount(account);
                    self.setMessage('');
                }
            },
            buttons:{
                confirm:{
                    label:'Disconnect',
                    className:'btn-danger'
                }
            }
        });
    },
    disconnectAccount: function(account) {
        var self = this;
        var url = '/api/v1/oauth/accounts/' + account.id + '/';
        var request = $osf.ajaxJSON(
            'DELETE',
            url,
            {
                isCors: true,
            },
        );
        request.done(function(data) {
            self.updateAccounts();
        });
        request.fail(function(xhr, status, error) {
            Raven.captureMessage('Error while removing addon authorization for ' + account.id, {
                extra: {
                    url: url,
                    status: status,
                    error: error
                }
            });
        });
        return request;
    },
    updateAccounts: function() {
        var self = this;
        var url = '/api/v1/settings/' + self.name + '/accounts/';
        if (USE_CHARON && self.name === 'box') {
            url = 'http://localhost:8011/charon/settings/box/accounts';
        }
        console.error('??? trying to updateAccounts at ' + url + ' without osfHelpers');
        // var request = $.get(url);
        var request = $osf.ajaxJSON(
            'GET',
            url,
            {
                isCors: true,
            },
        );
        request.done(function(data) {
            self.accounts($.map(data.accounts, function(account) {
                return new ExternalAccount(account);
            }));
            $('#' + self.name + '-header').osfToggleHeight({height: 160});
        });
        request.fail(function(xhr, status, error) {
            Raven.captureMessage('Error while updating addon account', {
                extra: {
                    url: url,
                    status: status,
                    error: error
                }
            });
        });
        return request;
    }
});

module.exports = {
    ConnectedProject: ConnectedProject,
    ExternalAccount: ExternalAccount,
    OAuthAddonSettingsViewModel: OAuthAddonSettingsViewModel
};
