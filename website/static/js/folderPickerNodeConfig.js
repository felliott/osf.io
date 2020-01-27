/**
 * Abstract module that controls the addon node settings. Includes Knockout view-model
 * for syncing data, and HGrid-folderpicker for selecting a folder.
 */
'use strict';
require('css/addon_folderpicker.css');
var ko = require('knockout');
var $ = require('jquery');
var bootbox = require('bootbox');
var Raven = require('raven-js');
var m = require('mithril');


var FolderPicker = require('js/folderpicker');
var $osf = require('js/osfHelpers');

var oop = require('js/oop');

var rdmGettext = require('js/rdmGettext');
var gt = rdmGettext.rdmGettext();
var _ = function(msgid) { return gt.gettext(msgid); };
var agh = require('agh.sprintf');

/**
 * @class FolderPickerViewModel
 * @param {String} addonName Full display name of the addon
 * @param {String} url API url to initially fetch settings
 * @param {String} selector CSS selector for containing div
 * @param {String} folderPicker CSS selector for folderPicker div
 *
 * Notes:
 * - Subclasses of this VM can be created using the oop module like: oop.extend(FolderPickerViewModel, { ... });
 * - Subclasses must:
 *   - provide a VM.messages.submitSettingsSuccess()
 *   - override VM.treebeardOptions.onPickFolder and VM.treebeardOptions.resolveLazyloadUrl
 * - Subclasses can:
 *   - implement an _updateCustomFields method to capture additional parameters in updateFromData
 */
