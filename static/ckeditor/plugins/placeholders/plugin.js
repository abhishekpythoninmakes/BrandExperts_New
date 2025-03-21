CKEDITOR.plugins.add('placeholders', {
    icons: 'placeholders',
    init: function(editor) {
        // Create the main button
        editor.ui.addButton('Placeholders', {
            label: 'Insert Placeholder',
            command: 'showPlaceholders',
            toolbar: 'insert',
            icon: this.path + 'icons/placeholders.png'
        });

        // Add the dropdown command
        editor.addCommand('showPlaceholders', {
            exec: function(editor) {
                // Create simple dropdown
                var items = {};

                // Add default items
                items['first_name'] = {
                    label: 'First Name',
                    command: function() {
                        editor.insertText('{first_name}');
                    }
                };

                items['last_name'] = {
                    label: 'Last Name',
                    command: function() {
                        editor.insertText('{last_name}');
                    }
                };

                // Show the dropdown
                editor.openMenuGroup('placeholdersMenu', {
                    onClick: function(menuItem) {
                        menuItem.command();
                    },
                    items: items
                });
            }
        });
    }
});