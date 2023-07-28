'use strict';

require('./box.css');
var OauthAddonNodeConfig = require('js/oauthAddonNodeConfig').OauthAddonNodeConfig;

// var url = window.contextVars.node.urls.api + 'box/settings/';
var url = 'http://localhost:8011/charon/projects/' + window.contextVars.node.id + '/box/settings/';
new OauthAddonNodeConfig('Box', '#boxScope', url, '#boxGrid');
