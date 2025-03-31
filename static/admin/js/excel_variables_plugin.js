   // Create this file at static/js/excel_variables_plugin.js
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
                // We'll populate this dynamically when it's opened
                this.startGroup('Excel Columns');

                // Fetch placeholders when the dropdown is opened
                this.on('open', function() {
                    const combo = this;
                    // Clear existing items first
                    combo._.items = {};
                    combo._.pendingHtml = '';

                    // Fetch the column names from your Django view
                    fetch('/admin/pep_app/emailtemplate/get_excel_columns/')
                        .then(response => response.json())
                        .then(data => {
                            // Add each column as an option
                            data.columns.forEach(column => {
                                combo.add(`[${column}]`, `[${column}]`, `Insert ${column} placeholder`);
                            });
                        })
                        .catch(error => {
                            console.error('Error fetching Excel columns:', error);
                            // Add a fallback item if fetch fails
                            combo.add('[Error loading placeholders]', '[Error]', 'Error loading placeholders');
                        });
                });
            },

            onClick: function(value) {
                // Insert the selected placeholder
                editor.insertText(value);
            }
        });
    }
});