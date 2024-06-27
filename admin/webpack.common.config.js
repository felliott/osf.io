var webpack = require('webpack');
var path = require('path');

var root = path.resolve('..', 'website', 'static');

/** Return the absolute path given a path relative to ../website/static */
var staticPath = function(dir) {
    return path.resolve(root, dir);
};
var nodePath = function(dir) {
    return path.resolve('..', 'node_modules', dir);
};

/**
 * Each JS module for a page on the OSF is webpack entry point. These are built
 * to website/static/public/
 */
var entry = {
    // JS
    // Commons chunk
    'vendor': [
        // Vendor libraries
        'knockout',
        'knockout.validation',
        'moment',
        'bootstrap',
        // 'bootbox',
        'bootstrap-editable',
        'select2',
        // 'dropzone',
        'knockout-sortable',
        'loaders.css',
        // 'treebeard',
        'lodash.get',
        // 'js-cookie',
        'URIjs',
        // Common internal modules
        // 'js/fangorn',
        // 'js/citations',
        'js/osfHelpers',
        // 'js/osfToggleHeight',
        // 'mithril',
        // Main CSS files that get loaded above the fold
        nodePath('select2/select2.css'),
        nodePath('bootstrap/dist/css/bootstrap.css'),
        '@centerforopenscience/osf-style',
        staticPath('css/style.css'),
    ],
};


var resolve = {
    modules: [
        root,
        '../website/static/vendor/bower_components',
        'node_modules',
    ],
    extensions: ['*', '.es6.js', '.js', '.min.js'],
    // Need to alias libraries that aren't managed by bower or npm
    alias: {
        'knockout-sortable': staticPath('vendor/knockout-sortable/knockout-sortable.js'),
        'bootstrap-editable': staticPath('vendor/bootstrap-editable-custom/js/bootstrap-editable.js'),
        'jquery-blockui': staticPath('vendor/jquery-blockui/jquery.blockui.js'),
        'bootstrap': nodePath('bootstrap/dist/js/bootstrap.js'),
        'Caret.js': staticPath('vendor/bower_components/Caret.js/dist/jquery.caret.min.js'),
        'osf-panel': staticPath('vendor/bower_components/osf-panel/dist/jquery-osfPanel.min.js'),
        'jquery-qrcode': staticPath('vendor/bower_components/jquery-qrcode/jquery.qrcode.min.js'),
        'jquery-tagsinput': staticPath('vendor/bower_components/jquery.tagsinput/jquery.tagsinput.js'),
        'clipboard': staticPath('vendor/bower_components/clipboard/dist/clipboard.js'),
        // Needed for knockout-sortable
        'jquery.ui.sortable': staticPath('vendor/bower_components/jquery-ui/ui/widgets/sortable.js'),
        'truncate': staticPath('vendor/bower_components/truncate/jquery.truncate.js'),
        // Needed for ace code editor in wiki
        'ace-noconflict': staticPath('vendor/bower_components/ace-builds/src-noconflict/ace.js'),
        'ace-ext-language_tools': staticPath('vendor/bower_components/ace-builds/src-noconflict/ext-language_tools.js'),
        'ace-mode-markdown': staticPath('vendor/bower_components/ace-builds/src-noconflict/mode-markdown.js'),
        'typo': staticPath('vendor/ace-plugins/typo.js'),
        'highlight-css': nodePath('highlight.js/styles/default.css'),
        'pikaday-css': nodePath('pikaday/css/pikaday.css'),
        // Also alias some internal libraries for easy access
        'tests': staticPath('js/tests'),
    }
};

var externals = {
    // require("jquery") is external and available
    //  on the global var jQuery, which is loaded with CDN
    'jquery': 'jQuery',
    'jquery-ui': 'jQuery.ui',
    'raven-js': 'Raven',
    'MathJax': 'MathJax'
};

var plugins = [
    // Bundle common code between modules
    new webpack.optimize.CommonsChunkPlugin({ name: 'vendor', filename: 'vendor.js' }),
    // Make jQuery available in all modules without having to do require('jquery')
    new webpack.ProvidePlugin({
        $: 'jquery',
        jQuery: 'jquery'
    }),
];

var output = {
    path: path.resolve(__dirname, 'website', 'static', 'public', 'js'),
    // publicPath: '/static/', // used to generate urls to e.g. images
    filename: '[name].js',
    sourcePrefix: ''
};

module.exports = {
    entry: entry,
    resolve: resolve,
    devtool: 'source-map',
    externals: externals,
    plugins: plugins,
    output: output,
    module: {
        rules: [
            {test: /\.es6\.js$/, exclude: [/node_modules/, /bower_components/, /vendor/], loader: 'babel-loader'},
            {test: /\.css$/, use: [{loader: 'style-loader'}, {loader: 'css-loader'}]},
            // url-loader uses DataUrls; files-loader emits files
            {test: /\.png$/, loader: 'url-loader?limit=100000&mimetype=image/png'},
            {test: /\.gif$/, loader: 'url-loader?limit=10000&mimetype=image/gif'},
            {test: /\.jpg$/, loader: 'url-loader?limit=10000&mimetype=image/jpg'},
            {test: /\.woff(2)?(\?v=[0-9]\.[0-9]\.[0-9])?$/, loader: 'url-loader?mimetype=application/font-woff'},
            {test: /\.svg/, loader: 'file-loader'},
            {test: /\.eot/, loader: 'file-loader'},
            {test: /\.ttf/, loader: 'file-loader'},
            { parser: { amd: false }}
        ]
    },
    node: {
       fs: 'empty'
    }
};