var FolderPickerViewModel = oop.defclass({
    constructor: function(addonName, url, selector, folderpickerSelector) {
        var self = this;
        self.url = url;
        self.addonName = addonName;
        self.selector = selector;
        self.folderpickerSelector = folderpickerSelector;
        self.folderpicker = null;
        // Auth information
        self.nodeHasAuth = ko.observable(false);
        // whether current user has an auth token
        self.userHasAuth = ko.observable(false);
        // whether current user is authorizer of the addon
        self.userIsOwner = ko.observable(false);
        // display name of owner of credentials
        self.ownerName = ko.observable('');
        // whether the auth token is valid
        self.validCredentials = ko.observable(true);
        // whether import token has been clicked
        self.loadingImport = ko.observable(false);
        // current folder
        self.folder = ko.observable({
            name: null,
            id: null,
            path: null
        });
        // current library
        self.library = ko.observable({
            name: null,
            id: null,
            path: null
        });
        // current libraries that the user has access to
        self.libraries = ko.observable([]);
        self.pendingLibraryRequest = ko.observable(false);
        // set of urls used for API calls internally
        self.urls = ko.observable({});
        // Flashed messages
        self.message = ko.observable('');
        self.messageClass = ko.observable('text-info');
        // Display names
        self.PICKER = 'picker';
        // Currently selected folder name
        self.selected = ko.observable(false);
        // Currently selected library name
        self.selectedLibrary = ko.observable(false);
        self.loading = ko.observable(false);
        self.libraryLoading = ko.observable(false);
        self.totalLibraries = ko.observable(null);
        self.libraryFirstLoad = ko.observable(true);
        self.numberLibrariesLoaded = ko.observable(0);
        // Whether the initial data has been fetched form the server. Used for
        // error handling.
        self.loadedSettings = ko.observable(false);
        // Current folder display
        self.currentDisplay = ko.observable(null);
        // Current library display
        this.currentLibraryDisplay = ko.observable(null);
        // Whether the folders have been loaded from the API
        self.loadedFolders = ko.observable(false);
        // Whether the group libraries have been loaded from the API
        self.loadedLibraries = ko.observable(false);
        // Button text for changing folders
        self.toggleChangeText = ko.observable('Change');
        // Button text for changing libraries
        self.toggleChangeLibraryText = ko.observable('Change');

        var addonSafeName = $osf.htmlEscape(self.addonName);

        self.messages = {
            invalidCredOwner: ko.pureComputed(function() {
                return agh.sprintf(_('Could not retrieve %1$s settings at this time. The credentials associated with this %1$s account may no longer be valid.'),addonSafeName) +
                    agh.sprintf(_(' Try disconnecting and reconnecting the %1$s account on your <a href="%2$s">account settings page</a>.'),addonSafeName,self.urls().settings);
            }),
            invalidCredNotOwner: ko.pureComputed(function() {
                return agh.sprintf(_('Could not retrieve %1$s settings at this time. The %1$s addon credentials may no longer be valid.'),addonSafeName) +
                    agh.sprintf(_(' Contact %1$s to verify.') , $osf.htmlEscape(self.ownerName()));
            }),
            cantRetrieveSettings: ko.pureComputed(function() {
                return agh.sprintf(_('Could not retrieve %1$s settings at this time. Please refresh the page. If the problem persists, email %2$s.'),addonSafeName,$osf.osfSupportLink());
            }),
            updateAccountsError: ko.pureComputed(function() {
                return agh.sprintf(_('Could not retrieve %1$s account list at this time. Please refresh the page. If the problem persists, email %2$s.'),addonSafeName,$osf.osfSupportLink());
            }),
            deauthorizeSuccess: ko.pureComputed(function() {
                return agh.sprintf(_('Disconnected %1$s.') , addonSafeName );
            }),
            deauthorizeFail: ko.pureComputed(function() {
                return agh.sprintf(_('Could not disconnect %1$s account because of an error. Please try again later.'),addonSafeName);
            }),
            connectAccountSuccess: ko.pureComputed(function() {
                return agh.sprintf(_('Successfully connected a %1$s account'),addonSafeName);
            }),
            connectAccountDenied: ko.pureComputed(function() {
                return agh.sprintf(_('Error while authorizing addon. Please log in to your %1$s account and grant access to the GakuNin RDM to enable this addon.'),addonSafeName);
            }),
            submitSettingsSuccess: ko.pureComputed(function() {
                throw new Error('Subclasses of FolderPickerViewModel must provide a message for successful settings updates. ' +
                                'This should take the form: "Successfully linked \'{FOLDER_NAME}\'. Go to the <a href="{URL}"> ' +
                                '{PAGE_NAME} to view your {CONTENT_TYPE}.');
            }),
            submitSettingsError: ko.pureComputed(function() {
                return agh.sprintf(_('Could not change %1$s settings. Please try again later.'),addonSafeName);
            }),
            confirmDeauth: ko.pureComputed(function() {
                return agh.sprintf(_('Are you sure you want to remove this %1$s account?'),addonSafeName);
            }),
            confirmAuth: ko.pureComputed(function() {
                return agh.sprintf(_('Are you sure you want to link your %1$s account with this project?'),addonSafeName);
            }),
            tokenImportSuccess: ko.pureComputed(function() {
                return agh.sprintf(_('Successfully imported %1$s account from profile.'),addonSafeName);
            }),
            tokenImportError: ko.pureComputed(function() {
                return agh.sprintf(_('Error occurred while importing %1$s account.'),addonSafeName);
            }),
            libraryImportError: ko.pureComputed(function() {
                return agh.sprintf(_('Error occurred while importing %1$s group libraries.'),addonSafeName);
            }),
            connectError: ko.pureComputed(function() {
                return agh.sprintf(_('Could not connect to %1$s at this time. Please try again later.'),addonSafeName);
            })
        };

        self.librariesPending = ko.pureComputed(function() {
            return (self.totalLibraries() && parseInt(self.numberLibrariesLoaded()) < parseInt(self.totalLibraries()));
        });

        /**
         * Whether or not to show the Import Access Token Button
         */
        self.showImport = ko.pureComputed(function() {
            // Invoke the observables to ensure dependency tracking
            var userHasAuth = self.userHasAuth();
            var nodeHasAuth = self.nodeHasAuth();
            var loaded = self.loadedSettings();
            var onclick = self.loadingImport();
            return userHasAuth && !nodeHasAuth && loaded && !onclick;
        });

        /** Whether or not show loading icon after import button */
        self.showLoading = ko.pureComputed(function() {
            var userHasAuth = self.userHasAuth();
            var nodeHasAuth = self.nodeHasAuth();
            var loaded = self.loadedSettings();
            var onclick = self.loadingImport();
            return userHasAuth && !nodeHasAuth && loaded && onclick;
        });

        /** Whether or not to show the full settings pane. */
        self.showSettings = ko.pureComputed(function() {
            return self.nodeHasAuth() && self.validCredentials();
        });

        /** Whether or not to show the Connect Account button */
        self.showTokenCreateButton = ko.pureComputed(function() {
            // Invoke the observables to ensure dependency tracking
            var userHasAuth = self.userHasAuth();
            var nodeHasAuth = self.nodeHasAuth();
            var loaded = self.loadedSettings();
            return loaded && !userHasAuth && !nodeHasAuth;
        });

        /** Computed functions for the linked and selected folders' display text.*/
        self.folderName = ko.pureComputed(function() {
            var nodeHasAuth = self.nodeHasAuth();
            var folder = self.folder();
            return (nodeHasAuth && folder && folder.name) ? folder.name.trim() : '';
        });

        /** Computed functions for the linked and selected library' display text.*/
        self.libraryName = ko.pureComputed(function() {
            var nodeHasAuth = self.nodeHasAuth();
            var library = self.library();
            return (nodeHasAuth && library && library.name) ? library.name.trim() : '';
        });

        self.selectedFolderName = ko.pureComputed(function() {
            var userIsOwner = self.userIsOwner();
            var selected = self.selected();
            var name = selected.name ? selected.name : 'None';
            name = name.replace('All Files', 'Full ' + addonName);
            return userIsOwner ? name : '';
        });

        self.treebeardOptions = {
            lazyLoadPreprocess: function(data) {
                return data;
            },
            onPickFolder: function() {
                throw new Error('Subclasses of FolderPickerViewModel must implement a "onPickFolder(evt, item)" method');
            },
            resolveLazyloadUrl: function(item) {
                throw new Error('Subclasses of FolderPickerViewModel must implement a "resolveLazyloadUrl(item)" method');
            }
        };
    },
    /**
     * Change the flashed message.
     *
     * @param {String} text Text to show
     * @param {String} css CSS class of text to be show, defaults to 'text-info'
     * @param {Number} timeout Optional number of ms to wait until removing the flashed message
     */
    changeMessage: function(text, css, timeout) {
        var self = this;

        self.message(text);
        var cssClass = css || 'text-info';
        self.messageClass(cssClass);
        if (timeout) {
            // Reset message after timeout period
            setTimeout(function() {
                self.resetMessage();
            }, timeout);
        }
    },
    resetMessage: function() {
        this.message('');
        this.messageClass('text-info');
    },
    /**
     * Abstract hook called after updateFromData, before the promise is resolved.
     * - use to validate the VM state after update
     **/
    afterUpdate: function() {},
    /**
     * Abstract hook where subclasses can capture extra data from the API response
     *
     * @param {Object} settings Settings passed from server response in #updateFromData
     */
    _updateCustomFields: function(settings) {},
    /**
     * Update the view model from data returned from the server or data passed explicitly.
     *
     * @param {Object} data optional data to update from rather than from API
     */
    updateFromData: function(data) {
        var self = this;
        var ret = $.Deferred();
        var applySettings = function(settings){
            self.ownerName(settings.ownerName);
            self.nodeHasAuth(settings.nodeHasAuth);
            self.userIsOwner(settings.userIsOwner);
            self.userHasAuth(settings.userHasAuth);
            self.folder(settings.folder || {
                name: null,
                path: null,
                id: null
            });
            self.library(settings.library || {
                name: null,
                path: null,
                id: null
            });
            self.urls(settings.urls);
            self._updateCustomFields(settings);
            self.afterUpdate();
            ret.resolve();
        };
        if (typeof data === 'undefined' || $.isEmptyObject(data)){
            self.fetchFromServer()
                .done(applySettings)
                .fail(ret.reject);
        }
        else{
            applySettings(data);
        }
        return ret.promise();
    },
    fetchFromServer: function() {
        var self = this;
        var ret = $.Deferred();
        var request = $.ajax({
            url: self.url,
            type: 'GET',
            dataType: 'json'
        });
        request.done(function(response) {
            self.loadedSettings(true);
            ret.resolve(response.result);
        });
        request.fail(function(xhr, textStatus, error) {
            self.changeMessage(self.messages.cantRetrieveSettings(), 'text-danger');
            Raven.captureMessage(agh.sprintf(_('Could not GET %1$s settings'),self.addonName), {
                extra: {
                    url: self.url,
                    textStatus: textStatus,
                    error: error
                }
            });
            ret.reject(xhr, textStatus, error);
        });
        return ret.promise();
    },
    _serializeSettings: function(){
        return ko.toJS(this);
    },
    /**
     * Send a PUT request to change the linked folder.
     */
    submitSettings: function() {
        var self = this;
        function onSubmitSuccess(response) {
            // Update folder in ViewModel
            self.folder(response.result.folder);
            self.urls(response.result.urls);
            self.cancelSelection();
            self.changeMessage(self.messages.submitSettingsSuccess(), 'text-success');
        }
        function onSubmitError(xhr, status, error) {
            self.changeMessage(self.messages.submitSettingsError(), 'text-danger');
            Raven.captureMessage(agh.sprintf(_('Failed to update %1$s settings.'),self.addonName), {
                extra: {
                    xhr: xhr,
                    status: status,
                    error: error
                }
            });
        }
        return $osf.putJSON(self.urls().config, self._serializeSettings())
            .done(onSubmitSuccess)
            .fail(onSubmitError);
    },
    /**
     * Send a PUT request to save the library
     */
    saveLibrary: function() {
        var self = this;
        function onSubmitSuccess(response) {
            // Update library in ViewModel
            self.library(response.result.library);
            self.currentLibraryDisplay(null);
            // Update folder in ViewModel - after library changed,
            // folders need to be reloaded
            self.folder(response.result.folder);
            self.currentDisplay(null);
            self.loadedFolders(false);
            self.destroyPicker();
            self.toggleChangeText('Change');
            self.urls(response.result.urls);
            self.changeMessage(self.messages.submitLibrarySettingsSuccess(), 'text-success');
        }
        function onSubmitError(xhr, status, error) {
            self.changeMessage(self.messages.submitSettingsError(), 'text-danger');
            Raven.captureMessage(agh.sprintf(_('Failed to update %1$s settings.'),self.addonName), {
                extra: {
                    xhr: xhr,
                    status: status,
                    error: error
                }
            });
        }
        var metadata = {
            'external_library_id': self.selectedLibrary().split(/,(.+)/)[0],
            'external_library_name': self.selectedLibrary().split(/,(.+)/)[1]
        };
        return $osf.putJSON(self.urls().config, metadata)
            .done(onSubmitSuccess)
            .fail(onSubmitError);
    },
    onImportSuccess: function(response) {
        var self = this;
        var msg = response.message || self.messages.tokenImportSuccess();
        // Update view model based on response
        self.changeMessage(msg, 'text-success', 3000);
        self.updateFromData(response.result);
        self.loadedFolders(false);
        self.activatePicker();
    },
    onImportLibrarySuccess: function(response, textStatus, xhr) {
        var self = this;
        self.pendingLibraryRequest(false);
        if (response) {
            var loaded = self.numberLibrariesLoaded();
            self.totalLibraries(response.pop());
            self.numberLibrariesLoaded(loaded + response.length);
            if (self.libraryFirstLoad()) {
                // On first load, the personal library was automatically appended to the
                // response on our end.  We need to remove this from the count.
                self.numberLibrariesLoaded(self.numberLibrariesLoaded() - 1);
                self.libraryFirstLoad(false);
            }
        }
        var libraries = self.libraries();
        Array.prototype.push.apply(libraries, response);
        self.libraries(libraries);
        // Update view model based on response
        self.libraryLoading(false);
        self.loadedLibraries(true);
    },
    onImportError: function(xhr, status, error) {
        var self = this;
        self.changeMessage(self.messages.tokenImportError(), 'text-danger');
        Raven.captureMessage(agh.sprintf(_('Failed to import %1$s access token.'),self.addonName), {
            extra: {
                xhr: xhr,
                status: status,
                error: error
            }
        });
    },
    onImportLibraryError: function(xhr, status, error) {
        var self = this;
        self.pendingLibraryRequest(false);
        self.changeMessage(self.messages.libraryImportError(), 'text-danger');
        Raven.captureMessage(agh.sprintf(_('Failed to import %1$s group libraries.'),self.addonName), {
            extra: {
                xhr: xhr,
                status: status,
                error: error
            }
        });
    },
    _importAuthPayload: function() {
        return {};
    },
    _importAuthConfirm: function() {
        var self = this;
        return $osf.putJSON(self.urls().importAuth, self._importAuthPayload())
            .done(self.onImportSuccess.bind(self))
            .fail(self.onImportError.bind(self));
    },
    importLibraries: function() {
        var self = this;
        if (!self.pendingLibraryRequest()) {
            if (self.libraryFirstLoad()) {
                self.libraryLoading(true);
            }
            var metadata = {
                'limit': 5,
                'start': self.numberLibrariesLoaded(),
                'return_count': true,
                'append_personal': self.libraryFirstLoad()
            };
            self.pendingLibraryRequest(true);
            return $.getJSON(self.urls().libraries, metadata)
                .done(self.onImportLibrarySuccess.bind(self))
                .fail(self.onImportLibraryError.bind(self));
        }
    },
    scrolled: function(data, event) {
       var self = this;
       var elem = event.target;
       if (elem.scrollTop > (elem.scrollHeight - elem.offsetHeight - 200)) {
           if (self.librariesPending()) {
                this.importLibraries();
           }
       }
   },
    onLibraryChange: function() {
        var self = this;
        self.currentLibraryDisplay('picker');
    },
    /**
     * Send PUT request to import access token from user profile.
     */
    importAuth: function() {
        var self = this;
        bootbox.confirm({
            title: agh.sprintf(_('Import %1$s Account?'),$osf.htmlEscape(self.addonName)),
            message: self.messages.confirmAuth(),
            callback: function(confirmed) {
                if (confirmed) {
                    self._importAuthConfirm();
                    self.loadingImport(true);
                }
            },
            buttons:{
                confirm:{
                    label:_('Import')
                }
            }
        });
    },
    /**
     * Send DELETE request to deauthorize this node.
     */
    _deauthorizeConfirm: function(){
        var self = this;
        var request = $.ajax({
            url: self.urls().deauthorize,
            type: 'DELETE'
        });
        request.done(function() {
            // Update observables
            self.nodeHasAuth(false);
            self.cancelSelection();
            self.currentDisplay(null);
            self.currentLibraryDisplay(null);
            self.changeMessage(self.messages.deauthorizeSuccess(), 'text-warning', 3000);
            self.loadedFolders(false);
            self.destroyPicker();
        });
        request.fail(function(xhr, textStatus, error) {
            self.changeMessage(self.messages.deauthorizeFail(), 'text-danger');
            Raven.captureMessage(agh.sprintf(_('Could not deauthorize %1$s account from node'),self.addonName), {
                extra: {
                    url: self.urls().deauthorize,
                    textStatus: textStatus,
                    error: error
                }
            });
        });
        return request;
    },
    /** Pop up a confirmation to deauthorize addon from this node.
     *  Send DELETE request if confirmed.
     */
    deauthorize: function() {
        var self = this;
        bootbox.confirm({
            title: agh.sprintf(_('Disconnect %1$s Account?'),$osf.htmlEscape(self.addonName)),
            message: self.messages.confirmDeauth(),
            callback: function(confirmed) {
                if (confirmed) {
                    self._deauthorizeConfirm();
                    self.loadingImport(false);
                }
            },
            buttons:{
                confirm:{
                    label:_('Disconnect'),
                    className:'btn-danger'
                }
            }
        });
    },
    /**
     * Must be used to update radio buttons and knockout view model simultaneously
     */
    cancelSelection: function() {
        this.selected(null);
    },
    /**
     * Must be used to update radio buttons and knockout view model simultaneously
     */
    cancelLibrarySelection: function() {
        this.currentLibraryDisplay(null);
    },
    /**
     *  Toggles the visibility of the folder picker and toggles
     *  Change button text between 'Change' and 'Close'
     */
    togglePicker: function() {
        var shown = this.currentDisplay() === this.PICKER;
        if (!shown) {
            this.currentDisplay(this.PICKER);
            this.toggleChangeText('Close');
            this.activatePicker();
        } else {
            this.toggleChangeText('Change');
            this.currentDisplay(null);
            // Clear selection
            this.cancelSelection();
        }
    },
    /**
     *  Toggles the visibility of the Library picker and toggles
     *  Change button text between 'Change' and 'Close'
     */
    toggleLibraryPicker: function() {
        if (this.toggleChangeLibraryText() === 'Change') {
            this.toggleChangeLibraryText('Close');
            if (!this.loadedLibraries()) {
                this.importLibraries();
            }
        } else {
            this.toggleChangeLibraryText('Change');
        }
    },
    destroyPicker: function() {
        if (this.folderpicker) {
            this.folderpicker.destroy();
        }
    },
    doActivatePicker: function(opts) {
        var self = this;
        // Show loading indicator
        self.loading(true);
        self.folderpicker = new FolderPicker(self.folderpickerSelector, opts);
    },
    /**
     *  Activates the HGrid folder picker.
     */
    activatePicker: function() {
        var self = this;
        var opts = $.extend({}, {
            initialFolderPath: self.folder().path || '',
            // Fetch folders with AJAX
            filesData: self.urls().folders, // URL for fetching folders
            // Lazy-load each folder's contents
            // Each row stores its url for fetching the folders it contains
            oddEvenClass: {
                odd: 'addon-folderpicker-odd',
                even: 'addon-folderpicker-even'
            },
            multiselect: false,
            allowMove: false,
            ondataloaderror: function(xhr) {
                self.loading(false);
                self.changeMessage(self.messages.connectError(), 'text-danger');
                Raven.captureMessage(agh.sprintf(_('Could not GET get %1$s contents.'),self.addonName), {
                    extra: {
                        textStatus: xhr.statusText,
                        error: xhr.status
                    }
                });
            },
            ajaxOptions: {
                error: function(xhr, textStatus, error) {
                    self.loading(false);
                    self.changeMessage(self.messages.connectError(), 'text-danger');
                    Raven.captureMessage(agh.sprintf(_('Could not GET get %1$s contents.'), self.addonName ), {
                        extra: {
                            textStatus: textStatus,
                            error: error
                        }
                    });
                }
            },
            folderPickerOnload: function() {
                // Hide loading indicator
                self.loading(false);
                // Set flag to prevent repeated requests
                self.loadedFolders(true);
            },
            resolveRows: function(item) {
                item.css = '';
                return [
                {
                    data : 'name',  // Data field name
                    folderIcons : true,
                    filter : false,
                    custom : function(item, col) {
                        return m('span', item.data.name);
                    }
                },
                {
                    css : 'p-l-xs',
                    sortInclude : false,
                    custom : FolderPicker.selectView
                }
            ];
            },
            xhrconfig: $osf.setXHRAuthorization,
            lazyLoadPreprocess: function(data) {
                // Also handle data from API -- squash `attributes` to what TB expects
                // TODO: [OSF-6384] DRY this up when PR #5240 goes in
                if (data.data) {
                    return $osf.squashAPIAttributes(data);
                }
                return data;
            },
        }, self.treebeardOptions);
        self.currentDisplay(self.PICKER);
        // Only load folders if they haven't already been requested
        if (!self.loadedFolders()) {
            self.doActivatePicker(opts);
        }
    }
});

module.exports = FolderPickerViewModel;
