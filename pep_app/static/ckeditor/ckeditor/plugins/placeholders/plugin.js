CKEDITOR.plugins.add('placeholders', {
    requires: 'richcombo',
    init: function(editor) {
        // Add the combo button
        editor.ui.addRichCombo('Placeholders', {
            label: 'Placeholders',
            title: 'Insert Placeholder',
            toolbar: 'insert',
            panel: {
                css: [CKEDITOR.skin.getPath('editor')].concat(editor.config.contentsCss),
                multiSelect: false
            },

            init: function() {
                // We'll load items immediately instead of waiting for open event
                this.startGroup('Excel Columns');

                // Fetch the column names from your Django view
                var combo = this;
                var appName = editor.config.appName || 'pep_app';
                var url = '/admin/' + appName + '/emailtemplate/get_excel_columns/';

                // Add a loading placeholder
                combo.add('[Loading...]', '[Loading...]', 'Loading placeholders...');

                // Use AJAX instead of fetch for better compatibility
                var xhr = new XMLHttpRequest();
                xhr.open('GET', url, true);
                xhr.onreadystatechange = function() {
                    if (xhr.readyState === 4) {
                        if (xhr.status === 200) {
                            try {
                                var data = JSON.parse(xhr.responseText);

                                // Clear the loading placeholder
                                combo._.items = {};
                                combo._.pendingHtml = '';
                                combo._.committed = false;
                                combo.startGroup('Excel Columns');

                                // Add each column as an option
                                data.columns.forEach(function(column) {
                                    combo.add('[' + column + ']', '[' + column + ']', 'Insert ' + column + ' placeholder');
                                });
                            } catch (e) {
                                console.error('Error parsing Excel columns:', e);
                                combo.add('[Error]', '[Error]', 'Error loading placeholders');
                            }
                        } else {
                            console.error('Error fetching Excel columns:', xhr.status);
                            combo.add('[Error]', '[Error]', 'Error loading placeholders');
                        }
                    }
                };
                xhr.send();
            },

            onClick: function(value) {
                // Insert the selected placeholder
                editor.insertText(value);
            }
        });
    }
});